#!/usr/bin/env python3
"""Assemble the multi-file OpenAPI spec and validate it as OpenAPI 3.1.

Layout (so parallel authors never collide on one file):
  openapi/root.yaml        info, servers, security, tags, components (NO paths)
  openapi/paths/*.yaml     each a map { "/path": { method: operation, ... } }
  openapi/schemas/*.yaml   each a map { SchemaName: <schema>, ... }

This script deep-merges paths/* into `paths` and schemas/* into
`components.schemas`, writes the bundled `openapi/openapi.yaml` (the
architecture-of-record artifact), then validates it. All $refs are local
(#/components/...), so no external resolution is needed after assembly.

Exit 0 = valid. Exit 1 = a real problem (duplicate path, unresolved $ref,
schema-invalid spec). Exit 2 = could not run.

Usage:
  python3 openapi/validate.py            # assemble + validate + write bundle
  python3 openapi/validate.py --check    # assemble + validate, do not write
"""
from __future__ import annotations

import glob
import os
import sys

try:
    import yaml
    from openapi_spec_validator import validate as validate_spec
except Exception as e:  # pragma: no cover
    print(f"tooling missing: {e}", file=sys.stderr)
    sys.exit(2)

HERE = os.path.dirname(os.path.abspath(__file__))


def _load(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f) or {}


def assemble() -> tuple[dict, list[str]]:
    problems: list[str] = []
    root_path = os.path.join(HERE, "root.yaml")
    if not os.path.exists(root_path):
        return {}, ["openapi/root.yaml is missing (the foundation task must create it)"]
    spec = _load(root_path)
    spec.setdefault("paths", {})
    spec.setdefault("components", {}).setdefault("schemas", {})

    for pf in sorted(glob.glob(os.path.join(HERE, "paths", "*.yaml"))):
        for path, ops in (_load(pf) or {}).items():
            if path in spec["paths"]:
                problems.append(f"duplicate path {path} (also in {os.path.basename(pf)})")
            spec["paths"][path] = ops

    for sf in sorted(glob.glob(os.path.join(HERE, "schemas", "*.yaml"))):
        for name, schema in (_load(sf) or {}).items():
            if name in spec["components"]["schemas"]:
                problems.append(f"duplicate schema {name} (also in {os.path.basename(sf)})")
            spec["components"]["schemas"][name] = schema

    return spec, problems


def check_local_refs(spec: dict) -> list[str]:
    """Every #/components/... $ref must resolve within the assembled doc."""
    bad: list[str] = []

    def walk(node, where):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == "$ref" and isinstance(v, str) and v.startswith("#/"):
                    target = spec
                    for part in v[2:].split("/"):
                        part = part.replace("~1", "/").replace("~0", "~")
                        if isinstance(target, dict) and part in target:
                            target = target[part]
                        else:
                            bad.append(f"unresolved $ref {v} (at {where})")
                            break
                else:
                    walk(v, f"{where}/{k}")
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{where}[{i}]")

    walk(spec, "")
    return bad


def main() -> int:
    write = "--check" not in sys.argv
    spec, problems = assemble()
    if not spec:
        for p in problems:
            print(f"  FAIL  {p}")
        print("VERDICT: FAIL")
        return 1

    problems += check_local_refs(spec)

    try:
        validate_spec(spec)
    except Exception as e:
        first = str(e).splitlines()[0]
        problems.append(f"OpenAPI 3.1 schema-invalid: {first}")

    n_paths = len(spec.get("paths", {}))
    n_ops = sum(
        1
        for ops in spec.get("paths", {}).values()
        for m in ops
        if m in {"get", "post", "put", "patch", "delete"}
    )
    n_schemas = len(spec.get("components", {}).get("schemas", {}))
    print(f"OpenAPI: {n_paths} paths · {n_ops} operations · {n_schemas} schemas")

    if problems:
        for p in problems:
            print(f"  FAIL  {p}")
        print("VERDICT: FAIL")
        return 1

    if write:
        out = os.path.join(HERE, "openapi.yaml")
        with open(out, "w") as f:
            yaml.safe_dump(spec, f, sort_keys=False, allow_unicode=True, width=100)
        print(f"  wrote {os.path.relpath(out)}")
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
