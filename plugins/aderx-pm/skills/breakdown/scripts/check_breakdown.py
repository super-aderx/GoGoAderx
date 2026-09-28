#!/usr/bin/env python3
"""Validate the issue graph in a breakdown.md.

Reads the first ```json block containing an "issues" array and checks:
  - issue ids are unique
  - every depends_on id exists
  - no dependency cycles
  - every dependency sits in an earlier wave
  - no two issues in the same wave touch overlapping paths

Exit code 0 when valid, 1 when problems are found, 2 on bad input (including issues
that are not objects with a string id, an integer wave, and string lists).
"""
import json
import re
import sys
from collections import defaultdict
from itertools import combinations


def load_graph(path):
    text = open(path, encoding="utf-8").read()
    for block in re.findall(r"```json\s*\n(.*?)```", text, re.DOTALL):
        try:
            data = json.loads(block)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and isinstance(data.get("issues"), list):
            return data
    print(f"error: no ```json block with an \"issues\" array found in {path}", file=sys.stderr)
    sys.exit(2)


def schema_errors(issues):
    """Shape problems that would make the graph checks meaningless (or crash)."""
    if not issues:
        return ["\"issues\" is empty"]
    errors = []
    for n, issue in enumerate(issues, 1):
        if not isinstance(issue, dict):
            errors.append(f"issue #{n} is not an object")
            continue
        name = issue.get("id")
        if not isinstance(name, str) or not name:
            errors.append(f"issue #{n} has no string \"id\"")
            name = f"issue #{n}"
        wave = issue.get("wave")
        if "wave" in issue and (not isinstance(wave, int) or isinstance(wave, bool)):
            errors.append(f"{name}: \"wave\" must be an integer")
        for key in ("depends_on", "touches"):
            value = issue.get(key, [])
            if not isinstance(value, list) or not all(isinstance(v, str) for v in value):
                errors.append(f"{name}: \"{key}\" must be a list of strings")
    return errors


def norm(p):
    """Strip glob suffixes so 'src/api/*' is treated as the directory 'src/api/'."""
    p = p.strip().lstrip("./")
    wild = re.search(r"[*?\[]", p)
    if wild:
        p = p[: wild.start()]
        p = p[: p.rfind("/") + 1]
    return p


def overlaps(a, b):
    a, b = norm(a), norm(b)
    if not a or not b:
        return True  # an empty/whole-repo path overlaps everything
    if a == b:
        return True
    if a.endswith("/") and b.startswith(a):
        return True
    if b.endswith("/") and a.startswith(b):
        return True
    return False


def find_cycle(issues):
    deps = {i["id"]: i.get("depends_on", []) for i in issues}
    state = {}

    def visit(n, stack):
        state[n] = 1
        for d in deps.get(n, []):
            if d not in deps:
                continue
            if state.get(d) == 1:
                return stack[stack.index(d):] + [d]
            if state.get(d) is None:
                c = visit(d, stack + [d])
                if c:
                    return c
        state[n] = 2
        return None

    for n in deps:
        if state.get(n) is None:
            c = visit(n, [n])
            if c:
                return c
    return None


def main():
    if len(sys.argv) != 2:
        print("usage: check_breakdown.py <breakdown.md>", file=sys.stderr)
        sys.exit(2)
    issues = load_graph(sys.argv[1])["issues"]
    bad = schema_errors(issues)
    if bad:
        print("error: the issue list is malformed:", file=sys.stderr)
        for e in bad:
            print(f"  - {e}", file=sys.stderr)
        sys.exit(2)
    errors = []

    ids = [i.get("id") for i in issues]
    for dup in {x for x in ids if ids.count(x) > 1}:
        errors.append(f"duplicate issue id {dup}")
    by_id = {i["id"]: i for i in issues}

    for i in issues:
        if "wave" not in i:
            errors.append(f"{i['id']}: missing wave")
        if not i.get("touches"):
            errors.append(f"{i['id']}: empty touches list — can't check for conflicts")
        for d in i.get("depends_on", []):
            if d not in by_id:
                errors.append(f"{i['id']}: depends on unknown issue {d}")
            elif by_id[d].get("wave", 0) >= i.get("wave", 0):
                errors.append(
                    f"{i['id']} (wave {i.get('wave')}) depends on {d} "
                    f"(wave {by_id[d].get('wave')}) — dependency must be in an earlier wave"
                )

    cycle = find_cycle(issues)
    if cycle:
        errors.append("dependency cycle: " + " -> ".join(cycle))

    waves = defaultdict(list)
    for i in issues:
        waves[i.get("wave", 0)].append(i)
    for w, members in waves.items():
        for a, b in combinations(members, 2):
            clashes = sorted(
                {f"{pa} ~ {pb}" for pa in a.get("touches", []) for pb in b.get("touches", []) if overlaps(pa, pb)}
            )
            if clashes:
                errors.append(
                    f"wave {w}: {a['id']} and {b['id']} touch overlapping paths: " + ", ".join(clashes)
                )

    print("Waves:")
    for w in sorted(waves):
        print(f"  wave {w}: " + ", ".join(i["id"] for i in waves[w]))
    print(f"Issues: {len(issues)} · waves: {len(waves)} · max parallel: {max(len(v) for v in waves.values())}")

    if errors:
        print(f"\n{len(errors)} problem(s):")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    print("\nOK: graph is acyclic, dependencies are ordered, and no same-wave file conflicts.")


if __name__ == "__main__":
    main()
