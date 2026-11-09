"""EVL-14 — the utility axis: D-20's `utility` in every record this module shapes.

Drives `docs/L1/utilities.md` §2, §5-§9, `docs/L1/records.md` §7-§10, §13,
`docs/L1/e2e-surface.md` §2, §3.4 and D-20: the utility catalogue read through
`agents.learners()["utilities"]` and never copied, the required key a version record
that names none is refused under, the family's one-rule-one-utility rule, the
digest payload's `id` `\\x1f` `rule` `\\x1f` `utility`, `offer`'s family check,
`pool_members`'s `utilities` beside its `rules`, a cell's and a matrix's per-member
`utilities` with their `utility_population`, the refusal of a member record that
contradicts its checkpoint, the report's pool family completed to the population its
table measured, and the fit that reads none of it.

The L1 battery already drives D-20 from above: `tests/e2e/test_fam18_utilities.py`
FAM-18.10 and FAM-18.11 take a two-utility table and a two-utility pool and ask
whether the records name what their policies carry.  This file is the layer below it:
whether each record's `utilities` is *derived* the way the documents say — the
catalogue's own members, the required key a membership declaration must carry beside the
bare record a policy entry point still admits without it, the window's order rather than
a sort, `None` excluded from a population, and a refusal that names the member and both
values before a hand is played.  Nothing here re-drives what FAM-18 asserts at the
surface.

The case ids are `EVL-14.k`.  `docs/L3/evaluation/guardrails.md` fixes the unit
battery's prefixes and records that 8 and 10 are unused, so this file takes the next
free number in the series rather than one of those reserved holes, and every assertion
below is quoted from the L1 documents this battery drives.

Cost discipline is the battery's (`_evaluation_support.py`): every real table a case
reads is one of the four shared matrices — `k5` for a one-objective table and `k7` for
its D-20 counterpart, whose pool member was written under `stack-shortfall` and whose
labelled variant under `net-chips` — and every other record is hand-built in
`records.md` §8-§10's shape.  No case builds a table of its own.
"""

import hashlib
import unittest
from unittest import mock

from _evaluation_support import (
    BASELINES,
    DEFAULT_RULE,
    DEFAULT_UTILITY,
    MATCH_HANDS,
    MATCH_SEED,
    OTHER_RULE,
    OTHER_UTILITY,
    POOL_M,
    RUNG_NAME,
    START_LABEL,
    UTILITIES,
    VERSION_IDS,
    EvaluationCase,
    SurfaceAbsent,
    balanced,
    checkpoint,
    declaration,
    family_value,
    first_legal,
    hand_matrix,
    last_legal,
    member_id,
    pool_digest,
    pool_member_ids,
    pool_rules,
    pool_utilities,
    rating_record,
    refusal_class,
    run_record,
    shortfall_checkpoint,
    version_chain,
    version_record,
)

#: A utility name the catalogue does not carry, for the "read, never copied" cases.
INVENTED_UTILITY = "shortfall-per-chip-5608"

#: The reward token the invented catalogue member declares, so a patched catalogue is a
#: catalogue entry and not a bare name (`utilities.md` §2).
INVENTED_REWARD = "invented-utility-reward-token"

#: The start label of a second family (`families.md` §1-§2).
SECOND_START_LABEL = "own-start-utility-5609"

#: A seed whose draw lands on the version member of a four-member pool:
#: `_draw_index(seed, n) = seed % n` (`scheduler.md` §3, `pool.md` §7).
DRAW_SEED = 7


def ids_digest(ids):
    """`families.md` §4's digest over bare ids — the payload a version's line replaces.

    A pool that digested its members' ids alone is what D-20's version line must be
    distinguishable from, so the case recomputes that weaker payload here rather than
    trusting the module's own `_pool_id` (`families.md` §4, ASM-27, D-20).
    """
    payload = "\n".join(str(name) for name in ids).encode("utf-8")
    return "pool-" + hashlib.sha256(payload).hexdigest()[:16]


def rule_digest(members):
    """The payload a version's line carried before D-20: its `id`, `\\x1f`, its `rule`.

    A digest that leaves the utility out is red for a membership declared under two
    objectives, so the case recomputes the rule-only payload too (`families.md` §4,
    ASM-27, D-19, D-20).
    """
    lines = []
    for member in members:
        if member.get("baseline"):
            lines.append(str(member["id"]))
        else:
            lines.append("%s\x1f%s" % (member["id"], member["rule"]))
    payload = "\n".join(lines).encode("utf-8")
    return "pool-" + hashlib.sha256(payload).hexdigest()[:16]


class UtilityCase(EvaluationCase):
    """The utility axis, driven through one helper that keeps the refusals honest."""

    def refused(self, call, entry, groups=(), label="", kind=None):
        """Run `call` and require this module's own refusal naming `entry` and `groups`.

        `errors.md` §1-§2: a refusal must be catchable as `EvaluationError`, so a
        `KeyError` from a mistyped record key or a NumPy error is an internal decision
        leaking as a crash and is red here.  `kind`, when the case gives one, is the
        refusal class `errors.md` §2 declares for the contract being driven —
        `UnknownUtility` and `UtilityMismatch`, D-20's two — and the message grammar is
        `errors.md` §3's.
        """
        where = label or entry
        root = refusal_class()
        try:
            value = call()
        except SurfaceAbsent:
            raise
        except Exception as exc:
            self.assertIsInstance(
                exc,
                root,
                "%s was refused with %s, which is not this module's own refusal (%s), so "
                "a caller catching EvaluationError would miss it: %r (errors.md §1-§2)"
                % (where, type(exc).__name__, root.__name__, exc),
            )
            self.assert_refused_like(exc, entry, groups, where)
            if kind is not None:
                self.assertEqual(
                    type(exc).__name__,
                    kind,
                    "%s is the refusal errors.md §2 declares for this contract, and the "
                    "refusal arrived as %s instead: %r (errors.md §2, utilities.md §5-§7, "
                    "D-20)" % (where, type(exc).__name__, exc),
                )
            return exc
        self.fail("%s accepted %r, which the contract refuses" % (where, value))

    def refused_playing_nothing(self, call, entry, groups=(), label="", kind=None):
        """`refused`, and the refusal must also leave the global stream where it found it.

        A refusal that names the contract is only half the promise: `errors.md` §1 and
        `scheduler.md` §6 also place it *before* the first hand is dealt, which is
        observable as an unmoved `random` stream (`surface.md` §1, ASM-2).
        """
        before = self.stream_state()
        exc = self.refused(call, entry, groups=groups, label=label, kind=kind)
        self.assert_stream_unchanged(before, label or entry)
        return exc

    def members_of_read(self, pool):
        """A pool record's members keyed by id (`records.md` §8)."""
        return {member_id(entry): entry for entry in self.pool_members(pool)["members"]}

    def patched_catalogue(self, utilities):
        """`agents.learners()` with its `utilities` entry replaced, everything else kept.

        The real catalogue's other keys — `learning_rules` among them — are carried
        through unchanged, so a patched call is still a catalogue `build_pool` can read
        and only the utility axis is the case's own (`utilities.md` §2, D-20).
        """
        declared = dict(self.agents().learners())
        declared["utilities"] = {name: dict(entry) for name, entry in utilities.items()}
        return declared, mock.patch.object(
            self.agents(), "learners", new=lambda: declared
        )

    # -- the catalogue, and the names it does not carry (utilities.md §2, §5) ----
    def test_evl_14_1_the_catalogue_is_the_source_and_a_name_it_lacks_is_refused(self):
        """EVL-14.1 a version's `utility` is one of `agents.learners()["utilities"]`'s members — read off the granted arrow and never copied — and a name the catalogue lacks is `UnknownUtility` naming the member, the name and the catalogue, while an empty name or one holding the digest's separator is refused as a rule's is (`utilities.md` §2, §5, `records.md` §7, `pool.md` §2, D-20)."""
        package = self.evaluation()
        catalogue = self.catalogue_utilities()
        self.assertEqual(
            tuple(catalogue[:2]),
            (DEFAULT_UTILITY, OTHER_UTILITY),
            "the catalogue publishes `net-chips` then `stack-shortfall`, so the names "
            "this case asserts against are the module's own and the first is the "
            "declared default (utilities.md §2, §5, D-20): %r" % (catalogue,),
        )
        self.assertEqual(
            tuple(catalogue),
            UTILITIES,
            "utilities.md §2 publishes exactly two members, so a third arriving without "
            "a case of its own is visible here (D-20): %r" % (catalogue,),
        )
        for utility in (DEFAULT_UTILITY, OTHER_UTILITY):
            with self.subTest(utility=utility):
                declared = version_record(VERSION_IDS[0], START_LABEL, utility=utility)
                read = self.members_of_read(
                    self.frozen_pool(members=[declared], m=POOL_M)
                )
                self.assertEqual(
                    read[VERSION_IDS[0]]["utility"],
                    utility,
                    "each version member carries the utility it was trained under, so a "
                    "table can name it and the pool id can certify it (records.md §7, "
                    "utilities.md §6, §7, ASM-27, D-20): %r"
                    % (read.get(VERSION_IDS[0]),),
                )
        for label, utility in (
            ("a name outside the catalogue", INVENTED_UTILITY),
            ("an empty name", ""),
            ("a name holding the digest's separator", "net\x1fchips"),
            ("a name holding a newline", "net-chips\n"),
            ("a name that is not a string", 42),
        ):
            with self.subTest(case=label):
                offender = version_record(VERSION_IDS[0], START_LABEL)
                offender["utility"] = utility
                if utility == INVENTED_UTILITY:
                    groups = (
                        (VERSION_IDS[0],),
                        (INVENTED_UTILITY,),
                        (DEFAULT_UTILITY,),
                        (OTHER_UTILITY,),
                    )
                    kind = "UnknownUtility"
                else:
                    groups = (("utility",), (VERSION_IDS[0],))
                    kind = None
                self.refused(
                    lambda offender=offender: package.build_pool(
                        declaration(members=[offender], m=POOL_M)
                    ),
                    entry="build_pool",
                    groups=groups,
                    label="a version declaring the utility %r" % (utility,),
                    kind=kind,
                )

    def test_evl_14_2_the_catalogue_is_read_at_call_time_and_never_copied(self):
        """EVL-14.2 a catalogue changed under the module changes what `build_pool` accepts and reads back — the catalogue's own order still governs what a name means — while a record that names no `utility` is refused by name under every catalogue, because no member of it, first or otherwise, speaks for a version that declares none (`utilities.md` §2, §5, `module-map.md` §2, D-20)."""
        package = self.evaluation()
        real = {
            name: dict(entry)
            for name, entry in self.agents().learners()["utilities"].items()
        }
        invented = dict(real)
        invented[INVENTED_UTILITY] = {
            "name": INVENTED_UTILITY,
            "reward": INVENTED_REWARD,
            "normaliser": "none",
        }
        declared, patch = self.patched_catalogue(invented)
        with patch:
            self.assertEqual(
                tuple(self.catalogue_utilities()),
                (DEFAULT_UTILITY, OTHER_UTILITY, INVENTED_UTILITY),
                "the case's catalogue is the one the module must read, in its order "
                "(utilities.md §2, D-20): %r" % (declared["utilities"],),
            )
            member = version_record(
                VERSION_IDS[0], START_LABEL, utility=INVENTED_UTILITY
            )
            pool = package.build_pool(declaration(members=[member], m=POOL_M))
            read = self.pool_members(pool)
            self.assertEqual(
                self.members_of_read(pool)[VERSION_IDS[0]]["utility"],
                INVENTED_UTILITY,
                "a name the catalogue publishes is a name a member may declare, so the "
                "module reads the catalogue on every call and holds no copy of it "
                "(utilities.md §2, §5, module-map.md §2, D-20): %r" % (read,),
            )
            self.assertEqual(
                tuple(pool_utilities(read)),
                (INVENTED_UTILITY,),
                "the record's `utilities` is the same catalogue read, so it names the "
                "patched member (records.md §8, D-20): %r" % (read,),
            )
        with self.subTest(case="no catalogue member is a version's default"):
            _declared, reordered = self.patched_catalogue({OTHER_UTILITY: real[OTHER_UTILITY]})
            with reordered:
                silent = version_record(VERSION_IDS[0], START_LABEL)
                silent.pop("utility")
                self.refused(
                    lambda: package.build_pool(
                        declaration(members=[silent], m=POOL_M)
                    ),
                    entry="build_pool",
                    groups=((VERSION_IDS[0],), ("utility",)),
                    label="a version declaring no utility under a one-member catalogue",
                    kind="MemberInvalid",
                )
                named = version_record(
                    VERSION_IDS[0], START_LABEL, utility=OTHER_UTILITY
                )
                pool = package.build_pool(declaration(members=[named], m=POOL_M))
                read = self.pool_members(pool)
                self.assertEqual(
                    self.members_of_read(pool)[VERSION_IDS[0]]["utility"],
                    OTHER_UTILITY,
                    "a name the patched catalogue publishes is admitted and reads back as "
                    "it, so the catalogue's order still governs what a name means while its "
                    "first member speaks for no membership (utilities.md §2, §5, "
                    "records.md §7, D-20): %r" % (read,),
                )
                self.assertEqual(
                    tuple(pool_utilities(read)),
                    (OTHER_UTILITY,),
                    "the record's `utilities` is the declared name and never the first "
                    "member of a catalogue the case patched (utilities.md §5, records.md "
                    "§8, D-20): %r" % (read,),
                )
                offender = version_record(
                    VERSION_IDS[0], START_LABEL, utility=DEFAULT_UTILITY
                )
                self.refused(
                    lambda: package.build_pool(
                        declaration(members=[offender], m=POOL_M)
                    ),
                    entry="build_pool",
                    groups=((VERSION_IDS[0],), (DEFAULT_UTILITY,), (OTHER_UTILITY,)),
                    label="a version declaring the catalogue's dropped first member",
                    kind="UnknownUtility",
                )
        with self.subTest(case="a catalogue that publishes nothing is no catalogue"):
            _declared, empty = self.patched_catalogue({})
            with empty:
                named = version_record(
                    VERSION_IDS[1], START_LABEL, utility=DEFAULT_UTILITY
                )
                self.refused(
                    lambda: package.build_pool(
                        declaration(members=[named], m=POOL_M)
                    ),
                    entry="build_pool",
                    groups=((VERSION_IDS[1],), (DEFAULT_UTILITY,), ("catalogue",)),
                    label="a named utility under a catalogue that publishes nothing",
                    kind="UnknownUtility",
                )
        self.assertEqual(
            tuple(self.catalogue_utilities()),
            UTILITIES,
            "the patch is the case's own: outside it the real catalogue governs again "
            "(utilities.md §2, D-20): %r" % (self.catalogue_utilities(),),
        )

    # -- the required key, refused by name (records.md §7, utilities.md §5) ---
    def test_evl_14_3_a_declared_version_that_omits_utility_is_refused_by_name(self):
        """EVL-14.3 a `build_pool` member that carries no `utility` is refused as `MemberInvalid` naming the member and the missing required key, never read as the catalogue's first member — and the same record that declares `net-chips` builds and reads back carrying it, so the refusal is the absence and not the record (`records.md` §7, `utilities.md` §5, §6, ASM-27, D-20)."""
        package = self.evaluation()
        self.assertEqual(
            self.catalogue_utilities()[0],
            DEFAULT_UTILITY,
            "the catalogue's first member is `net-chips`, the name a silent record would "
            "have been read under — so the refusal is the required key's requirement and "
            "not a catalogue that holds no default to read (utilities.md §2, §5, D-20): %r"
            % (self.catalogue_utilities(),),
        )
        silent = version_record(VERSION_IDS[0], START_LABEL, step=240, samples=960)
        silent.pop("utility")
        self.refused(
            lambda: package.build_pool(declaration(members=[silent], m=POOL_M)),
            entry="build_pool",
            groups=((VERSION_IDS[0],), ("utility",)),
            label="a version member carrying no utility",
            kind="MemberInvalid",
        )
        explicit = version_record(
            VERSION_IDS[0], START_LABEL, step=240, samples=960, utility=DEFAULT_UTILITY
        )
        control = package.build_pool(declaration(members=[explicit], m=POOL_M))
        read_explicit = self.pool_members(control)
        member = self.members_of_read(control)[VERSION_IDS[0]]
        self.assertIn(
            "utility",
            member,
            "the member read back carries the key records.md §7 marks required, so a "
            "reader is never left to infer it (records.md §7, utilities.md §5, §6): %r"
            % (member,),
        )
        self.assertEqual(
            member["utility"],
            DEFAULT_UTILITY,
            "the control is that same record declaring `net-chips`, and the member read "
            "back carries that name: the refusal above is the absent key and not the "
            "record (records.md §7, utilities.md §5, §6, ASM-27, D-20): %r" % (member,),
        )
        self.assertEqual(
            tuple(pool_utilities(read_explicit)),
            (DEFAULT_UTILITY,),
            "the pool record's `utilities` names the objective its member declared, read "
            "off the member and never filled in (records.md §8, D-20): %r"
            % (read_explicit,),
        )
        with self.subTest(case="no default is substituted for a member of a chain"):
            chain = version_chain(VERSION_IDS[:2], utility=DEFAULT_UTILITY)
            chain[1].pop("utility")
            self.refused(
                lambda: package.build_pool(declaration(members=chain, m=POOL_M)),
                entry="build_pool",
                groups=((VERSION_IDS[1],), ("utility",)),
                label="a chain whose newest member carries no utility",
                kind="MemberInvalid",
            )
            declared_chain = version_chain(VERSION_IDS[:2], utility=DEFAULT_UTILITY)
            read_chain = self.pool_members(
                package.build_pool(declaration(members=declared_chain, m=POOL_M))
            )
            self.assertEqual(
                tuple(pool_utilities(read_chain)),
                (DEFAULT_UTILITY,),
                "the same two-member chain with both utilities declared builds, and its "
                "`utilities` names only what its members declared (records.md §7, §8, "
                "D-20): %r" % (read_chain,),
            )
            self.assertEqual(
                pool_member_ids(read_chain),
                tuple(BASELINES) + tuple(VERSION_IDS[:2]),
                "a membership carries every member or none: the chain is read back in "
                "full only when each member of it names its objective, so no member is "
                "read back under a name its record did not carry (records.md §7, §8, "
                "ASM-27, D-20): %r" % (pool_member_ids(read_chain),),
            )

    # -- one family is one chain under one rule and one utility --------------
    def test_evl_14_4_a_family_is_one_chain_under_one_rule_and_one_utility(self):
        """EVL-14.4 a chain whose members declare two utilities is `UtilityMismatch` naming the member, the utility and the family's, and a two-family pool under two utilities is accepted — one chain under one utility, every member of it (`families.md` §1, §6, `records.md` §8, ASM-26, D-20)."""
        package = self.evaluation()
        for utility in (DEFAULT_UTILITY, OTHER_UTILITY):
            with self.subTest(utility=utility):
                read = self.pool_members(
                    self.frozen_pool(
                        members=version_chain(VERSION_IDS[:2], utility=utility),
                        m=POOL_M,
                    )
                )
                self.assertEqual(
                    tuple(pool_utilities(read)),
                    (utility,),
                    "one chain of two snapshots declares one utility, which is what "
                    "makes it one family (families.md §1, ASM-26, D-20): %r" % (read,),
                )
                self.assertEqual(
                    pool_member_ids(read),
                    tuple(BASELINES) + tuple(VERSION_IDS[:2]),
                    "a family's one utility changes no membership (families.md §1): %r"
                    % (pool_member_ids(read),),
                )
        chain = version_chain(VERSION_IDS[:2], utility=DEFAULT_UTILITY)
        chain[1] = dict(chain[1], utility=OTHER_UTILITY)
        self.refused(
            lambda: package.build_pool(declaration(members=chain, m=POOL_M)),
            entry="build_pool",
            groups=(
                (VERSION_IDS[1],),
                (OTHER_UTILITY,),
                (DEFAULT_UTILITY,),
                (START_LABEL,),
            ),
            label="a chain whose two members declare two utilities",
            kind="UtilityMismatch",
        )
        two_utilities = version_chain(VERSION_IDS[:2], utility=DEFAULT_UTILITY) + (
            version_chain(
                VERSION_IDS[2:4], start=SECOND_START_LABEL, utility=OTHER_UTILITY
            )
        )
        read = self.pool_members(
            package.build_pool(declaration(members=two_utilities, m=5))
        )
        self.assertEqual(
            tuple(pool_utilities(read)),
            (DEFAULT_UTILITY, OTHER_UTILITY),
            "a two-family pool under two objectives is accepted, and its `utilities` "
            "names both in the window's order: the pool holds a heterogeneous objective "
            "population on purpose (records.md §8, utilities.md §7, D-18, D-20): %r"
            % (read,),
        )
        self.assertEqual(
            tuple(pool_rules(read)),
            (DEFAULT_RULE,),
            "the two families declare one rule, so the objective population is not the "
            "rule population (records.md §8, D-19, D-20): %r" % (read,),
        )
        self.assertEqual(
            pool_member_ids(read),
            tuple(BASELINES) + tuple(VERSION_IDS[:4]),
            "the two chains are listed contiguously oldest to newest, the families in the "
            "order they entered (families.md §2, ASM-26): %r"
            % (pool_member_ids(read),),
        )

    # -- the digest payload (families.md §4, ASM-27, D-20) -------------------
    def test_evl_14_5_the_id_digests_each_version_s_utility_beside_its_rule(self):
        """EVL-14.5 a version's line carries `id`, `\\x1f`, `rule`, `\\x1f`, `utility`, so one membership under two utilities wears two ids — each recomputed here — while a baselines-only pool keeps its id and `m`, `frozen`, `step` and `samples` stay outside the payload (`families.md` §4, `records.md` §8, ASM-27, D-20)."""
        package = self.evaluation()
        chips = version_record(
            VERSION_IDS[0], START_LABEL, step=120, samples=480, utility=DEFAULT_UTILITY
        )
        shortfall = dict(chips, utility=OTHER_UTILITY)
        read_chips = self.pool_members(
            package.build_pool(declaration(members=[chips], m=POOL_M))
        )
        read_shortfall = self.pool_members(
            package.build_pool(declaration(members=[shortfall], m=POOL_M))
        )
        for label, read in (
            ("net-chips", read_chips),
            ("stack-shortfall", read_shortfall),
        ):
            with self.subTest(utility=label):
                self.assertEqual(
                    read["id"],
                    pool_digest(read["members"]),
                    "the id is `pool-` and the first sixteen hex of the SHA-256 over one "
                    "line per member, a version's line carrying its id, the separator, "
                    "its rule, the separator, then its utility — recomputed here from the "
                    "read-back's own order (families.md §4, ASM-27, D-20): %r against %r"
                    % (read["id"], pool_digest(read["members"])),
                )
        self.assertNotEqual(
            read_chips["id"],
            read_shortfall["id"],
            "one membership under two objectives does not wear one id, so a table can say "
            "which objective population a rating was fitted over (records.md §8, "
            "utilities.md §7, ASM-27, D-20): %r against %r"
            % (read_chips["id"], read_shortfall["id"]),
        )
        for label, weaker in (
            ("the ids alone", ids_digest(pool_member_ids(read_chips))),
            ("the ids and the rule", rule_digest(read_chips["members"])),
        ):
            with self.subTest(payload=label):
                self.assertNotEqual(
                    read_chips["id"],
                    weaker,
                    "a payload of %s leaves the utility out, and D-20 puts it in the "
                    "version's line, so the two digests differ (families.md §4, ASM-27, "
                    "D-20): %r against %r" % (label, read_chips["id"], weaker),
                )
        with self.subTest(case="a baselines-only pool keeps its id"):
            baselines_only = self.pool_members(
                package.build_pool(declaration(members=(), m=5, frozen=True))
            )
            self.assertEqual(
                baselines_only["id"],
                pool_digest(BASELINES),
                "a baseline contributes its id alone, so a baselines-only pool digests as "
                "a bare list of names and the id a shipped artefact records survives "
                "D-20's arrival unchanged (families.md §4, ASM-27, D-20): %r against %r"
                % (baselines_only["id"], pool_digest(BASELINES)),
            )
            self.assertEqual(
                baselines_only["id"],
                ids_digest(BASELINES),
                "with no version in the window the two payloads coincide, which is what "
                "keeps R1's id stable (families.md §4, ASM-27): %r"
                % (baselines_only["id"],),
            )
        with self.subTest(case="m, frozen, step, samples and seed stay outside it"):
            corrected = dict(chips, step=999, samples=4321, seed=99991)
            other = self.pool_members(
                package.build_pool(declaration(members=[corrected], m=1, frozen=False))
            )
            self.assertEqual(
                other["id"],
                read_chips["id"],
                "a corrected step, samples or seed is not a membership change, and "
                "neither is the bound or the frozen flag, so the pool keeps its id "
                "(families.md §4, pool.md §4, ASM-27): %r against %r"
                % (other["id"], read_chips["id"]),
            )
            self.assertIs(
                other["frozen"],
                False,
                "the read-back states the frozen flag it was given, which the payload "
                "excludes (records.md §8, families.md §4): %r" % (other,),
            )

    # -- offer's family check (families.md §5, §6) --------------------------
    def test_evl_14_6_offer_holds_a_version_to_its_family_s_utility(self):
        """EVL-14.6 `offer` refuses a version whose utility differs from its family's as `UtilityMismatch` naming the member, both utilities and the family's newest member, refuses an offered version that names no `utility` as a missing required key before that family comparison, and refuses an uncatalogued one by name (`families.md` §5, §6, `surface.md` §7, `utilities.md` §5, `records.md` §7, D-20)."""
        package = self.evaluation()
        chips_pool = self.open_pool(
            members=version_chain(VERSION_IDS[:2], utility=DEFAULT_UTILITY), m=5
        )
        advanced = package.offer(
            chips_pool, version_record(VERSION_IDS[2], VERSION_IDS[1], step=320)
        )
        read = self.pool_members(advanced)
        self.assertEqual(
            self.members_of_read(advanced)[VERSION_IDS[2]]["utility"],
            DEFAULT_UTILITY,
            "an offered version that declares `net-chips`, as the helper's declared name "
            "is, is admitted into a family under that utility and the member read back "
            "carries it (utilities.md §5, §6, records.md §7, D-20): %r" % (read,),
        )
        self.assertEqual(
            read["id"],
            pool_digest(read["members"]),
            "the advanced pool's id digests its newest member's utility like every other "
            "version's line (families.md §4, ASM-27, D-20): %r" % (read["id"],),
        )
        relabelled = version_record(
            VERSION_IDS[3], VERSION_IDS[2], step=400, utility=OTHER_UTILITY
        )
        self.refused(
            lambda: package.offer(advanced, relabelled),
            entry="offer",
            groups=(
                (VERSION_IDS[3],),
                (OTHER_UTILITY,),
                (DEFAULT_UTILITY,),
                (VERSION_IDS[2],),
            ),
            label="an offer whose utility is not its family's",
            kind="UtilityMismatch",
        )
        shortfall_pool = self.open_pool(
            members=version_chain(VERSION_IDS[:2], utility=OTHER_UTILITY), m=5
        )
        silent = version_record(VERSION_IDS[4], VERSION_IDS[1], step=480)
        silent.pop("utility")
        exc = self.refused(
            lambda: package.offer(shortfall_pool, silent),
            entry="offer",
            groups=((VERSION_IDS[4],), ("utility",)),
            label="an offer declaring none into a family that declares the other utility",
            kind="MemberInvalid",
        )
        self.assertNotIn(
            OTHER_UTILITY,
            str(exc),
            "the absent key is refused before the family's own utility is even compared, "
            "so the message names the missing key and no family objective — the version "
            "never reaches UtilityMismatch (utilities.md §5, records.md §7, families.md "
            "§5, D-20): %r" % (str(exc),),
        )
        uncatalogued = version_record(
            VERSION_IDS[5], VERSION_IDS[1], step=560, utility=INVENTED_UTILITY
        )
        self.refused(
            lambda: package.offer(chips_pool, uncatalogued),
            entry="offer",
            groups=(
                (VERSION_IDS[5],),
                (INVENTED_UTILITY,),
                (DEFAULT_UTILITY,),
                (OTHER_UTILITY,),
            ),
            label="an offer naming a utility the catalogue does not carry",
            kind="UnknownUtility",
        )
        self.assertEqual(
            pool_member_ids(self.pool_members(chips_pool)),
            tuple(BASELINES) + tuple(VERSION_IDS[:2]),
            "a refused offer leaves its argument pool unchanged (pool.md §1, §6): %r"
            % (pool_member_ids(self.pool_members(chips_pool)),),
        )

    # -- pool_members' utilities beside its rules (records.md §8) -----------
    def test_evl_14_7_the_pool_record_declares_the_utilities_its_versions_hold(self):
        """EVL-14.7 `pool_members` returns a `utilities` tuple beside `rules` — the distinct utilities its version members declare, in the window's order and not sorted, the empty tuple for a baselines-only pool — freshly built on every call (`records.md` §8, `pool.md` §5, `utilities.md` §7, D-20)."""
        package = self.evaluation()
        shortfall_first = version_chain(
            VERSION_IDS[:2], start=SECOND_START_LABEL, utility=OTHER_UTILITY
        )
        chips_second = version_chain(VERSION_IDS[2:4], utility=DEFAULT_UTILITY)
        # The families enter in declaration order: the second utility's family first, so
        # a sorted `utilities` would be red and a window-ordered one is the contract.
        members = shortfall_first + chips_second
        pool = package.build_pool(declaration(members=members, m=5))
        read = self.pool_members(pool)
        self.assertIn(
            "utilities",
            read,
            "a pool record carries `utilities` beside `rules`, both required keys of "
            "records.md §8 (D-20): %r" % (sorted(read),),
        )
        self.assertEqual(
            tuple(pool_utilities(read)),
            (OTHER_UTILITY, DEFAULT_UTILITY),
            "the distinct utilities the version members declare, in the window's order — "
            "the family that entered first names the first entry (records.md §8, "
            "utilities.md §7, D-20): %r" % (read,),
        )
        self.assertEqual(
            tuple(pool_rules(read)),
            (DEFAULT_RULE,),
            "one rule for both families keeps `rules` a single entry, so the objective "
            "population is read off its own key (records.md §8, D-19, D-20): %r"
            % (read,),
        )
        self.assertEqual(
            len(tuple(pool_utilities(read))),
            len(set(pool_utilities(read))),
            "a pool record declares the **distinct** utilities, never one entry per "
            "member (records.md §8): %r" % (read,),
        )
        baselines_only = self.pool_members(
            package.build_pool(declaration(members=(), m=5))
        )
        self.assertEqual(
            tuple(pool_utilities(baselines_only)),
            (),
            "R1's pool is the three baselines alone, which declare no utility, so its "
            "`utilities` is the empty tuple and never `(None,)` (records.md §8, "
            "utilities.md §7, D-20): %r" % (baselines_only,),
        )
        self.assertEqual(
            (tuple(pool_rules(baselines_only)), tuple(pool_utilities(baselines_only))),
            ((), ()),
            "the two populations stand beside each other and are empty together for a "
            "baselines-only pool (records.md §8, D-20): %r" % (baselines_only,),
        )
        with self.subTest(case="the record is freshly built per call"):
            first = self.pool_members(pool)
            first["utilities"] = ("edited-by-the-case",)
            first["members"][-1]["utility"] = INVENTED_UTILITY
            second = self.pool_members(pool)
            self.assertEqual(
                tuple(pool_utilities(second)),
                (OTHER_UTILITY, DEFAULT_UTILITY),
                "editing the record a caller was handed changes nothing: a pool reads "
                "back what it holds (pool.md §5, records.md §8): %r" % (second,),
            )
            self.assertEqual(
                self.members_of_read(pool)[VERSION_IDS[3]]["utility"],
                DEFAULT_UTILITY,
                "and the member records are fresh copies too, so a member's utility is "
                "the one the declaration carried (pool.md §5, records.md §7): %r"
                % (self.members_of_read(pool)[VERSION_IDS[3]],),
            )

    # -- a cell names each member's utility (records.md §9) -----------------
    def test_evl_14_8_a_cell_names_the_utility_each_member_carried(self):
        """EVL-14.8 a cell's `utilities` names each member's utility by its id — the catalogue member its policy carries, so a member loaded from a checkpoint names the utility its container records, and `None` for a baseline or an opaque callable that carries none (`scheduler.md` §4-§5, `records.md` §9, `utilities.md` §6, §7, D-20)."""
        package = self.evaluation()
        saved = shortfall_checkpoint()
        cell = package.match(
            package.policy_from(saved["path"]), first_legal, MATCH_HANDS, MATCH_SEED
        )
        utilities = cell["utilities"]
        self.assertEqual(
            sorted(utilities),
            sorted(member_id(entry) for entry in cell["members"]),
            "a cell's `utilities` names each member of its pair by the cell's own ids "
            "(records.md §9, D-20): %r" % (utilities,),
        )
        self.assertEqual(
            utilities[cell["members"][0]],
            OTHER_UTILITY,
            "a member policy built from a checkpoint reports the utility its own "
            "container records, so the cell names the objective that met (utilities.md "
            "§6, §7, e2e-surface.md §2, D-20): %r" % (utilities,),
        )
        self.assertIsNone(
            utilities[cell["members"][1]],
            "an opaque callable carries no utility, and the cell says so with `None` "
            "rather than inventing one (records.md §9, e2e-surface.md §2, D-20): %r"
            % (utilities,),
        )
        with self.subTest(case="a baseline cell declares none"):
            baseline_cell = package.match("random", "oracle", MATCH_HANDS, MATCH_SEED)
            self.assertEqual(
                tuple(baseline_cell["utilities"].values()),
                (None, None),
                "a baseline is a fixed policy and not a model trained on a reward, so "
                "both sides of a baseline cell declare no utility (records.md §9, D-20): "
                "%r" % (baseline_cell["utilities"],),
            )
            self.assertEqual(
                tuple(baseline_cell["rules"].values()),
                (None, None),
                "the two catalogues are reported side by side and a baseline declares "
                "neither (records.md §9, D-19, D-20): %r" % (baseline_cell,),
            )
        with self.subTest(case="a version record side is the player its file records"):
            record = version_record(
                VERSION_IDS[0], START_LABEL, path=saved["path"], utility=OTHER_UTILITY
            )
            played = package.match(
                record,
                package.policy_from(checkpoint()["path"]),
                MATCH_HANDS,
                MATCH_SEED,
            )
            self.assertEqual(
                (
                    played["utilities"][VERSION_IDS[0]],
                    played["utilities"][played["members"][1]],
                ),
                (OTHER_UTILITY, DEFAULT_UTILITY),
                "a record side and a policy side each name the utility its checkpoint "
                "records, so one cell says which two objectives met (scheduler.md §5, "
                "records.md §9, D-20): %r" % (played["utilities"],),
            )
        with self.subTest(case="a policy this module did not build carries its own"):
            holder = checkpoint(name="utility-holder", utility=OTHER_UTILITY)
            carried = self.agents().as_policy(
                holder["learner"], holder["encoder"], holder["seed"]
            )
            named = package.match(carried, last_legal, MATCH_HANDS, MATCH_SEED)
            self.assertEqual(
                named["utilities"][named["members"][0]],
                OTHER_UTILITY,
                "a policy handed in from outside is named by the utility it carries and "
                "by nothing else — the cell reads it, it is not inferred (records.md §9, "
                "utilities.md §7, D-20): %r" % (named["utilities"],),
            )
        for label, utility, kind in (
            ("an uncatalogued name", INVENTED_UTILITY, "UnknownUtility"),
            ("an empty name", "", None),
            ("a name holding the separator", "stack\x1fshortfall", None),
        ):
            with self.subTest(case=label):
                offender = version_record(
                    VERSION_IDS[1], START_LABEL, path=saved["path"]
                )
                offender["utility"] = utility
                if utility == INVENTED_UTILITY:
                    groups = (
                        (VERSION_IDS[1],),
                        (INVENTED_UTILITY,),
                        (DEFAULT_UTILITY,),
                        (OTHER_UTILITY,),
                    )
                else:
                    groups = ((VERSION_IDS[1],), ("utility",))
                self.refused(
                    lambda offender=offender: package.match(
                        offender, "always-call", MATCH_HANDS, MATCH_SEED
                    ),
                    entry="match",
                    groups=groups,
                    label="a cell side declaring the utility %r" % (utility,),
                    kind=kind,
                )

    # -- a table names its objectives and their population (records.md §10) -
    def test_evl_14_9_a_matrix_names_each_member_s_utility_and_its_population(self):
        """EVL-14.9 a matrix's `utilities` names each member's utility by its id — `None` for a baseline and for a variant handed in as an opaque policy — and its `utility_population` is the distinct utilities those members declared, **sorted**, beside `rules` and `population` (`matrix.md` §5, `records.md` §10, `utilities.md` §9, D-20)."""
        one = self.shared_matrix("k5")
        members = list(one["members"])
        utilities = one["utilities"]
        self.assertEqual(
            sorted(utilities),
            sorted(members),
            "a table states each member's utility by its id, so the mapping names the "
            "whole membership (records.md §10, D-20): %r" % (utilities,),
        )
        for name in BASELINES:
            with self.subTest(baseline=name):
                self.assertIsNone(
                    utilities[name],
                    "a baseline is a fixed policy and declares no utility, and the table "
                    "says so with `None` (records.md §10, e2e-surface.md §2, D-20): %r"
                    % (utilities,),
                )
        self.assertEqual(
            utilities["variant-1"],
            DEFAULT_UTILITY,
            "a variant handed in as a member policy reports the utility its learner was "
            "built under, so the table names the objective it measured (utilities.md §7, "
            "records.md §10, D-20): %r" % (utilities,),
        )
        self.assertIsNone(
            utilities["variant-2"],
            "an opaque variant carries no utility and the record invents none (records.md "
            "§10, errors.md §5, D-20): %r" % (utilities,),
        )
        self.assertEqual(
            tuple(one["utility_population"]),
            (DEFAULT_UTILITY,),
            "`utility_population` is the distinct utilities the members declared, with "
            "the baselines' and the opaque policy's `None` excluded (records.md §10, "
            "D-20): %r" % (one["utility_population"],),
        )
        self.assertEqual(
            tuple(one["population"]),
            (DEFAULT_RULE,),
            "the objective population stands beside the rule population, each excluding "
            "its own `None`s (records.md §10, D-19, D-20): %r" % (one,),
        )
        for record, name in zip(list(one["member_records"]), members):
            with self.subTest(member=name):
                self.assertIn(
                    "utility",
                    record,
                    "each member record carries the utility its policy carries, so a "
                    "reader of one row is told which objective it is (matrix.md §5, "
                    "D-20): %r" % (record,),
                )
                self.assertEqual(
                    record["utility"],
                    utilities[name],
                    "a member's record and the table's `utilities` name one utility "
                    "(matrix.md §5): %r against %r"
                    % (record["utility"], utilities[name]),
                )
        with self.subTest(case="a table whose members declare two objectives"):
            # `k7`'s pool member was written under the second utility and its labelled
            # variant under the first, and the pool member is listed first: the population
            # must be sorted, so insertion order is red here.
            two = self.shared_matrix("k7")
            declared = two["utilities"]
            self.assertEqual(
                (declared[VERSION_IDS[1]], declared["variant-1"]),
                (OTHER_UTILITY, DEFAULT_UTILITY),
                "the table names the pool member's objective and the variant's, each the "
                "utility its own checkpoint records (matrix.md §4-§5, utilities.md §6, "
                "§7, D-20): %r" % (declared,),
            )
            self.assertEqual(
                tuple(two["utility_population"]),
                tuple(sorted(UTILITIES)),
                "`utility_population` holds both objectives in sorted order — the "
                "membership's own order is the reverse, so a population in insertion "
                "order is red (records.md §10, utilities.md §9, D-20): %r"
                % (two["utility_population"],),
            )
            self.assertEqual(
                tuple(
                    sorted(
                        declared[name]
                        for name in two["members"]
                        if declared[name] is not None
                    )
                ),
                tuple(two["utility_population"]),
                "the population is exactly the members' non-`None` utilities, distinct "
                "and sorted (records.md §10, D-20): %r against %r"
                % (tuple(two["utility_population"]), declared),
            )
            self.assertEqual(
                tuple(two["population"]),
                tuple(
                    sorted({rule for rule in two["rules"].values() if rule is not None})
                ),
                "the two populations are derived on the same terms, one from the rules "
                "and one from the utilities (records.md §10, D-19, D-20): %r" % (two,),
            )
            self.assertEqual(
                two["pool"],
                self.pool_members(self.shared_pool("k7"))["id"],
                "the table names the pool it measured by id, and that pool's window "
                "declares the second objective (records.md §8, §10, matrix.md §5, D-20)",
            )

    # -- a member record against its checkpoint (utilities.md §6, ASM-20) ---
    def test_evl_14_10_a_member_record_contradicting_its_checkpoint_is_refused(self):
        """EVL-14.10 a version record whose `utility` disagrees with the one its checkpoint records is `UtilityMismatch` naming the member and both values — through `match`, `matrix` and `opponent` alike — and the refusal comes before a hand is played, so it moves no stream (`scheduler.md` §5, `records.md` §7, `utilities.md` §6, ASM-20, D-20)."""
        package = self.evaluation()
        saved = self.checkpoint(name="contradicted-utility")
        witness = package.policy_from(saved["path"])
        self.assertEqual(
            getattr(witness, "utility", None),
            DEFAULT_UTILITY,
            "the file is the witness: a checkpoint built under no declared utility "
            "records the catalogue's first member, which is what a member record is held "
            "to (utilities.md §6, scheduler.md §5, ASM-20, D-20): %r" % (witness,),
        )
        honest = version_record(
            VERSION_IDS[0], START_LABEL, path=saved["path"], utility=DEFAULT_UTILITY
        )
        cell = package.match(honest, "always-call", MATCH_HANDS, MATCH_SEED)
        self.assertEqual(
            cell["utilities"][VERSION_IDS[0]],
            DEFAULT_UTILITY,
            "a member record that agrees with its file is played and its utility "
            "recorded (records.md §7, scheduler.md §5, D-20): %r" % (cell["utilities"],),
        )
        liar = dict(honest, utility=OTHER_UTILITY)
        groups = ((VERSION_IDS[0],), (OTHER_UTILITY,), (DEFAULT_UTILITY,))
        self.refused_playing_nothing(
            lambda: package.match(liar, "always-call", MATCH_HANDS, MATCH_SEED),
            entry="match",
            groups=groups,
            label="a member record contradicting its checkpoint's utility",
            kind="UtilityMismatch",
        )
        with self.subTest(case="the same contradiction through a table"):
            pool = self.frozen_pool(members=[liar], m=POOL_M)
            self.refused_playing_nothing(
                lambda: package.matrix(pool, [first_legal], "live"),
                entry="matrix",
                groups=groups,
                label="a table over a member record that contradicts its checkpoint",
                kind="UtilityMismatch",
            )
        with self.subTest(case="the same contradiction through a drawn opponent"):
            self.refused_playing_nothing(
                lambda: package.opponent(self.open_pool(members=[liar], m=POOL_M), DRAW_SEED),
                entry="opponent",
                groups=groups,
                label="a drawn member whose record contradicts its checkpoint",
                kind="UtilityMismatch",
            )
            drawn = package.opponent(
                self.open_pool(members=[honest], m=POOL_M), DRAW_SEED
            )
            self.assertEqual(
                getattr(drawn, "utility", None),
                DEFAULT_UTILITY,
                "the same draw of the honest record yields the player its file records, "
                "carrying the utility it was trained under (utilities.md §6, §7, "
                "pool.md §7, D-20): %r" % (drawn,),
            )

    # -- the report's pool family, and the population it states (records.md §13) --
    def test_evl_14_11_the_report_completes_its_pool_family_to_the_measured_objectives(self):
        """EVL-14.11 `report` completes its pool family's `utilities` to the matrix's `utility_population` in the same way it completes `rules` to `population`, adding no member and no third key and editing nothing it was handed (`records.md` §13, `report.md` §2, §4, `utilities.md` §7, §9, D-20)."""
        package = self.evaluation()
        membership = tuple(BASELINES) + ("variant-1", "variant-2")
        table = hand_matrix(balanced, members=membership)
        utilities = {name: None for name in membership}
        utilities["variant-1"] = DEFAULT_UTILITY
        utilities["variant-2"] = OTHER_UTILITY
        rules = {name: None for name in membership}
        rules["variant-1"] = DEFAULT_RULE
        rules["variant-2"] = OTHER_RULE
        measured = dict(
            table,
            rules=rules,
            population=tuple(sorted((DEFAULT_RULE, OTHER_RULE))),
            utilities=utilities,
            utility_population=tuple(sorted(UTILITIES)),
        )
        rating = rating_record(measured)
        # R1's pool row: the three baselines alone, declaring no objective of its own.
        pool = {
            "id": pool_digest([{"id": name, "baseline": True} for name in BASELINES]),
            "m": 5,
            "frozen": True,
            "members": tuple(
                {"id": name, "baseline": True, "pinned": True, "params": 0}
                for name in BASELINES
            ),
            "rules": (),
            "utilities": (),
        }
        record = run_record(measured, rating, pool=pool)
        reported = package.report(RUNG_NAME, record, measured, rating)
        family = family_value(reported, "pool")
        self.assertEqual(
            tuple(pool_utilities(family)),
            tuple(measured["utility_population"]),
            "the report's pool family carries the objectives the table measured — the "
            "pool's own utilities completed to the matrix's `utility_population` — so a "
            "reader of the pool row is told which objectives the table fitted over "
            "(records.md §13, utilities.md §7, §9, D-20): %r" % (family,),
        )
        self.assertEqual(
            tuple(pool_rules(family)),
            tuple(measured["population"]),
            "the two populations are completed on the same terms, one beside the other "
            "(records.md §13, D-19, D-20): %r" % (family,),
        )
        self.assertEqual(
            pool_member_ids(family),
            BASELINES,
            "completing the pool family's `utilities` adds no member and drops none "
            "(report.md §4, D-20): %r" % (family,),
        )
        self.assertEqual(
            set(pool_utilities(family)),
            set(measured["utility_population"]),
            "the completed utilities are the table's population and no objective the "
            "table did not measure (records.md §13, D-20): %r" % (family,),
        )
        self.assertEqual(
            set(family),
            set(pool),
            "the completion edits the two population keys and adds no third: a pool "
            "family gains no nested family and no new field (report.md §2, §4, D-20): %r"
            % (sorted(family),),
        )
        self.assertEqual(
            record["pool"],
            pool,
            "the run record is read, not mutated, so the caller keeps the pool family "
            "training gave it (report.md §4, records.md §13): %r" % (record["pool"],),
        )
        with self.subTest(case="a pool family that declares no utilities of its own"):
            handed = dict(
                record,
                pool={key: value for key, value in pool.items() if key != "utilities"},
            )
            completed = package.report(RUNG_NAME, handed, measured, rating)
            self.assertNotIn(
                "utilities",
                handed["pool"],
                "the report completes its own copy, so the record handed in still "
                "declares no utilities (report.md §4, D-20): %r" % (handed["pool"],),
            )
            self.assertEqual(
                tuple(pool_utilities(family_value(completed, "pool"))),
                tuple(measured["utility_population"]),
                "a pool row that declares no `utilities` of its own still yields a family "
                "naming the measured objectives (records.md §13, D-20): %r"
                % (family_value(completed, "pool"),),
            )
        with self.subTest(case="a matrix stating only its members' utilities"):
            partial = {
                key: value
                for key, value in measured.items()
                if key != "utility_population"
            }
            partial_rating = rating_record(partial)
            partial_record = run_record(partial, partial_rating, pool=pool)
            stated = package.report(RUNG_NAME, partial_record, partial, partial_rating)
            self.assertEqual(
                tuple(pool_utilities(family_value(stated, "pool"))),
                tuple(measured["utility_population"]),
                "when the table states no `utility_population` the report reads the "
                "objectives off its members' `utilities` and still names the population "
                "it measured (report.md §2, utilities.md §9, D-20): %r"
                % (family_value(stated, "pool"),),
            )
        with self.subTest(case="a family that already names the population is left alone"):
            complete_pool = dict(pool, utilities=tuple(sorted(UTILITIES)))
            complete_record = run_record(measured, rating, pool=complete_pool)
            left = package.report(RUNG_NAME, complete_record, measured, rating)
            self.assertEqual(
                tuple(pool_utilities(family_value(left, "pool"))),
                tuple(complete_pool["utilities"]),
                "nothing is added to a family that already names the population, so a "
                "report never reorders what it was handed (report.md §4, D-20): %r"
                % (family_value(left, "pool"),),
            )

    # -- the objective population is evidence, and never an input to the fit --
    def test_evl_14_12_the_rating_reads_neither_the_utilities_nor_their_population(self):
        """EVL-14.12 `rating` fits the same values, intervals and hands for two tables whose cells are identical and whose members' utilities and `utility_population` differ, because the fit is a function of the cells and the objective population is evidence about who played (`utility.md` §3, `matrix.md` §5, `rating.md` §1, `league.md` §4, D-20)."""
        package = self.evaluation()
        membership = tuple(BASELINES) + ("variant-1", "variant-2")
        table = hand_matrix(balanced, members=membership)
        trained = ("variant-1", "variant-2")
        one_objective = dict(
            table,
            rules={name: (DEFAULT_RULE if name in trained else None) for name in membership},
            population=(DEFAULT_RULE,),
            utilities={name: (DEFAULT_UTILITY if name in trained else None) for name in membership},
            utility_population=(DEFAULT_UTILITY,),
        )
        two_objectives = dict(
            one_objective,
            utilities=dict(one_objective["utilities"], **{"variant-2": OTHER_UTILITY}),
            utility_population=tuple(sorted((DEFAULT_UTILITY, OTHER_UTILITY))),
        )
        first = package.rating(one_objective)
        second = package.rating(two_objectives)
        self.assertEqual(
            first["values"],
            second["values"],
            "a table whose members were asked two questions is fitted exactly as the same "
            "cells under one are: the rating reads neither `utilities` nor "
            "`utility_population`, so D-20's axis is evidence and not an input "
            "(utility.md §3, matrix.md §5, rating.md §1, D-20): %r against %r"
            % (first["values"], second["values"]),
        )
        self.assertEqual(
            first["bootstrap_seed"],
            second["bootstrap_seed"],
            "the fit's interval seed comes from the table seed alone, so a changed "
            "objective population reseeds nothing (rating.md §4, ASM-17, D-20): %r"
            % (first["bootstrap_seed"],),
        )
        self.assertEqual(
            tuple(sorted(first["values"])),
            tuple(sorted(membership)),
            "and the fit still names every member of the table, the baselines included "
            "(records.md §11, rating.md §5): %r" % (sorted(first["values"]),),
        )

    # -- the bare record a policy entry point admits (utility.md §2) -------
    def test_evl_14_13_a_bare_record_handed_to_an_entry_point_may_declare_none(self):
        """EVL-14.13 a bare `records.md` §7 record handed to `match` is admitted with no `utility` key — the same record declared as a pool member is refused — and the cell names the utility its checkpoint records, because there the record declares nothing into a pool and the container is the witness (`scheduler.md` §5, `utilities.md` §5, §6, `records.md` §7, D-20)."""
        package = self.evaluation()
        saved = shortfall_checkpoint()
        bare = version_record(VERSION_IDS[0], START_LABEL, path=saved["path"])
        bare.pop("utility")
        # `matrix` and `opponent` read their members out of a `build_pool` pool, every
        # version member of which named its utility (EVL-14.3, EVL-14.6), so the silence
        # this reading admits is observable through `match`, the entry point handed the
        # record itself (scheduler.md §5, utilities.md §5, D-20).
        self.refused(
            lambda: package.build_pool(declaration(members=[bare], m=POOL_M)),
            entry="build_pool",
            groups=((VERSION_IDS[0],), ("utility",)),
            label="the bare record declared as a pool member",
            kind="MemberInvalid",
        )
        cell = package.match(bare, "always-call", MATCH_HANDS, MATCH_SEED)
        self.assertEqual(
            cell["utilities"][VERSION_IDS[0]],
            OTHER_UTILITY,
            "a §7 record that declares no utility is admitted where it is played as a "
            "policy, and the cell names the utility its checkpoint records — "
            "`stack-shortfall`, not the catalogue's first member — because the container "
            "is the witness where the record declares nothing into a pool (scheduler.md "
            "§5, utilities.md §5, §6, D-20): %r" % (cell["utilities"],),
        )
        self.assertIn(
            VERSION_IDS[0],
            cell["members"],
            "the admitted record plays as the member its record names, so the cell is the "
            "pair the caller asked for (scheduler.md §5, records.md §9, D-20): %r"
            % (cell["members"],),
        )
        self.assertIsNone(
            cell["utilities"][cell["members"][1]],
            "the other side is a baseline and names no objective, so the cell's one named "
            "utility is the one the admitted record's container recorded (records.md §9, "
            "utilities.md §6, D-20): %r" % (cell["utilities"],),
        )


if __name__ == "__main__":
    unittest.main()
