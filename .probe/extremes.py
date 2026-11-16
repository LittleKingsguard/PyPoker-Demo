import random, numpy as np, pokerkit as pk
RANKS='23456789TJQKA'; SUITS='cdhs'
DECK=[r+s for r in RANKS for s in SUITS]
CARD={c: list(pk.Card.parse(c))[0] for c in DECK}
def ev(hole, board):
    h=pk.StandardHighHand.from_game_or_none([CARD[c] for c in hole],[CARD[c] for c in board])
    return h.entry
def flush_possible(cards):
    return max(sum(1 for c in cards if c[1]==s) for s in SUITS) >= 5
def straight_possible(cards):
    rs=sorted({RANKS.index(c[0]) for c in cards})
    if 12 in rs: rs=sorted(set(rs)|{-1})
    run=1
    for i in range(1,len(rs)):
        run = run+1 if rs[i]==rs[i-1]+1 else 1
        if run>=5: return True
    return False
SCEN = [
 ("BEST trip aces, no flush/straight", ("As","Ad"), ["Ah","Kd","7c","5s","2c"]),
 ("BEST quad aces",                    ("As","Ad"), ["Ah","Ac","7d","5s","2h"]),
 ("BEST nut flush",                    ("As","Qs"), ["Js","9s","4s","2h","7d"]),
 ("BEST ace-high straight",            ("As","Kd"), ["Qc","Js","Th","2d","7c"]),
 ("MID  pair of kings, dry",           ("Kh","Kd"), ["7c","5s","2c","9d","Jh"]),
 ("WORST 2-3 offsuit, no pair/draw",   ("2c","3d"), ["8h","9s","Jd","Qh","Kc"]),
 ("WORST 2-7 offsuit, no pair/draw",   ("2d","7c"), ["8h","9s","Jd","Qh","Kc"]),
 ("WORST 2-3 offsuit, all-high board", ("2c","3d"), ["Ah","Kd","Qc","Js","9h"]),
]
def mc_equity(hole, board, draws=20000, seed=1):
    rnd=random.Random(seed); fixed=set(hole)|set(board)
    rest=[c for c in DECK if c not in fixed]; mine=ev(hole,board); win=0.0
    for _ in range(draws):
        o=rnd.sample(rest,10)
        top=mine; ties=1
        for i in range(5):
            e=ev(o[i*2:i*2+2],board)
            if e>top: ties=0; break
            if e==top: ties+=1
        if ties: win += 1.0/ties
    return win/draws
print(f"{'scenario':36} {'flush?':>7} {'straight?':>10} {'MC equity':>10}")
for name,hole,board in SCEN:
    cards=list(hole)+list(board)
    fp=flush_possible(cards); sp=straight_possible(cards); eq=mc_equity(hole,board)
    print(f"{name:36} {str(fp):>7} {str(sp):>10} {100*eq:9.2f}%")
