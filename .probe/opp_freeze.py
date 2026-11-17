"""Freeze the opponent model as .probe/opp.pt: predicts the acting seat's action family and its strength
from the table's action history.  Trained WITHOUT identity (the loop has none)."""
import numpy as np, torch, torch.nn as nn, torch.nn.functional as F, random, collections, sys
sys.path.insert(0,'.probe')
from oppmodel import OppNet, collect, MAXH
rows=collect(600, 11)
print("rows:", len(rows), flush=True)
tok=torch.tensor([r['tok']+[0]*(MAXH-len(r['tok'])) for r in rows])
pub=torch.tensor([r['pub'][:5]+[0.0]*(len(r['pub'])-5) for r in rows], dtype=torch.float32)  # identity zeroed
y=torch.tensor([r['y'] for r in rows])
torch.manual_seed(0); net=OppNet(); opt=torch.optim.Adam(net.parameters(),2e-3)
# strength head is trained on the action label only here: the loop needs a *prediction*, not a label
for ep in range(8):
    p=torch.randperm(len(tok))
    for i in range(0,len(tok),1024):
        b=p[i:i+1024]; la,ls=net(tok[b],pub[b])
        loss=F.cross_entropy(la,y[b],weight=torch.tensor([6.0,1.0,8.0]))
        opt.zero_grad(); loss.backward(); opt.step()
torch.save(net.state_dict(), '.probe/opp.pt')
with torch.no_grad():
    la,ls=net(tok[:500],pub[:500])
print("frozen: .probe/opp.pt | action mix", {k:round(100*v/len(rows),1) for k,v in collections.Counter(r['y'] for r in rows).items()})
