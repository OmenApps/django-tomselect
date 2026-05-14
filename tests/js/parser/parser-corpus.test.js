import { describe, it, expect } from 'vitest'
import { readFileSync } from 'node:fs'
import { resolve, dirname } from 'node:path'
import { fileURLToPath } from 'node:url'

import { parseQuery } from '../../../client/plugins/token/parser.js'

// Shared corpus drives both this suite and the Python tests in
// example_project/test_query_parser.py. Adding a new edge case is one entry;
// both parsers must agree.
const here = dirname(fileURLToPath(import.meta.url))
const corpusPath = resolve(here, '../../../tests/fixtures/parser_corpus.json')
const corpus = JSON.parse(readFileSync(corpusPath, 'utf-8'))

describe('parser corpus parity (cross-language fixture)', () => {
  for (const c of corpus.cases) {
    it(c.name, () => {
      const operators = c.operators || corpus.default_operators
      const caps = Object.assign({}, corpus.default_caps, c.caps || {})

      const result = parseQuery(c.input, operators, caps)

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

      expect(actualTokens).toEqual(expectedTokens)
      expect(result.free_text).toEqual(c.free_text)
      expect(result.errors.map(e => e.code)).toEqual(c.errors)
    })
  }
})
