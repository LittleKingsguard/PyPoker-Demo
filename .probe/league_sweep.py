"""Rank every available six-seat checkpoint against the same league mix (1,000 hands each)."""
import json, glob, numpy as np, engine, agents, evaluation, collections
SH='six-seat-no-limit-100'
CAND=[('raiser-50-50','/tmp/cfmeasure/checkpoints/raiser-seed/raiser-seed/seed-0/final.ckpt'),
      ('raiser-83','/tmp/foldloop/high/foldloop-high/card-tokens/seed-0/final.ckpt'),
      ('folder','/tmp/foldloop/control/foldloop-control/card-tokens/seed-0/final.ckpt'),
      ('mask-only','/tmp/mask-mask-only/mask-only/card-tokens/seed-0/final.ckpt'),
      ('mask-no-squash','/tmp/mask-mask-no-squash/mask-no-squash/card-tokens/seed-0/final.ckpt'),
      ('pool-today','/tmp/pool-probe/today/pool-today/card-tokens/seed-0/final.ckpt'),
      ('pool-mean-real','/tmp/pool-probe/mean-real/pool-mean-real/card-tokens/seed-0/final.ckpt'),
      ('pool-no-squash','/tmp/pool-probe/no-squash/pool-no-squash/card-tokens/seed-0/final.ckpt'),
      ('pool-sum','/tmp/pool-probe/sum-pool/pool-sum-pool/card-tokens/seed-0/final.ckpt'),
      ('ours-s0','.probe/strength-control-s0/strength-control-s0/card-tokens/seed-0/final.ckpt'),
     ]
MIX=['/tmp/foldloop/control/foldloop-control/card-tokens/seed-0/final.ckpt',
     '/tmp/cfmeasure/checkpoints/raiser-seed/raiser-seed/seed-0/final.ckpt',
     '/tmp/foldloop/high/foldloop-high/card-tokens/seed-0/final.ckpt']
mix=[evaluation.policy_from(p, exploration='off') for p in MIX]
caller=agents.build_baseline('always-call',0)
out=[]
for name,path in CAND:
    try: pol=evaluation.policy_from(path, exploration='off')
    except Exception as e:
        print(f"{name:16} unreadable {type(e).__name__}"); continue
    chips=[]; census=collections.Counter()
    try:
        for h in range(1000):
            seat=h%5
            seats=[mix[(s+seat)%3] if (s+seat)%5 else caller for s in range(6)]
            seats[seat]=pol
            r=engine.play_hand(9_000_000+h, shape=SH, seats=tuple(seats))
            chips.append(r['payoffs'][seat])
            for d in r['decisions']:
                if d['seat'][0]==seat: census[d['action']]+=1
    except Exception as e:
        print(f"{name:16} cannot play: {type(e).__name__}"); continue
    tot=sum(census.values()) or 1
    out.append({'name':name,'chips':round(float(np.mean(chips)),3),
                'ci':round(2*float(np.std(chips))/len(chips)**0.5,3),
                'top':{k:round(100*v/tot,1) for k,v in census.most_common(2)}})
out.sort(key=lambda d:-d['chips'])
print(f"{'member':16} {'chips/hand':>12} {'95%':>8}  behaviour")
for d in out: print(f"{d['name']:16} {d['chips']:+12.3f} {d['ci']:8.2f}  {d['top']}")
json.dump(out, open('.probe/league-sweep.json','w'), indent=1)
