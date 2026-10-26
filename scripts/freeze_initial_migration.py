"""One-time development utility: freeze the initial metadata into explicit DDL."""
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from sqlalchemy import create_engine
from alembic.migration import MigrationContext
from alembic.autogenerate import produce_migrations, render_python_code
from app.db.models import Base

target = ROOT / "backend/migrations/versions/0001_initial.py"
if "Base.metadata.create_all" not in target.read_text():
    raise SystemExit("Initial migration already frozen; create a new revision for further changes.")
with create_engine("sqlite://").connect() as connection:
    changes = produce_migrations(MigrationContext.configure(connection), Base.metadata)
    code = render_python_code(changes.upgrade_ops)
target.write_text('"""Initial immutable demo schema."""\nfrom alembic import op\nimport sqlalchemy as sa\n\nrevision = "0001"\ndown_revision = None\nbranch_labels = None\ndepends_on = None\n\ndef upgrade():\n' + code + '\n\ndef downgrade():\n    raise RuntimeError("Destructive downgrade is disabled; restore a reviewed backup instead.")\n', encoding="utf-8")
print("Initial migration frozen as explicit DDL.")
