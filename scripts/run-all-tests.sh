#!/usr/bin/env bash
# Run every battery in its own pytest invocation.
#
# A single `pytest tests` cannot collect this tree: batteries in sibling directories reuse
# file basenames (test_seeds.py, test_episode.py, test_join_seeds.py) and each battery imports
# its own same-directory support module, so the prepend import mode aborts with
# "import file mismatch" while importlib mode breaks those helper imports. Per-directory runs
# are the supported way to execute the whole suite; this script is what "run the tests" means.
set -u
cd "$(dirname "$0")/.." || exit 1
python=${PYTHON:-.venv/bin/python}
fail=0
for d in tests/engine tests/features tests/agents tests/evaluation tests/training tests/harness \
         tests/integration/engine tests/integration/features tests/integration/agents \
         tests/integration/evaluation tests/integration/training tests/integration/harness \
         tests/e2e; do
  line=$("$python" -m pytest "$d" -q 2>&1 | tail -1)
  printf '%-38s %s\n' "$d" "$line"
  case "$line" in *failed*) fail=1 ;; esac
done
echo
[ "$fail" -eq 0 ] && echo "all batteries green" || echo "FAILURES PRESENT"
exit "$fail"
