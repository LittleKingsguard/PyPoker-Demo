"""How does each league member itself score against the same league mix?  The reference bar."""
import json, numpy as np, engine, agents, evaluation, collections
SH='six-seat-no-limit-100'
LEAGUE=['/tmp/foldloop/control/foldloop-control/card-tokens/seed-0/final.ckpt',
        '/tmp/cfmeasure/checkpoints/raiser-seed/raiser-seed/seed-0/final.ckpt',
        '/tmp/foldloop/high/foldloop-high/card-tokens/seed-0/final.ckpt']
pols=[evaluation.policy_from(p, exploration='off') for p in LEAGUE]
caller=agents.build_baseline('always-call',0)
for i,p in enumerate(pols):
    chips=[]; census=collections.Counter()
    for h in range(1500):
        seat=h%5
        seats=[pols[(s+seat)%3] if (s+seat)%5 else caller for s in range(6)]
        seats[seat]=p
        res=engine.play_hand(8_000_000+i*100_000+h, shape=SH, seats=tuple(seats))
        chips.append(res['payoffs'][seat])
        for d in res['decisions']:
            if d['seat'][0]==seat: census[d['action']]+=1
    tot=sum(census.values()) or 1
    print(json.dumps({'member':['folder','raiser-50-50','raiser-83'][i],
                      'chips':round(float(np.mean(chips)),3),
                      'ci':round(2*float(np.std(chips))/len(chips)**0.5,3),
                      'census':{k:round(100*v/tot,1) for k,v in census.most_common(3)}}))
