"""Replay the reference hands through every surviving checkpoint and emit a self-contained HTML grid.
Cells show the model's action sequence (preflop/flop/turn/river); rows carry the hand and its true equity."""
import json, engine, agents, evaluation
SH='six-seat-no-limit-100'; RANKS='23456789TJQKA'; SUITS='cdhs'
REF=[("quad aces",("As","Ad"),["Ah","Ac","7d","5s","2h"],100.00),
     ("nut flush",("As","Qs"),["Js","9s","4s","2h","7d"],100.00),
     ("ace-high straight",("As","Kd"),["Qc","Js","Th","2d","7c"],97.77),
     ("trip aces",("As","Ad"),["Ah","Kd","7c","5s","2c"],91.84),
     ("pair of kings (dry)",("Kh","Kd"),["7c","5s","2c","9d","Jh"],45.07),
     ("2-3 offsuit junk",("2c","3d"),["8h","9s","Jd","Qh","Kc"],0.00),
     ("2-7 offsuit junk",("2d","7c"),["8h","9s","Jd","Qh","Kc"],0.00),
     ("2-3 offsuit, all-high board",("2c","3d"),["Ah","Kd","Qc","Js","9h"],0.02)]
MODELS={
 "dead":[("600-scale reward, 3k hands",".probe/dead/dead-ckpt/card-tokens/seed-0/final.ckpt"),
         ("600-scale reward, raiser run","/tmp/cfmeasure/checkpoints/raiser-seed/raiser-seed/seed-0/final.ckpt")],
 "live":[("normalised, foldloop-high","/tmp/foldloop/high/foldloop-high/card-tokens/seed-0/final.ckpt"),
         ("normalised, foldloop-control","/tmp/foldloop/control/foldloop-control/card-tokens/seed-0/final.ckpt"),
         ("normalised + card strength",".probe/strength-strength-s0/strength-strength-s0/card-tokens/seed-0/final.ckpt")],
}
f1=agents.build_baseline('fold-no-pair-or-face',0); f2=agents.build_baseline('fold-no-pair-or-better',0)
caller=agents.build_baseline('always-call',0)
def deal(hole, board, seat=3):
    used=set(hole)|set(board); rest=[r+s for r in RANKS for s in SUITS if r+s not in used]
    holes=[]; k=0
    for s in range(6):
        if s==seat: holes.append(list(hole))
        else: holes.append([rest[k],rest[k+1]]); k+=2
    return {"holes":holes,"board":list(board)}
def shorten(a):
    return 'f' if a=='fold' else ('c' if a=='check-call' else 'r')
def run(path):
    pol=evaluation.policy_from(path, exploration='off')
    out={}
    for name,hole,board,eq in REF:
        try:
            r=engine.play_hand(20261115, shape=SH, seats=(f1,caller,f2,pol,f1,f2), deal=deal(hole,board))
            acts=[shorten(d['action']) for d in r['decisions'] if d['seat'][0]==3]
            out[name]=''.join(acts) or '–'
        except Exception as e:
            out[name]='ERR'
    return out
results={k:{n:run(p) for n,p in v} for k,v in MODELS.items()}
for grp in results:
    for m in results[grp]: print(f"{grp:5} {m:32} " + "  ".join(f"{h[:12]}:{results[grp][m][h]}" for h,_,_,_ in REF))
json.dump({'ref':[(n,round(e,2)) for n,_,_,e in REF],'results':results}, open('.probe/grids.json','w'), indent=1)
