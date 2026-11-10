import io
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app import database, main


class DashboardTest(unittest.TestCase):
    def test_fresh_dashboard_and_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = create_async_engine(f"sqlite+aiosqlite:///{directory}/market.db")
            session = async_sessionmaker(engine, expire_on_commit=False)
            with patch.object(database, "engine", engine), patch.object(database, "async_session", session), \
                 patch.object(main, "async_session", session), patch.object(main, "BASE_DIR", directory), \
                 TestClient(main.app) as client:
                overview = client.get("/api/v1/dashboard/overview").json()
                self.assertEqual(overview["total_signals"], 20 * 8 * 12)
                self.assertEqual(len(client.get("/api/v1/dashboard/heatmap?category_id=1").json()), 20)
                for fmt, member in [("pdf", None), ("pptx", "ppt/presentation.xml"), ("xlsx", "xl/workbook.xml")]:
                    response = client.post("/api/v1/reports/generate", json={"format": fmt})
                    self.assertEqual(response.status_code, 200)
                    if member:
                        with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
                            self.assertIn(member, archive.namelist())
                    else:
                        self.assertTrue(response.content.startswith(b"%PDF"))
