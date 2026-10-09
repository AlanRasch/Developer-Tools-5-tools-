"""Look up known vulnerabilities in the free OSV database (https://osv.dev)."""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

OSV_URL = "https://api.osv.dev/v1/query"


def query_osv(name: str, version: str, timeout: int = 20) -> list[dict]:
    """Return the vulnerability records for one PyPI package version."""
    body = json.dumps({"version": version, "package": {"name": name, "ecosystem": "PyPI"}}).encode("utf-8")
    request = urllib.request.Request(
        OSV_URL, data=body, method="POST",
        headers={"Content-Type": "application/json", "User-Agent": "dep-triage"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.loads(response.read().decode("utf-8")).get("vulns", [])
    except urllib.error.URLError as err:
        raise ConnectionError(f"could not reach the OSV database ({err.reason})") from err


def severity_of(vuln: dict) -> str:
    severity = (vuln.get("database_specific") or {}).get("severity")
    return severity.upper() if isinstance(severity, str) else "UNKNOWN"


def version_key(version: str) -> tuple:
    """Crude version ordering: '1.10.2' > '1.9'. Good enough for choosing an upgrade."""
    return tuple(int(part) if part.isdigit() else 0 for part in re.split(r"[.+_-]", version))


def lowest_fix(vuln: dict, current: str) -> str | None:
    """The smallest published fixed version that is newer than the one installed."""
    fixes = []
    for affected in vuln.get("affected", []):
        for rng in affected.get("ranges", []):
            for event in rng.get("events", []):
                if "fixed" in event:
                    fixes.append(event["fixed"])
    newer = [f for f in fixes if version_key(f) > version_key(current)]
    return min(newer, key=version_key) if newer else None


def cached(lookup, cache_file):
    """Wrap a lookup function so repeated runs do not query the network again."""
    import pathlib
    path = pathlib.Path(cache_file)
    store = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}

    def wrapper(name: str, version: str) -> list[dict]:
        key = f"{name}=={version}"
        if key not in store:
            store[key] = lookup(name, version)
            path.write_text(json.dumps(store, indent=2), encoding="utf-8")
        return store[key]

    return wrapper
