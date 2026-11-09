"""FAM-6 — the pool: a bounded window, pinned baselines, a deterministic id.

`docs/L1/battery.md` §3 FAM-6 and `docs/L1/league.md` §2 (D-16, ASM-14, ASM-16,
ASM-18, ASM-32, D-21).  The pool is the object the agent trains against and the table
measures; it holds at most M versions plus D-6's three anchor baselines, which are pinned
and never evicted; `offer` advances it by one version and drops the oldest evictable one;
R1's pool is the baselines alone; and the same membership declaration always yields the
same ordered members and the same id.

D-21 added the declaration's **optional** `baselines` key, so a configuration admits its
folding baselines explicitly and never silently: a declaration that names none holds the
flagged three and nothing more, its id is the one it always had, and a name outside the
catalogue is refused by name (`records.md` §8, `folders.md` §4, ASM-32).

Every instance below — the version names, their lineages, steps, samples and seeds, the
memberships built from them, and the invented baseline name of FAM-6.20 — is the
battery's own; no document in `docs/L1/` carries it (``battery.md`` §4).
"""

import os
import sys
import unittest

try:  # discovered as part of the tests.e2e package (unittest discover -t .)
    from . import _records as R  # noqa: F401
    from . import _surface as S  # noqa: F401
except ImportError:  # discovered as a plain directory, as pytest's prepend mode does
    _HERE = os.path.dirname(os.path.abspath(__file__))
    if _HERE not in sys.path:
        sys.path.insert(0, _HERE)
    import _records as R  # noqa: E402
    import _surface as S  # noqa: E402


class FAM6Pool(S.SurfaceCase):
    """The rolling window, its pinned baselines and its id."""

    # -- helpers -----------------------------------------------------------
    def league(self):
        return self.ep("evaluation", "league")()

    def declaration(self, versions, m=None, frozen=True, baselines=()):
        """A pool declaration in the shape ``records.md`` §8 pins.

        ``baselines`` is §8's **optional** key — the catalogue names a configuration
        admits beyond the three anchor baselines, which is how D-21's folders join a
        membership — and it is left out when empty, so a declaration that names no folder
        is the declaration a pool has always been built from (`records.md` §8, ASM-32).
        """
        declaration = {
            "members": list(versions),
            "m": S.LEAGUE_BOUND if m is None else m,
            "frozen": frozen,
        }
        if baselines:
            declaration["baselines"] = list(baselines)
        return declaration

    def built(self, versions, m=None, frozen=True, baselines=()):
        pool = self.pool(self.declaration(versions, m, frozen, baselines))
        row = self.members(pool)
        return pool, row

    def advancing(self, versions, m=None, baselines=()):
        """A pool a case means to advance.

        ``records.md`` §8 ties frozen-ness to the membership not changing while the pool
        is used, so a case that observes ``offer`` rolling the window builds an unfrozen
        pool: a frozen one either refuses the offer or holds its membership still, and
        the rolling operation would not be observable through it (``e2e-surface.md`` §2,
        ASM-16).  ``baselines`` declares the catalogue baselines the pool admits beyond
        the anchor three, which is how a case tables a membership holding D-21's folders
        (``records.md`` §8, ASM-32).
        """
        return self.built(versions, m, frozen=False, baselines=baselines)

    def five(self):
        """Five invented versions: a full window at the league's bound."""
        return R.version_chain(self, ("kestrel", "bramble", "thistle", "quarry", "marlin"))

    def test_fam6_1_the_league_declares_the_bound_and_the_pinned_baselines(self):
        """FAM-6.1 evaluation.league declares M = 5 and the three pinned baselines."""
        league = self.league()
        self.assertEqual(
            R.league_m(league),
            S.LEAGUE_BOUND,
            "the league's pool holds at most M = 5 versions (league.md §2): %r" % (league,),
        )
        text = S.flatten_text(league)
        for baseline in S.ANCHOR_BASELINES:
            self.assertIn(
                baseline,
                text,
                "the league pins the %r baseline and says so (league.md §2, D-16): %r"
                % (baseline, league),
            )

    def test_fam6_2_r1_s_pool_is_the_three_baselines_alone(self):
        """FAM-6.2 a pool with no lineage is the three baselines and no version."""
        pool, row = self.built([])
        members = R.member_ids(row)
        self.assertEqual(
            len(members),
            len(S.ANCHOR_BASELINES),
            "R1 has no lineage, so its pool is the three anchor baselines alone and no "
            "version (league.md §2, ASM-32): %r" % (members,),
        )
        self.assertEqual(
            R.version_members(row),
            [],
            "the report may not invent a version for a first rung (protocol.md §5): %r"
            % (members,),
        )
        for baseline in S.ANCHOR_BASELINES:
            self.assertIsNotNone(
                R.baseline_member(members, baseline),
                "the %r baseline is always a pool member (league.md §2): %r"
                % (baseline, members),
            )

    def test_fam6_3_a_pool_holds_at_most_m_versions(self):
        """FAM-6.3 a declaration over the bound is windowed to its last M versions."""
        names = ("alpha", "bravo", "charlie", "delta", "echo", "foxtrot", "golf")
        versions = R.version_chain(self, names)
        pool, row = self.built(versions)
        del pool
        kept = R.version_members(row)
        self.assertEqual(
            len(kept),
            S.LEAGUE_BOUND,
            "a pool holds at most M = %d versions whatever it is offered (league.md §2): %r"
            % (S.LEAGUE_BOUND, kept),
        )
        self.assertEqual(
            sorted(kept),
            sorted("version-%s" % name for name in names[-S.LEAGUE_BOUND:]),
            "the window keeps the last M versions by lineage order (ASM-18): %r" % (kept,),
        )

    def test_fam6_4_the_window_keeps_the_most_recent_versions_by_lineage(self):
        """FAM-6.4 the window's order is the declared lineage's, oldest dropped first."""
        versions = R.version_chain(self, ("kestrel", "bramble", "thistle", "quarry",
                                          "marlin", "osprey"))
        _pool, row = self.built(versions)
        kept = R.version_members(row)
        self.assertNotIn(
            "version-kestrel",
            kept,
            "the oldest version leaves the window first (league.md §2, ASM-18): %r" % (kept,),
        )
        for name in ("osprey", "marlin", "quarry", "thistle", "bramble"):
            self.assertIn(
                "version-%s" % name,
                kept,
                "the window is the last M versions in lineage order, so it holds %r: %r"
                % (name, kept),
            )

    def test_fam6_5_the_baselines_are_always_present(self):
        """FAM-6.5 whatever the membership, the three baselines are pool members."""
        for tags in ((), ("kestrel",), ("kestrel", "bramble", "thistle")):
            _pool, row = self.built([self.version(tag) for tag in tags])
            members = R.member_ids(row)
            for baseline in S.ANCHOR_BASELINES:
                self.assertIsNotNone(
                    R.baseline_member(members, baseline),
                    "a pool always holds the %r baseline (D-16, league.md §2): %r"
                    % (baseline, members),
                )

    def test_fam6_6_offer_drops_the_oldest_evictable_version_and_nothing_else(self):
        """FAM-6.6 offering a sixth version evicts the first and keeps the other four."""
        versions = self.five()
        pool, row = self.advancing(versions)
        before = R.version_members(row)
        offered = R.next_version(self, "nimbus", versions[-1])
        after_pool = self.ep("evaluation", "offer")(pool, offered)
        after = R.version_members(self.members(after_pool))
        self.assertEqual(
            len(after),
            S.LEAGUE_BOUND,
            "offering a version into a full window keeps the window full (league.md §2): %r"
            % (after,),
        )
        self.assertIn(
            "version-nimbus",
            after,
            "the offered version descends from the window's newest member, so it joins the "
            "window at the head of the lineage order (records.md §7): %r" % (after,),
        )
        self.assertNotIn(
            "version-kestrel",
            after,
            "offer drops the oldest evictable version, and it is the oldest that goes "
            "(ASM-18): %r" % (after,),
        )
        self.assertEqual(
            set(after),
            set(before[1:]) | {"version-nimbus"},
            "offer drops the oldest evictable version and adds the offered one, leaving "
            "the others alone (ASM-18): before %r, after %r" % (before, after),
        )

    def test_fam6_7_offer_never_evicts_a_baseline(self):
        """FAM-6.7 the baselines are pinned: repeated offers leave all three in place."""
        versions = self.five()
        pool, _row = self.advancing(versions)
        newest = versions[-1]
        for tag in ("nimbus", "osprey", "petrel", "skua"):
            offered = R.next_version(self, tag, newest)
            pool = self.ep("evaluation", "offer")(pool, offered)
            newest = offered
        members = R.member_ids(self.members(pool))
        for baseline in S.ANCHOR_BASELINES:
            self.assertIsNotNone(
                R.baseline_member(members, baseline),
                "the baselines are pinned and never evicted (league.md §2, ASM-16): %r"
                % (members,),
            )
        self.assertEqual(
            len(R.version_members(self.members(pool))),
            S.LEAGUE_BOUND,
            "four offers into a full window still leave M versions (league.md §2): %r"
            % (members,),
        )

    def test_fam6_8_offer_changes_the_id_because_the_membership_changed(self):
        """FAM-6.8 a pool's id changes when its members do (records.md §8, D-16)."""
        versions = self.five()
        pool, row = self.advancing(versions)
        before = R.version_members(row)
        advanced = self.ep("evaluation", "offer")(
            pool, R.next_version(self, "petrel", versions[-1])
        )
        after = R.version_members(self.members(advanced))
        self.assertNotEqual(
            set(after),
            set(before),
            "the offered version is newer than the window's newest member, so the window "
            "really rolls and the membership really changes (records.md §7, league.md §2): "
            "before %r, after %r" % (before, after),
        )
        self.assertNotEqual(
            R.pool_id(pool, row),
            R.pool_id(advanced, self.members(advanced)),
            "a run record and a table are compared by the pool id alone, so an advanced "
            "pool must not carry the id of the membership it left (records.md §8, D-16): %r"
            % (pool,),
        )

    def test_fam6_9_one_declaration_yields_one_pool(self):
        """FAM-6.9 the same declaration yields the same ordered members and id."""
        versions = self.five()
        first_pool, first_row = self.built(versions)
        second_pool, second_row = self.built(versions)
        self.assertEqual(
            R.member_ids(first_row),
            R.member_ids(second_row),
            "the same membership declaration yields the same ordered member list "
            "(league.md §2, ASM-2): %r against %r"
            % (R.member_ids(first_row), R.member_ids(second_row)),
        )
        self.assertEqual(
            R.pool_id(first_pool, first_row),
            R.pool_id(second_pool, second_row),
            "the same declaration yields the same pool id (D-16, ASM-2)",
        )

    def test_fam6_10_a_version_member_carries_the_seven_keys_of_section_7(self):
        """FAM-6.10 every version member is a records.md §7 record."""
        _pool, row = self.built(self.five()[2:])
        records = R.member_records(row)
        self.assertTrue(records, "pool_members returns its members' records: %r" % (row,))
        for member in records:
            # The catalogue's **six** names, because a folder is a baseline member exactly
            # as `always-call` is: a member named by any of them carries no version record,
            # and none of them is required to (records.md §7, §8, ASM-32, D-21).
            if any(str(baseline) in S.flatten_text(member) for baseline in S.BASELINES):
                continue
            for key in ("id", "path", "rung", "variant", "seed", "step", "samples",
                        "lineage"):
                R.required(
                    member,
                    "a version member of the pool (records.md §7)",
                    key,
                )

    def test_fam6_11_pool_members_reports_the_bound_and_the_frozen_flag(self):
        """FAM-6.11 pool_members reports the bound M and whether the pool is frozen."""
        pool, row = self.built(self.five()[:1])
        self.assertEqual(
            R.pool_bound(row),
            S.LEAGUE_BOUND,
            "pool_members reports the bound the pool holds to (e2e-surface §3.4): %r" % (row,),
        )
        # records.md §8 marks a pool record's `frozen` **required**, because it says
        # whether the pool was frozen when it was used — which is how a pair's parity is
        # read.  The case reads the flag's value: it is a boolean, and this pool was
        # declared frozen, so the read-back says so.
        flag = R.pool_frozen(row)
        self.assertTrue(
            S.is_flag(flag),
            "records.md §8 makes `frozen` a required boolean flag on a pool record: it says "
            "whether the pool was frozen when it was used; the read-back gives %r" % (flag,),
        )
        self.assertIs(
            bool(flag),
            True,
            "this membership was declared frozen, so the pool it builds reports the flag "
            "set, and an unfrozen declaration would report it clear (records.md §8, "
            "ASM-16): %r" % (row,),
        )

    def test_fam6_12_a_frozen_pool_does_not_change_while_it_is_used(self):
        """FAM-6.12 a frozen pool refuses to advance; the same declaration unfrozen rolls."""
        versions = self.five()
        frozen, row = self.built(versions, frozen=True)
        before = R.version_members(row)
        frozen_id = R.pool_id(frozen, row)
        offered = R.next_version(self, "nimbus", versions[-1])

        refused = None
        returned = None
        try:
            returned = self.ep("evaluation", "offer")(frozen, offered)
        except S.SurfaceAbsent:
            raise
        except Exception as exc:  # a refusal is the other legal edge (e2e-surface §2)
            refused = "%s: %s" % (type(exc).__name__, exc)

        if refused is not None:
            body = R.tok(refused)
            self.assertTrue(
                any(word in body for word in ("frozen", "freeze", "pool", "member")),
                "offering into a frozen pool is a contract violation, and the refusal names "
                "what it refused — the frozen membership (e2e-surface §2, records.md §8): %r"
                % (refused,),
            )
        else:
            self.assertIsNotNone(returned, "evaluation.offer returned nothing at all")
            after = R.version_members(self.members(returned))
            self.assertEqual(
                set(after),
                set(before),
                "a frozen pool's membership does not change while it is used, so an offer "
                "into it either is refused or leaves the membership alone (records.md §8, "
                "ASM-16): before %r, after %r" % (before, after),
            )
            self.assertEqual(
                R.pool_id(returned, self.members(returned)),
                frozen_id,
                "an unchanged membership keeps its id, because the id changes when and only "
                "when the members do (records.md §8, D-16)",
            )

        open_pool, _open_row = self.advancing(versions)
        rolled = self.ep("evaluation", "offer")(open_pool, offered)
        self.assertNotEqual(
            set(R.version_members(self.members(rolled))),
            set(before),
            "the same declaration built unfrozen does advance on the same offer, so it is "
            "the frozen flag that held the first pool still (records.md §8, ASM-16): "
            "before %r, after %r" % (before, R.version_members(self.members(rolled))),
        )

    # -- the rule a member was trained under (D-19) ------------------------
    def test_fam6_13_a_version_member_carries_the_rule_it_was_trained_under(self):
        """FAM-6.13 a version member records the rule its model was trained under."""
        version = self.version("kestrel", rule=S.RULE_SECOND)
        _pool, row = self.built([version])
        member = None
        for record in R.member_records(row):
            if R.tok(record.get("id")) == R.tok(version["id"]):
                member = record
                break
        self.assertIsNotNone(
            member,
            "pool_members returns the version members it holds, by id (records.md §8): %r"
            % (R.member_ids(row),),
        )
        self.assertEqual(
            R.version_rule(member),
            S.RULE_SECOND,
            "records.md §7 makes `rule` a required key of a version member — the catalogue "
            "member it was trained under — so a table can name the population it measured "
            "and a member is never confused with one from another rule (rules.md §6, D-19): "
            "%r" % (member,),
        )

    def test_fam6_14_pool_members_reports_the_rules_the_pool_holds(self):
        """FAM-6.14 a pool record states the distinct rules its versions declare."""
        # Two families under two rules: one lineage chain each, every member of a family
        # trained under that family's rule (league.md §2, ASM-26).
        masked = R.version_chain(self, ("kestrel", "bramble"), rule=S.RULE_DEFAULT)
        doubled = R.version_chain(
            self,
            ("thistle", "quarry"),
            rule=S.RULE_SECOND,
            lineage_start="R5-residual-battery",
        )
        _pool, row = self.built(masked + doubled)
        rules = R.pool_rules(row)
        self.assertEqual(
            sorted(R.rule_names_of(rules)),
            sorted(S.RULES),
            "a pool record carries `rules` — the distinct rules its version members "
            "declare — because that is the population a table over it measured (records.md "
            "§8, league.md §2, D-19): %r" % (rules,),
        )
        _single_pool, single_row = self.built(masked)
        self.assertEqual(
            R.rule_names_of(R.pool_rules(single_row)),
            [S.RULE_DEFAULT],
            "a pool whose versions are one family under one rule declares that one rule, "
            "which is what every pool in the shipped tree holds today (rules.md §8): %r"
            % (R.pool_rules(single_row),),
        )

    def test_fam6_15_the_pool_id_certifies_the_rule_and_no_other_field(self):
        """FAM-6.15 the id changes with a member's rule, not with its step or samples."""
        masked = self.version("kestrel", rule=S.RULE_DEFAULT)
        doubled = self.version("kestrel", rule=S.RULE_SECOND)
        self.assertEqual(
            masked["id"],
            doubled["id"],
            "the two members compared here are the same version under two rules, so both "
            "carry one id and only the rule moves (records.md §7, ASM-27): %r against %r"
            % (masked["id"], doubled["id"]),
        )
        for key in ("rung", "variant", "seed", "step", "samples", "lineage"):
            self.assertEqual(
                masked[key],
                doubled[key],
                "the two members differ on their rule and on nothing else, so the pool id "
                "difference below is the rule's: %r differs (%r against %r)"
                % (key, masked[key], doubled[key]),
            )
        one, one_row = self.built([masked])
        two, two_row = self.built([doubled])
        self.assertNotEqual(
            R.pool_id(one, one_row),
            R.pool_id(two, two_row),
            "the pool id digests each version's id and its rule, so two pools of one "
            "membership under two estimators do not wear one id — a table must be able to "
            "say which population a rating was fitted over (records.md §8, ASM-27, D-19)",
        )
        corrected = dict(masked)
        corrected["step"] = int(masked["step"]) + 907
        corrected["samples"] = int(masked["samples"]) + 811
        three, three_row = self.built([corrected])
        self.assertEqual(
            R.pool_id(one, one_row),
            R.pool_id(three, three_row),
            "`m`, `frozen` and every other member field stay outside the digest's payload, "
            "so a corrected step or sample count does not rename the pool — the id changes "
            "when and only when the membership does (records.md §8, ASM-27)",
        )

    def test_fam6_16_a_version_naming_an_uncatalogued_rule_is_refused(self):
        """FAM-6.16 a version declaring a rule the catalogue lacks is refused by name."""
        offending = "n-step-returns-battery"
        version = self.version("kestrel")
        version["rule"] = offending
        text = S.refusal_text(lambda: self.built([version]))
        self.assertIsNotNone(
            text,
            "a version declaring a rule outside the catalogue is refused where it is "
            "declared, and never mapped onto the declared default (rules.md §4, §6, "
            "records.md §7, D-19): the declaration %r built a pool" % (version,),
        )
        self.assertIn(
            R.tok(offending),
            R.tok(text),
            "the refusal names the rule it refused (rules.md §4): %r" % (text,),
        )

    def test_fam6_17_a_second_family_rolls_in_and_a_full_window_keeps_every_family(self):
        """FAM-6.17 a second family is accepted, and fair-share eviction keeps each one."""
        # One family resident: a second family's next version is a label no member
        # carries, which opens a new family rather than extending the one that is there
        # (league.md §2, ASM-26).
        first = R.version_chain(self, ("kestrel", "bramble"), rule=S.RULE_DEFAULT)
        pool, row = self.advancing(first)
        self.assertEqual(
            len(R.version_members(row)),
            2,
            "the case starts from one family of two versions (league.md §2): %r"
            % (R.version_members(row),),
        )
        opening = R.make_version(
            self,
            "thistle",
            seed=S.SEED_C,
            step=53,
            lineage="R5-battery-family-b",
            rule=S.RULE_SECOND,
        )
        pool = self.ep("evaluation", "offer")(pool, opening)
        members = R.version_members(self.members(pool))
        self.assertIn(
            "version-thistle",
            members,
            "a version whose lineage is a label no member carries opens a second family, and "
            "the offer is accepted where a single-chain window refused a second chain "
            "(league.md §2, ASM-26, D-19): %r" % (members,),
        )
        self.assertEqual(
            len(members),
            3,
            "the window grew by the version it was offered and dropped nothing, because it "
            "was under its bound (league.md §2): %r" % (members,),
        )

        # Two families of three at a bound of four: the full window evicts fair-share, so
        # neither family is emptied while the other holds two or more (ASM-26).
        alpha = R.version_chain(
            self,
            ("alpha1", "alpha2", "alpha3"),
            rule=S.RULE_DEFAULT,
            lineage_start="R6-battery-family-a",
        )
        bravo = R.version_chain(
            self,
            ("bravo1", "bravo2", "bravo3"),
            rule=S.RULE_SECOND,
            lineage_start="R5-battery-family-b",
        )
        full_pool, full_row = self.advancing(alpha + bravo, m=4)
        kept = R.version_members(full_row)
        self.assertEqual(
            len(kept),
            4,
            "a pool holds at most the bound it declares, which may be tighter than the "
            "league's M (league.md §2, records.md §8): %r" % (kept,),
        )
        for family in ("alpha", "bravo"):
            self.assertTrue(
                any(member.startswith("version-" + family) for member in kept),
                "the window's eviction is fair-share: the version that leaves is the "
                "oldest of the family that holds the most, so no family is emptied while "
                "another holds two or more (league.md §2, ASM-26, D-19): %r" % (kept,),
            )

        seventh = R.next_version(self, "alpha4", alpha[-1], rule=S.RULE_DEFAULT)
        rolled = self.ep("evaluation", "offer")(full_pool, seventh)
        after = R.version_members(self.members(rolled))
        self.assertEqual(
            len(after),
            4,
            "offering into a full window keeps the window at its bound (league.md §2): %r"
            % (after,),
        )
        self.assertIn(
            "version-alpha4",
            after,
            "the offered version extends its family's newest member, so it joins the window "
            "(league.md §2, ASM-26): %r" % (after,),
        )
        for family in ("alpha", "bravo"):
            self.assertTrue(
                any(member.startswith("version-" + family) for member in after),
                "after a seventh version is offered, the window still holds a member of "
                "each family, which is how heterogeneity survives the bound (league.md §2, "
                "ASM-26, D-19): %r" % (after,),
            )


    # -- the baselines a declaration names (D-21, records.md §8) -----------
    def test_fam6_18_a_declaration_naming_no_folder_holds_the_anchor_baselines(self):
        """FAM-6.18 a declaration with no `baselines` key holds D-6's three and no folder.

        `records.md` §8 makes the declaration's `baselines` key **optional**: the three
        anchor baselines are members whether it names them or not, and a folder joins only
        when a declaration names it (`protocol.md` §3, `league.md` §2, ASM-32, D-21).  So a
        declaration that names none holds exactly the flagged three plus the versions it
        declares — and its id is the id the same declaration had before D-21.
        """
        version = self.version("kestrel")
        _pool, row = self.built([version])
        members = R.member_ids(row)
        self.assertEqual(
            set(members),
            set(S.ANCHOR_BASELINES) | {version["id"]},
            "a declaration that names no folder holds exactly the three anchor baselines "
            "and the version it declares (records.md §8, ASM-32, D-21): %r" % (members,),
        )
        for folder in S.FOLDER_BASELINES:
            self.assertNotIn(
                folder,
                members,
                "a folding baseline joins a pool only when the declaration names it, so %r "
                "is not a member of a declaration that names none (records.md §8, "
                "'never silently', ASM-32, D-21): %r" % (folder, members),
            )
        self.assertEqual(
            R.version_members(row),
            [version["id"]],
            "the pool's version members are the declaration's versions and nothing else "
            "(records.md §8): %r" % (members,),
        )

    def test_fam6_19_a_declaration_naming_the_folders_holds_them_after_the_three(self):
        """FAM-6.19 declared folders join pinned after D-6's three, and move the id.

        `records.md` §8 orders a pool's members as the pinned baselines first — the three
        of D-6 in the catalogue's order, then the declared folders in the catalogue's order
        — and then the families.  A folder is a member the same declaration does not hold
        when it names none, so the two pools of one membership differ in membership and
        therefore in id (`records.md` §8, `league.md` §2, ASM-27, ASM-32, ASM-33, D-21).
        """
        plain, plain_row = self.built([])
        declared, declared_row = self.built([], baselines=list(S.FOLDER_BASELINES))
        plain_members = R.member_ids(plain_row)
        members = R.member_ids(declared_row)
        self.assertEqual(
            plain_members,
            list(S.ANCHOR_BASELINES),
            "the same declaration without the folders holds the anchor three alone "
            "(records.md §8, ASM-32): %r" % (plain_members,),
        )
        self.assertEqual(
            members,
            list(S.ANCHOR_BASELINES) + list(S.FOLDER_BASELINES),
            "the declared folders join pinned **after** the three of D-6, in the catalogue's "
            "order, so the pool's first six members are the catalogue's baselines in its own "
            "order (records.md §8, ASM-32, ASM-33, D-21): %r" % (members,),
        )
        for folder in S.FOLDER_BASELINES:
            self.assertIsNotNone(
                R.baseline_member(members, folder),
                "the declared %r is a member of the pool that named it (records.md §8, "
                "D-21): %r" % (folder, members),
            )
        self.assertNotEqual(
            R.pool_id(declared, declared_row),
            R.pool_id(plain, plain_row),
            "the two pools do not hold the same members, so they must not wear one id — a "
            "table must be able to say which population it measured (records.md §8, ASM-27, "
            "D-21)",
        )
        _again_pool, again_row = self.built([], baselines=list(S.FOLDER_BASELINES))
        self.assertEqual(
            R.member_ids(again_row),
            members,
            "one declaration yields one ordered membership, folders included (records.md "
            "§8, ASM-2): %r against %r" % (members, R.member_ids(again_row)),
        )

    def test_fam6_21_offer_never_evicts_a_declared_folder(self):
        """FAM-6.21 a declared folder is pinned exactly as D-6's three are.

        `records.md` §8 and `league.md` §2: eviction is the version window's and takes no
        baseline — a baseline a declaration names joins **pinned**, so repeated offers into
        a full window leave the folders in place as they leave the anchor three
        (ASM-16, ASM-32, D-21).  An implementation that treated a declared folder as
        evictable, or that rebuilt the pool's pinned set from the flagged three only, would
        lose it here.
        """
        versions = self.five()
        pool, row = self.advancing(versions, baselines=list(S.FOLDER_BASELINES))
        before = R.member_ids(row)
        for name in S.FOLDER_BASELINES:
            self.assertIsNotNone(
                R.baseline_member(before, name),
                "the declared %r folder is a member of the pool before any offer "
                "(records.md §8, ASM-32, D-21): %r" % (name, before),
            )
        newest = versions[-1]
        for tag in ("nimbus", "osprey", "petrel", "skua"):
            offered = R.next_version(self, tag, newest)
            pool = self.ep("evaluation", "offer")(pool, offered)
            newest = offered
        members = R.member_ids(self.members(pool))
        for name in S.ANCHOR_BASELINES + S.FOLDER_BASELINES:
            self.assertIsNotNone(
                R.baseline_member(members, name),
                "every pinned baseline — the anchor three and each declared folder — "
                "survives four offers into a full window (records.md §8, league.md §2, "
                "ASM-16, ASM-32, D-21): %r" % (members,),
            )
        self.assertEqual(
            len(R.version_members(self.members(pool))),
            S.LEAGUE_BOUND,
            "the window is still full of versions after the offers, so what was evicted was "
            "a version and not a baseline (league.md §2, ASM-16): %r" % (members,),
        )

    def test_fam6_20_a_declaration_naming_an_uncatalogued_baseline_is_refused(self):
        """FAM-6.20 a declared baseline the catalogue does not carry is refused by name.

        `records.md` §8: "a name outside the catalogue is refused by name" — a membership
        that admitted a baseline the project cannot build would be a table row no member
        plays (ASM-32, D-21, `e2e-surface.md` §2).  The invented name is the battery's own
        (`battery.md` §4).
        """
        offending = S.UNKNOWN_BASELINE
        self.assertNotIn(
            offending,
            S.BASELINES,
            "the name this case invents is outside the catalogue it names",
        )
        text = S.refusal_text(
            lambda: self.built([], baselines=[offending])
        )
        self.assertIsNotNone(
            text,
            "build_pool must refuse a declaration naming the baseline %r, which the "
            "catalogue does not carry, instead of building a pool that holds it "
            "(records.md §8, ASM-32, D-21)" % (offending,),
        )
        self.assertIn(
            R.tok(offending),
            R.tok(text),
            "the refusal names the baseline it refused (records.md §8, ASM-32): %r" % (text,),
        )


if __name__ == "__main__":
    unittest.main()
