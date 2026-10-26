from pathlib import Path
import os
import sys

ROOT = Path(__file__).resolve().parents[1]
os.chdir(ROOT)
sys.path.insert(0, str(ROOT / "backend"))
from alembic import command
from alembic.config import Config
from app.db.seed import seed
from app.db.session import SessionLocal

command.upgrade(Config(str(ROOT / "backend" / "alembic.ini")), "head")
with SessionLocal() as db:
    seed(db)
print("Migrations and idempotent demo seed completed.")
