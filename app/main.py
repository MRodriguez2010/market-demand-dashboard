import sqlite3
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .config import API_PREFIX
from .database import init_db, async_session

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    # Check if already seeded using sync sqlite3
    db_path = os.path.join(BASE_DIR, "data", "market.db")
    needs_seed = True
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        try:
            count = conn.execute("SELECT COUNT(*) FROM regions").fetchone()[0]
            needs_seed = count == 0
        except Exception:
            needs_seed = True
        finally:
            conn.close()
    if needs_seed:
        from .seed import seed_data
        async with async_session() as session:
            await seed_data(session)
    yield

app = FastAPI(title="Local Market Demand Heatmap", version="1.0.0", lifespan=lifespan)


from .routes import router as dashboard_router
from .reports import router as reports_router
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(reports_router, prefix=API_PREFIX)

static_dir = os.path.join(BASE_DIR, "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/")
async def root():
    return FileResponse(os.path.join(static_dir, "index.html"))
