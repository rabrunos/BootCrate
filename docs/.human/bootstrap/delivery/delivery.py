"""Offline delivery preflight: immutable candidate identity and independent destinations.

This reference never uploads or infers remote success. Read authorized, structured
Issue receipts into a temporary JSON file and reconcile with the actual provider.
"""
from __future__ import annotations
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
from typing import Any

ENTRY = re.compile(r"^## v([^\s]+) — (.+)$")
META = re.compile(r"^<!-- change:([A-Za-z0-9_.#/-]+) audience:(public|maintainers) -->$")
ALLOWED = re.compile(r"^[^\x00-\x08\x0b-\x1f<>]+$")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf-8")


def changelog(text: str) -> list[dict]:
    """A deliberately small, human-readable Markdown grammar; unknown syntax fails."""
    versions, seen_versions, seen_changes = [], set(), set()
    current, pending = None, None
    for number, line in enumerate(text.splitlines(),1):
        line=line.rstrip()
        if not line or line == "# Changelog": continue
        match=ENTRY.fullmatch(line)
        if match:
            if pending: raise ValueError("Orphan change metadata at line " + str(number))
            version,title=match.groups()
            if version in seen_versions: raise ValueError("Duplicate changelog version")
            seen_versions.add(version)
            current={"version":version,"title":title,"changes":[]};versions.append(current)
            continue
        match=META.fullmatch(line)
        if match and current and not pending:
            pending=match.groups();continue
        if line.startswith("- ") and current:
            content=line[2:].strip()
            if not content or not ALLOWED.fullmatch(content):
                raise ValueError("Unsupported or unsafe note at line " + str(number))
            inline_tokens(content)
            change_id,audience=pending if pending else (current["version"]+"/"+str(len(current["changes"])+1),"public")
            if change_id in seen_changes: raise ValueError("Duplicate change identity")
            seen_changes.add(change_id)
            current["changes"].append({"id":change_id,"text":content,"audience":audience})
            pending=None;continue
        raise ValueError("Unsupported changelog syntax at line " + str(number))
    if pending: raise ValueError("Orphan change metadata")
    if not versions or any(not version["changes"] for version in versions):
        raise ValueError("Every formalized version needs a useful entry")
    return versions


def inline_tokens(text: str) -> list[tuple[str,str,str | None]]:
    """Tokenize the documented inline subset before any renderer rewrites it."""
    tokens=[];plain=[];index=0
    def flush():
        if plain:tokens.append(("text","".join(plain),None));plain.clear()
    while index < len(text):
        if text[index] == "\\" and index + 1 < len(text) and text[index+1] in r"\\`*[]()":
            plain.append(text[index+1]);index += 2;continue
        if text[index] == "`":
            end=text.find("`",index+1)
            if end < 0:raise ValueError("Unclosed inline code")
            flush();tokens.append(("code",text[index+1:end],None));index=end+1;continue
        if text.startswith("**",index) or text[index] == "*":
            marker="**" if text.startswith("**",index) else "*"
            end=text.find(marker,index+len(marker))
            if end < 0:raise ValueError("Unclosed emphasis")
            inner=text[index+len(marker):end]
            if not inner:raise ValueError("Empty emphasis")
            if any(kind != "text" for kind,_,_ in inline_tokens(inner)):
                raise ValueError("Nested Markdown is unsupported")
            flush();tokens.append(("strong" if marker=="**" else "emphasis",inner,None));index=end+len(marker);continue
        if text.startswith("![",index):
            close=text.find("](",index+2)
            if close >= 0:raise ValueError("Markdown images are unsupported")
        if text[index] == "[":
            close=text.find("](",index+1)
            if close >= 0:
                end=text.find(")",close+2)
                if end < 0:raise ValueError("Unclosed Markdown link")
                label=text[index+1:close];url=text[close+2:end]
                if label and not any(char in label for char in "[]`*") and re.fullmatch(r"https://[^\s()]+",url):
                    flush();tokens.append(("link",label,url));index=end+1;continue
                raise ValueError("Unsupported Markdown link")
        plain.append(text[index]);index += 1
    flush();return tokens


def plain_inline(text: str) -> str:
    pieces=[]
    for kind,value,url in inline_tokens(text):
        pieces.append(value + (" ("+url+")" if kind=="link" else ""))
    return "".join(pieces)


def render(entries: list[dict], field: str, audience: str = "public") -> str:
    if field not in {"markdown","plain","bbcode"}: raise ValueError("Unverified destination field format")
    lines=[]
    for entry in entries:
        notes=[c["text"] for c in entry["changes"] if audience == "maintainers" or c["audience"] == "public"]
        if not notes: continue
        if field == "markdown":
            lines += ["## v"+entry["version"]+" — "+entry["title"],"",*["- "+n for n in notes],""]
        elif field == "plain":
            lines += ["v"+entry["version"]+" — "+entry["title"],*["- "+plain_inline(n) for n in notes],""]
        else:
            # Use only a verified BBCode-capable field; encode all literal delimiters.
            def escape(s): return s.replace("[","&#91;").replace("]","&#93;")
            lines += ["[b]v"+escape(entry["version"])+" — "+escape(entry["title"])+"[/b]",
                      *["• "+escape(plain_inline(n)) for n in notes],""]
    return "\n".join(lines).rstrip()+"\n" if lines else ""


def identity(candidate: dict) -> str:
    if not isinstance(candidate,dict): raise ValueError("Candidate must be an object")
    required={"version","source_commit","payload_sha256","artifacts","included_changes"}
    if not required <= candidate.keys(): raise ValueError("Candidate identity incomplete")
    if type(candidate.get("integration_order")) is not int or candidate["integration_order"] < 0:
        raise ValueError("Candidate integration order missing")
    if not re.fullmatch(r"[0-9a-f]{40}",candidate["source_commit"]): raise ValueError("Invalid source commit")
    if not re.fullmatch(r"[0-9a-f]{64}",candidate["payload_sha256"]): raise ValueError("Invalid payload digest")
    changes=candidate["included_changes"]
    if not isinstance(changes,list) or any(not isinstance(change,str) for change in changes):
        raise ValueError("Candidate change identity list is invalid")
    if len(changes) != len(set(changes)):
        raise ValueError("Duplicate change in candidate")
    artifacts=candidate["artifacts"]
    if not isinstance(artifacts,dict) or not artifacts or any(not isinstance(key,str) for key in artifacts):
        raise ValueError("Candidate artifacts mapping is invalid")
    for artifact in artifacts.values():
        if not isinstance(artifact,str) or not re.fullmatch(r"[0-9a-f]{64}",artifact):
            raise ValueError("Invalid artifact digest")
    return digest(canonical(candidate))


def _observed_time(value: Any) -> datetime:
    if not isinstance(value,str) or len(value)>64:raise ValueError("Invalid receipt observation time")
    try:
        parsed=datetime.fromisoformat(value.replace("Z","+00:00"))
    except ValueError as error:
        raise ValueError("Invalid receipt observation time") from error
    if parsed.tzinfo is None:raise ValueError("Receipt observation time needs a timezone")
    return parsed


def _receipt_identity(receipt: dict) -> tuple:
    required=("attempt_id","destination","channel","version","candidate_id","artifact_sha256","notes_sha256")
    if any(not isinstance(receipt.get(key),str) or not receipt[key] for key in required):
        raise ValueError("Receipt attempt identity is incomplete")
    if not re.fullmatch(r"[0-9a-f]{64}",receipt["candidate_id"]):
        raise ValueError("Receipt candidate identity is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}",receipt["artifact_sha256"]):
        raise ValueError("Receipt artifact digest is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}",receipt["notes_sha256"]):
        raise ValueError("Receipt notes digest is invalid")
    if type(receipt.get("integration_order")) is not int or receipt["integration_order"]<0:
        raise ValueError("Receipt integration order missing")
    changes=receipt.get("included_changes")
    if not isinstance(changes,list) or any(not isinstance(item,str) for item in changes) or len(changes)!=len(set(changes)):
        raise ValueError("Receipt change identity list is invalid")
    return tuple(receipt[key] for key in required)+(receipt["integration_order"],tuple(changes))


def reduce_receipts(receipts: list[dict]) -> tuple[list[dict] | None,str | None]:
    """Project event history without letting a later error erase a confirmation."""
    attempts={}
    for index,receipt in enumerate(receipts):
        if (not isinstance(receipt,dict) or receipt.get("schema")!="bootcrate-receipt/v1" or
            receipt.get("status") not in {"confirmed","failed","pending","unknown"} or
            not isinstance(receipt.get("observed_by"),str) or not receipt["observed_by"] or
            not isinstance(receipt.get("evidence_ref"),str) or not receipt["evidence_ref"]):
            return None,"Receipt lacks identified evidence or has unknown format"
        try:
            identity_value=_receipt_identity(receipt);observed=_observed_time(receipt.get("observed_at"))
        except ValueError as error:
            return None,str(error)
        attempt=receipt["attempt_id"]
        if attempt in attempts and attempts[attempt]["identity"]!=identity_value:
            return None,"Attempt identity changed across receipt events"
        row=attempts.setdefault(attempt,{"identity":identity_value,"events":[]})
        row["events"].append((observed,index,receipt))
    reduced=[]
    for row in attempts.values():
        ordered=[item[2] for item in sorted(row["events"],key=lambda item:(item[0],item[1]))]
        definitive={event["status"] for event in ordered if event["status"] in {"confirmed","failed"}}
        if definitive=={"confirmed","failed"}:
            return None,"Contradictory confirmed/failed events require reconciliation"
        if "confirmed" in definitive:
            reduced.append(next(event for event in reversed(ordered) if event["status"]=="confirmed"))
        elif ordered[-1]["status"] in {"pending","unknown"}:
            reduced.append(ordered[-1])
        elif "failed" in definitive:
            reduced.append(next(event for event in reversed(ordered) if event["status"]=="failed"))
        else:
            reduced.append(ordered[-1])
    return reduced,None


def plan(candidate: dict, receipts: list[dict], target: dict, entries: list[dict]) -> dict:
    """Return READY, SKIP or BLOCK; no provider mutation or ledger state is inferred."""
    cid=identity(candidate)
    key=(target["id"],target["channel"])
    if key[0] not in candidate["artifacts"]: raise ValueError("Target artifact absent from candidate")
    if target["field"] not in {"markdown","plain","bbcode"}: raise ValueError("Destination field must be verified")
    if not isinstance(receipts,list) or len(receipts)>10000:
        raise ValueError("Expected a bounded receipt event list")
    # Validate attempts globally so one ID cannot be reused for another destination/channel.
    reduced,problem=reduce_receipts(receipts)
    if problem:return {"status":"BLOCK","reason":problem}
    matches=[r for r in reduced if (r.get("destination"),r.get("channel"))==key]
    # The caller must additionally check Issue authorship and the provider's actual state.
    if any(r.get("status") in {"unknown","pending"} for r in matches):
        return {"status":"BLOCK","reason":"Reconcile pending/unknown remote outcome before retry"}
    confirmed=[r for r in matches if r.get("status")=="confirmed"]
    ordered=sorted(confirmed,key=lambda r:r["integration_order"])
    for previous,current in zip(ordered,ordered[1:]):
        if previous["integration_order"] == current["integration_order"]:
            if (previous["candidate_id"],previous["artifact_sha256"],previous["version"],
                set(previous["included_changes"]),previous["notes_sha256"]) != (
                current["candidate_id"],current["artifact_sha256"],current["version"],
                set(current["included_changes"]),current["notes_sha256"]):
                return {"status":"BLOCK","reason":"Ambiguous confirmed integration order requires reconciliation"}
        elif not set(previous["included_changes"]) <= set(current["included_changes"]):
            return {"status":"BLOCK","reason":"Confirmed integration history is not cumulative"}
    if any(r.get("integration_order",-1)>=candidate["integration_order"] and r.get("version")!=candidate["version"] for r in confirmed):
        return {"status":"BLOCK","reason":"Later candidate active; rollback requires separate authorization"}
    # A confirmed receipt does not waive the candidate's canonical history.
    version_index=next((index for index,entry in enumerate(entries)
                        if entry.get("version")==candidate["version"]),None)
    if version_index is None:
        return {"status":"BLOCK","reason":"Candidate version has no canonical changelog entry"}
    version_entry=entries[version_index]
    eligible_entries=entries[version_index:] # candidate and older, excluding newer entries
    version_changes={change["id"] for change in version_entry["changes"]}
    if not version_changes <= set(candidate["included_changes"]):
        return {"status":"BLOCK","reason":"Candidate omits a change from its formalized version entry"}
    known_changes={change["id"] for entry in eligible_entries for change in entry["changes"]}
    if not set(candidate["included_changes"]) <= known_changes:
        return {"status":"BLOCK","reason":"Candidate references a later or missing changelog change"}
    same=[r for r in confirmed if r.get("version")==candidate["version"]]
    if same:
        if any(r.get("candidate_id") != cid or r.get("artifact_sha256") != candidate["artifacts"][key[0]] for r in same):
            return {"status":"BLOCK","reason":"Same version has different confirmed bytes"}
        if any(r["integration_order"] != candidate["integration_order"] or
               r["included_changes"] != candidate["included_changes"] for r in same):
            return {"status":"BLOCK","reason":"Same candidate receipt has inconsistent integration metadata"}
        prior=[r for r in confirmed if r["integration_order"]<candidate["integration_order"]]
        baseline=max(prior,key=lambda r:r["integration_order"]) if prior else None
    elif not confirmed and target.get("baseline") != "never_published":
        return {"status":"BLOCK","reason":"Unknown baseline; verify destination history first"}
    elif confirmed:
        # Sequence is a confirmed integration order, not lexicographic version sorting.
        if any(type(r.get("integration_order")) is not int for r in confirmed):
            return {"status":"BLOCK","reason":"Receipt integration order missing"}
        baseline=max(confirmed,key=lambda r:r["integration_order"])
        if not set(baseline.get("included_changes",[])) <= set(candidate["included_changes"]):
            return {"status":"BLOCK","reason":"Candidate does not contain the confirmed baseline"}
        if baseline["integration_order"] >= candidate.get("integration_order",-1):
            return {"status":"BLOCK","reason":"Later or equal candidate already active; rollback requires separate authorization"}
    else:
        baseline=None
    already=set(baseline["included_changes"]) if baseline else set()
    selected=[];selected_ids=[]
    for entry in reversed(eligible_entries): # candidate and older entries, oldest first
        changes=[]
        for change in entry["changes"]:
            if change["id"] in candidate["included_changes"] and change["id"] not in already:
                changes.append(change);selected_ids.append(change["id"])
        if changes:selected.append({**entry,"changes":changes})
    if set(selected_ids) != (set(candidate["included_changes"])-already):
        return {"status":"BLOCK","reason":"Candidate references a missing changelog change"}
    notes=render(selected,target["field"],target.get("audience","public"))
    if len(notes.encode("utf-8")) > target.get("max_bytes",65536):
        return {"status":"BLOCK","reason":"Notes exceed verified destination field limit"}
    notes_sha256=digest(notes.encode("utf-8"))
    if same:
        if any(r["notes_sha256"]!=notes_sha256 for r in same):
            return {"status":"BLOCK","reason":"Same candidate has different confirmed notes"}
        return {"status":"SKIP","reason":"Same candidate, package and notes already confirmed"}
    return {"status":"READY","candidate_id":cid,"destination":key[0],"channel":key[1],
            "artifact_sha256":candidate["artifacts"][key[0]],"baseline":baseline["version"] if baseline else "never_published",
            "included_changes":list(candidate["included_changes"]),"new_change_ids":selected_ids,
            "notes":notes,"notes_sha256":notes_sha256,
            "warning":"Preview only; verify provider state and authorize the exact operation separately"}


def read_input(path: Path, limit: int = 1024 * 1024) -> str:
    """Read only a bounded regular file, without following a leaf symlink."""
    before = path.lstat()
    reparse = (getattr(before, "st_file_attributes", 0) &
               getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0))
    if not stat.S_ISREG(before.st_mode) or reparse:
        raise ValueError("Input must be a regular, unlinked file")
    if before.st_size > limit:
        raise ValueError("Input exceeds 1 MiB")
    flags = (os.O_RDONLY | getattr(os, "O_NONBLOCK", 0) |
             getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0))
    with os.fdopen(os.open(path, flags), "rb") as stream:
        opened = os.fstat(stream.fileno())
        if (not stat.S_ISREG(opened.st_mode) or opened.st_size > limit or
                (opened.st_dev, opened.st_ino) != (before.st_dev, before.st_ino)):
            raise ValueError("Input changed or exceeds 1 MiB")
        content = stream.read(limit + 1)
    if len(content) > limit:
        raise ValueError("Input exceeds 1 MiB")
    return content.decode("utf-8")


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--candidate",required=True,type=Path)
    p.add_argument("--receipts",required=True,type=Path)
    p.add_argument("--target",required=True,type=Path)
    p.add_argument("--changelog",required=True,type=Path)
    a=p.parse_args()
    try:
        result=plan(json.loads(read_input(a.candidate)),json.loads(read_input(a.receipts)),
                    json.loads(read_input(a.target)),changelog(read_input(a.changelog)))
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0 if result["status"] in {"READY","SKIP"} else 2
    except (OSError,ValueError,TypeError,KeyError) as error:
        print("BLOCKED: " + str(error),file=sys.stderr);return 2


if __name__=="__main__":raise SystemExit(main())
