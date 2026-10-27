import json
import os
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
# Schema generation requires no application secrets or database connection.
os.environ.update({"AITRADER_ENV_FILE": "", "DATABASE_URL": "sqlite://"})
from app.main import app
(ROOT / "artifacts").mkdir(exist_ok=True)
(ROOT / "artifacts/openapi.json").write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
print("Exported OpenAPI; run pnpm generate-client in frontend.")
