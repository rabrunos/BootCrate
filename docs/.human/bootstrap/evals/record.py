"""Validate external eval evidence; never run a model or create a fake observation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
from jsonschema import Draft202012Validator

HERE=Path(__file__).resolve().parent


def check(run: dict) -> list[str]:
    schema=json.loads((HERE/'eval-run.schema.json').read_text())
    errors=[str(error.message) for error in Draft202012Validator(schema).iter_errors(run)]
    if errors:return errors
    catalog={s['id'] for s in json.loads((HERE/'scenarios.json').read_text())['scenarios']}
    if run['identity']['scenario_id'] not in catalog:errors.append('Scenario not in current catalog')
    if run['identity']['modality'] in {'L2','L3'} and not run['observations']:
        errors.append('Real planning/execution requires actual observable traces')
    if run['identity']['modality']=='L3' and not run['checks']:
        errors.append('Materialization requires external checks')
    if run['outcome']=='completed' and any(x['status'] in {'fail','blocked','not_run'} for x in run['checks']):
        errors.append('Completed outcome conflicts with required checks; review applicability')
    if run['identity']['modality'] in {'L2','L3'} and run['identity']['executor']=='none':
        errors.append('Real model evaluation cannot have executor=none')
    return errors


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('result',type=Path);args=p.parse_args()
    try:
        if args.result.stat().st_size>1024*1024:raise ValueError('Result exceeds 1 MiB')
        run=json.loads(args.result.read_text());errors=check(run)
        for error in errors:print('FAIL:',error)
        if not errors:print('PASS: shape/consistency only; independent evidence must still be reviewed')
        return int(bool(errors))
    except (OSError,ValueError,TypeError) as error:
        print('BLOCKED:',error,file=sys.stderr);return 2


if __name__=='__main__':raise SystemExit(main())
