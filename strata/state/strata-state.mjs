#!/usr/bin/env node
/**
 * strata-state — the only writer of unit state, and the only progress record that survives
 * a dead session. Every verb is a transition; illegal transitions are refused rather than
 * recorded. Nothing here is prose: the file is machine-written and overwritten in place.
 */
import { existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { join } from 'node:path'

export const LAYERS = ['L0', 'L1', 'L2', 'L3', 'L4']
export const THRESHOLD = 3

export function emptyState(unit) {
  return {
    unit,
    layer: 'L0',
    stage: 'design',
    artifacts: [],
    assumptions: [],
    streaks: {},
    rebuildEligible: false,
    updated: new Date().toISOString(),
  }
}

/** Highest streak across artifacts, which is what the rebuild threshold is measured on. */
export function maxStreak(state) {
  return Math.max(0, ...Object.values(state.streaks ?? {}))
}

/**
 * Apply one event. Returns {state, error} — `error` set means the transition was refused and
 * the state is returned unchanged.
 */
export function transition(state, event) {
  const next = { ...state, streaks: { ...state.streaks }, assumptions: [...state.assumptions] }
  const artifact = event.artifact ?? 'unit'

  switch (event.kind) {
    case 'enter': {
      if (!LAYERS.includes(event.layer)) return { state, error: `unknown layer "${event.layer}"` }
      next.layer = event.layer
      return { state: next }
    }
    case 'artifact': {
      if (!next.artifacts.includes(event.id)) next.artifacts.push(event.id)
      return { state: next }
    }
    case 'assume': {
      if (!event.alternative) return { state, error: 'an assumption requires the alternative it rejected (D-5)' }
      next.assumptions.push({ id: event.id, text: event.text, alternative: event.alternative, status: 'open' })
      return { state: next }
    }
    case 'pass': {
      delete next.streaks[artifact]
      next.rebuildEligible = maxStreak(next) >= THRESHOLD
      if (next.assumptions.length > 0) next.assumptions = next.assumptions.map((a) => ({ ...a, status: 'reviewed' }))
      return { state: next }
    }
    case 'fail': {
      // A rebuild is pending: further failures would hide the case for a rebuild, not inform it.
      if (next.rebuildEligible) return { state, error: 'rebuild eligible; run `rebuild` or `pass` before failing again (D-12)' }
      next.streaks[artifact] = (next.streaks[artifact] ?? 0) + 1
      if (event.reason === 'adjudication') {
        // Counted exactly like a red battery: asking is not a pause and not free (D-15).
        next.lastFailure = { artifact, reason: 'adjudication' }
      } else {
        next.lastFailure = { artifact, reason: event.reason ?? 'red' }
      }
      if (event.from === 'L4') next.routedTo = 'L2' // L4 owns no design (D-13)
      next.rebuildEligible = maxStreak(next) >= THRESHOLD
      return { state: next }
    }
    case 'rebuild': {
      if (!next.rebuildEligible) return { state, error: 'no artifact at the rebuild threshold (D-12)' }
      next.streaks = {}
      next.rebuildEligible = false
      next.builds = (next.builds ?? 1) + 1
      next.stage = 'design'
      delete next.lastFailure
      delete next.routedTo
      return { state: next }
    }
    case 'close': {
      next.stage = 'done'
      return { state: next }
    }
    default:
      return { state, error: `unknown event "${event.kind}"` }
  }
}

/** Where a unit lives on disk. One file per unit, overwritten on every transition. */
export function statePath(root, unit) {
  return join(root, '.strata', 'units', `${unit}.json`)
}

export function load(root, unit) {
  const path = statePath(root, unit)
  return existsSync(path) ? JSON.parse(readFileSync(path, 'utf8')) : undefined
}

export function save(root, state) {
  const path = statePath(root, state.unit)
  mkdirSync(join(root, '.strata', 'units'), { recursive: true })
  writeFileSync(path, `${JSON.stringify({ ...state, updated: new Date().toISOString() }, null, 2)}\n`)
  return path
}

const USAGE = `strata-state <root> <verb> <unit> [flags]
  init <unit>                          start a unit at L0
  enter <unit> --layer L3              record the current layer
  artifact <unit> --id A-1             declare an artifact id
  assume <unit> --id A-1 --text ... --alternative ...   record an assumption
  pass <unit> [--artifact A-1]         battery green; clears that artifact's streak
  fail <unit> [--artifact A-1] [--reason adjudication|red|early-fail] [--from L4]
  rebuild <unit>                       teardown after a rebuild recommendation
  close <unit>                         unit done
  show <unit>`

if (process.argv[1] !== undefined && process.argv[1].endsWith('strata-state.mjs')) {
  const [, , root, verb, unit, ...rest] = process.argv
  const flag = (name) => {
    const i = rest.indexOf(`--${name}`)
    return i === -1 ? undefined : rest[i + 1]
  }
  if (root === undefined || verb === undefined) {
    process.stderr.write(`${USAGE}\n`)
    process.exitCode = 2
  } else if (verb === 'show') {
    process.stdout.write(`${JSON.stringify(load(root, unit) ?? null, null, 2)}\n`)
  } else if (verb === 'init') {
    process.stdout.write(`init ${unit} → ${save(root, emptyState(unit))}\n`)
  } else {
    const base = verb === 'init' ? emptyState(unit) : load(root, unit)
    if (base === undefined) {
      process.stderr.write(`no state for ${unit}; run init first\n`)
      process.exitCode = 2
    } else {
      const events = {
        enter: { kind: 'enter', layer: flag('layer') },
        artifact: { kind: 'artifact', id: flag('id') },
        assume: { kind: 'assume', id: flag('id'), text: flag('text'), alternative: flag('alternative') },
        pass: { kind: 'pass', artifact: flag('artifact') },
        fail: { kind: 'fail', artifact: flag('artifact'), reason: flag('reason'), from: flag('from') },
        rebuild: { kind: 'rebuild' },
        close: { kind: 'close' },
      }[verb]
      if (events === undefined) {
        process.stderr.write(`${USAGE}\n`)
        process.exitCode = 2
      } else {
        const result = transition(base, events)
        if (result.error !== undefined) {
          process.stderr.write(`refused: ${result.error}\n`)
          process.exitCode = 1
        } else {
          const path = save(root, result.state)
          process.stdout.write(`${verb} ${unit} → ${path}\n`)
        }
      }
    }
  }
}
