"""Read-only gate over work target assignments exported from their existing Issues.

This cannot reserve a target atomically or authorize a merge. A single coordinator
must serialize assignment/integration and recheck the actual remote HEAD.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import re
import sys

TARGET = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.+_-]{0,63}$")
SHA = re.compile(r"^[0-9a-f]{40}$")
STATUSES = {"assigned", "abandoned", "accepted", "integrated"}


def assignment(records: list[dict], issue: str, target: str,
               expected_head: str, observed_head: str) -> dict:
    if not isinstance(records, list) or len(records) > 10000:
        raise ValueError("Expected a bounded list of Issue assignment records")
    if not isinstance(issue, str) or not re.fullmatch(r"#[1-9][0-9]*",issue):
        raise ValueError("Issue must be an existing identified work item")
    if not isinstance(target, str) or not TARGET.fullmatch(target):
        raise ValueError("Invalid native work version")
    if any(not isinstance(s,str) or not SHA.fullmatch(s) for s in (expected_head, observed_head)):
        raise ValueError("Expected and observed remote HEAD must be full commit IDs")
    if expected_head != observed_head:
        return {"status":"BLOCK","reason":"Remote HEAD changed; refresh Issue evidence and integration basis"}
    reserved = {}
    for row in records:
        if not isinstance(row,dict) or not isinstance(row.get("issue"),str) or not re.fullmatch(r"#[1-9][0-9]*",row["issue"]) or not isinstance(row.get("target"),str) or not TARGET.fullmatch(row["target"]) or row.get("status") not in STATUSES:
            raise ValueError("Invalid Issue assignment record")
        if row["target"] in reserved and reserved[row["target"]] != row["issue"]:
            return {"status":"BLOCK","reason":"Conflicting assignment history requires reconciliation"}
        reserved[row["target"]] = row["issue"]
    if target in reserved and reserved[target] != issue:
        return {"status":"BLOCK","reason":"Work version already reserved by another Issue, including abandoned work"}
    own = [row for row in records if row["issue"] == issue and row["target"] == target]
    if any(row["status"] in {"abandoned","accepted","integrated"} for row in own):
        return {"status":"BLOCK","reason":"Finished or abandoned work target cannot be silently reopened"}
    if any(row["issue"] == issue and row["status"] == "assigned" and row["target"] != target for row in records):
        return {"status":"BLOCK","reason":"Same Issue has a different active work target"}
    return {"status":"READY","issue":issue,"target":target,"remote_head":observed_head,
            "operation":"continue" if own else "propose",
            "warning":"Read-only preview; record assignment in the Issue through the authorized single writer"}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--assignments",required=True,type=Path)
    p.add_argument("--issue",required=True)
    p.add_argument("--target",required=True)
    p.add_argument("--expected-head",required=True)
    p.add_argument("--observed-head",required=True)
    args=p.parse_args()
    try:
        if args.assignments.stat().st_size > 1024*1024:raise ValueError("Input exceeds 1 MiB")
        result=assignment(json.loads(args.assignments.read_text()),args.issue,args.target,
                          args.expected_head,args.observed_head)
        print(json.dumps(result,indent=2));return 0 if result["status"]=="READY" else 2
    except (ValueError,OSError,TypeError) as error:
        print("BLOCKED: "+str(error),file=sys.stderr);return 2


if __name__=="__main__":raise SystemExit(main())
