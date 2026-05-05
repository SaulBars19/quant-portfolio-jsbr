from pathlib import Path 
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parents[1]

DATA_RAW = BASE_DIR / "data" / "raw"
DATA_PROCESSED = BASE_DIR / "data" / "processed"

DATA_RAW.mkdir(parents = True, exist_ok = True)
DATA_PROCESSED.mkdir(parents = True, exist_ok = True)

# FMP_API_KEY = os.getenv("FMP_API_KEY") # IBKR doesn't use API, uses Open TWS + Local Port 

# Project settings
START_DATE = "2016-01-01"
BASE_CURRENCY = "CHF"

# Portfolio Settings
INITIAL_CAPITAL_CHF = 5000
MAX_ASSETS = 10
MAX_WEIGHT = 0.20

# Risk Management
STOP_LOSS = -0.20
TAKE_PROFIT = 1
RISK_FREE_RATE_CHF = 0.01

# IBKR Settings 
IBKR_HOST = "127.0.0.1"
IBKR_PORT = 7497 # LIVE, 7496 PAPER
IBKR_CLIENT_ID = 1 # OR 101

# Historical Data Settings
IBKR_DURATION = "5 Y"
IBKR_BAR_SIZE = "1 day"
IBKR_WHAT_TO_SHOW = "TRADES"
IBKR_USE_RTH = 1