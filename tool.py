"""Standalone deterministic synthetic prototype. No runtime integration or domain authority."""
import argparse
import copy
import datetime
import hashlib
import json
import math
from pathlib import Path
import sys


def obj(x, keys):
    if not isinstance(x, dict) or set(x) != set(keys.split()):
        raise ValueError("object fields must be: " + keys)
    return x


def text(x):
    if not isinstance(x, str) or not x or len(x) > 2048:
        raise ValueError("expected nonempty bounded string")
    return x


def arr(x):
    if not isinstance(x, list) or len(x) > 500:
        raise ValueError("expected list of at most 500 elements")
    return x


def names(x):
    values = [text(v) for v in arr(x)]
    if len(values) != len(set(values)):
        raise ValueError("duplicate identifiers")
    return values


def num(x, minimum=0):
    if type(x) not in (int, float) or not math.isfinite(x) or x < minimum or x > 1e12:
        raise ValueError("invalid bounded number")
    return x


def integer(x, minimum=0):
    if type(x) is not int:
        raise ValueError("expected integer")
    return num(x, minimum)


def boolean(x):
    if type(x) is not bool:
        raise ValueError("expected boolean")
    return x


def unique(rows):
    ids = [text(x["id"]) for x in rows]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate record ID")


def scalar(x):
    if x is not None and type(x) not in (str, int, float, bool):
        raise ValueError("expected scalar value")
    if type(x) in (int,float) and not math.isfinite(x):
        raise ValueError("nonfinite number")
    return x


def result(**kw):
    return {"evidence_class": "simulated", "analysis_completed": True, **kw}


def analyze(payload):
    obj(payload, "spec_version evidence_class data")
    if type(payload["spec_version"]) is not int or payload["spec_version"] != 1 or payload["evidence_class"] != "simulated":
        raise ValueError("only spec_version 1 synthetic evidence_class simulated supported")
    return run(copy.deepcopy(payload["data"]))


def matches(actual, expected):
    if isinstance(expected, dict):
        return isinstance(actual, dict) and all(k in actual and matches(actual[k], v) for k,v in expected.items())
    return actual == expected


def read_json(path):
    if path.stat().st_size > 1000000:
        raise ValueError("input exceeds 1000000 bytes")
    return json.loads(path.read_text())


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", required=True, type=Path)
    p.add_argument("--output", required=True, type=Path)
    p.add_argument("--expect", type=Path, help="optional recursive subset oracle; mismatch exits 1")
    a=p.parse_args()
    try:
        if a.input.resolve() == a.output.resolve() or (a.expect and a.expect.resolve() == a.output.resolve()):
            raise ValueError("output must not overwrite input or oracle")
        output=analyze(read_json(a.input))
        expected=read_json(a.expect) if a.expect else None
        a.output.write_text(json.dumps(output,indent=2,sort_keys=True,allow_nan=False)+"\n")
        return 0 if expected is None or matches(output,expected) else 1
    except (ValueError, KeyError, TypeError, OSError, RecursionError, OverflowError) as e:
        print("invalid input: "+str(e),file=sys.stderr)
        return 2

def run(d):
    obj(d,'current_version minimum_n max_error_upper required_groups cohorts');text(d['current_version']);minimum=integer(d['minimum_n'],1);threshold=num(d['max_error_upper']);groups=names(d['required_groups']);cohorts=arr(d['cohorts'])
    if not groups or threshold>1:raise ValueError('nonempty groups and probability threshold required')
    indexed={}
    for c in cohorts:
        obj(c,'group version n errors');text(c['group']);text(c['version']);n=integer(c['n']);errors=integer(c['errors'])
        if errors>n or c['group'] in indexed:raise ValueError('invalid counts or duplicate subgroup')
        indexed[c['group']]=c
    missing=sorted(set(groups)-set(indexed));blocked=list(missing);out=[]
    for g in groups:
        if g not in indexed:continue
        c=indexed[g];n=c['n'];reasons=[];upper=None
        if c['version']!=d['current_version']:reasons.append('stale_version')
        if n<minimum:reasons.append('insufficient_n')
        if n:
            phat=c['errors']/n;z=1.959963984540054
            upper=(phat+z*z/(2*n)+z*math.sqrt(phat*(1-phat)/n+z*z/(4*n*n)))/(1+z*z/n)
            if upper>threshold:reasons.append('error_bound_exceeds_limit')
        if reasons:blocked.append(g)
        out.append({'group':g,'n':n,'errors':c['errors'],'wilson_95_upper':upper,'reasons':reasons})
    return result(status='hold' if blocked else 'eligible_for_owner_review',blocking_groups=sorted(blocked),missing_groups=missing,subgroups=out,automatic_promotion=False,statistical_limit='Approximate two-sided 95% Wilson upper endpoint; no simultaneous subgroup guarantee, independence unverified.')

if __name__ == "__main__":
    sys.exit(main())
