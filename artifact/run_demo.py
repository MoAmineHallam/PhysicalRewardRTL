"""Reproduce the RF-SFT supplement from archived draws; optionally simulate the RTL pair."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys
import time

ROOT=Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def sha(data):
    return hashlib.sha256(data).hexdigest()


def require(condition,message):
    if not condition: raise RuntimeError(message)


def reproduce(root=ROOT):
    import numpy as np
    manifest=read(root/'SHA256SUMS.json')
    for name,expected in manifest.items():
        require(sha((root/name).read_bytes())==expected,'Changed input: '+name)
    split=read(root/'data/sealed_split.json')['designs']
    expected=read(root/'data/expected.json')
    identity=expected['identity']
    physics={p.stem:read(p) for p in (root/'data/physical').glob('*.json')}
    rows=[]
    for arm in ('sft','rf'):
        for seed in (1,2):
            directory=root/'data/draws'/f'{arm}_{seed}'
            names={f"{d['design']}__{i:02d}.json" for d in split for i in range(24)}
            require({p.name for p in directory.glob('*.json')}==names,'Missing or extra draws')
            for design in split:
                for draw in range(24):
                    row=read(directory/f"{design['design']}__{draw:02d}.json")
                    for k,v in dict(identity=identity,arm=arm,replicate=seed,design=design['design'],draw=draw).items():
                        require(row[k]==v,'Draw identity mismatch: '+k)
                    require(isinstance(row['correct'],bool),'Missing oracle verdict')
                    score=0.
                    if row.get('rtl') is not None:
                        require(sha(row['rtl'].encode())==row['rtl_sha256'],'RTL hash mismatch')
                    if row['correct']:
                        require(row['oracle']['correct'],'Missing functional evidence')
                        key=sha((row['design']+'\0'+row['rtl']).encode())
                        result=physics[key]
                        require(result['identity']==identity and result['key']==key,'Physical identity mismatch')
                        require(result['rtl_sha256']==row['rtl_sha256'],'Physical RTL mismatch')
                        require(result['status'] in ('COMPLETE','FAILED'),'Unfinished implementation')
                        score=float(result['closure_fmax_mhz'])
                        require(math.isfinite(score) and score>=0,'Invalid endpoint')
                        if result['status']=='FAILED': require(score==0,'Failed implementation must score zero')
                        else:
                            require(math.isclose(score,1000/result['loose_passing_period_ns'],rel_tol=1e-10),'Endpoint is not the passing bracket boundary')
                            require(any(t['closed'] and t['valid_measurement'] and math.isclose(t['period_ns'],result['loose_passing_period_ns'],rel_tol=1e-10) for t in result['trials']),'No passing boundary evidence')
                        row['physical_key']=key
                    row['score']=score
                    rows.append(row)
    arms={}; per_design={}; selection={}
    for arm in ('sft','rf'):
        group=[r for r in rows if r['arm']==arm]
        per_design[arm]=[float(np.mean([r['score'] for r in group if r['design']==d['design']])) for d in split]
        arms[arm]=dict(mean_mhz=float(np.mean(per_design[arm])),passed=sum(r['correct'] for r in group),total=len(group),
            correctness=float(np.mean([r['correct'] for r in group])),
            per_replicate_mhz={str(s):float(np.mean([r['score'] for r in group if r['replicate']==s])) for s in (1,2)})
        for name in ('mean_mhz','correctness'):
            require(math.isclose(arms[arm][name],expected['arms'][arm][name],abs_tol=1e-10),'Aggregate does not reproduce: '+arm+'/'+name)
        selection[arm]={}
        for n in (1,4,8,24):
            means=[]
            for d in split:
                maxima=[]
                for s in (1,2):
                    ordered=sorted([r for r in group if r['design']==d['design'] and r['replicate']==s],key=lambda r:r['draw'])
                    maxima.extend(max(r['score'] for r in ordered[i:i+n]) for i in range(0,24,n))
                means.append(float(np.mean(maxima)))
            selection[arm][str(n)]=float(np.mean(means))
            require(math.isclose(selection[arm][str(n)],expected['best_of_n'][arm][str(n)]['mean_mhz'],abs_tol=1e-10),'Selection curve does not reproduce')
    diffs=np.array(per_design['rf'])-np.array(per_design['sft'])
    strata=defaultdict(list)
    for i,d in enumerate(split): strata[(d['family'],d['regime'])].append(i)
    rng=np.random.default_rng(20260915); totals=np.zeros(100000)
    for indices in strata.values():
        draws=rng.choice(indices,size=(100000,len(indices)),replace=True)
        totals+=diffs[draws].sum(axis=1)
    paired=dict(mean_mhz=float(diffs.mean()),interval95=[float(x) for x in np.quantile(totals/len(split),[.025,.975])])
    for actual,wanted in zip([paired['mean_mhz'],*paired['interval95']],
                             [expected['paired']['mean_mhz'],*expected['paired']['interval95']]):
        require(math.isclose(actual,wanted,abs_tol=1e-10),'Paired inference does not reproduce')
    demo=read(root/'demo/demo.json')
    for arm,item in demo['candidates'].items():
        matching=[r for r in rows if r['arm']==arm and r['design']==demo['design']]
        counts=Counter(r['rtl_sha256'] for r in matching if r['correct'])
        require(counts[item['rtl_sha256']]==item['multiplicity'],'Demo multiplicity mismatch')
        require(item['rtl_sha256']==min(counts,key=lambda k:(-counts[k],k)),'Demo is not the deterministic modal passing candidate')
        require(sha((root/item['rtl_file']).read_bytes())==item['rtl_sha256'],'Demo RTL changed')
        require(physics[item['physical_key']]['closure_fmax_mhz']==item['frequency_mhz'],'Demo timing mismatch')
    output=dict(status='PASS',designs=[d['design'] for d in split],arms=arms,paired=paired,
        per_design_mhz=per_design,best_of_n=selection,
        unique_physical_candidates=len(physics),physical_failures=sum(p['status']=='FAILED' for p in physics.values()),
        demo=demo,scope='Archived-output reproduction, not retraining, new routing, full timing signoff, or a test of circuit novelty.')
    return output


def simulate(root=ROOT):
    sys.path.insert(0,str(root/'research'))
    from functional import check
    demo=read(root/'demo/demo.json');results={}
    for arm,item in demo['candidates'].items():
        result=check((root/item['rtl_file']).read_text(),demo['design'])
        require(result['correct'],'Demo candidate failed the shared simulation gate: '+arm)
        require(result['valid_latencies']==item['valid_latencies'],'Simulation latency differs from archive: '+arm)
        results[arm]=result
    return results


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--simulate',action='store_true',help='Run Icarus on both archived RTL implementations')
    args=parser.parse_args();start=time.monotonic()
    value=reproduce();out=ROOT/'outputs';out.mkdir(exist_ok=True)
    if args.simulate:
        result=simulate();(out/'simulation.json').write_text(json.dumps(result,indent=2)+'\n')
        print('PASS: both RTL implementations pass the exact shared simulation/reset gate.')
    (out/'reproduced.json').write_text(json.dumps(value,indent=2)+'\n')
    lines=['arm,utility_mhz,oracle_pass_percent,passed,total']
    for arm,row in value['arms'].items(): lines.append(f"{arm},{row['mean_mhz']:.8f},{100*row['correctness']:.8f},{row['passed']},{row['total']}")
    (out/'comparison.csv').write_text('\n'.join(lines)+'\n')
    print('PASS: all packaged hashes, 1920 draws, physical endpoints, paired interval, and selection budgets reproduce.')
    print('\n'.join(lines));print('RF minus SFT:',json.dumps(value['paired']))
    print(f'Elapsed: {time.monotonic()-start:.1f} seconds. Scope: '+value['scope'])


if __name__=='__main__':main()
