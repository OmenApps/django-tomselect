// Token parser - pure JS mirror of the Python parser in
// src/django_tomselect/_tokenize.py and query.py.
// Drift between this and the Python implementation is caught in CI by running
// the shared JSON corpus at tests/fixtures/parser_corpus.json against both.

/* eslint-disable no-multi-spaces */

export const PARSE_ERRORS = {
  UNKNOWN_OPERATOR: 'UNKNOWN_OPERATOR',
  UNTERMINATED_QUOTE: 'UNTERMINATED_QUOTE',
  MAX_RAW_LENGTH_EXCEEDED: 'MAX_RAW_LENGTH_EXCEEDED',
  MAX_TOKENS_EXCEEDED: 'MAX_TOKENS_EXCEEDED',
  MAX_VALUES_PER_OPERATOR_EXCEEDED: 'MAX_VALUES_PER_OPERATOR_EXCEEDED',
  EMPTY_VALUE: 'EMPTY_VALUE'
}

const OPERATOR_KEY_RE = /^([A-Za-z][A-Za-z0-9_]*):([\s\S]*)$/

const DEFAULT_CAPS = {
  max_raw_length: 4096,
  max_tokens: 32,
  max_values_per_operator: 16
}

// ---------------------------------------------------------------------------
// Tokenizer - returns [{text, was_quoted}, ...] or throws on unterminated quote.
// ---------------------------------------------------------------------------

export function tokenize (raw, opts = {}) {
  const maxBytes = opts.max_raw_length_bytes ?? DEFAULT_CAPS.max_raw_length
  if (raw == null) return []

  // Byte-length cap - utf-8 encoded.
  const utf8Len = new TextEncoder().encode(raw).length
  if (utf8Len > maxBytes) {
    const e = new Error('Raw query exceeds maximum byte length (' + maxBytes + ').')
    e.code = 'MAX_RAW_LENGTH'
    throw e
  }

  const segments = []
  let i = 0
  const n = raw.length
  let buf = []
  let inQuote = null
  let quotedSegment = false

  function flush () {
    if (buf.length || quotedSegment) {
      segments.push({ text: buf.join(''), was_quoted: quotedSegment })
      buf = []
    }
    quotedSegment = false
  }

  while (i < n) {
    const ch = raw[i]
    if (inQuote !== null) {
      if (ch === '\\' && i + 1 < n) {
        const nxt = raw[i + 1]
        if (nxt === '"' || nxt === "'" || nxt === '\\') {
          buf.push(nxt)
          i += 2
          continue
        }
        buf.push(ch)
        i += 1
        continue
      }
      if (ch === inQuote) {
        inQuote = null
        quotedSegment = true
        i += 1
        continue
      }
      buf.push(ch)
      i += 1
      continue
    }
    if (/\s/.test(ch)) {
      flush()
      i += 1
      continue
    }
    if (ch === '"' || ch === "'") {
      inQuote = ch
      i += 1
      continue
    }
    buf.push(ch)
    i += 1
  }

  if (inQuote !== null) {
    const e = new Error('Unterminated quote starting with ' + JSON.stringify(inQuote) + '.')
    e.code = 'UNTERMINATED_QUOTE'
    throw e
  }

  flush()
  return segments
}

// ---------------------------------------------------------------------------
// Parser - given an operator registry, produces tokens / free_text / errors.
//
// operators: { key: { multi: bool } }
// caps: { max_raw_length, max_tokens, max_values_per_operator }
// ---------------------------------------------------------------------------

export function parseQuery (raw, operators, caps = {}) {
  const merged = Object.assign({}, DEFAULT_CAPS, caps)
  const result = { tokens: [], free_text: [], errors: [] }

  if (raw == null || raw === '') return result

  let segments
  try {
    segments = tokenize(raw, { max_raw_length_bytes: merged.max_raw_length })
  } catch (e) {
    if (e.code === 'MAX_RAW_LENGTH') {
      result.errors.push({ code: PARSE_ERRORS.MAX_RAW_LENGTH_EXCEEDED, message: e.message })
    } else {
      result.errors.push({ code: PARSE_ERRORS.UNTERMINATED_QUOTE, message: e.message })
    }
    return result
  }

  if (segments.length > merged.max_tokens) {
    result.errors.push({
      code: PARSE_ERRORS.MAX_TOKENS_EXCEEDED,
      message: 'Too many tokens (' + segments.length + ' > ' + merged.max_tokens + ').'
    })
    return result
  }

  for (let s = 0; s < segments.length; s++) {
    const seg = segments[s]
    const m = seg.text.match(OPERATOR_KEY_RE)
    if (m === null) {
      result.free_text.push(seg.text)
      continue
    }
    const key = m[1]
    const value = m[2]
    const opSpec = operators[key]
    if (opSpec == null) {
      result.errors.push({
        code: PARSE_ERRORS.UNKNOWN_OPERATOR,
        message: 'Unknown operator ' + JSON.stringify(key) + '.',
        operator_key: key
      })
      continue
    }

    let values
    if (opSpec.multi) {
      values = value === '' ? [''] : value.split(',')
      if (values.length > merged.max_values_per_operator) {
        result.errors.push({
          code: PARSE_ERRORS.MAX_VALUES_PER_OPERATOR_EXCEEDED,
          message: 'Operator ' + JSON.stringify(key) + ' has ' + values.length +
                   ' values (maximum ' + merged.max_values_per_operator + ').',
          operator_key: key
        })
        continue
      }
      // Mirror the Python parser: reject "status:draft," / "category:1,,2".
      if (values.length > 1 && values.some(v => v.trim() === '')) {
        result.errors.push({
          code: PARSE_ERRORS.EMPTY_VALUE,
          message: 'Operator ' + JSON.stringify(key) + ' has an empty value in ' +
                   JSON.stringify(seg.text) + '.',
          operator_key: key
        })
        continue
      }
    } else {
      values = [value]
    }

    result.tokens.push({ key, values, was_quoted: seg.was_quoted })
  }

  return result
}
