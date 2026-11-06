# PyPoker-Demo — module isolation

Procedure for D-13. Ceiling: 40 lines.

## 1. What a module agent gets

Exactly one module: `docs/L3/<module>/`, `src/<module>/`, `tests/<module>/`, and that module's L2
interface document. Nothing else (D-13).

Folders are the unit of isolation — `engine`, `features`, `agents`, `evaluation` are siblings, not
parents of each other. A module agent that needs another module's surface reads the **L2
interface**, never that module's code or docs (D-13).

## 2. Why it is a control, not hygiene

One module's examples and single-decision rules cannot leak into another module's design if the
other never sees them (D-15). Isolation also bounds each agent's context — the brief's line
ceiling applied to context rather than files (D-1).

## 3. Cross-module needs

If the L2 interface is insufficient for the work, the module agent has found an L2 defect. That is
an adjudication request, counted as a failure and routed to L2 (D-12).

The forbidden route is reading the sibling module and inferring the contract from its code. That
is how one module's implementation choices become another module's assumed rules (D-13).

## 4. Enforcement

Subfolder convention plus diff-scope lint (D-13). The module agent stays a delegation child;
`strata-lint` checks that every written path lies inside the module's declared subtree. Reads
outside it are not prevented — only writes are checked. Isolation is prompt-and-lint enforced,
not sandbox-enforced (D-13).

`modules.json` declares one entry per module with `name`, `paths` (the subtrees it owns) and
`endpoints` (its declared entry-point count). Two modules may never claim one path — that fails
the lint (D-13).
