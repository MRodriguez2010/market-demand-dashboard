import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
DATABASE_URL = f"sqlite+aiosqlite:///{os.path.join(BASE_DIR, 'data', 'market.db')}"
SYNC_DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'data', 'market.db')}"
API_PREFIX = "/api/v1"
PORT = 8002
