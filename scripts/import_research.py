"""Import up to 100 explicit source records without fetching URLs or calling models.

All payloads are schema-validated before writes. Database constraints, including
domain membership and existing request keys, are checked per record. Each record
commits with its own idempotency key, so partial completion is safe to retry.
"""
import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.db.session import SessionLocal
from app.gathering.contracts import GatheringManualImport
from app.gathering.service import import_document


def import_file(path, sessions=SessionLocal):
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not 1 <= len(payload) <= 100:
        raise ValueError("Supply a JSON array containing 1 to 100 source records")
    requests = [GatheringManualImport.model_validate(item) for item in payload]
    keys = [request.idempotency_key for request in requests]
    if len(set(keys)) != len(keys):
        raise ValueError("Each record in an import file must have a different idempotency key")
    results = []
    for request in requests:
        with sessions() as db:
            results.append(import_document(db, "owner", request))
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", type=Path, help="JSON source records to import into the configured local workspace")
    args = parser.parse_args()
    results = import_file(args.path)
    print(json.dumps({"records": len(results), "results": results}, indent=2))
