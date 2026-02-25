from __future__ import annotations

import os
from typing import Annotated, TypedDict

from dotenv import load_dotenv
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from src.agent.prompts import SYSTEM_PROMPT
from src.agent.tools import get_db_schema, execute_sql
from src.config import MODEL, AGENT_RECURSION_LIMIT

load_dotenv()

# ── Tools ──────────────────────────────────────────────────────────────────────
TOOLS = [get_db_schema, execute_sql]

MAX_SQL_RETRIES = 3  # Max consecutive SQL errors before giving up

# ── State ──────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    retry_count: int
    sql_steps: list[str]   # Accumulate SQL queries for transparency


# ── LLM ────────────────────────────────────────────────────────────────────────
def _build_llm() -> ChatOpenAI:
    return ChatOpenAI(model=MODEL, temperature=0).bind_tools(TOOLS)


# ── Nodes ──────────────────────────────────────────────────────────────────────

def agent_node(state: AgentState) -> dict:
    """Calls the LLM with current message history."""
    llm = _build_llm()
    messages = [SystemMessage(content=SYSTEM_PROMPT)] + state["messages"]
    response = llm.invoke(messages)
    return {"messages": [response]}


def tools_node_with_tracking(state: AgentState) -> dict:
    """Executes tool calls, tracks SQL queries, and counts consecutive SQL errors."""
    from langchain_core.messages import ToolMessage

    last_message = state["messages"][-1]
    tool_calls = last_message.tool_calls if hasattr(last_message, "tool_calls") else []

    sql_steps = list(state.get("sql_steps", []))
    retry_count = state.get("retry_count", 0)
    tool_messages = []
    had_sql_error = False

    for tc in tool_calls:
        tool_name = tc["name"]
        tool_args = tc["args"]

        # Track SQL queries
        if tool_name == "execute_sql":
            sql = tool_args.get("query", "")
            sql_steps.append(sql)

        # Execute the tool
        try:
            if tool_name == "get_db_schema":
                result = get_db_schema.invoke(tool_args)
            elif tool_name == "execute_sql":
                result = execute_sql.invoke(tool_args)
            else:
                result = f"Unknown tool: {tool_name}"
        except Exception as e:
            result = f"ERROR: Tool execution failed: {e}"

        result_str = str(result)

        # Track consecutive SQL errors
        if tool_name == "execute_sql":
            if result_str.startswith("ERROR:"):
                had_sql_error = True
            else:
                retry_count = 0  # Reset on success

        tool_messages.append(
            ToolMessage(content=result_str, tool_call_id=tc["id"])
        )

    if had_sql_error:
        retry_count += 1

    return {"messages": tool_messages, "sql_steps": sql_steps, "retry_count": retry_count}


# ── Routing ────────────────────────────────────────────────────────────────────

def should_continue(state: AgentState) -> str:
    """Routes to tools, end, or fail node after too many SQL errors."""
    if state.get("retry_count", 0) >= MAX_SQL_RETRIES:
        return "fail"
    last_message = state["messages"][-1]
    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        return "tools"
    return END


def fail_node(state: AgentState) -> dict:
    """Injected when the agent exceeds MAX_SQL_RETRIES consecutive SQL errors."""
    msg = AIMessage(
        content=(
            "Não consegui executar uma consulta SQL válida após "
            f"{MAX_SQL_RETRIES} tentativas. "
            "Por favor, reformule sua pergunta ou tente novamente."
        )
    )
    return {"messages": [msg]}


# ── Build Graph ────────────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)
    graph.add_node("tools", tools_node_with_tracking)
    graph.add_node("fail", fail_node)

    graph.add_edge(START, "agent")
    graph.add_conditional_edges(
        "agent",
        should_continue,
        {"tools": "tools", "fail": "fail", END: END},
    )
    graph.add_edge("tools", "agent")
    graph.add_edge("fail", END)

    return graph.compile()


# ── Public API ─────────────────────────────────────────────────────────────────

def run_agent(question: str, chat_history: list[dict] | None = None) -> dict:
    """
    Runs the agent for a given user question.

    Args:
        question:     The current question in natural language.
        chat_history: Previous turns as list of {"role": "user"|"assistant", "content": str}.
                      Injected as context before the current question so the agent
                      can answer follow-up questions (e.g. "e em 2023?").

    Returns:
        {
            "answer": str,          # The final natural language answer
            "sql_steps": list[str], # SQL queries executed
            "last_result": dict,    # Last SQL result {columns, rows} or None
        }
    """
    graph = build_graph()

    # Build context messages from prior turns (user + assistant text only)
    context_messages: list[BaseMessage] = []
    if chat_history:
        for turn in chat_history:
            role = turn.get("role", "")
            content = turn.get("content", "")
            if not content:
                continue
            if role == "user":
                context_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                context_messages.append(AIMessage(content=content))

    initial_state: AgentState = {
        "messages": context_messages + [HumanMessage(content=question)],
        "retry_count": 0,
        "sql_steps": [],
    }

    final_state = graph.invoke(initial_state, {"recursion_limit": AGENT_RECURSION_LIMIT})

    # Extract answer from last AI message
    answer = ""
    for msg in reversed(final_state["messages"]):
        if isinstance(msg, AIMessage) and msg.content:
            answer = msg.content
            break

    # Try to extract the last SQL result from tool messages
    last_result = None
    import json
    for msg in reversed(final_state["messages"]):
        from langchain_core.messages import ToolMessage
        if isinstance(msg, ToolMessage):
            try:
                data = json.loads(msg.content)
                if "columns" in data and "rows" in data:
                    last_result = data
                    break
            except (json.JSONDecodeError, Exception):
                pass

    return {
        "answer": answer,
        "sql_steps": final_state.get("sql_steps", []),
        "last_result": last_result,
    }


def stream_agent_response(question: str, chat_history: list[dict] | None = None):
    """
    Streaming generator — yields events for real-time display in Streamlit.

    Event types:
      {"type": "token",  "content": str}
      {"type": "done",   "sql_steps": list, "last_result": dict|None, "answer": str}
      {"type": "error",  "content": str}

    Uses stream_mode=["messages", "updates"]:
      - "messages" → token-level LLM output for streaming text
      - "updates"  → graph state diffs to reliably capture sql_steps and last_result
    """
    import json as _json
    from langchain_core.messages import AIMessageChunk, ToolMessage as _TMsg

    graph = build_graph()

    # Build context from chat history
    context_messages: list[BaseMessage] = []
    if chat_history:
        for turn in chat_history:
            role = turn.get("role", "")
            content = turn.get("content", "")
            if not content:
                continue
            if role == "user":
                context_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                context_messages.append(AIMessage(content=content))

    initial_state: AgentState = {
        "messages": context_messages + [HumanMessage(content=question)],
        "retry_count": 0,
        "sql_steps": [],
    }

    sql_steps: list[str] = []
    last_result = None
    full_answer = ""

    try:
        for mode, data in graph.stream(
            initial_state,
            config={"recursion_limit": AGENT_RECURSION_LIMIT},
            stream_mode=["messages", "updates"],
        ):
            # ── Token streaming (messages mode) ───────────────────────────────
            if mode == "messages":
                chunk, metadata = data
                if (
                    isinstance(chunk, AIMessageChunk)
                    and chunk.content
                    and not getattr(chunk, "tool_call_chunks", None)
                ):
                    full_answer += chunk.content
                    yield {"type": "token", "content": chunk.content}

            # ── State updates (updates mode) ───────────────────────────────────
            elif mode == "updates":
                for node_name, node_update in data.items():
                    # Capture accumulated sql_steps from tools node
                    if "sql_steps" in node_update:
                        sql_steps = node_update["sql_steps"]

                    # Capture last SQL result from ToolMessages
                    for msg in node_update.get("messages", []):
                        if isinstance(msg, _TMsg):
                            try:
                                parsed = _json.loads(msg.content)
                                if isinstance(parsed, dict) and "columns" in parsed and "rows" in parsed:
                                    last_result = parsed
                            except (_json.JSONDecodeError, Exception):
                                pass

        yield {
            "type": "done",
            "sql_steps": sql_steps,
            "last_result": last_result,
            "answer": full_answer,
        }

    except Exception as e:
        yield {"type": "error", "content": str(e)}
