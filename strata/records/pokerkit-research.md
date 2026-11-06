# `pokerkit` and poker-RL facts · established 2026-11-05 (D-15)

Sources are primary: PyPI JSON, the GitHub API, and the repository at tag `main` as staged to
`/tmp/intake-sources`. Claims with no primary source are labelled `unsourced`.

| Claim | Source | Confidence | If false |
|---|---|---|---|
| `pokerkit` 0.7.7, MIT, requires Python ≥ 3.11, no runtime dependencies | `pypi.org/pypi/pokerkit/json` (`info.version`, `info.requires_python`, `classifiers`, `requires_dist: null`) | high | dependency and env plan change |
| Repository `uoftcprg/pokerkit`, 520 stars, last push 2026-10-12 | `api.github.com/repos/uoftcprg/pokerkit` | high | maintenance-risk row changes |
| Variants include `FixedLimitTexasHoldem` (games.py:534), `NoLimitTexasHoldem` (:625), `PotLimitOmahaHoldem` (:1057), `FixedLimitSevenCardStud` (:1352), `FixedLimitBadugi` (:1886), `KuhnPoker` (:2071), `LeducHoldem` (:2162) | repo tree + `games.py` class list | high | D-2's game choice or Phase 2 options change |
| A state is created by `NoLimitTexasHoldem.create_state(automations, ante_trimming_status, raw_antes, raw_blinds_or_straddles, min_bet, raw_starting_stacks, …)` (games.py:629-646) | `games.py`, `examples.rst` §"A Fixed-Limit Texas Hold'em Hand" | high | the engine is driven differently |
| Actions are applied by direct methods: `fold()` (state.py:4439), `check_or_call()` (:4553), `complete_bet_or_raise_to()` (:5021) | `state.py` | high | action encoding changes |
| Legality is queried by predicates: `can_fold()` (:4383), `can_check_or_call()` (:4503), `can_complete_bet_or_raise_to()` (:4906), with `min_`/`max_completion_betting_or_raising_to_amount` (:4679, :4733) | `state.py` | high | legal-action enumeration changes |
| Per-player data exposed: `actor_index` (:4342), `player_indices` (:1399), `stacks`, `status`, `showdown_index` (:5344), `can_win_now()` (:2203), `collect_bets()` (:3227) | `state.py` | high | feature extraction changes |
| No gym-style wrapper, no observation encoding, no `reset`/`step`/`render` anywhere: grep for `gym|reset(|observation|.step(|render(` across sources and docs returns zero matches | staged sources + `docs/*.rst` | high | a shortcut exists and should be used |
| The deck is shuffled at state creation with Python's `random.shuffle` (:1239-1241) and no seed parameter is accepted | `state.py` | high | reproducibility plan changes (ASM-2) |
| Analysis helpers exist: `calculate_equities` (analysis.py:225), `calculate_hand_strength` (:340), `calculate_icm` (:525), `parse_range` (:114), `Statistics` (:425) | `analysis.py` | high | the oracle baseline and hand-strength features change |
| RLCard 1.2.0, MIT, gym-style card-game envs plus DQN/CFR agents, last push 2024-06-26 | `pypi.org/pypi/rlcard/json`; `api.github.com/repos/datamllab/rlcard` | high | option row only — the project builds its own machinery to show it |
| OpenSpiel 2.0.2 (Python ≥ 3.11) — broad game suite with reference solvers | `pypi.org/pypi/open-spiel/json` | high | reference-solver row only |
| PokerRL 0.0.3, MIT — a research framework for no-limit Hold'em | `pypi.org/pypi/PokerRL/json` | medium (older release) | option row only |
| Acceptance predicates: RLCard satisfies "ready-made env and agent zoo"; OpenSpiel satisfies "reference solvers and benchmarks"; neither satisfies "the listener watches the learning machinery get built rung by rung", which is this project's purpose (brief §0) | derived from the two PyPI descriptions above | medium | a substitute library would be reconsidered |
| Plain tabular Q-learning over full no-limit Hold'em is impractical at demo scale; the documented simplifications are heads-up, fixed-limit, small stacks and long-run self-play | `unsourced` (general knowledge; not verified against a primary source in this pass) | low | Phase 1's game and Phase 2's ambition would be re-examined |
