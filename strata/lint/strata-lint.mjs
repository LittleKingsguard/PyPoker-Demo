#!/usr/bin/env node
/**
 * strata-lint — mechanical checks for the strata workflow artifacts.
 *
 * Every check is named and reports one line. Failing checks exit non-zero; the layer fails
 * with them. Provenance ships in REPORT mode: its attachment rule is not ratified (D-21), so
 * the lint measures and does not judge.
 *
 * Dependency-free on purpose: it must run wherever a layer runs.
 */
import { existsSync, readFileSync, readdirSync } from 'node:fs'
import { createRequire } from 'node:module'
import { basename, dirname, join, relative } from 'node:path'

/** Class maxima. A document may declare a lower ceiling; it may never declare a higher one.
 *  `record` is the handover's 60, the widest record shape; `tracker` is what `pending.md:1` and
 *  `next-steps.md:1` declare, so a tracker declaring more prints the class-max FAIL (D-25). */
const CLASS_MAX = { brief: 150, procedure: 60, reference: 60, register: 40, record: 60, tracker: 40 }

/** Artifact registry: file, class, default ceiling. A missing file is reported, not fatal. */
const REGISTRY = [
  ['brief.md', 'brief', 150],
  ['walkthrough.md', 'procedure', 60],
  ['rebuild.md', 'procedure', 40],
  ['examiner.md', 'procedure', 45],
  ['modules.md', 'procedure', 40],
  ['envelope.md', 'procedure', 40],
  ['research.md', 'procedure', 40],
  ['proposals.md', 'procedure', 40],
  ['platform.md', 'reference', 60],
  ['decisions.md', 'register', Infinity],
]

/** The trackers a corpus roots beside the register, in REGISTRY's row shape. They are named
 *  entries, so a missing one prints its own absence row exactly as `research.md` does.
 *  `README.md` and `archive.md` need no class of their own — `reference` bounds them at 60. */
const TRACKERS = [
  ['pending.md', 'tracker', 40],
  ['next-steps.md', 'tracker', 40],
  ['archive.md', 'reference', 60],
  ['README.md', 'reference', 60],
]

/** Record shapes by path pattern, in precedence order: first match wins, so the handover's 60
 *  and a retrospective's 20 are read before the catch-all's 40. A record gets no leniency and
 *  no extra severity — only its ceiling resolves from its path (D-25, design §2). */
const RECORD_PATTERNS = [
  ['records/handover.md', 'record', 60],
  ['records/*-retrospective.md', 'record', 20],
  ['records/*.md', 'record', 40],
]

const LAYERS = ['L0', 'L1', 'L2', 'L3', 'L4']
const VERDICTS = ['PASS', 'FAIL', 'ADJUDICATION', 'REBUILD']

const NORMATIVE = /\b(must|shall|never|always|required|forbidden)\b/i
const DECISION_ID = /^##\s+(D-\d+)\b/gm
/** A citation is a decision, an assumption, a ratified failure mode (§1), or a section. */
const CITATION = /D-\d+|ASM-\d+|F-\d+|§/

/** A document's own declared ceiling, when it states one in its header region.
 *  Header-scoped: a register legitimately quotes a rule containing "Ceiling: 150 lines",
 *  and reading the whole body would parse that quotation as a declaration.
 *
 *  Site rule (D-25, design §3): a declaration is read only from a site line — one of the first
 *  `headerLines` (12) that is neither a table row (its first non-space character is `|`) nor
 *  inside a fenced block (a backtick or tilde fence opening within the window toggles the fenced
 *  state, and the fence line itself is no site either). A table cell naming another document's
 *  ceiling and a fenced quotation of one are therefore no declaration at all (F-2, F-5).
 *
 *  Grammar: three forms, tried over the site lines in file order — form 1, then 2, then 3 — and
 *  the first match wins, so precedence is by form, then by line. Form 1 is
 *  `/\bceiling\b[ \t*_]*(?::[ \t*_]*)?(\d+)(?!\d)/i`: the word, a run of emphasis or spaces
 *  around one optional colon, then the number, and nothing is read after it — the unit word
 *  `lines` is optional and a colon may sit inside or outside the emphasis (`**Ceiling:** 40`,
 *  `**Ceiling**: 40`, `Ceiling: 40`). It is deliberately unanchored, so a record's single
 *  metadata line (`· **Ceiling:** 40 lines (D-1)`) still declares. Form 2
 *  `/[—–-][ \t]*ceiling[ \t]+(\d+)\b/i` is the H1 dash form with the unit elided, and form 3
 *  `/this file['’]s is[ \t]+(\d+)[ \t]+lines/i` is the self-reference. The third requires
 *  "this file": a header naming another document's ceiling declares nothing. No form spans a
 *  line break — a declaration is one site line.
 *
 *  A missed parse falls back to the pattern ceiling, a maximum, so it never raises a limit
 *  (D-25, design §3). */
export function parseDeclaredCeiling(text, headerLines = 12) {
  const sites = []
  let fenced = false
  for (const line of text.split('\n').slice(0, headerLines)) {
    const lead = line.trimStart()
    if (lead.startsWith('```') || lead.startsWith('~~~')) {
      fenced = !fenced
      continue
    }
    if (fenced || lead.startsWith('|')) continue
    sites.push(line)
  }
  for (const form of [
    /\bceiling\b[ \t*_]*(?::[ \t*_]*)?(\d+)(?!\d)/i,
    /[—–-][ \t]*ceiling[ \t]+(\d+)\b/i,
    /this file['’]s is[ \t]+(\d+)[ \t]+lines/i,
  ]) {
    for (const line of sites) {
      const m = form.exec(line)
      if (m !== null) return Number(m[1])
    }
  }
  return undefined
}

/** A record pattern as a predicate: the whole relative path, anchored, `.` escaped, and `*`
 *  standing for zero or more non-`/` characters — so a nested `records/a/b.md` matches nothing
 *  (design §2, §4). */
const recordPattern = (pattern) =>
  new RegExp(`^${pattern.split('*').map((part) => part.replace(/[.+?^${}()|[\]\\]/g, '\\$&')).join('[^/]*')}$`)

/** The record files a corpus roots under `records/`: `records/*.md` sorted for stable output,
 *  `undefined` when the directory is absent, `[]` when it is present and empty. Not recursive:
 *  the whole surface a corpus declares, and `readdirSync` order is not guaranteed (D-25, §4). */
export function recordFiles(root) {
  const dir = join(root, 'records')
  if (!existsSync(dir)) return undefined
  return readdirSync(dir)
    .filter((name) => name.endsWith('.md'))
    .sort()
    .map((name) => `records/${name}`)
}

/** Every markdown document a corpus keeps under `docs/`, relative to the repository root.
 *  The layer documents declare their own ceilings in their headers; nothing else measures them,
 *  which is how three of them sat over their limit unnoticed (F-1 applied to layer docs, not just
 *  to the strata root). Returns `undefined` when there is no `docs/` directory at all, `[]` when
 *  it exists and is empty — absent and empty are different facts, as for `records/`. */
export function docFiles(root) {
  const repo = dirname(root)
  const top = join(repo, 'docs')
  if (!existsSync(top)) return undefined
  const out = []
  const walk = (dir) => {
    for (const entry of readdirSync(dir, { withFileTypes: true })) {
      const path = join(dir, entry.name)
      if (entry.isDirectory()) walk(path)
      else if (entry.name.endsWith('.md')) out.push(relative(repo, path).split('\\').join('/'))
    }
  }
  walk(top)
  return out.sort()
}

/** The registry entry for one record path: the first `RECORD_PATTERNS` row that matches it.
 *  The table is a predicate, not the measured set, so a record no corpus names still resolves
 *  to its shape's ceiling instead of escaping the four checks (design §2; F-4). */
export function recordEntry(relPath) {
  const row = RECORD_PATTERNS.find(([pattern]) => recordPattern(pattern).test(relPath))
  return row === undefined ? undefined : [relPath, row[1], row[2]]
}

/** Length of each register row, so the per-row ceiling can be checked without a file cap. */
export function registerRowLengths(text) {
  const lines = text.replace(/\n$/, '').split('\n')
  const rows = []
  let current
  for (let i = 0; i < lines.length; i++) {
    const m = /^##\s+(D-\d+)\b/.exec(lines[i])
    if (m === null) continue
    if (current !== undefined) rows.push({ id: current.id, lines: i - current.start })
    current = { id: m[1], start: i }
  }
  if (current !== undefined) rows.push({ id: current.id, lines: lines.length - current.start })
  return rows
}

/** Defined decision ids, read from the register's own headings. */
export function decisionIds(decisionsText) {
  const ids = new Set()
  for (const m of decisionsText.matchAll(DECISION_ID)) ids.add(m[1])
  return ids
}

/** ASM ids that are either open in the brief or ratified in the register's table rows. */
export function asmIds(briefText, decisionsText) {
  const ids = new Set()
  for (const m of briefText.matchAll(/^-\s+`(ASM-\d+)`/gm)) ids.add(m[1])
  for (const m of decisionsText.matchAll(/`(ASM-\d+)`/g)) ids.add(m[1])
  return ids
}

/** Citations a document makes, excluding its own heading ids when it is the register. */
export function citations(text) {
  const found = new Set()
  for (const m of text.matchAll(/D-\d+|ASM-\d+/g)) found.add(m[0])
  return found
}

/** Exemplar instances that leaked into normative text.
 *  A token confined to EXEMPLAR blocks is correctly quarantined; the violation is the
 *  overlap — an exemplar's instance carried into a line that states a rule. */
export function leakedExemplarTokens(text) {
  const tokensIn = (lines) => {
    const set = new Set()
    for (const line of lines) {
      for (const m of line.matchAll(/`([^`]+)`|"([^"]+)"/g)) {
        const token = (m[1] ?? m[2]).trim()
        if (token.length > 1 && !/^D-\d+$|^ASM-\d+$/.test(token)) set.add(token)
      }
    }
    return set
  }
  const lines = text.split('\n')
  const exemplar = tokensIn(lines.filter((l) => l.startsWith('>')))
  const body = tokensIn(lines.filter((l) => !l.startsWith('>')))
  return [...exemplar].filter((t) => body.has(t))
}

/** Split a document into statements — a bullet, a table row (with its preamble), or a
 *  paragraph — joined across their wrapped lines. Header metadata before the first H2 is
 *  exempt: a document's own ceiling line is not a rule about the workflow. */
export function statements(text) {
  const lines = text.split('\n')
  const firstHeading = lines.findIndex((l) => /^##\s/.test(l))
  const start = firstHeading === -1 ? 0 : firstHeading
  const out = []
  let current
  let preamble = ''
  const flush = () => {
    if (current === undefined) return
    out.push(current)
    if (current.kind === 'para') preamble = current.text
    current = undefined
  }
  for (let i = start; i < lines.length; i++) {
    const line = lines[i]
    if (line.trim() === '' || /^##\s/.test(line)) {
      flush()
      continue
    }
    if (line.startsWith('|')) {
      if (current?.kind === 'table') current.text += `\n${line}`
      else {
        flush()
        current = { kind: 'table', line: i + 1, text: line, preamble }
      }
      continue
    }
    const bullet = /^([-*+]|\d+\.)\s/.test(line)
    if (bullet) {
      flush()
      current = { kind: 'bullet', line: i + 1, text: line }
      continue
    }
    if (current !== undefined) current.text += `\n${line}`
    else current = { kind: 'para', line: i + 1, text: line }
  }
  flush()
  return out
}

/** Normative statements that carry no citation marker, once joined into statements.
 *  A table row inherits its preamble's attribution; a bullet inherits its own continuation
 *  lines. This is the D-22 attachment rule, and it is a failing check. */
export function uncitedNormative(text) {
  return statements(text)
    // An EXEMPLAR block is non-normative by construction; it never carries a rule.
    .filter((s) => !s.text.startsWith('>'))
    // Inline code is a value, not a modal: `never` as an approval policy is not a rule.
    .filter((s) => NORMATIVE.test(s.text.replace(/`[^`]*`/g, '')))
    .filter((s) => !CITATION.test(s.text))
    .filter((s) => !(s.kind === 'table' && CITATION.test(s.preamble)))
    .map((s) => ({ line: s.line, text: s.text.replace(/\s+/g, ' ').slice(0, 72) }))
}

/** Envelope validation: the contract every layer return crosses (envelope.md). */
export function validateEnvelope(value) {
  const errors = []
  if (typeof value !== 'object' || value === null) return { ok: false, errors: ['envelope is not an object'] }
  for (const key of ['unit', 'from', 'to', 'verdict', 'artifact']) {
    if (value[key] === undefined || value[key] === '') errors.push(`missing ${key}`)
  }
  if (!LAYERS.includes(value.from)) errors.push(`from "${value.from}" is not a layer id`)
  if (!VERDICTS.includes(value.verdict)) errors.push(`verdict "${value.verdict}" is outside the closed set`)
  if (LAYERS.includes(value.from) && LAYERS.includes(value.to)) {
    const expected = value.from === 'L4' && value.verdict !== 'PASS' ? 2 : Number(value.from[1]) - 1
    if (Number(value.to[1]) !== expected) errors.push(`to should be L${expected} (D-13)`)
  }
  if (value.verdict !== 'PASS' && (value.rootCause === undefined || value.rootCause === '')) {
    errors.push('a non-PASS verdict requires rootCause (D-12)')
  }
  if (value.verdict === 'PASS' && !(Array.isArray(value.citations) && value.citations.length > 0)) {
    errors.push('a PASS verdict requires citations (D-22)')
  }
  for (const a of value.assumptions ?? []) {
    if (a.alternative === undefined || a.alternative === '') errors.push(`assumption "${a.id ?? '?'}" lacks the alternative it rejected (D-5)`)
  }
  return { ok: errors.length === 0, errors }
}

/** The last fenced json block of a return is its envelope. */
export function parseEnvelope(text) {
  const blocks = [...text.matchAll(/```json\n([\s\S]*?)```/g)]
  if (blocks.length === 0) return { ok: false, errors: ['no fenced json envelope'] }
  try {
    return { ok: true, value: JSON.parse(blocks[blocks.length - 1][1]) }
  } catch {
    return { ok: false, errors: ['envelope is not parseable JSON'] }
  }
}

/** A full return: the envelope plus the no-patch rule. */
export function validateReturn(text) {
  const problems = []
  if (/^@@ /m.test(text)) problems.push('the report carries a diff hunk (D-12)')
  for (const [, lang] of text.matchAll(/```(\w*)/g)) {
    if (lang !== '' && lang !== 'json') problems.push(`the report carries a ${lang} code block (D-12)`)
  }
  const parsed = parseEnvelope(text)
  if (!parsed.ok) return { ok: false, errors: [...problems, ...parsed.errors] }
  const envelope = validateEnvelope(parsed.value)
  return { ok: problems.length === 0 && envelope.ok, errors: [...problems, ...envelope.errors] }
}
/** Module declarations: one entry per module, no path claimed twice (modules.md §4). */
export function parseModules(value) {
  const errors = []
  if (!Array.isArray(value?.modules)) return { ok: false, errors: ['modules.json has no modules array'] }
  const claimed = new Map()
  value.modules.forEach((m, i) => {
    const label = m.name ?? `module[${i}]`
    if (!m.name) errors.push(`${label} has no name`)
    if (!Array.isArray(m.paths) || m.paths.length === 0) errors.push(`${label} declares no paths`)
    if (!Number.isInteger(m.endpoints) || m.endpoints < 0) errors.push(`${label} endpoints must be a non-negative integer`)
    for (const path of m.paths ?? []) {
      const base = path.replace(/\/+$/, '')
      if (claimed.has(base)) errors.push(`path "${base}" claimed by "${claimed.get(base)}" and "${m.name}"`)
      else claimed.set(base, m.name)
    }
  })
  return { ok: errors.length === 0, errors, modules: value.modules }
}

/** Every module claiming a changed file. Exactly one owner is the only legal answer. */
export function ownersOf(modules, file) {
  const target = file.replace(/^\.\//, '')
  return modules
    .filter((m) => (m.paths ?? []).some((p) => {
      const base = p.replace(/\/+$/, '')
      return target === base || target.startsWith(`${base}/`)
    }))
    .map((m) => m.name)
}

/** The D-19 harness cap for a module's declared endpoint count. */
export function harnessCap(endpoints) {
  return 50 + 10 * endpoints
}

/** Split a composition into its `- id:` rows by indentation. */
export function presetRows(text) {
  const lines = text.split('\n')
  const rows = []
  for (let i = 0; i < lines.length; i++) {
    const m = /^(\s*)- id:\s+(\S+)\s*$/.exec(lines[i])
    if (m === null) continue
    const indent = m[1].length
    let end = i + 1
    while (end < lines.length) {
      const next = /^(\s*)- id:\s+\S+/.exec(lines[end])
      if (next !== null && next[1].length <= indent) break
      end++
    }
    rows.push({ id: m[2], start: i + 1, text: lines.slice(i, end).join('\n') })
  }
  return rows
}

/** The persona block of a row, or undefined when the row carries none. */
export function personaOf(rowText) {
  const m = /persona:\s*\|-\n([\s\S]*)$/.exec(rowText)
  return m === null ? undefined : m[1].replace(/\s+$/, '')
}

const normalize = (line) => line.toLowerCase().replace(/[`*_]/g, '').replace(/[^\w\s]/g, ' ').replace(/\s+/g, ' ').trim()

/** Persona lines that repeat a procedure file's line verbatim. A restated rule is a rule
 *  that will drift: the copy in the persona is the one nobody lints. */
export function duplicatedRuleLines(presetText, procedures) {
  const procedureLines = new Set()
  for (const text of procedures) {
    for (const line of text.split('\n')) {
      const n = normalize(line)
      if (n.split(' ').length >= 8) procedureLines.add(n)
    }
  }
  const hits = []
  for (const row of presetRows(presetText)) {
    const persona = personaOf(row.text)
    if (persona === undefined) continue
    for (const line of persona.split('\n')) {
      const n = normalize(line)
      if (n.split(' ').length >= 8 && procedureLines.has(n)) hits.push(`${row.id}: "${line.trim().slice(0, 50)}"`)
    }
  }
  return hits
}

/** A resolver for composition package names, searched where this deployment keeps plugins.
 *  Returns (name) => true | false. A wrong package name is a mount failure, and boot is
 *  fail-loud, so this is the one composition defect a static check can catch in advance. */
export function defaultPackageResolver() {
  const roots = []
  const nodeModules = join(dirname(process.execPath), '..', 'lib', 'node_modules')
  roots.push(nodeModules, join(nodeModules, '@deepseek-ai', 'dsh', 'node_modules'))
  const home = process.env.DSH_HOME ?? join(process.env.HOME ?? '', '.dsh')
  const profiles = join(home, 'profiles')
  if (existsSync(profiles)) {
    for (const profile of readdirSync(profiles)) roots.push(join(profiles, profile, 'node_modules'))
  }
  const local = createRequire(import.meta.url)
  return (name) => {
    const pkg = name.startsWith('@') ? name.split('/').slice(0, 2).join('/') : name.split('/')[0]
    try {
      local.resolve(`${pkg}/package.json`)
      return true
    } catch {
      // Fall through to the deployment's own package roots.
    }
    return roots.some((root) => existsSync(join(root, pkg, 'package.json')))
  }
}

/** The preset walls: a tool-subagent row per role, a maxDepth that spans five layers, an
 *  explicit allow list, and a short persona that points instead of restating. */
export function checkPreset(presetText, options = {}) {
  const errors = []
  const all = presetRows(presetText)
  const rows = all.filter((r) => r.id.startsWith('role-'))

  if (options.resolvePackage !== undefined) {
    for (const row of all) {
      const name = /name:\s*'([^']+)'/.exec(row.text)
      const declared = name === null ? undefined : name[1]
      if (declared === undefined || declared === 'cordis:group') continue
      if (!options.resolvePackage(declared)) errors.push(`${row.id}: package ${declared} does not resolve`)
    }
  }

  // The delegation walls. A layer lead drives its OWN layer's test/examine cycle and delegates
  // design to the layer below; the implementer delegates nothing. A missing entry does not fail
  // loudly — the step becomes reachable only from further up and runs in a stand-in seat.
  const walls = new Map()
  for (const row of rows) {
    const tool = /toolName:\s*(\S+)/.exec(row.text)
    const allow = /allow:\s*\[([\s\S]*?)\]/.exec(row.text)
    if (tool !== null) walls.set(tool[1], allow === null ? [] : allow[1].split(',').map((s) => s.trim()).filter(Boolean))
  }
  for (const [lead, layer] of [['role_l1_architect', 1], ['role_l2_integration', 2], ['role_l3_designer', 3]]) {
    const allow = walls.get(lead)
    if (allow === undefined) continue
    const expected = []
    for (const name of walls.keys()) {
      const m = /^role_l(\d)_/.exec(name)
      if (m === null) continue
      const depth = Number(m[1])
      if (depth === layer + 1) expected.push(name)
      if (depth === layer && /_(test_writer|examiner)$/.test(name)) expected.push(name)
    }
    for (const name of expected) {
      if (!allow.includes(name)) errors.push(`${lead}: allow list omits ${name} — that step would run in a stand-in seat`)
    }
  }
  for (const [name, allow] of walls) {
    const delegating = allow.filter((entry) => entry.startsWith('role_'))
    if (delegating.length > 0 && !['role_l1_architect', 'role_l2_integration', 'role_l3_designer'].includes(name)) {
      errors.push(`${name}: delegates nothing — only a layer lead may delegate, but this allows ${delegating.join(', ')}`)
    }
  }

  for (const row of rows) {
    if (!/name:\s*'@deepseek-ai\/dsh-tool-subagent'/.test(row.text)) errors.push(`${row.id}: not a tool-subagent row`)
    if (!/toolName:\s*role_/.test(row.text)) errors.push(`${row.id}: toolName must be role_*`)
    if (!/maxDepth:\s*4\b/.test(row.text)) errors.push(`${row.id}: maxDepth must be 4`)
    if (!/toolFilter:\s*\n\s*allow:/.test(row.text)) errors.push(`${row.id}: no toolFilter.allow wall`)
    const persona = personaOf(row.text)
    if (persona === undefined) errors.push(`${row.id}: no persona`)
    else {
      const length = persona.split('\n').length
      if (length > 14) errors.push(`${row.id}: persona is ${length} lines (max 14)`)
      for (const mention of row.text.matchAll(/strata\/([\w.-]+\.(?:md|json))/g)) {
        if (options.exists !== undefined && !options.exists(mention[1])) errors.push(`${row.id}: points at missing strata/${mention[1]}`)
      }
    }
  }
  for (const hit of duplicatedRuleLines(presetText, options.procedures ?? [])) errors.push(`restated rule ${hit}`)
  return { ok: errors.length === 0, errors, count: rows.length }
}

/** Run every check over one strata root. Returns {rows, failed}. */
export function lint(root, options = {}) {
  const rows = []
  const add = (status, check, detail) => rows.push({ status, check, detail })
  const read = (file) => {
    const path = join(root, file)
    return existsSync(path) ? readFileSync(path, 'utf8') : undefined
  }

  const decisionsText = read('decisions.md') ?? ''
  const briefText = read('brief.md') ?? ''
  const defined = decisionIds(decisionsText)
  const asms = asmIds(briefText, decisionsText)

  // 1. ceilings
  // Coverage: the registry as filed, then the trackers, then every record the directory holds,
  // so all four checks measure them and no check needs a second code path (D-25, design §1/§2).
  const recordPaths = recordFiles(root)
  const coverage = [...REGISTRY, ...TRACKERS, ...(recordPaths ?? []).map(recordEntry)]
  for (const [file, cls, fallback] of coverage) {
    const text = read(file)
    if (text === undefined) {
      add('INFO', 'ceiling', `${file} absent`)
      continue
    }
    if (file === 'decisions.md') continue // bounded per row below, not per file
    const lines = text.replace(/\n$/, '').split('\n').length
    const declared = parseDeclaredCeiling(text)
    if (declared !== undefined && declared > CLASS_MAX[cls]) {
      add('FAIL', 'ceiling', `${file} declares ${declared}, above the ${cls} class max ${CLASS_MAX[cls]}`)
      continue
    }
    const ceiling = declared ?? (fallback === Infinity ? CLASS_MAX[cls] : fallback)
    const bounded = Number.isFinite(ceiling) && Number.isFinite(fallback) ? Math.min(ceiling, fallback) : ceiling
    const over = Number.isFinite(bounded) && lines > bounded
    add(over ? 'FAIL' : 'PASS', 'ceiling', `${file} ${lines}/${Number.isFinite(bounded) ? bounded : 'unbounded'}`)
  }
  // `records/` is a pattern table, not a named entry, so no file exists to name: one row covers
  // the directory, because silence would not be distinguishable from "not measured" (design §5).
  // Absent and empty are different facts, so each prints its own row: an empty directory is no
  // absence (the directory exists and no file is absent), and it reports its zero rather than
  // falling silent — an emptied `records/` must not let a whole class stop being measured with
  // nothing red, the failure F-1 exists to prevent. The zero is INFO, never FAIL, so no corpus is
  // reddened for having no records. Records present print their per-file rows and no row here (D-26).
  if (recordPaths === undefined) add('INFO', 'ceiling', 'records/ absent')
  else if (recordPaths.length === 0) add('INFO', 'ceiling', 'records/ 0 file(s)')

  // 1d. layer-document ceilings — `docs/` declares its own limits in each header, and until now
  // nothing measured them. A violating file is named; a clean corpus is one summary row, because
  // ninety per-file rows would bury every other check.
  const docPaths = docFiles(root)
  if (docPaths === undefined) add('INFO', 'ceiling', 'docs/ absent')
  else {
    const over = []
    let undeclared = 0
    for (const rel of docPaths) {
      const text = readFileSync(join(dirname(root), rel), 'utf8')
      const declared = parseDeclaredCeiling(text)
      if (declared === undefined) { undeclared += 1; continue }
      const lines = text.replace(/\n$/, '').split('\n').length
      if (lines > declared) over.push(`${rel} ${lines}/${declared}`)
    }
    for (const detail of over) add('FAIL', 'ceiling', detail)
    add(over.length === 0 ? 'PASS' : 'FAIL', 'ceiling',
      `docs/ ${docPaths.length} file(s): ${docPaths.length - over.length - undeclared} within their declared ceilings`
      + `${undeclared > 0 ? `, ${undeclared} undeclared` : ''}${over.length > 0 ? `, ${over.length} over` : ''}`)
  }

  // 1b. register rows
  if (decisionsText !== '') {
    const over = registerRowLengths(decisionsText).filter((r) => r.lines > CLASS_MAX.register)
    add(over.length === 0 ? 'PASS' : 'FAIL', 'register',
      over.length === 0
        ? `${decisionsText.match(/^##\s+D-\d+/gm).length} rows, all within ${CLASS_MAX.register} lines`
        : over.map((r) => `${r.id} is ${r.lines} lines`).join('; '))
  }

  // 2. citation resolution
  for (const [file] of coverage) {
    if (file === 'decisions.md') continue
    const text = read(file)
    if (text === undefined) continue
    const missing = []
    for (const id of citations(text)) {
      if (id.startsWith('D-') && !defined.has(id)) missing.push(id)
      if (id.startsWith('ASM-') && !asms.has(id)) missing.push(id)
    }
    add(missing.length === 0 ? 'PASS' : 'FAIL', 'citations',
      missing.length === 0 ? `${file} resolves` : `${file} unresolved: ${[...new Set(missing)].join(', ')}`)
  }

  // 3. exemplar quarantine
  for (const [file] of coverage) {
    if (file === 'decisions.md') continue
    const text = read(file)
    if (text === undefined) continue
    const marks = text.split('\n').filter((l) => l.startsWith('> EXEMPLAR'))
    const badMark = marks.filter((l) => !/non-normative/i.test(l))
    const leaked = leakedExemplarTokens(text)
    const problems = []
    if (badMark.length > 0) problems.push(`${badMark.length} exemplar block(s) missing "non-normative"`)
    if (leaked.length > 0) problems.push(`exemplar instances in normative text: ${leaked.join(', ')}`)
    add(problems.length === 0 ? 'PASS' : 'FAIL', 'exemplar',
      problems.length === 0 ? `${file} quarantined (${marks.length} block(s))` : `${file}: ${problems.join('; ')}`)
  }

  // 4. provenance — statement-level attachment (D-22), failing
  for (const [file] of coverage) {
    if (file === 'decisions.md') continue
    const text = read(file)
    if (text === undefined) continue
    const uncited = uncitedNormative(text)
    const first = uncited.length === 0 ? '' : ` (first: line ${uncited[0].line} "${uncited[0].text}")`
    add(uncited.length === 0 ? 'PASS' : 'FAIL', 'provenance',
      `${file} ${uncited.length} uncited normative statement(s)${first}`)
  }

  // 5. record kinds — state files and layer returns, when units exist
  const unitsDir = join(root, '.strata', 'units')
  if (existsSync(unitsDir)) {
    const required = ['unit', 'layer', 'stage', 'artifacts', 'assumptions', 'streaks']
    for (const file of readdirSync(unitsDir).filter((f) => f.endsWith('.json'))) {
      let parsed
      try {
        parsed = JSON.parse(readFileSync(join(unitsDir, file), 'utf8'))
      } catch {
        add('FAIL', 'state', `${file} is not JSON`)
        continue
      }
      const missing = required.filter((k) => !(k in parsed))
      add(missing.length === 0 ? 'PASS' : 'FAIL', 'state',
        missing.length === 0 ? `${file} well-formed` : `${file} missing ${missing.join(', ')}`)
    }
  } else {
    add('INFO', 'state', 'no .strata/units yet')
  }

  const returnsDir = join(root, '.strata', 'returns')
  if (existsSync(returnsDir)) {
    for (const file of readdirSync(returnsDir).filter((f) => f.endsWith('.json'))) {
      let parsed
      try {
        parsed = JSON.parse(readFileSync(join(returnsDir, file), 'utf8'))
      } catch {
        add('FAIL', 'envelope', `${file} is not JSON`)
        continue
      }
      const result = validateEnvelope(parsed)
      add(result.ok ? 'PASS' : 'FAIL', 'envelope',
        result.ok ? `${file} conforms` : `${file}: ${result.errors.join('; ')}`)
    }
  } else {
    add('INFO', 'envelope', 'no .strata/returns yet')
  }

  // 6. module diff scope — D-17's only enforcement
  const modulesPath = join(root, 'modules.json')
  if (!existsSync(modulesPath)) {
    add('INFO', 'modules', 'no modules.json; diff scope unchecked')
  } else {
    let declared
    try {
      declared = JSON.parse(readFileSync(modulesPath, 'utf8'))
    } catch {
      add('FAIL', 'modules', 'modules.json is not JSON')
    }
    if (declared !== undefined) {
      const parsedModules = parseModules(declared)
      add(parsedModules.ok ? 'PASS' : 'FAIL', 'modules',
        parsedModules.ok ? `${parsedModules.modules.length} modules declared` : parsedModules.errors.join('; '))
      if (parsedModules.ok) {
        add('INFO', 'harness', parsedModules.modules.map((m) => `${m.name}:${harnessCap(m.endpoints)}`).join(' '))
        const changed = options.changed ?? []
        if (changed.length > 0) {
          const escapes = []
          for (const file of changed) {
            const owners = ownersOf(parsedModules.modules, file)
            if (owners.length === 0) escapes.push(`${file} owned by no module`)
            if (owners.length > 1) escapes.push(`${file} claimed by ${owners.join(' and ')}`)
          }
          add(escapes.length === 0 ? 'PASS' : 'FAIL', 'diff scope',
            escapes.length === 0 ? `${changed.length} changed file(s) inside their modules` : escapes.join('; '))
        } else {
          add('INFO', 'diff scope', 'no --changed list supplied')
        }
      }
    }
  }

  // 7. the preset walls
  const presetPath = join(root, 'preset', 'agent.cordis.yml')
  if (!existsSync(presetPath)) {
    add('INFO', 'preset', 'no preset/agent.cordis.yml')
  } else {
    const presetText = readFileSync(presetPath, 'utf8')
    const procedures = ['examiner.md', 'rebuild.md', 'walkthrough.md', 'modules.md', 'envelope.md',
      'research.md', 'proposals.md', 'platform.md']
      .map((f) => (existsSync(join(root, f)) ? readFileSync(join(root, f), 'utf8') : ''))
    const checked = checkPreset(presetText, {
      exists: (f) => existsSync(join(root, f)),
      procedures,
      resolvePackage: defaultPackageResolver(),
    })
    add(checked.ok ? 'PASS' : 'FAIL', 'preset',
      checked.ok ? `${checked.count} role rows walled; packages resolve; personas point, never restate` : checked.errors.join('; '))
  }

  const failed = rows.filter((r) => r.status === 'FAIL').length
  return { rows, failed }
}

/** Render rows as the report the caller prints. */
export function render(root, rows, failed) {
  const width = Math.max(...rows.map((r) => r.check.length))
  const body = rows.map((r) => `${r.status.padEnd(4)} ${r.check.padEnd(width)}  ${r.detail}`)
  return [`strata-lint · root=${root}`, ...body,
    failed === 0 ? `exit 0 — ${rows.length} checks, no failures` : `exit 1 — ${failed} failing check(s)`].join('\n')
}

if (process.argv[1] !== undefined && basename(process.argv[1]) === 'strata-lint.mjs') {
  const args = process.argv.slice(2)
  const flag = (name) => {
    const i = args.indexOf(`--${name}`)
    return i === -1 ? undefined : args[i + 1]
  }
  const root = (() => {
    const values = new Set(args.filter((a) => a.startsWith('--')).map((a) => flag(a.slice(2))))
    return args.find((a) => !a.startsWith('--') && !values.has(a)) ?? '.'
  })()
  const changed = (flag('changed') ?? '').split(',').map((s) => s.trim()).filter(Boolean)
  const { rows, failed } = lint(root, { changed })
  process.stdout.write(`${render(root, rows, failed)}\n`)
  process.exitCode = failed === 0 ? 0 : 1
}
