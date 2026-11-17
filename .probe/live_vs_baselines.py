"""Naive model (flat-numeric + naive-stack) against each deterministic/random baseline, five copies at the table."""
import json, collections, numpy as np, engine, agents, evaluation
SH='six-seat-no-limit-100'; HANDS=1000
NAIVE='.probe/naive/naive6/card-tokens/seed-0/final.ckpt'
BASES=['random','always-call','oracle','fold-no-pair-or-face','fold-no-pair-or-better','fold-large-bet']
naive=evaluation.policy_from(NAIVE, exploration='off')
out={}
for b in BASES:
    opp=agents.build_baseline(b, 0)
    chips=[]; census=collections.Counter()
    for h in range(HANDS):
        seat=h%5
        seats=[opp]*6; seats[seat]=naive
        r=engine.play_hand(32_000_000+h, shape=SH, seats=tuple(seats))
        chips.append(r['payoffs'][seat])
        for d in r['decisions']:
            if d['seat'][0]==seat: census[d['action']]+=1
    m=float(np.mean(chips)); ci=2*float(np.std(chips))/len(chips)**0.5
    tot=sum(census.values()) or 1
    out[b]={'chips':round(m,3),'ci':round(ci,3),'hands':HANDS,
            'census':{k:round(100*v/tot,1) for k,v in census.most_common(3)}}
    print(f"{b:24} {m:+7.3f} +-{ci:5.2f}   {out[b]['census']}")
json.dump(out, open('.probe/live-vs-baselines.json','w'), indent=1)
