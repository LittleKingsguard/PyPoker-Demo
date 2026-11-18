# The browser table

A local demonstration table for the PyPoker league. You take one seat; a trained checkpoint or
a deterministic baseline takes the other, or five others on a six-seat table. The point is to
make the league playable by hand, not to be a seventh module: the table calls the same public
entry points the notebooks do (`engine.new_hand`, `readout`, `apply_action`, `is_terminal`,
`payoffs`, `agents.build_baseline` and `evaluation.policy_from`) and lives outside `src/`.

```sh
# from the repository root
.venv/bin/python ui/serve.py --open
```

The server is the Python standard library, binds to `127.0.0.1:8000`, and has **no
authentication**. It is a single-user demo; do not expose it to an untrusted network. Use
`--port`, `--host`, `--checkpoint-root` or `--probe-root` to change the bind address or the
two discovery roots.

The core runtime is `pokerkit` and `numpy`. PyTorch checkpoints (most of `.probe/`) need
`torch`; without it they are listed as unavailable with a reason instead of failing at the
table.

## The league

Discovery walks `checkpoints/` (labelled **Shipped**) and `.probe/` (labelled **Probe**), reads
each checkpoint's `metadata.json` inside the container, and derives:

- the game shape from `game` — only shapes the engine declares (`fixed-limit-20`,
  `no-limit-100`, `six-seat-no-limit-100`) are offered;
- the group from the path, for example `R1 · naive-numeric` or
  `strength-control-s2 · card-tokens`;
- seed, step, parameter count, backend, kind and encoding.

A checkpoint that declares a training artefact outside itself — some probe runs were fitted
from the frozen `attn-60` estimator — is offered only if the artefact is present. The three
`strength-strength-*` probe groups reference `.probe/attn60.pt`; while that file is in the tree
they load, and if it is removed they are listed as unavailable with that reason rather than
failing at the table.

Every entry is **labelled by what it is**, not by where it lives: `DISPLAY_NAMES` in `table.py`
maps a discovered group to a readable name — `Naive · flat numbers`, `Dead trunk · 600-scale
reward`, `Live trunk, masked pooler · seed 2`, `Live trunk + card strength · seed 0` — and an
unlisted group falls back to its derived path label.

### Top performers

The two best-measured policies of the integration experiments were saved as **torch state dicts**,
not checkpoint containers: `.probe/saved-base-s0-eps0.6.pt` and `.probe/saved-opp2-s0-eps0.6.pt`.
`ui/probe_policies.py` is an adapter that presents them with the same `(readout, legal) → action`
signature as any other member, so they appear in the drawer as **Top performer · exploration floor
0.60** and **Top performer · floor 0.60 + opponent model** and are playable at six seats. Their
inputs are the frozen `attn-60` card model plus five table facts (and, for the second, the frozen
per-seat opponent model); both artefacts must be present.

Checkpoints play greedily with exploration off. The six deterministic policies
(`random`, `always-call`, `oracle`, `fold-no-pair-or-face`, `fold-no-pair-or-better`,
`fold-large-bet`) are rebuilt for the chosen table and seed, so `random`, `oracle` and
`fold-large-bet` still key on the same inputs they do in training.

## Tables and seats

| Shape | Seats | Model members | Structure |
|---|---|---|---|
| `fixed-limit-20` | 2 | shipped R1 | 20 chips, blinds 1/2, bets 2/4, four raises |
| `no-limit-100` | 2 | baselines only | 100 chips, blinds 1/2, any legal bet |
| `six-seat-no-limit-100` | 6 | probe | 100 chips, blinds 1/2, any legal bet |

The table's shape follows a selected model automatically; the shape selector applies when you
choose a baseline. **Your seat** is fixed for a match; engine seat 0 is the button, seat 1 the
small blind, seat 2 the big blind, and seats 3–5 are under the gun, hijack and cutoff. On the
heads-up table seat 0 is button/small blind and seat 1 is the big blind.

On a six-seat table, **Mix the league across seats** keeps the selected member and fills the
five opponent seats with a deterministic seed-keyed mix: one or two fixed policies and the
rest from the checkpoints trained on that shape. `oracle` is deliberately left out of the mix
because it samples equity at every decision and five copies would make the demo crawl; it is
still selectable on its own.

## Files

| Path | What it does |
|---|---|
| `table.py` | discovery, the registry, policies, one hand at a time, and a match across hands |
| `serve.py` | the stdlib HTTP server, cookie sessions, JSON API and static file serving |
| `static/index.html` | the table, drawer, hand log and help dialog |
| `static/style.css` | casino-table styling, including the five-seat ring around your seat |
| `static/app.js` | rendering, controls, keyboard shortcuts and the API client |
| `static/favicon.svg` | the tab icon |

## API

All responses are JSON. A random `pypoker_sid` cookie identifies one browser's match; sessions
and their matches live in server memory and are lost on restart.

| Method | Path | Body | Meaning |
|---|---|---|---|
| `GET` | `/api/opponents` | — | league, shapes, featured starters, torch availability |
| `GET` | `/api/state` | — | the current match, or `{"match": null}` |
| `POST` | `/api/start` | `opponent_id`, `shape`, `seat`, `seed`, `lineup_mode` | deal a new match |
| `POST` | `/api/action` | `action` | apply one human action descriptor |
| `POST` | `/api/next` | — | deal the next hand of the same match |
| `POST` | `/api/reset` | — | forget this session's match |
| `GET` | `/api/health` | — | liveness and league counts |

`shape` follows a model opponent; a baseline uses the requested shape (default
`fixed-limit-20`). `lineup_mode` is `same` (repeat the chosen member) or `mixed` (six-seat
tables only). Seed may be omitted for a random one; replaying a seed replays the deal and the
opponents' decisions.

The state payload carries `match` (shape, seats, lineup, score, record, config) and `hand`
(board, pot, street, every seat, your legal actions, history and, when finished, the result
with per-seat deltas). No-limit action rows carry the resolved **total** amount in `amount` and
a short `label` such as `Raise to 52`.

## Reading the table

Your hole cards are always visible. Opponents' cards are hidden until a showdown, and a folded
hand stays mucked. A finished hand shows each live seat's five-card rank, every seat's net
delta for the hand, and the resulting stacks; the sidebar keeps the full action log and the
match score. The hand is stepped one decision at a time, so the models act through the same
`policy(readout, legal)` call the evaluation harness uses.

Keyboard: `F` fold, `C` check/call, `R` raise (half pot when offered, otherwise the descriptor
the engine calls `raise`), `L` league drawer, `?` help, `Enter` next hand, `Esc` close.

## Tests

The table has its own battery, outside `src/` and outside the module batteries:

```sh
.venv/bin/python -m pytest tests/ui -q
```

It covers shape-aware discovery, unavailable checkpoints, two- and six-seat settlement,
mixed lineups, shape/seat refusals, the HTTP API from start through next hand, and static
serving. It does not need a browser.

## Limits

- Sessions are in-memory; restarting the server drops every match.
- A model is cached per checkpoint after its first load. Loading a PyTorch checkpoint the
  first time can take a second or two; subsequent hands reuse it.
- The table does not train, evaluate or write checkpoints. It only reads them.
- The result messages describe the hand; they are not a claim about model skill. The shipped
  evidence under `checkpoints/evidence/` is the place to read that.
