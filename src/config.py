"""
config.py – Centralized configuration for DataPilot.
All environment variables and constants live here.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

_ENV_FILE = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_ENV_FILE, override=True)

# ── Paths ──────────────────────────────────────────────────────────────────────
ROOT_DIR = Path(__file__).parent.parent
DATA_DIR = ROOT_DIR / "data"
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "anexo_desafio_1.db"))

# ── LLM ────────────────────────────────────────────────────────────────────────
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL = os.getenv("MODEL", "gpt-4o-mini")
AGENT_RECURSION_LIMIT = int(os.getenv("AGENT_RECURSION_LIMIT", "25"))

# ── App ────────────────────────────────────────────────────────────────────────
APP_TITLE = "DataPilot – Assistente de Dados"
APP_ICON  = None
APP_VERSION = "1.0"

EXAMPLE_QUESTIONS = [
    "Liste os 5 estados com maior número de clientes que compraram via app em maio",
    "Quantos clientes interagiram com campanhas de WhatsApp em 2024?",
    "Quais categorias de produto tiveram o maior número de compras em média por cliente?",
    "Qual o número de reclamações não resolvidas por canal?",
    "Qual a tendência de reclamações por canal no último ano?",
]
