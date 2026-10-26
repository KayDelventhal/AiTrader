"""Record installed direct dependency versions and license evidence without secrets."""
import importlib.metadata as md
import json
from pathlib import Path
import re
import yaml

ROOT = Path(__file__).resolve().parents[1]
python_sources = {
    "fastapi": "https://github.com/fastapi/fastapi", "uvicorn": "https://github.com/encode/uvicorn",
    "sqlalchemy": "https://github.com/sqlalchemy/sqlalchemy", "alembic": "https://github.com/sqlalchemy/alembic",
    "pydantic": "https://github.com/pydantic/pydantic", "pydantic-settings": "https://github.com/pydantic/pydantic-settings",
    "numpy": "https://github.com/numpy/numpy", "pandas": "https://github.com/pandas-dev/pandas",
    "numba": "https://github.com/numba/numba", "vectorbt": "https://github.com/polakowo/vectorbt",
    "langgraph": "https://github.com/langchain-ai/langgraph", "langchain-openai": "https://github.com/langchain-ai/langchain",
    "chromadb": "https://github.com/chroma-core/chroma", "lppls": "https://github.com/Boulder-Investment-Technologies/lppls",
    "celery": "https://github.com/celery/celery", "redis": "https://github.com/redis/redis-py",
    "psycopg": "https://github.com/psycopg/psycopg", "httpx": "https://github.com/encode/httpx", "feedparser": "https://github.com/kurtmckee/feedparser",
    "pytest": "https://github.com/pytest-dev/pytest", "pytest-cov": "https://github.com/pytest-dev/pytest-cov"
}
entries = []
notice = ROOT / "docs/licenses"
notice.mkdir(exist_ok=True)
for package, repo in python_sources.items():
    dist = md.distribution(package)
    license_paths = [p for p in dist.files or [] if re.search(r"(?:^|/)(?:LICENSE|LICENCE|COPYING)(?:\.|$)", str(p), re.I)]
    copies = []
    for i, path in enumerate(license_paths):
        target = notice / f"{package}-{i}.license"
        target.write_text(Path(dist.locate_file(path)).read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
        copies.append(target.relative_to(ROOT).as_posix())
    label = dist.metadata.get("License-Expression") or dist.metadata.get("License") or "See packaged license file; review required"
    if len(label) > 200: label = "See packaged license file"
    entries.append({"package": package, "version": dist.version, "repository": repo, "tag_or_commit": f"PyPI release {dist.version}; no repository code copied", "license": label, "license_files": copies, "used_paths": ["published Python distribution"], "use": "dependency", "checked_at": "2026-10-27"})

manifest = json.loads((ROOT / "frontend/package.json").read_text())
for group in ["dependencies", "devDependencies"]:
    for name in manifest[group]:
        package_file = ROOT / "frontend/node_modules" / name / "package.json"
        package = json.loads(package_file.read_text())
        manifest[group][name] = package["version"]
        repo = package.get("repository", {})
        if isinstance(repo, dict): repo = repo.get("url", "See package metadata")
        licenses = []
        for file in package_file.parent.iterdir():
            if file.is_file() and re.match(r"^(LICENSE|LICENCE|NOTICE)(\.|$)", file.name, re.I):
                target = notice / f"{name.replace('/', '-').replace('@', '')}-{file.stem}.license"
                target.write_text(file.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
                licenses.append(target.relative_to(ROOT).as_posix())
        entries.append({"package": name, "version": package["version"], "repository": repo, "tag_or_commit": f"npm release {package['version']}", "license": package.get("license", "Review required"), "license_files": licenses, "used_paths": ["published npm package"], "use": "dependency", "checked_at": "2026-10-27"})
(ROOT / "frontend/package.json").write_text(json.dumps(manifest, indent=2) + "\n")
(ROOT / "docs/source-manifest.yaml").write_text(yaml.safe_dump({"review_date": "2026-10-27", "method": "Installed release metadata and packaged license inspection. No third-party repository source copied.", "dependencies": entries}, sort_keys=False), encoding="utf-8")
print(f"Pinned {len(entries)} direct dependencies and copied packaged license evidence.")
