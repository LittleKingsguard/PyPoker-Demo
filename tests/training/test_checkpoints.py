"""TRN-6 — the artefacts, the layout and the index: `checkpoints()`.

Drives `docs/L3/training/checkpoints.md` §1-§5, `docs/L2/training/write-root.md` §1-§3
and `docs/L2/training/surface.md` §7: the file layout under `checkpoints/`, the `.ckpt`
suffix, the ten written and the five retained plus that pair's final model, the layout's
private names `README.md` §4 makes contract (`ROOT`, `CHECKPOINT_ROOT`, `OVERRIDE`,
`_write_root`, `_write_path`, `_final_path`, `_snapshot_path`, `_prepare`, `_relative`,
`_resolve`, `_resolved`) — the declared layout and its naming helpers, the write root
`PYPOKER_CHECKPOINT_ROOT` and the directory the run makes before the first save — and
the index — declared data, one entry per artefact, listed once, in §4's order, with the
window as one lineage chain.

The listing is counted, never de-duplicated: FAM-12.6 fails on a single repeat and
`battery.md` §2 makes a case that cannot fail a defect, so `listed_paths` keeps every
repeat it finds.
"""

import hashlib
import os
import shutil
import tempfile
import unittest

from _training_support import (
    CHECKPOINT_ROOT,
    RETAINED,
    REPO_ROOT,
    RUNG_NAMES,
    SIXTY_BUDGET,
    SNAPSHOTS,
    TINY_BUDGET,
    TrainingCase,
    as_int,
    as_mapping,
    as_sequence,
    as_text,
    baseline_names,
    checkpoint_block,
    checkpoint_tree,
    internal,
    internal_module,
    listed_paths,
    one_seed_run,
    repo_relative,
    resolved,
    seed_set,
    sixty_hand_run,
    training,
    write_root,
    write_tree,
)

#: `checkpoints.md` §4's nine keys of one entry, `records.md` §7's eight plus `kind`.
ENTRY_KEYS = {
    "id",
    "path",
    "rung",
    "variant",
    "seed",
    "step",
    "samples",
    "lineage",
    "kind",
}

#: `checkpoints.md` §2's suffix.
SUFFIX = ".ckpt"

#: `write-root.md` §3's one ambient override, by the name it declares.
OVERRIDE = "PYPOKER_CHECKPOINT_ROOT"

#: Invented labels for the layout cases: a pair no run of this repository writes.
LAYOUT_RUNG = "R9-layout-5520"
LAYOUT_VARIANT = "variant-layout-5520"
LAYOUT_SEED = 5520

#: Invented seed for the write-root case: no other case in this battery runs it, so the
#: eleven artefacts a run at it leaves under the write root are this case's own and its
#: record cannot be another case's (`write-root.md` §1, §3, loop.md §4).
DECLARED_SEED = 5521


def tree_digest(paths):
    """A sha256 of every file `paths` names, as `{path: hexdigest}`.

    `paths` are `checkpoint_tree()`'s repository-relative names, so each is opened through
    `resolved()` — a recorded spelling is read from the repository root and never from the
    caller's working directory (`checkpoints.md` §2) — and read in binary, because "the
    shipped set is never added to and never overwritten" is a claim about bytes and not
    only about names (`checkpoints.md` §5, `write-root.md` §2, guardrails G20).
    """
    digests = {}
    for path in paths:
        with open(resolved(path), "rb") as handle:
            digests[path] = hashlib.sha256(handle.read()).hexdigest()
    return digests


def tree_directories():
    """Every directory under `<repo>/checkpoints`, repository-relative, sorted.

    The counterpart of `checkpoint_tree()`, which lists files only: `checkpoints.md` §2
    fixes a directory layout — `checkpoints/<rung>/<variant>/seed-<seed>/` — that a file
    listing cannot see, so a run that spells the declared root where `_prepare` means the
    write root adds a directory and no file at all. Guardrails G20's "a battery-started
    run adds no path under `<repo>/checkpoints`" is a claim about paths and not only about
    files, and a directory is a path (`write-root.md` §1, §3, `checkpoints.md` §2, §5).
    The root itself is not a level below itself and is never listed; each entry is spelled
    the way `checkpoint_tree()` spells its files, through `repo_relative()` — POSIX
    separators, from the repository root (`checkpoints.md` §1-§2).
    """
    found = []
    for base, directories, _files in os.walk(CHECKPOINT_ROOT):
        for name in directories:
            found.append(repo_relative(os.path.join(base, name)))
    return sorted(found)


class CheckpointTest(TrainingCase):
    def index(self):
        return as_mapping(training().checkpoints(), "the checkpoint index")

    def entries(self):
        return [
            as_mapping(entry, "one index entry")
            for entry in as_sequence(self.index().get("entries"), "'entries'")
        ]

    def test_trn_6_1_a_pair_names_six_artefacts_and_a_sixty_hand_run_still_five(self):
        """TRN-6.1 a pair's record names the last M = 5 snapshots plus its final model — six artefacts — at 10 hands and at 60 hands alike, each of which exists (checkpoints.md §2-§3, loop.md §2, guardrails G5, FAM-12.1, FAM-12.4)."""
        for label, record, budget in (
            ("10 hands", one_seed_run(), TINY_BUDGET),
            ("60 hands", sixty_hand_run(), SIXTY_BUDGET),
        ):
            seed = as_int(as_sequence(record["seeds"], "seeds")[0], "the run's seed")
            block = checkpoint_block(record, "naive-numeric", seed)
            with self.subTest(run=label):
                paths = listed_paths(block)
                self.assertEqual(
                    len(paths),
                    RETAINED + 1,
                    "a pair's record names M + 1 artefacts — the retained five and the "
                    "final model — and never the ten plus the final "
                    "(checkpoints.md §3, guardrails G5): %r" % (paths,),
                )
                for path in paths:
                    self.assertTrue(
                        repo_relative(path).endswith(SUFFIX),
                        "every named artefact is a .ckpt file (checkpoints.md §2): %r"
                        % (path,),
                    )
                    self.assertTrue(
                        os.path.exists(resolved(path)),
                        "the record carries the paths agents.save wrote, so they are "
                        "files (checkpoints.md §2, FAM-12.1): %r" % (path,),
                    )
                snapshots = as_sequence(block["snapshots"], "'snapshots'")
                self.assertEqual(
                    len(snapshots),
                    RETAINED,
                    "at %s the run wrote ten snapshots and the record retains the last "
                    "five, because the interval is budget // 10 and not the declared "
                    "100 (checkpoints.md §3, loop.md §2, FAM-12.4): %r"
                    % (label, snapshots),
                )
                interval = budget // 10
                steps = [
                    as_int(
                        int(
                            os.path.basename(repo_relative(path))
                            .replace("step-", "")
                            .replace(SUFFIX, "")
                        ),
                        "a snapshot's step",
                    )
                    for path in snapshots
                ]
                self.assertEqual(
                    steps,
                    [budget - RETAINED * interval + offset * interval
                     for offset in range(1, RETAINED + 1)],
                    "the retained five are the last five of the ten the pair wrote, so "
                    "at %s they are steps %r (checkpoints.md §3, loop.md §2)"
                    % (label, [budget - RETAINED * interval + offset * interval
                               for offset in range(1, RETAINED + 1)]),
                )

    def test_trn_6_2_no_artefact_is_listed_twice(self):
        """TRN-6.2 the index lists every artefact exactly once — counting listings, repeats included — and `shipped` holds rung names rather than paths (checkpoints.md §4, guardrails G12, FAM-12.6)."""
        record = self.index()
        listings = listed_paths(record)
        self.assertTrue(
            listings,
            "the index names the shipped artefacts; an empty listing is a defect of the "
            "shipped set, not a pass (checkpoints.md §4-§5, protocol.md §5)",
        )
        self.assertEqual(
            len(listings),
            len(set(listings)),
            "checkpoint_path_listing counts listings, repeats included, and FAM-12.6 "
            "fails on a single repeat, so the index carries one list and no second copy "
            "of any path (checkpoints.md §4, guardrails G12): %r"
            % ([path for path in listings if listings.count(path) > 1],),
        )
        self.assertEqual(
            len(listings),
            len(self.entries()),
            "each entry names one artefact and the index names no other path beside the "
            "entries (checkpoints.md §4): %d listings for %d entries"
            % (len(listings), len(self.entries())),
        )
        shipped = [
            as_text(name, "a shipped rung name")
            for name in as_sequence(record.get("shipped"), "'shipped'")
        ]
        self.assertTrue(shipped, "`shipped` names the rungs whose runs exist")
        for name in shipped:
            self.assertIn(
                name,
                RUNG_NAMES,
                "`shipped` holds rung names and not paths (checkpoints.md §4, §6): %r"
                % (name,),
            )
            self.assertFalse(
                name.endswith(SUFFIX),
                "`shipped` holds rung names and not paths (checkpoints.md §4): %r"
                % (name,),
            )

    def test_trn_6_3_every_entry_is_one_artefact_inside_the_repository(self):
        """TRN-6.3 every entry carries the nine keys, a `kind` of `snapshot` or `final`, and a path ending in the checkpoint suffix that resolves to a file inside the repository (checkpoints.md §2, §4-§5, FAM-12.5, FAM-16.31)."""
        entries = self.entries()
        self.assertTrue(entries, "the index carries the entries of the shipped runs")
        root = os.path.abspath(REPO_ROOT)
        ids = []
        for entry in entries:
            with self.subTest(entry=entry.get("id")):
                self.assertEqual(
                    set(entry),
                    ENTRY_KEYS,
                    "one entry is a records.md §7 record extended with `kind` "
                    "(checkpoints.md §4): %r" % (sorted(entry),),
                )
                self.assertIn(
                    as_text(entry["kind"], "kind"),
                    ("snapshot", "final"),
                    "`kind` is `snapshot` or `final`, which is what lets a window be "
                    "read as the snapshot entries alone (checkpoints.md §4): %r"
                    % (entry["kind"],),
                )
                path = repo_relative(entry["path"])
                self.assertTrue(
                    path.endswith(SUFFIX),
                    "the artefact's suffix is .ckpt, because .gitignore ignores *.pt and "
                    "*.npz and a checkpoint written with either cannot be committed "
                    "(checkpoints.md §2): %r" % (path,),
                )
                absolute = os.path.abspath(resolved(entry["path"]))
                self.assertTrue(
                    absolute.startswith(root + os.sep),
                    "every artefact is inside the repository, so a talk loads it from "
                    "the shipped set (checkpoints.md §5, module-map.md §5): %r"
                    % (absolute,),
                )
                self.assertTrue(
                    os.path.exists(absolute),
                    "an artefact the index names and the repository does not carry is a "
                    "defect of the shipped set, not a silent omission (surface.md §7, "
                    "checkpoints.md §5, FAM-12.5): %r" % (absolute,),
                )
                self.assertEqual(
                    as_int(entry["samples"], "samples"),
                    as_int(entry["step"], "step"),
                    "the loop trains one hand and learns once, so a snapshot's step and "
                    "its sample count are the same integer (checkpoints.md §4, "
                    "records.md §7): %r against %r" % (entry["step"], entry["samples"]),
                )
                self.assertIn(
                    as_int(entry["seed"], "seed"),
                    (0, 1, 2),
                    "the shipped set is a live run at protocol.md §2's seed set "
                    "(checkpoints.md §5): %r" % (entry["seed"],),
                )
                for baseline in baseline_names():
                    self.assertNotIn(
                        baseline,
                        as_text(entry["id"], "id"),
                        "an entry's id contains none of the three baseline names "
                        "(checkpoints.md §4, records.md §7): %r" % (entry["id"],),
                    )
                ids.append(as_text(entry["id"], "id"))
        self.assertEqual(
            len(ids),
            len(set(ids)),
            "an entry's id is stable and unique within the index (checkpoints.md §4): "
            "%r" % ([name for name in ids if ids.count(name) > 1],),
        )

    def test_trn_6_4_the_path_helpers_are_pure_and_end_in_the_declared_suffix(self):
        """TRN-6.4 `_snapshot_path` and `_final_path` are pure, end in `.ckpt`, sit under `<repo>/checkpoints/<rung>/<variant>/seed-<seed>/`, spell the seed decimal and the step `04d`, and naming one creates nothing (checkpoints.md §1-§2, guardrails G19)."""
        layout = internal_module("layout")
        final = internal("layout", "_final_path")(LAYOUT_RUNG, LAYOUT_VARIANT, LAYOUT_SEED)
        snapshot = internal("layout", "_snapshot_path")(
            LAYOUT_RUNG, LAYOUT_VARIANT, LAYOUT_SEED, 60
        )
        pair_directory = os.path.join(
            REPO_ROOT, "checkpoints", LAYOUT_RUNG, LAYOUT_VARIANT,
            "seed-%d" % (LAYOUT_SEED,),
        )
        self.assertEqual(
            repo_relative(final),
            "checkpoints/%s/%s/seed-%d/final%s"
            % (LAYOUT_RUNG, LAYOUT_VARIANT, LAYOUT_SEED, SUFFIX),
            "the layout is checkpoints/<rung>/<variant>/seed-<seed>/final.ckpt "
            "(checkpoints.md §1, §2): %r" % (repo_relative(final),),
        )
        self.assertEqual(
            repo_relative(snapshot),
            "checkpoints/%s/%s/seed-%d/step-0060%s"
            % (LAYOUT_RUNG, LAYOUT_VARIANT, LAYOUT_SEED, SUFFIX),
            "a snapshot is step-<step:04d>.ckpt, zero-padded so the ten names sort "
            "lexicographically in the order they were written (checkpoints.md §2): %r"
            % (repo_relative(snapshot),),
        )
        self.assertEqual(
            os.path.dirname(os.path.abspath(resolved(final))),
            pair_directory,
            "one directory per variant × seed keeps a pair's six named artefacts "
            "together (checkpoints.md §2): %r" % (pair_directory,),
        )
        self.assertFalse(
            os.path.exists(pair_directory),
            "naming a path creates nothing: the run makes the pair's directory with "
            "os.makedirs before the first save (checkpoints.md §1-§2, guardrails G19)",
        )
        relative = as_text(layout._relative(final), "_relative")
        self.assertEqual(
            relative,
            repo_relative(final),
            "`_relative` is the path spelled relative to the repository root, POSIX "
            "separators — the spelling the index uses (checkpoints.md §1-§2): %r"
            % (relative,),
        )
        self.assertNotIn(
            "\\",
            relative,
            "a shipped path is repository-relative with POSIX separators "
            "(checkpoints.md §2): %r" % (relative,),
        )
        resolver = internal("layout", "_resolve")
        self.assertEqual(
            resolver(final),
            final,
            "`_resolve` takes an absolute path as it stands, because `agents.save` is "
            "handed one and writes it (checkpoints.md §1-§2): %r" % (final,),
        )
        self.assertEqual(
            resolver(relative),
            final,
            "`_resolve` reads a recorded path from the repository root and never from "
            "the caller's working directory, so a talk started elsewhere reads the "
            "version the record names (checkpoints.md §1-§2, registry.md §3): %r"
            % (resolver(relative),),
        )
        self.assertEqual(
            repo_relative(resolver("checkpoints/nowhere/seed-0/final%s" % (SUFFIX,))),
            "checkpoints/nowhere/seed-0/final%s" % (SUFFIX,),
            "`_resolve` joins and does not check: whether a declared path is a file is "
            "its reader's test, never a resolver's side effect (checkpoints.md §2)",
        )
        self.assertEqual(
            internal("layout", "_final_path")(LAYOUT_RUNG, LAYOUT_VARIANT, LAYOUT_SEED),
            final,
            "one pair and one path: the helper is pure (checkpoints.md §1)",
        )
        self.assertEqual(
            internal("layout", "_snapshot_path")(
                LAYOUT_RUNG, LAYOUT_VARIANT, LAYOUT_SEED, 60
            ),
            snapshot,
            "one pair and one step give one path, twice alike (checkpoints.md §1)",
        )
        self.assertEqual(
            repo_relative(internal("layout", "_snapshot_path")(
                LAYOUT_RUNG, LAYOUT_VARIANT, LAYOUT_SEED, 10000)),
            "checkpoints/%s/%s/seed-%d/step-10000%s"
            % (LAYOUT_RUNG, LAYOUT_VARIANT, LAYOUT_SEED, SUFFIX),
            "`04d` is a minimum width and not a truncation: a step of 10,000 hands spells "
            "five digits (checkpoints.md §2)",
        )
        self.assertFalse(
            os.path.exists(pair_directory),
            "neither helper writes a directory, however often it is asked "
            "(checkpoints.md §1, guardrails G19)",
        )

    def test_trn_6_5_the_pair_directory_is_made_before_the_first_save(self):
        """TRN-6.5 the layout makes the pair's directory under the write root and nothing else — the one write the run needs before `agents.save`, which invents no directory — so the declared `<repo>/checkpoints` tree gains nothing, and the write root follows `PYPOKER_CHECKPOINT_ROOT` alone, read on every call and never cached (docs/L3/training/checkpoints.md §1-§2, docs/L3/training/loop.md §2, docs/L2/training/write-root.md §1, §3)."""
        layout = internal_module("layout")
        maker_names = (
            "_prepare",
            "_prepare_pair",
            "_prepare_directory",
            "_make_directory",
            "_ensure_directory",
        )
        prepare = next(
            (
                getattr(layout, name)
                for name in maker_names
                if callable(getattr(layout, name, None))
            ),
            None,
        )
        if prepare is None:
            self.fail(
                "the layout exposes no directory-maker (%r) and checkpoints.md §2 "
                "requires one: the run makes the pair's directory with os.makedirs "
                "before agents.save, which invents none (README.md §4, loop.md §2)"
                % (maker_names,)
            )
        root = write_root()
        pair_root = os.path.join(root, LAYOUT_RUNG)
        pair_directory = os.path.join(
            pair_root, LAYOUT_VARIANT, "seed-%d" % (LAYOUT_SEED,)
        )
        declared_pair_root = os.path.join(CHECKPOINT_ROOT, LAYOUT_RUNG)
        redirected = os.path.abspath(root) != os.path.abspath(CHECKPOINT_ROOT)
        self.addCleanup(shutil.rmtree, pair_root, True)
        before_shipped = checkpoint_tree()
        self.assertFalse(
            os.path.exists(pair_directory),
            "the pair's directory does not exist under the write root before the run "
            "makes it (write-root.md §1, checkpoints.md §2): %r" % (pair_directory,),
        )
        prepare(LAYOUT_RUNG, LAYOUT_VARIANT, LAYOUT_SEED)
        self.assertTrue(
            os.path.isdir(pair_directory),
            "the layout makes the pair's directory under the write root, which is what "
            "lets agents.save write into it (checkpoints.md §2, loop.md §1 step 7): %r"
            % (pair_directory,),
        )
        made = []
        written = []
        for base, directories, files in os.walk(pair_root):
            for name in directories:
                made.append(
                    os.path.relpath(os.path.join(base, name), root).replace(os.sep, "/")
                )
            for name in files:
                written.append(
                    os.path.relpath(os.path.join(base, name), root).replace(os.sep, "/")
                )
        self.assertEqual(
            sorted(made),
            ["%s/%s" % (LAYOUT_RUNG, LAYOUT_VARIANT),
             "%s/%s/seed-%d" % (LAYOUT_RUNG, LAYOUT_VARIANT, LAYOUT_SEED)],
            "the maker creates the pair's directory under the write root — spelled from "
            "that root — and nothing else (checkpoints.md §2, write-root.md §1): %r"
            % (sorted(made),),
        )
        self.assertEqual(
            written,
            [],
            "the maker creates the directory and writes no artefact of its own: making "
            "the directory is the preparation and agents.save is the write "
            "(checkpoints.md §2, guardrails G19): %r" % (written,),
        )
        self.assert_tree_untouched(before_shipped, "the layout's directory-maker")
        if redirected:
            self.assertFalse(
                os.path.exists(declared_pair_root),
                "the maker makes the pair's directory under the write root %r and never "
                "the declared one, so nothing may be added to the shipped tree "
                "(write-root.md §1, §3, checkpoints.md §5): %r must not exist"
                % (root, declared_pair_root),
            )
        prepare(LAYOUT_RUNG, LAYOUT_VARIANT, LAYOUT_SEED)
        self.assertTrue(
            os.path.isdir(pair_directory),
            "making the directory twice is not an error, because the run calls it with "
            "exist_ok=True (checkpoints.md §2): %r" % (pair_directory,),
        )
        declared_root = layout.CHECKPOINT_ROOT
        declared = layout._final_path(LAYOUT_RUNG, LAYOUT_VARIANT, LAYOUT_SEED)
        self.assertEqual(
            internal("layout", "OVERRIDE"),
            OVERRIDE,
            "the one ambient override's name is %r exactly, spelled `layout.OVERRIDE` "
            "and never a seventh entry point (write-root.md §3, checkpoints.md §1): %r"
            % (OVERRIDE, getattr(layout, "OVERRIDE", None)),
        )
        had_previous = OVERRIDE in os.environ
        previous = os.environ.get(OVERRIDE)

        def restore_override():
            if had_previous:
                os.environ[OVERRIDE] = previous
            else:
                os.environ.pop(OVERRIDE, None)

        self.addCleanup(restore_override)
        for label, value in (("unset", None), ("empty", "")):
            with self.subTest(override=label):
                if value is None:
                    os.environ.pop(OVERRIDE, None)
                else:
                    os.environ[OVERRIDE] = value
                self.assertEqual(
                    layout._write_root(),
                    declared_root,
                    "with %s %s the write root is the declared <repo>/checkpoints root "
                    "and no other (write-root.md §1, §3): %r against %r"
                    % (OVERRIDE, label, layout._write_root(), declared_root),
                )
                self.assertEqual(
                    layout._write_path(declared),
                    declared,
                    "with %s %s `_write_path` returns the declared path unchanged, "
                    "because the two roots are one root (write-root.md §1, §3): %r "
                    "against %r"
                    % (OVERRIDE, label, layout._write_path(declared), declared),
                )
        elsewhere = tempfile.mkdtemp(prefix="training-write-root-case-")
        self.addCleanup(shutil.rmtree, elsewhere, True)
        os.environ[OVERRIDE] = elsewhere
        expected_root = os.path.abspath(elsewhere)
        self.assertEqual(
            layout._write_root(),
            expected_root,
            "%s is read on every call and never cached at import, so a value set after "
            "this package was imported moves the write root on the very next call "
            "(write-root.md §3, checkpoints.md §2): %r against %r"
            % (OVERRIDE, layout._write_root(), expected_root),
        )
        expected_path = os.path.join(
            expected_root, os.path.relpath(declared, declared_root)
        )
        self.assertEqual(
            layout._write_path(declared),
            expected_path,
            "with %s set, one declared path is re-rooted at the write root: "
            "os.path.join(_write_root(), os.path.relpath(declared, CHECKPOINT_ROOT)) "
            "(write-root.md §1, §3, checkpoints.md §1): %r against %r"
            % (OVERRIDE, layout._write_path(declared), expected_path),
        )
        self.assertEqual(
            os.path.abspath(layout._write_root()),
            os.path.abspath(elsewhere),
            "the write root is the override's path made absolute and nothing else, so "
            "one command line points a run anywhere (write-root.md §3, §4): %r"
            % (layout._write_root(),),
        )
        restore_override()
        self.assertEqual(
            layout._write_root(),
            os.path.abspath(write_root()),
            "restoring the environment puts the write root back exactly where the "
            "session left it, so this case leaves no trace behind "
            "(write-root.md §3, §4): %r against %r"
            % (layout._write_root(), os.path.abspath(write_root())),
        )

    def test_trn_6_6_the_window_is_one_lineage_chain_in_the_seed_sets_order(self):
        """TRN-6.6 the retained window's first version descends from its rung's own start and every later one from the version before it — one chain across the recorded seed set's order (checkpoints.md §3-§4, records.md §7, loop.md §7)."""
        snapshots = [entry for entry in self.entries() if entry.get("kind") == "snapshot"]
        self.assertGreaterEqual(
            len(snapshots),
            RETAINED,
            "the shipped rung's window holds the retained five versions it inherits "
            "(checkpoints.md §3, §5, FAM-12.4): %r" % (len(snapshots),),
        )
        ids = [as_text(entry["id"], "id") for entry in snapshots]
        first = as_text(snapshots[0]["lineage"], "the first version's lineage")
        self.assertNotIn(
            first,
            ids,
            "the window's first version descends from its rung's own start and not "
            "from a version of the window (checkpoints.md §3): %r" % (first,),
        )
        self.assertTrue(
            first.strip(),
            "a start label is a name and never a blank (checkpoints.md §3)",
        )
        for previous, entry in zip(snapshots, snapshots[1:]):
            with self.subTest(version=entry.get("id")):
                self.assertEqual(
                    as_text(entry["lineage"], "a version's lineage"),
                    as_text(previous["id"], "the previous version's id"),
                    "snapshot k+1 descends from snapshot k, and a seed's first from the "
                    "last version the run wrote before it, so the retained versions are "
                    "one chain (checkpoints.md §3, records.md §7): %r after %r"
                    % (entry["lineage"], previous["id"]),
                )
        seeds = [as_int(entry["seed"], "seed") for entry in snapshots]
        self.assertEqual(
            seeds,
            sorted(seeds),
            "the chain runs in the recorded seed set's order, so the three seeds' passes "
            "lie end to end (checkpoints.md §3, §4): %r" % (seeds,),
        )

    def test_trn_6_7_the_index_is_declared_data_and_two_calls_agree(self):
        """TRN-6.7 two calls return equal listings in one declared order, rung then variant then seed then step then that pair's final — declared data and never a directory scan (checkpoints.md §4, surface.md §7, guardrails G11)."""
        first = self.index()
        second = as_mapping(training().checkpoints(), "the second index call")
        self.assertEqual(
            [as_mapping(entry, "entry")["path"] for entry in
             as_sequence(first["entries"], "'entries'")],
            [as_mapping(entry, "entry")["path"] for entry in
             as_sequence(second["entries"], "'entries'")],
            "two calls return equal listings in one declared order (surface.md §7, "
            "checkpoints.md §4)",
        )
        self.assertEqual(
            first.get("shipped"), second.get("shipped"),
            "the shipped rung names agree across two calls (surface.md §7)",
        )
        entries = self.entries()
        order = [
            (
                RUNG_NAMES.index(as_text(entry["rung"], "rung")),
                as_int(entry["seed"], "seed"),
                as_int(entry["step"], "step"),
                1 if as_text(entry["kind"], "kind") == "final" else 0,
            )
            for entry in entries
        ]
        self.assertEqual(
            order,
            sorted(order),
            "the order is rung in brief §2's order, then variant in the declaration's, "
            "then seed ascending, then step ascending, then that pair's final — "
            "ordering by the declaration and never by a directory listing "
            "(checkpoints.md §4, §6): %r" % (order,),
        )

    def test_trn_6_8_the_window_is_read_from_the_repository_root(self):
        """TRN-6.8 a declared window is resolved from the repository root, so `rung` reports one membership from any working directory and a pool never empties because a talk was started elsewhere (checkpoints.md §1-§2, registry.md §3, protocol.md §5)."""
        package = training()
        from_root = as_mapping(package.rung("R2")["pool"], "a pool entry")
        declared = internal_module("layout").ROOT
        self.assertTrue(
            os.path.isdir(os.path.join(declared, "checkpoints")),
            "`layout.ROOT` is the repository root and `checkpoints/` sits under it "
            "(checkpoints.md §1): %r" % (declared,),
        )
        elsewhere = tempfile.mkdtemp(prefix="training-window-case-")
        self.addCleanup(shutil.rmtree, elsewhere, True)
        previous = os.getcwd()
        self.addCleanup(os.chdir, previous)
        os.chdir(elsewhere)
        from_elsewhere = as_mapping(package.rung("R2")["pool"], "a pool entry")
        os.chdir(previous)
        self.assertEqual(
            from_elsewhere,
            from_root,
            "one membership reads back one entry and one id whatever directory the "
            "process was started in, because a declared path is resolved from the "
            "repository root (checkpoints.md §2, registry.md §3, records.md §8): %r "
            "against %r" % (from_elsewhere, from_root),
        )
        members = as_sequence(from_elsewhere["members"], "a pool entry's members")
        self.assertGreater(
            len(members),
            RETAINED,
            "R2 inherits R1's retained window, so its declaration is not empty while "
            "the repository carries those artefacts (registry.md §3, FAM-12.4): %r"
            % (len(members),),
        )
        for member in members:
            member = as_mapping(member, "a pool member")
            self.assertFalse(
                os.path.isabs(as_text(member["path"], "a member's path")),
                "a member record spells its path repository-relative, the way a run "
                "record and the index do (checkpoints.md §2): %r" % (member["path"],),
            )
            self.assertTrue(
                os.path.isfile(resolved(member["path"])),
                "the declared window names files the repository carries "
                "(protocol.md §5, FAM-12.5): %r" % (member["path"],),
            )

    def test_trn_6_9_a_run_adds_nothing_and_changes_nothing_under_the_declared_tree(self):
        """TRN-6.9 a successful `training.run` adds no path under `<repo>/checkpoints` and no byte — files and directories both: no file added, no directory added, neither lost, no byte changed — while its own eleven artefacts land under the write root, which this case reads from `PYPOKER_CHECKPOINT_ROOT` alone and never from `layout._write_root()`, `layout.OVERRIDE` or any internal of `src/training/`, and are the paths its record names (docs/L3/training/checkpoints.md §2, §5, docs/L2/training/write-root.md §1, §3, §5, docs/L3/training/loop.md §2, §4, guardrails G20, FAM-16.31); it requires the session's write-root redirection and fails, before it runs and before it snapshots, when that redirection is absent."""
        root = os.path.abspath(write_root())
        self.assertNotEqual(
            root,
            os.path.abspath(CHECKPOINT_ROOT),
            "this case holds a run against the shipped set, so it needs the session's "
            "write-root redirection: tests/conftest.py points PYPOKER_CHECKPOINT_ROOT "
            "at a private mkdtemp for the whole session, and with it absent the write "
            "root IS <repo>/checkpoints — the run below would write the shipped tree "
            "this guardrail forbids, and the failure would name the implementation for "
            "a redirection the runner never set. Run the battery as "
            "`.venv/bin/python -m pytest tests/training -q` from the repository root "
            "(docs/L2/training/write-root.md §1, §3, docs/L3/training/checkpoints.md "
            "§5, battery.md §2): the write root is %r and the declared root is %r"
            % (root, os.path.abspath(CHECKPOINT_ROOT)),
        )
        package = training()
        before_tree = checkpoint_tree()
        before_directories = tree_directories()
        before_bytes = tree_digest(before_tree)
        self.assertTrue(
            before_tree,
            "the declared tree carries the shipped artefacts this case holds a run "
            "against, so an empty snapshot would make the guardrail vacuous "
            "(checkpoints.md §5, protocol.md §5): %r" % (before_tree,),
        )
        record = as_mapping(
            package.run("R1", [DECLARED_SEED], TINY_BUDGET), "training.run's record"
        )
        after_tree = checkpoint_tree()
        after_directories = tree_directories()
        after_bytes = tree_digest(after_tree)
        added = [path for path in after_tree if path not in before_tree]
        self.assertEqual(
            added,
            [],
            "a run writes under the write root and never into the shipped set, so "
            "<repo>/checkpoints gains no path — no snapshot, no final model, no "
            "directory holding them — after a run has succeeded "
            "(write-root.md §1, §3, checkpoints.md §5, guardrails G20): %r was added — "
            "and if another process is writing the declared tree while this case runs "
            "(a reader's default run, `scripts/regenerate-evidence.py`, a notebook "
            "kernel), that concurrent writer is the cause and not this module's write "
            "path, since a run of this battery is redirected away from the shipped set "
            "and this case's whole window is one ten-hand run" % (added,),
        )
        added_directories = [
            path for path in after_directories if path not in before_directories
        ]
        self.assertEqual(
            added_directories,
            [],
            "and gains no directory either, because a directory is a path and "
            "`checkpoints.md` §2's `<rung>/<variant>/seed-<seed>/` is one the write root "
            "carries a copy of: a run that makes the pair's directory under "
            "<repo>/checkpoints while saving under the write root adds `checkpoints/"
            "R1/naive-numeric/seed-<seed>/` and leaves the file listing above blind to "
            "it, which is exactly the defect this half names "
            "(write-root.md §1, §3, checkpoints.md §2, §5, guardrails G20): %r was "
            "added — and if another process is writing the declared tree while this "
            "case runs (a reader's default run, `scripts/regenerate-evidence.py`, a "
            "notebook kernel), that concurrent writer is the cause and not this "
            "module's write path, since a run of this battery is redirected away from "
            "the shipped set and this case's whole window is one ten-hand run"
            % (added_directories,),
        )
        lost = [path for path in before_tree if path not in after_tree]
        self.assertEqual(
            lost,
            [],
            "and the run loses none either: a write is never a move or a removal, so the "
            "shipped artefacts the index and every declared window name are all still "
            "under <repo>/checkpoints (write-root.md §1, checkpoints.md §5, guardrails "
            "G20): %r went missing" % (lost,),
        )
        lost_directories = [
            path for path in before_directories if path not in after_directories
        ]
        self.assertEqual(
            lost_directories,
            [],
            "and the run loses no directory either: a write is never a move or a "
            "removal, so the rung, variant and seed-<seed> levels the declared layout "
            "fixes are all still under <repo>/checkpoints "
            "(write-root.md §1, checkpoints.md §2, §5, guardrails G20): %r went missing"
            % (lost_directories,),
        )
        changed = [
            path
            for path in sorted(set(before_bytes) | set(after_bytes))
            if before_bytes.get(path) != after_bytes.get(path)
        ]
        self.assertEqual(
            changed,
            [],
            "the run changes no byte under <repo>/checkpoints — not a retained snapshot "
            "and not the pair's final model, not even in place — because every path "
            "agents.save is handed is re-rooted at the write root before the save "
            "(write-root.md §1, §3, §5, checkpoints.md §5, guardrails G20): these "
            "paths changed: %r — and if another process is writing the declared tree "
            "while this case runs (a reader's default run, "
            "`scripts/regenerate-evidence.py`, a notebook kernel), that concurrent "
            "writer is the cause and not this module's write path, since a run of this "
            "battery is redirected away from the shipped set and this case's whole "
            "window is one ten-hand run" % (changed,),
        )
        self.assertIn(
            DECLARED_SEED,
            seed_set(record),
            "the record states the seed set this case asked for, so a record from another "
            "run — a cached one, or an earlier case's — cannot stand in for this run and "
            "leave the two snapshots above measuring nothing (loop.md §4, §5, "
            "records.md §12): %r" % (record.get("seeds"),),
        )
        block = checkpoint_block(record, "naive-numeric", DECLARED_SEED)
        paths = listed_paths(block)
        self.assertEqual(
            len(paths),
            RETAINED + 1,
            "a pair's record names M + 1 artefacts — the retained five and the final "
            "model — and never the ten plus the final (checkpoints.md §3, guardrails G5, "
            "FAM-12.4): %r" % (paths,),
        )
        snapshots = as_sequence(block["snapshots"], "'snapshots'")
        self.assertEqual(
            len(snapshots),
            RETAINED,
            "the run wrote a snapshot every budget // 10 hands and the record retains the "
            "last five of the ten (checkpoints.md §3, loop.md §2, FAM-12.4): %r"
            % (snapshots,),
        )
        own = write_tree()
        for path in paths:
            with self.subTest(artefact=path):
                absolute = os.path.abspath(resolved(path))
                self.assertTrue(
                    os.path.isfile(absolute),
                    "the record carries the paths agents.save wrote, so each one is a "
                    "file a talk can load (checkpoints.md §2, write-root.md §5, "
                    "FAM-12.1): %r" % (absolute,),
                )
                self.assertTrue(
                    absolute == root or absolute.startswith(root + os.sep),
                    "the artefact lies under the write root and not merely somewhere, so "
                    "the run wrote where write-root.md §1 says it writes and nowhere "
                    "else (write-root.md §1, §3, guardrails G20): %r is not under %r"
                    % (absolute, root),
                )
                relative = os.path.relpath(absolute, root).replace(os.sep, "/")
                self.assertIn(
                    relative,
                    own,
                    "the file the record names is one the run actually left under the "
                    "write root, which is the positive half of this guardrail: a run that "
                    "wrote nowhere would leave the shipped tree untouched and prove "
                    "nothing (write-root.md §1, checkpoints.md §5, battery.md §2): %r is "
                    "not in %r" % (relative, own),
                )
        pair = [name for name in own if "seed-%d" % (DECLARED_SEED,) in name]
        self.assertEqual(
            len(pair),
            SNAPSHOTS + 1,
            "the write root holds this pair's eleven artefacts — budget // 10 is one "
            "hand at the battery's ten, so ten snapshots and the final model — because "
            "the run wrote every snapshot it took and not only the retained five "
            "(checkpoints.md §3, loop.md §2, write-root.md §1, guardrails G20): %r"
            % (pair,),
        )


if __name__ == "__main__":
    unittest.main()
