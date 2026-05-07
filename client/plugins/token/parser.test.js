// Node-runnable parser parity test against the shared corpus.
//
// Run via:  npm test
//
// The same JSON fixture (tests/fixtures/parser_corpus.json) drives the Python
// test suite (example_project/test_query_parser.py). Drift between the two
// parsers is caught here.

import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, resolve } from 'node:path'

import { parseQuery } from './parser.js'

const here = dirname(fileURLToPath(import.meta.url))
const corpusPath = resolve(here, '..', '..', '..', 'tests', 'fixtures', 'parser_corpus.json')
const corpus = JSON.parse(readFileSync(corpusPath, 'utf-8'))

let passed = 0
let failed = 0

function deepEqual (a, b) {
  return JSON.stringify(a) === JSON.stringify(b)
}

function reportFail (caseName, message, actual, expected) {
  failed++
  console.error('  FAIL: ' + caseName)
  console.error('    ' + message)
  console.error('    actual:   ' + JSON.stringify(actual))
  console.error('    expected: ' + JSON.stringify(expected))
}

for (const c of corpus.cases) {
  const operators = c.operators || corpus.default_operators
  const caps = Object.assign({}, corpus.default_caps, c.caps || {})

  const result = parseQuery(c.input, operators, caps)

  // Tokens - compare key, values (as array), was_quoted.
  const actualTokens = result.tokens.map(t => ({
    key: t.key,
    values: t.values,
    was_quoted: t.was_quoted
  }))
  const expectedTokens = c.tokens.map(t => ({
    key: t.key,
    values: t.values,
    was_quoted: t.was_quoted
  }))

  if (!deepEqual(actualTokens, expectedTokens)) {
    reportFail(c.name, 'token mismatch', actualTokens, expectedTokens)
    continue
  }

  if (!deepEqual(result.free_text, c.free_text)) {
    reportFail(c.name, 'free_text mismatch', result.free_text, c.free_text)
    continue
  }

  const actualErrorCodes = result.errors.map(e => e.code)
  if (!deepEqual(actualErrorCodes, c.errors)) {
    reportFail(c.name, 'errors mismatch', actualErrorCodes, c.errors)
    continue
  }

  passed++
}

console.log('  ' + passed + ' passed, ' + failed + ' failed (out of ' + corpus.cases.length + ')')
if (failed > 0) {
  process.exit(1)
}
