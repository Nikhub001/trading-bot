import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_API_ID = int(os.getenv("TELEGRAM_API_ID", "0"))
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")
TELEGRAM_CHANNELS = [c.strip() for c in os.getenv("TELEGRAM_CHANNELS", "").split(",") if c.strip()]

GATE_API_KEY = os.getenv("GATE_API_KEY", "")
GATE_API_SECRET = os.getenv("GATE_API_SECRET", "")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

RISK_PERCENT = float(os.getenv("RISK_PERCENT", "15"))
LEVERAGE = int(os.getenv("LEVERAGE", "10"))
DEFAULT_STOP_PERCENT = float(os.getenv("DEFAULT_STOP_PERCENT", "2"))
DEFAULT_TP_PERCENT = float(os.getenv("DEFAULT_TP_PERCENT", "4"))
