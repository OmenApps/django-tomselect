(() => {
  var __create = Object.create;
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __getProtoOf = Object.getPrototypeOf;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __commonJS = (cb, mod) => function __require() {
    return mod || (0, cb[__getOwnPropNames(cb)[0]])((mod = { exports: {} }).exports, mod), mod.exports;
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toESM = (mod, isNodeMode, target) => (target = mod != null ? __create(__getProtoOf(mod)) : {}, __copyProps(
    // If the importer is in node compatibility mode or this is not an ESM
    // file that has been converted to a CommonJS file using a Babel-
    // compatible transform (i.e. "__esModule" has not been set), then set
    // "default" to the CommonJS "module.exports" for node compatibility.
    isNodeMode || !mod || !mod.__esModule ? __defProp(target, "default", { value: mod, enumerable: true }) : target,
    mod
  ));

  // node_modules/tom-select/dist/js/tom-select.base.js
  var require_tom_select_base = __commonJS({
    "node_modules/tom-select/dist/js/tom-select.base.js"(exports, module) {
      (function(global, factory) {
        typeof exports === "object" && typeof module !== "undefined" ? module.exports = factory() : typeof define === "function" && define.amd ? define(factory) : (global = typeof globalThis !== "undefined" ? globalThis : global || self, global.TomSelect = factory());
      })(exports, function() {
        "use strict";
        function forEvents(events, callback) {
          events.split(/\s+/).forEach((event) => {
            callback(event);
          });
        }
        class MicroEvent {
          constructor() {
            this._events = void 0;
            this._events = {};
          }
          on(events, fct) {
            forEvents(events, (event) => {
              const event_array = this._events[event] || [];
              event_array.push(fct);
              this._events[event] = event_array;
            });
          }
          off(events, fct) {
            var n = arguments.length;
            if (n === 0) {
              this._events = {};
              return;
            }
            forEvents(events, (event) => {
              if (n === 1) {
                delete this._events[event];
                return;
              }
              const event_array = this._events[event];
              if (event_array === void 0)
                return;
              event_array.splice(event_array.indexOf(fct), 1);
              this._events[event] = event_array;
            });
          }
          trigger(events, ...args) {
            var self2 = this;
            forEvents(events, (event) => {
              const event_array = self2._events[event];
              if (event_array === void 0)
                return;
              event_array.forEach((fct) => {
                fct.apply(self2, args);
              });
            });
          }
        }
        function MicroPlugin(Interface) {
          Interface.plugins = {};
          return class extends Interface {
            constructor(...args) {
              super(...args);
              this.plugins = {
                names: [],
                settings: {},
                requested: {},
                loaded: {}
              };
            }
            /**
             * Registers a plugin.
             *
             * @param {function} fn
             */
            static define(name, fn) {
              Interface.plugins[name] = {
                "name": name,
                "fn": fn
              };
            }
            /**
             * Initializes the listed plugins (with options).
             * Acceptable formats:
             *
             * List (without options):
             *   ['a', 'b', 'c']
             *
             * List (with options):
             *   [{'name': 'a', options: {}}, {'name': 'b', options: {}}]
             *
             * Hash (with options):
             *   {'a': { ... }, 'b': { ... }, 'c': { ... }}
             *
             * @param {array|object} plugins
             */
            initializePlugins(plugins) {
              var key, name;
              const self2 = this;
              const queue = [];
              if (Array.isArray(plugins)) {
                plugins.forEach((plugin) => {
                  if (typeof plugin === "string") {
                    queue.push(plugin);
                  } else {
                    self2.plugins.settings[plugin.name] = plugin.options;
                    queue.push(plugin.name);
                  }
                });
              } else if (plugins) {
                for (key in plugins) {
                  if (plugins.hasOwnProperty(key)) {
                    self2.plugins.settings[key] = plugins[key];
                    queue.push(key);
                  }
                }
              }
              while (name = queue.shift()) {
                self2.require(name);
              }
            }
            loadPlugin(name) {
              var self2 = this;
              var plugins = self2.plugins;
              var plugin = Interface.plugins[name];
              if (!Interface.plugins.hasOwnProperty(name)) {
                throw new Error('Unable to find "' + name + '" plugin');
              }
              plugins.requested[name] = true;
              plugins.loaded[name] = plugin.fn.apply(self2, [self2.plugins.settings[name] || {}]);
              plugins.names.push(name);
            }
            /**
             * Initializes a plugin.
             *
             */
            require(name) {
              var self2 = this;
              var plugins = self2.plugins;
              if (!self2.plugins.loaded.hasOwnProperty(name)) {
                if (plugins.requested[name]) {
                  throw new Error('Plugin has circular dependency ("' + name + '")');
                }
                self2.loadPlugin(name);
              }
              return plugins.loaded[name];
            }
          };
        }
        const arrayToPattern = (chars) => {
          chars = chars.filter(Boolean);
          if (chars.length < 2) {
            return chars[0] || "";
          }
          return maxValueLength(chars) == 1 ? "[" + chars.join("") + "]" : "(?:" + chars.join("|") + ")";
        };
        const sequencePattern = (array) => {
          if (!hasDuplicates(array)) {
            return array.join("");
          }
          let pattern = "";
          let prev_char_count = 0;
          const prev_pattern = () => {
            if (prev_char_count > 1) {
              pattern += "{" + prev_char_count + "}";
            }
          };
          array.forEach((char, i) => {
            if (char === array[i - 1]) {
              prev_char_count++;
              return;
            }
            prev_pattern();
            pattern += char;
            prev_char_count = 1;
          });
          prev_pattern();
          return pattern;
        };
        const setToPattern = (chars) => {
          let array = toArray(chars);
          return arrayToPattern(array);
        };
        const hasDuplicates = (array) => {
          return new Set(array).size !== array.length;
        };
        const escape_regex = (str) => {
          return (str + "").replace(/([\$\(\)\*\+\.\?\[\]\^\{\|\}\\])/gu, "\\$1");
        };
        const maxValueLength = (array) => {
          return array.reduce((longest, value) => Math.max(longest, unicodeLength(value)), 0);
        };
        const unicodeLength = (str) => {
          return toArray(str).length;
        };
        const toArray = (p) => Array.from(p);
        const allSubstrings = (input) => {
          if (input.length === 1)
            return [[input]];
          let result = [];
          const start = input.substring(1);
          const suba = allSubstrings(start);
          suba.forEach(function(subresult) {
            let tmp = subresult.slice(0);
            tmp[0] = input.charAt(0) + tmp[0];
            result.push(tmp);
            tmp = subresult.slice(0);
            tmp.unshift(input.charAt(0));
            result.push(tmp);
          });
          return result;
        };
        const code_points = [[0, 65535]];
        const accent_pat = "[\u0300-\u036F\xB7\u02BE\u02BC]";
        let unicode_map;
        let multi_char_reg;
        const max_char_length = 3;
        const latin_convert = {};
        const latin_condensed = {
          "/": "\u2044\u2215",
          "0": "\u07C0",
          "a": "\u2C65\u0250\u0251",
          "aa": "\uA733",
          "ae": "\xE6\u01FD\u01E3",
          "ao": "\uA735",
          "au": "\uA737",
          "av": "\uA739\uA73B",
          "ay": "\uA73D",
          "b": "\u0180\u0253\u0183",
          "c": "\uA73F\u0188\u023C\u2184",
          "d": "\u0111\u0257\u0256\u1D05\u018C\uABB7\u0501\u0266",
          "e": "\u025B\u01DD\u1D07\u0247",
          "f": "\uA77C\u0192",
          "g": "\u01E5\u0260\uA7A1\u1D79\uA77F\u0262",
          "h": "\u0127\u2C68\u2C76\u0265",
          "i": "\u0268\u0131",
          "j": "\u0249\u0237",
          "k": "\u0199\u2C6A\uA741\uA743\uA745\uA7A3",
          "l": "\u0142\u019A\u026B\u2C61\uA749\uA747\uA781\u026D",
          "m": "\u0271\u026F\u03FB",
          "n": "\uA7A5\u019E\u0272\uA791\u1D0E\u043B\u0509",
          "o": "\xF8\u01FF\u0254\u0275\uA74B\uA74D\u1D11",
          "oe": "\u0153",
          "oi": "\u01A3",
          "oo": "\uA74F",
          "ou": "\u0223",
          "p": "\u01A5\u1D7D\uA751\uA753\uA755\u03C1",
          "q": "\uA757\uA759\u024B",
          "r": "\u024D\u027D\uA75B\uA7A7\uA783",
          "s": "\xDF\u023F\uA7A9\uA785\u0282",
          "t": "\u0167\u01AD\u0288\u2C66\uA787",
          "th": "\xFE",
          "tz": "\uA729",
          "u": "\u0289",
          "v": "\u028B\uA75F\u028C",
          "vy": "\uA761",
          "w": "\u2C73",
          "y": "\u01B4\u024F\u1EFF",
          "z": "\u01B6\u0225\u0240\u2C6C\uA763",
          "hv": "\u0195"
        };
        for (let latin in latin_condensed) {
          let unicode = latin_condensed[latin] || "";
          for (let i = 0; i < unicode.length; i++) {
            let char = unicode.substring(i, i + 1);
            latin_convert[char] = latin;
          }
        }
        const convert_pat = new RegExp(Object.keys(latin_convert).join("|") + "|" + accent_pat, "gu");
        const initialize = (_code_points) => {
          if (unicode_map !== void 0)
            return;
          unicode_map = generateMap(_code_points || code_points);
        };
        const normalize = (str, form = "NFKD") => str.normalize(form);
        const asciifold2 = (str) => {
          return toArray(str).reduce(
            /**
             * @param {string} result
             * @param {string} char
             */
            (result, char) => {
              return result + _asciifold(char);
            },
            ""
          );
        };
        const _asciifold = (str) => {
          str = normalize(str).toLowerCase().replace(convert_pat, (char) => {
            return latin_convert[char] || "";
          });
          return normalize(str, "NFC");
        };
        function* generator(code_points2) {
          for (const [code_point_min, code_point_max] of code_points2) {
            for (let i = code_point_min; i <= code_point_max; i++) {
              let composed = String.fromCharCode(i);
              let folded = asciifold2(composed);
              if (folded == composed.toLowerCase()) {
                continue;
              }
              if (folded.length > max_char_length) {
                continue;
              }
              if (folded.length == 0) {
                continue;
              }
              yield {
                folded,
                composed,
                code_point: i
              };
            }
          }
        }
        const generateSets = (code_points2) => {
          const unicode_sets = {};
          const addMatching = (folded, to_add) => {
            const folded_set = unicode_sets[folded] || /* @__PURE__ */ new Set();
            const patt = new RegExp("^" + setToPattern(folded_set) + "$", "iu");
            if (to_add.match(patt)) {
              return;
            }
            folded_set.add(escape_regex(to_add));
            unicode_sets[folded] = folded_set;
          };
          for (let value of generator(code_points2)) {
            addMatching(value.folded, value.folded);
            addMatching(value.folded, value.composed);
          }
          return unicode_sets;
        };
        const generateMap = (code_points2) => {
          const unicode_sets = generateSets(code_points2);
          const unicode_map2 = {};
          let multi_char = [];
          for (let folded in unicode_sets) {
            let set = unicode_sets[folded];
            if (set) {
              unicode_map2[folded] = setToPattern(set);
            }
            if (folded.length > 1) {
              multi_char.push(escape_regex(folded));
            }
          }
          multi_char.sort((a, b) => b.length - a.length);
          const multi_char_patt = arrayToPattern(multi_char);
          multi_char_reg = new RegExp("^" + multi_char_patt, "u");
          return unicode_map2;
        };
        const mapSequence = (strings, min_replacement = 1) => {
          let chars_replaced = 0;
          strings = strings.map((str) => {
            if (unicode_map[str]) {
              chars_replaced += str.length;
            }
            return unicode_map[str] || str;
          });
          if (chars_replaced >= min_replacement) {
            return sequencePattern(strings);
          }
          return "";
        };
        const substringsToPattern = (str, min_replacement = 1) => {
          min_replacement = Math.max(min_replacement, str.length - 1);
          return arrayToPattern(allSubstrings(str).map((sub_pat) => {
            return mapSequence(sub_pat, min_replacement);
          }));
        };
        const sequencesToPattern = (sequences, all = true) => {
          let min_replacement = sequences.length > 1 ? 1 : 0;
          return arrayToPattern(sequences.map((sequence) => {
            let seq = [];
            const len = all ? sequence.length() : sequence.length() - 1;
            for (let j = 0; j < len; j++) {
              seq.push(substringsToPattern(sequence.substrs[j] || "", min_replacement));
            }
            return sequencePattern(seq);
          }));
        };
        const inSequences = (needle_seq, sequences) => {
          for (const seq of sequences) {
            if (seq.start != needle_seq.start || seq.end != needle_seq.end) {
              continue;
            }
            if (seq.substrs.join("") !== needle_seq.substrs.join("")) {
              continue;
            }
            let needle_parts = needle_seq.parts;
            const filter = (part) => {
              for (const needle_part of needle_parts) {
                if (needle_part.start === part.start && needle_part.substr === part.substr) {
                  return false;
                }
                if (part.length == 1 || needle_part.length == 1) {
                  continue;
                }
                if (part.start < needle_part.start && part.end > needle_part.start) {
                  return true;
                }
                if (needle_part.start < part.start && needle_part.end > part.start) {
                  return true;
                }
              }
              return false;
            };
            let filtered = seq.parts.filter(filter);
            if (filtered.length > 0) {
              continue;
            }
            return true;
          }
          return false;
        };
        class Sequence {
          constructor() {
            this.parts = [];
            this.substrs = [];
            this.start = 0;
            this.end = 0;
          }
          /**
           * @param {TSequencePart|undefined} part
           */
          add(part) {
            if (part) {
              this.parts.push(part);
              this.substrs.push(part.substr);
              this.start = Math.min(part.start, this.start);
              this.end = Math.max(part.end, this.end);
            }
          }
          last() {
            return this.parts[this.parts.length - 1];
          }
          length() {
            return this.parts.length;
          }
          /**
           * @param {number} position
           * @param {TSequencePart} last_piece
           */
          clone(position, last_piece) {
            let clone = new Sequence();
            let parts = JSON.parse(JSON.stringify(this.parts));
            let last_part = parts.pop();
            for (const part of parts) {
              clone.add(part);
            }
            let last_substr = last_piece.substr.substring(0, position - last_part.start);
            let clone_last_len = last_substr.length;
            clone.add({
              start: last_part.start,
              end: last_part.start + clone_last_len,
              length: clone_last_len,
              substr: last_substr
            });
            return clone;
          }
        }
        const getPattern = (str) => {
          initialize();
          str = asciifold2(str);
          let pattern = "";
          let sequences = [new Sequence()];
          for (let i = 0; i < str.length; i++) {
            let substr = str.substring(i);
            let match = substr.match(multi_char_reg);
            const char = str.substring(i, i + 1);
            const match_str = match ? match[0] : null;
            let overlapping = [];
            let added_types = /* @__PURE__ */ new Set();
            for (const sequence of sequences) {
              const last_piece = sequence.last();
              if (!last_piece || last_piece.length == 1 || last_piece.end <= i) {
                if (match_str) {
                  const len = match_str.length;
                  sequence.add({
                    start: i,
                    end: i + len,
                    length: len,
                    substr: match_str
                  });
                  added_types.add("1");
                } else {
                  sequence.add({
                    start: i,
                    end: i + 1,
                    length: 1,
                    substr: char
                  });
                  added_types.add("2");
                }
              } else if (match_str) {
                let clone = sequence.clone(i, last_piece);
                const len = match_str.length;
                clone.add({
                  start: i,
                  end: i + len,
                  length: len,
                  substr: match_str
                });
                overlapping.push(clone);
              } else {
                added_types.add("3");
              }
            }
            if (overlapping.length > 0) {
              overlapping = overlapping.sort((a, b) => {
                return a.length() - b.length();
              });
              for (let clone of overlapping) {
                if (inSequences(clone, sequences)) {
                  continue;
                }
                sequences.push(clone);
              }
              continue;
            }
            if (i > 0 && added_types.size == 1 && !added_types.has("3")) {
              pattern += sequencesToPattern(sequences, false);
              let new_seq = new Sequence();
              const old_seq = sequences[0];
              if (old_seq) {
                new_seq.add(old_seq.last());
              }
              sequences = [new_seq];
            }
          }
          pattern += sequencesToPattern(sequences, true);
          return pattern;
        };
        const getAttr = (obj, name) => {
          if (!obj)
            return;
          return obj[name];
        };
        const getAttrNesting = (obj, name) => {
          if (!obj)
            return;
          var part, names = name.split(".");
          while ((part = names.shift()) && (obj = obj[part]))
            ;
          return obj;
        };
        const scoreValue = (value, token, weight) => {
          var score, pos;
          if (!value)
            return 0;
          value = value + "";
          if (token.regex == null)
            return 0;
          pos = value.search(token.regex);
          if (pos === -1)
            return 0;
          score = token.string.length / value.length;
          if (pos === 0)
            score += 0.5;
          return score * weight;
        };
        const propToArray = (obj, key) => {
          var value = obj[key];
          if (typeof value == "function")
            return value;
          if (value && !Array.isArray(value)) {
            obj[key] = [value];
          }
        };
        const iterate$1 = (object, callback) => {
          if (Array.isArray(object)) {
            object.forEach(callback);
          } else {
            for (var key in object) {
              if (object.hasOwnProperty(key)) {
                callback(object[key], key);
              }
            }
          }
        };
        const cmp = (a, b) => {
          if (typeof a === "number" && typeof b === "number") {
            return a > b ? 1 : a < b ? -1 : 0;
          }
          a = asciifold2(a + "").toLowerCase();
          b = asciifold2(b + "").toLowerCase();
          if (a > b)
            return 1;
          if (b > a)
            return -1;
          return 0;
        };
        class Sifter {
          // []|{};
          /**
           * Textually searches arrays and hashes of objects
           * by property (or multiple properties). Designed
           * specifically for autocomplete.
           *
           */
          constructor(items, settings) {
            this.items = void 0;
            this.settings = void 0;
            this.items = items;
            this.settings = settings || {
              diacritics: true
            };
          }
          /**
           * Splits a search string into an array of individual
           * regexps to be used to match results.
           *
           */
          tokenize(query, respect_word_boundaries, weights) {
            if (!query || !query.length)
              return [];
            const tokens = [];
            const words = query.split(/\s+/);
            var field_regex;
            if (weights) {
              field_regex = new RegExp("^(" + Object.keys(weights).map(escape_regex).join("|") + "):(.*)$");
            }
            words.forEach((word) => {
              let field_match;
              let field = null;
              let regex = null;
              if (field_regex && (field_match = word.match(field_regex))) {
                field = field_match[1];
                word = field_match[2];
              }
              if (word.length > 0) {
                if (this.settings.diacritics) {
                  regex = getPattern(word) || null;
                } else {
                  regex = escape_regex(word);
                }
                if (regex && respect_word_boundaries)
                  regex = "\\b" + regex;
              }
              tokens.push({
                string: word,
                regex: regex ? new RegExp(regex, "iu") : null,
                field
              });
            });
            return tokens;
          }
          /**
           * Returns a function to be used to score individual results.
           *
           * Good matches will have a higher score than poor matches.
           * If an item is not a match, 0 will be returned by the function.
           *
           * @returns {T.ScoreFn}
           */
          getScoreFunction(query, options) {
            var search = this.prepareSearch(query, options);
            return this._getScoreFunction(search);
          }
          /**
           * @returns {T.ScoreFn}
           *
           */
          _getScoreFunction(search) {
            const tokens = search.tokens, token_count = tokens.length;
            if (!token_count) {
              return function() {
                return 0;
              };
            }
            const fields = search.options.fields, weights = search.weights, field_count = fields.length, getAttrFn = search.getAttrFn;
            if (!field_count) {
              return function() {
                return 1;
              };
            }
            const scoreObject = function() {
              if (field_count === 1) {
                return function(token, data) {
                  const field = fields[0].field;
                  return scoreValue(getAttrFn(data, field), token, weights[field] || 1);
                };
              }
              return function(token, data) {
                var sum = 0;
                if (token.field) {
                  const value = getAttrFn(data, token.field);
                  if (!token.regex && value) {
                    sum += 1 / field_count;
                  } else {
                    sum += scoreValue(value, token, 1);
                  }
                } else {
                  iterate$1(weights, (weight, field) => {
                    sum += scoreValue(getAttrFn(data, field), token, weight);
                  });
                }
                return sum / field_count;
              };
            }();
            if (token_count === 1) {
              return function(data) {
                return scoreObject(tokens[0], data);
              };
            }
            if (search.options.conjunction === "and") {
              return function(data) {
                var score, sum = 0;
                for (let token of tokens) {
                  score = scoreObject(token, data);
                  if (score <= 0)
                    return 0;
                  sum += score;
                }
                return sum / token_count;
              };
            } else {
              return function(data) {
                var sum = 0;
                iterate$1(tokens, (token) => {
                  sum += scoreObject(token, data);
                });
                return sum / token_count;
              };
            }
          }
          /**
           * Returns a function that can be used to compare two
           * results, for sorting purposes. If no sorting should
           * be performed, `null` will be returned.
           *
           * @return function(a,b)
           */
          getSortFunction(query, options) {
            var search = this.prepareSearch(query, options);
            return this._getSortFunction(search);
          }
          _getSortFunction(search) {
            var implicit_score, sort_flds = [];
            const self2 = this, options = search.options, sort = !search.query && options.sort_empty ? options.sort_empty : options.sort;
            if (typeof sort == "function") {
              return sort.bind(this);
            }
            const get_field = function get_field2(name, result) {
              if (name === "$score")
                return result.score;
              return search.getAttrFn(self2.items[result.id], name);
            };
            if (sort) {
              for (let s of sort) {
                if (search.query || s.field !== "$score") {
                  sort_flds.push(s);
                }
              }
            }
            if (search.query) {
              implicit_score = true;
              for (let fld of sort_flds) {
                if (fld.field === "$score") {
                  implicit_score = false;
                  break;
                }
              }
              if (implicit_score) {
                sort_flds.unshift({
                  field: "$score",
                  direction: "desc"
                });
              }
            } else {
              sort_flds = sort_flds.filter((fld) => fld.field !== "$score");
            }
            const sort_flds_count = sort_flds.length;
            if (!sort_flds_count) {
              return null;
            }
            return function(a, b) {
              var result, field;
              for (let sort_fld of sort_flds) {
                field = sort_fld.field;
                let multiplier = sort_fld.direction === "desc" ? -1 : 1;
                result = multiplier * cmp(get_field(field, a), get_field(field, b));
                if (result)
                  return result;
              }
              return 0;
            };
          }
          /**
           * Parses a search query and returns an object
           * with tokens and fields ready to be populated
           * with results.
           *
           */
          prepareSearch(query, optsUser) {
            const weights = {};
            var options = Object.assign({}, optsUser);
            propToArray(options, "sort");
            propToArray(options, "sort_empty");
            if (options.fields) {
              propToArray(options, "fields");
              const fields = [];
              options.fields.forEach((field) => {
                if (typeof field == "string") {
                  field = {
                    field,
                    weight: 1
                  };
                }
                fields.push(field);
                weights[field.field] = "weight" in field ? field.weight : 1;
              });
              options.fields = fields;
            }
            return {
              options,
              query: query.toLowerCase().trim(),
              tokens: this.tokenize(query, options.respect_word_boundaries, weights),
              total: 0,
              items: [],
              weights,
              getAttrFn: options.nesting ? getAttrNesting : getAttr
            };
          }
          /**
           * Searches through all items and returns a sorted array of matches.
           *
           */
          search(query, options) {
            var self2 = this, score, search;
            search = this.prepareSearch(query, options);
            options = search.options;
            query = search.query;
            const fn_score = options.score || self2._getScoreFunction(search);
            if (query.length) {
              iterate$1(self2.items, (item, id) => {
                score = fn_score(item);
                if (options.filter === false || score > 0) {
                  search.items.push({
                    "score": score,
                    "id": id
                  });
                }
              });
            } else {
              iterate$1(self2.items, (_, id) => {
                search.items.push({
                  "score": 1,
                  "id": id
                });
              });
            }
            const fn_sort = self2._getSortFunction(search);
            if (fn_sort)
              search.items.sort(fn_sort);
            search.total = search.items.length;
            if (typeof options.limit === "number") {
              search.items = search.items.slice(0, options.limit);
            }
            return search;
          }
        }
        const iterate2 = (object, callback) => {
          if (Array.isArray(object)) {
            object.forEach(callback);
          } else {
            for (var key in object) {
              if (object.hasOwnProperty(key)) {
                callback(object[key], key);
              }
            }
          }
        };
        const getDom2 = (query) => {
          if (query.jquery) {
            return query[0];
          }
          if (query instanceof HTMLElement) {
            return query;
          }
          if (isHtmlString2(query)) {
            var tpl = document.createElement("template");
            tpl.innerHTML = query.trim();
            return tpl.content.firstChild;
          }
          return document.querySelector(query);
        };
        const isHtmlString2 = (arg) => {
          if (typeof arg === "string" && arg.indexOf("<") > -1) {
            return true;
          }
          return false;
        };
        const escapeQuery = (query) => {
          return query.replace(/['"\\]/g, "\\$&");
        };
        const triggerEvent = (dom_el, event_name) => {
          var event = document.createEvent("HTMLEvents");
          event.initEvent(event_name, true, false);
          dom_el.dispatchEvent(event);
        };
        const applyCSS = (dom_el, css) => {
          Object.assign(dom_el.style, css);
        };
        const addClasses2 = (elmts, ...classes) => {
          var norm_classes = classesArray2(classes);
          elmts = castAsArray2(elmts);
          elmts.map((el) => {
            norm_classes.map((cls) => {
              el.classList.add(cls);
            });
          });
        };
        const removeClasses = (elmts, ...classes) => {
          var norm_classes = classesArray2(classes);
          elmts = castAsArray2(elmts);
          elmts.map((el) => {
            norm_classes.map((cls) => {
              el.classList.remove(cls);
            });
          });
        };
        const classesArray2 = (args) => {
          var classes = [];
          iterate2(args, (_classes) => {
            if (typeof _classes === "string") {
              _classes = _classes.trim().split(/[\11\12\14\15\40]/);
            }
            if (Array.isArray(_classes)) {
              classes = classes.concat(_classes);
            }
          });
          return classes.filter(Boolean);
        };
        const castAsArray2 = (arg) => {
          if (!Array.isArray(arg)) {
            arg = [arg];
          }
          return arg;
        };
        const parentMatch = (target, selector, wrapper) => {
          if (wrapper && !wrapper.contains(target)) {
            return;
          }
          while (target && target.matches) {
            if (target.matches(selector)) {
              return target;
            }
            target = target.parentNode;
          }
        };
        const getTail = (list, direction = 0) => {
          if (direction > 0) {
            return list[list.length - 1];
          }
          return list[0];
        };
        const isEmptyObject = (obj) => {
          return Object.keys(obj).length === 0;
        };
        const nodeIndex = (el, amongst) => {
          if (!el)
            return -1;
          amongst = amongst || el.nodeName;
          var i = 0;
          while (el = el.previousElementSibling) {
            if (el.matches(amongst)) {
              i++;
            }
          }
          return i;
        };
        const setAttr = (el, attrs) => {
          iterate2(attrs, (val, attr) => {
            if (val == null) {
              el.removeAttribute(attr);
            } else {
              el.setAttribute(attr, "" + val);
            }
          });
        };
        const replaceNode = (existing, replacement) => {
          if (existing.parentNode)
            existing.parentNode.replaceChild(replacement, existing);
        };
        const highlight = (element, regex) => {
          if (regex === null)
            return;
          if (typeof regex === "string") {
            if (!regex.length)
              return;
            regex = new RegExp(regex, "i");
          }
          const highlightText = (node) => {
            var match = node.data.match(regex);
            if (match && node.data.length > 0) {
              var spannode = document.createElement("span");
              spannode.className = "highlight";
              var middlebit = node.splitText(match.index);
              middlebit.splitText(match[0].length);
              var middleclone = middlebit.cloneNode(true);
              spannode.appendChild(middleclone);
              replaceNode(middlebit, spannode);
              return 1;
            }
            return 0;
          };
          const highlightChildren = (node) => {
            if (node.nodeType === 1 && node.childNodes && !/(script|style)/i.test(node.tagName) && (node.className !== "highlight" || node.tagName !== "SPAN")) {
              Array.from(node.childNodes).forEach((element2) => {
                highlightRecursive(element2);
              });
            }
          };
          const highlightRecursive = (node) => {
            if (node.nodeType === 3) {
              return highlightText(node);
            }
            highlightChildren(node);
            return 0;
          };
          highlightRecursive(element);
        };
        const removeHighlight = (el) => {
          var elements = el.querySelectorAll("span.highlight");
          Array.prototype.forEach.call(elements, function(el2) {
            var parent = el2.parentNode;
            parent.replaceChild(el2.firstChild, el2);
            parent.normalize();
          });
        };
        const KEY_A = 65;
        const KEY_RETURN = 13;
        const KEY_ESC2 = 27;
        const KEY_LEFT = 37;
        const KEY_UP = 38;
        const KEY_RIGHT = 39;
        const KEY_DOWN = 40;
        const KEY_BACKSPACE = 8;
        const KEY_DELETE = 46;
        const KEY_TAB2 = 9;
        const IS_MAC2 = typeof navigator === "undefined" ? false : /Mac/.test(navigator.userAgent);
        const KEY_SHORTCUT = IS_MAC2 ? "metaKey" : "ctrlKey";
        var defaults = {
          options: [],
          optgroups: [],
          plugins: [],
          delimiter: ",",
          splitOn: null,
          // regexp or string for splitting up values from a paste command
          persist: true,
          diacritics: true,
          create: null,
          createOnBlur: false,
          createFilter: null,
          highlight: true,
          openOnFocus: true,
          shouldOpen: null,
          maxOptions: 50,
          maxItems: null,
          hideSelected: null,
          duplicates: false,
          addPrecedence: false,
          selectOnTab: false,
          preload: null,
          allowEmptyOption: false,
          //closeAfterSelect: false,
          loadThrottle: 300,
          loadingClass: "loading",
          dataAttr: null,
          //'data-data',
          optgroupField: "optgroup",
          valueField: "value",
          labelField: "text",
          disabledField: "disabled",
          optgroupLabelField: "label",
          optgroupValueField: "value",
          lockOptgroupOrder: false,
          sortField: "$order",
          searchField: ["text"],
          searchConjunction: "and",
          mode: null,
          wrapperClass: "ts-wrapper",
          controlClass: "ts-control",
          dropdownClass: "ts-dropdown",
          dropdownContentClass: "ts-dropdown-content",
          itemClass: "item",
          optionClass: "option",
          dropdownParent: null,
          controlInput: '<input type="text" autocomplete="off" size="1" />',
          copyClassesToDropdown: false,
          placeholder: null,
          hidePlaceholder: null,
          shouldLoad: function(query) {
            return query.length > 0;
          },
          /*
          load                 : null, // function(query, callback) { ... }
          score                : null, // function(search) { ... }
          onInitialize         : null, // function() { ... }
          onChange             : null, // function(value) { ... }
          onItemAdd            : null, // function(value, $item) { ... }
          onItemRemove         : null, // function(value) { ... }
          onClear              : null, // function() { ... }
          onOptionAdd          : null, // function(value, data) { ... }
          onOptionRemove       : null, // function(value) { ... }
          onOptionClear        : null, // function() { ... }
          onOptionGroupAdd     : null, // function(id, data) { ... }
          onOptionGroupRemove  : null, // function(id) { ... }
          onOptionGroupClear   : null, // function() { ... }
          onDropdownOpen       : null, // function(dropdown) { ... }
          onDropdownClose      : null, // function(dropdown) { ... }
          onType               : null, // function(str) { ... }
          onDelete             : null, // function(values) { ... }
          */
          render: {
            /*
            item: null,
            optgroup: null,
            optgroup_header: null,
            option: null,
            option_create: null
            */
          }
        };
        const hash_key2 = (value) => {
          if (typeof value === "undefined" || value === null)
            return null;
          return get_hash2(value);
        };
        const get_hash2 = (value) => {
          if (typeof value === "boolean")
            return value ? "1" : "0";
          return value + "";
        };
        const escape_html2 = (str) => {
          return (str + "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
        };
        const loadDebounce = (fn, delay) => {
          var timeout;
          return function(value, callback) {
            var self2 = this;
            if (timeout) {
              self2.loading = Math.max(self2.loading - 1, 0);
              clearTimeout(timeout);
            }
            timeout = setTimeout(function() {
              timeout = null;
              self2.loadedSearches[value] = true;
              fn.call(self2, value, callback);
            }, delay);
          };
        };
        const debounce_events = (self2, types, fn) => {
          var type;
          var trigger = self2.trigger;
          var event_args = {};
          self2.trigger = function() {
            var type2 = arguments[0];
            if (types.indexOf(type2) !== -1) {
              event_args[type2] = arguments;
            } else {
              return trigger.apply(self2, arguments);
            }
          };
          fn.apply(self2, []);
          self2.trigger = trigger;
          for (type of types) {
            if (type in event_args) {
              trigger.apply(self2, event_args[type]);
            }
          }
        };
        const getSelection = (input) => {
          return {
            start: input.selectionStart || 0,
            length: (input.selectionEnd || 0) - (input.selectionStart || 0)
          };
        };
        const preventDefault2 = (evt, stop = false) => {
          if (evt) {
            evt.preventDefault();
            if (stop) {
              evt.stopPropagation();
            }
          }
        };
        const addEvent2 = (target, type, callback, options) => {
          target.addEventListener(type, callback, options);
        };
        const isKeyDown = (key_name, evt) => {
          if (!evt) {
            return false;
          }
          if (!evt[key_name]) {
            return false;
          }
          var count = (evt.altKey ? 1 : 0) + (evt.ctrlKey ? 1 : 0) + (evt.shiftKey ? 1 : 0) + (evt.metaKey ? 1 : 0);
          if (count === 1) {
            return true;
          }
          return false;
        };
        const getId = (el, id) => {
          const existing_id = el.getAttribute("id");
          if (existing_id) {
            return existing_id;
          }
          el.setAttribute("id", id);
          return id;
        };
        const addSlashes = (str) => {
          return str.replace(/[\\"']/g, "\\$&");
        };
        const append = (parent, node) => {
          if (node)
            parent.append(node);
        };
        function getSettings(input, settings_user) {
          var settings = Object.assign({}, defaults, settings_user);
          var attr_data = settings.dataAttr;
          var field_label = settings.labelField;
          var field_value = settings.valueField;
          var field_disabled = settings.disabledField;
          var field_optgroup = settings.optgroupField;
          var field_optgroup_label = settings.optgroupLabelField;
          var field_optgroup_value = settings.optgroupValueField;
          var tag_name = input.tagName.toLowerCase();
          var placeholder = input.getAttribute("placeholder") || input.getAttribute("data-placeholder");
          if (!placeholder && !settings.allowEmptyOption) {
            let option = input.querySelector('option[value=""]');
            if (option) {
              placeholder = option.textContent;
            }
          }
          var settings_element = {
            placeholder,
            options: [],
            optgroups: [],
            items: [],
            maxItems: null
          };
          var init_select = () => {
            var tagName;
            var options = settings_element.options;
            var optionsMap = {};
            var group_count = 1;
            var readData = (el) => {
              var data = Object.assign({}, el.dataset);
              var json = attr_data && data[attr_data];
              if (typeof json === "string" && json.length) {
                data = Object.assign(data, JSON.parse(json));
              }
              return data;
            };
            var addOption = (option, group) => {
              var value = hash_key2(option.value);
              if (value == null)
                return;
              if (!value && !settings.allowEmptyOption)
                return;
              if (optionsMap.hasOwnProperty(value)) {
                if (group) {
                  var arr = optionsMap[value][field_optgroup];
                  if (!arr) {
                    optionsMap[value][field_optgroup] = group;
                  } else if (!Array.isArray(arr)) {
                    optionsMap[value][field_optgroup] = [arr, group];
                  } else {
                    arr.push(group);
                  }
                }
              } else {
                var option_data = readData(option);
                option_data[field_label] = option_data[field_label] || option.textContent;
                option_data[field_value] = option_data[field_value] || value;
                option_data[field_disabled] = option_data[field_disabled] || option.disabled;
                option_data[field_optgroup] = option_data[field_optgroup] || group;
                option_data.$option = option;
                optionsMap[value] = option_data;
                options.push(option_data);
              }
              if (option.selected) {
                settings_element.items.push(value);
              }
            };
            var addGroup = (optgroup) => {
              var id, optgroup_data;
              optgroup_data = readData(optgroup);
              optgroup_data[field_optgroup_label] = optgroup_data[field_optgroup_label] || optgroup.getAttribute("label") || "";
              optgroup_data[field_optgroup_value] = optgroup_data[field_optgroup_value] || group_count++;
              optgroup_data[field_disabled] = optgroup_data[field_disabled] || optgroup.disabled;
              settings_element.optgroups.push(optgroup_data);
              id = optgroup_data[field_optgroup_value];
              iterate2(optgroup.children, (option) => {
                addOption(option, id);
              });
            };
            settings_element.maxItems = input.hasAttribute("multiple") ? null : 1;
            iterate2(input.children, (child) => {
              tagName = child.tagName.toLowerCase();
              if (tagName === "optgroup") {
                addGroup(child);
              } else if (tagName === "option") {
                addOption(child);
              }
            });
          };
          var init_textbox = () => {
            const data_raw = input.getAttribute(attr_data);
            if (!data_raw) {
              var value = input.value.trim() || "";
              if (!settings.allowEmptyOption && !value.length)
                return;
              const values = value.split(settings.delimiter);
              iterate2(values, (value2) => {
                const option = {};
                option[field_label] = value2;
                option[field_value] = value2;
                settings_element.options.push(option);
              });
              settings_element.items = values;
            } else {
              settings_element.options = JSON.parse(data_raw);
              iterate2(settings_element.options, (opt) => {
                settings_element.items.push(opt[field_value]);
              });
            }
          };
          if (tag_name === "select") {
            init_select();
          } else {
            init_textbox();
          }
          return Object.assign({}, defaults, settings_element, settings_user);
        }
        var instance_i = 0;
        class TomSelect3 extends MicroPlugin(MicroEvent) {
          // @deprecated 1.8
          constructor(input_arg, user_settings) {
            super();
            this.control_input = void 0;
            this.wrapper = void 0;
            this.dropdown = void 0;
            this.control = void 0;
            this.dropdown_content = void 0;
            this.focus_node = void 0;
            this.order = 0;
            this.settings = void 0;
            this.input = void 0;
            this.tabIndex = void 0;
            this.is_select_tag = void 0;
            this.rtl = void 0;
            this.inputId = void 0;
            this._destroy = void 0;
            this.sifter = void 0;
            this.isOpen = false;
            this.isDisabled = false;
            this.isRequired = void 0;
            this.isInvalid = false;
            this.isValid = true;
            this.isLocked = false;
            this.isFocused = false;
            this.isInputHidden = false;
            this.isSetup = false;
            this.ignoreFocus = false;
            this.ignoreHover = false;
            this.hasOptions = false;
            this.currentResults = void 0;
            this.lastValue = "";
            this.caretPos = 0;
            this.loading = 0;
            this.loadedSearches = {};
            this.activeOption = null;
            this.activeItems = [];
            this.optgroups = {};
            this.options = {};
            this.userOptions = {};
            this.items = [];
            instance_i++;
            var dir;
            var input = getDom2(input_arg);
            if (input.tomselect) {
              throw new Error("Tom Select already initialized on this element");
            }
            input.tomselect = this;
            var computedStyle = window.getComputedStyle && window.getComputedStyle(input, null);
            dir = computedStyle.getPropertyValue("direction");
            const settings = getSettings(input, user_settings);
            this.settings = settings;
            this.input = input;
            this.tabIndex = input.tabIndex || 0;
            this.is_select_tag = input.tagName.toLowerCase() === "select";
            this.rtl = /rtl/i.test(dir);
            this.inputId = getId(input, "tomselect-" + instance_i);
            this.isRequired = input.required;
            this.sifter = new Sifter(this.options, {
              diacritics: settings.diacritics
            });
            settings.mode = settings.mode || (settings.maxItems === 1 ? "single" : "multi");
            if (typeof settings.hideSelected !== "boolean") {
              settings.hideSelected = settings.mode === "multi";
            }
            if (typeof settings.hidePlaceholder !== "boolean") {
              settings.hidePlaceholder = settings.mode !== "multi";
            }
            var filter = settings.createFilter;
            if (typeof filter !== "function") {
              if (typeof filter === "string") {
                filter = new RegExp(filter);
              }
              if (filter instanceof RegExp) {
                settings.createFilter = (input2) => filter.test(input2);
              } else {
                settings.createFilter = (value) => {
                  return this.settings.duplicates || !this.options[value];
                };
              }
            }
            this.initializePlugins(settings.plugins);
            this.setupCallbacks();
            this.setupTemplates();
            const wrapper = getDom2("<div>");
            const control = getDom2("<div>");
            const dropdown = this._render("dropdown");
            const dropdown_content = getDom2(`<div role="listbox" tabindex="-1">`);
            const classes = this.input.getAttribute("class") || "";
            const inputMode = settings.mode;
            var control_input;
            addClasses2(wrapper, settings.wrapperClass, classes, inputMode);
            addClasses2(control, settings.controlClass);
            append(wrapper, control);
            addClasses2(dropdown, settings.dropdownClass, inputMode);
            if (settings.copyClassesToDropdown) {
              addClasses2(dropdown, classes);
            }
            addClasses2(dropdown_content, settings.dropdownContentClass);
            append(dropdown, dropdown_content);
            getDom2(settings.dropdownParent || wrapper).appendChild(dropdown);
            if (isHtmlString2(settings.controlInput)) {
              control_input = getDom2(settings.controlInput);
              var attrs = ["autocorrect", "autocapitalize", "autocomplete"];
              iterate$1(attrs, (attr) => {
                if (input.getAttribute(attr)) {
                  setAttr(control_input, {
                    [attr]: input.getAttribute(attr)
                  });
                }
              });
              control_input.tabIndex = -1;
              control.appendChild(control_input);
              this.focus_node = control_input;
            } else if (settings.controlInput) {
              control_input = getDom2(settings.controlInput);
              this.focus_node = control_input;
            } else {
              control_input = getDom2("<input/>");
              this.focus_node = control;
            }
            this.wrapper = wrapper;
            this.dropdown = dropdown;
            this.dropdown_content = dropdown_content;
            this.control = control;
            this.control_input = control_input;
            this.setup();
          }
          /**
           * set up event bindings.
           *
           */
          setup() {
            const self2 = this;
            const settings = self2.settings;
            const control_input = self2.control_input;
            const dropdown = self2.dropdown;
            const dropdown_content = self2.dropdown_content;
            const wrapper = self2.wrapper;
            const control = self2.control;
            const input = self2.input;
            const focus_node = self2.focus_node;
            const passive_event = {
              passive: true
            };
            const listboxId = self2.inputId + "-ts-dropdown";
            setAttr(dropdown_content, {
              id: listboxId
            });
            setAttr(focus_node, {
              role: "combobox",
              "aria-haspopup": "listbox",
              "aria-expanded": "false",
              "aria-controls": listboxId
            });
            const control_id = getId(focus_node, self2.inputId + "-ts-control");
            const query = "label[for='" + escapeQuery(self2.inputId) + "']";
            const label = document.querySelector(query);
            const label_click = self2.focus.bind(self2);
            if (label) {
              addEvent2(label, "click", label_click);
              setAttr(label, {
                for: control_id
              });
              const label_id = getId(label, self2.inputId + "-ts-label");
              setAttr(focus_node, {
                "aria-labelledby": label_id
              });
              setAttr(dropdown_content, {
                "aria-labelledby": label_id
              });
            }
            wrapper.style.width = input.style.width;
            if (self2.plugins.names.length) {
              const classes_plugins = "plugin-" + self2.plugins.names.join(" plugin-");
              addClasses2([wrapper, dropdown], classes_plugins);
            }
            if ((settings.maxItems === null || settings.maxItems > 1) && self2.is_select_tag) {
              setAttr(input, {
                multiple: "multiple"
              });
            }
            if (settings.placeholder) {
              setAttr(control_input, {
                placeholder: settings.placeholder
              });
            }
            if (!settings.splitOn && settings.delimiter) {
              settings.splitOn = new RegExp("\\s*" + escape_regex(settings.delimiter) + "+\\s*");
            }
            if (settings.load && settings.loadThrottle) {
              settings.load = loadDebounce(settings.load, settings.loadThrottle);
            }
            self2.control_input.type = input.type;
            addEvent2(dropdown, "mousemove", () => {
              self2.ignoreHover = false;
            });
            addEvent2(dropdown, "mouseenter", (e) => {
              var target_match = parentMatch(e.target, "[data-selectable]", dropdown);
              if (target_match)
                self2.onOptionHover(e, target_match);
            }, {
              capture: true
            });
            addEvent2(dropdown, "click", (evt) => {
              const option = parentMatch(evt.target, "[data-selectable]");
              if (option) {
                self2.onOptionSelect(evt, option);
                preventDefault2(evt, true);
              }
            });
            addEvent2(control, "click", (evt) => {
              var target_match = parentMatch(evt.target, "[data-ts-item]", control);
              if (target_match && self2.onItemSelect(evt, target_match)) {
                preventDefault2(evt, true);
                return;
              }
              if (control_input.value != "") {
                return;
              }
              self2.onClick();
              preventDefault2(evt, true);
            });
            addEvent2(focus_node, "keydown", (e) => self2.onKeyDown(e));
            addEvent2(control_input, "keypress", (e) => self2.onKeyPress(e));
            addEvent2(control_input, "input", (e) => self2.onInput(e));
            addEvent2(focus_node, "blur", (e) => self2.onBlur(e));
            addEvent2(focus_node, "focus", (e) => self2.onFocus(e));
            addEvent2(control_input, "paste", (e) => self2.onPaste(e));
            const doc_mousedown = (evt) => {
              const target = evt.composedPath()[0];
              if (!wrapper.contains(target) && !dropdown.contains(target)) {
                if (self2.isFocused) {
                  self2.blur();
                }
                self2.inputState();
                return;
              }
              if (target == control_input && self2.isOpen) {
                evt.stopPropagation();
              } else {
                preventDefault2(evt, true);
              }
            };
            const win_scroll = () => {
              if (self2.isOpen) {
                self2.positionDropdown();
              }
            };
            addEvent2(document, "mousedown", doc_mousedown);
            addEvent2(window, "scroll", win_scroll, passive_event);
            addEvent2(window, "resize", win_scroll, passive_event);
            this._destroy = () => {
              document.removeEventListener("mousedown", doc_mousedown);
              window.removeEventListener("scroll", win_scroll);
              window.removeEventListener("resize", win_scroll);
              if (label)
                label.removeEventListener("click", label_click);
            };
            this.revertSettings = {
              innerHTML: input.innerHTML,
              tabIndex: input.tabIndex
            };
            input.tabIndex = -1;
            input.insertAdjacentElement("afterend", self2.wrapper);
            self2.sync(false);
            settings.items = [];
            delete settings.optgroups;
            delete settings.options;
            addEvent2(input, "invalid", () => {
              if (self2.isValid) {
                self2.isValid = false;
                self2.isInvalid = true;
                self2.refreshState();
              }
            });
            self2.updateOriginalInput();
            self2.refreshItems();
            self2.close(false);
            self2.inputState();
            self2.isSetup = true;
            if (input.disabled) {
              self2.disable();
            } else {
              self2.enable();
            }
            self2.on("change", this.onChange);
            addClasses2(input, "tomselected", "ts-hidden-accessible");
            self2.trigger("initialize");
            if (settings.preload === true) {
              self2.preload();
            }
          }
          /**
           * Register options and optgroups
           *
           */
          setupOptions(options = [], optgroups = []) {
            this.addOptions(options);
            iterate$1(optgroups, (optgroup) => {
              this.registerOptionGroup(optgroup);
            });
          }
          /**
           * Sets up default rendering functions.
           */
          setupTemplates() {
            var self2 = this;
            var field_label = self2.settings.labelField;
            var field_optgroup = self2.settings.optgroupLabelField;
            var templates = {
              "optgroup": (data) => {
                let optgroup = document.createElement("div");
                optgroup.className = "optgroup";
                optgroup.appendChild(data.options);
                return optgroup;
              },
              "optgroup_header": (data, escape) => {
                return '<div class="optgroup-header">' + escape(data[field_optgroup]) + "</div>";
              },
              "option": (data, escape) => {
                return "<div>" + escape(data[field_label]) + "</div>";
              },
              "item": (data, escape) => {
                return "<div>" + escape(data[field_label]) + "</div>";
              },
              "option_create": (data, escape) => {
                return '<div class="create">Add <strong>' + escape(data.input) + "</strong>&hellip;</div>";
              },
              "no_results": () => {
                return '<div class="no-results">No results found</div>';
              },
              "loading": () => {
                return '<div class="spinner"></div>';
              },
              "not_loading": () => {
              },
              "dropdown": () => {
                return "<div></div>";
              }
            };
            self2.settings.render = Object.assign({}, templates, self2.settings.render);
          }
          /**
           * Maps fired events to callbacks provided
           * in the settings used when creating the control.
           */
          setupCallbacks() {
            var key, fn;
            var callbacks = {
              "initialize": "onInitialize",
              "change": "onChange",
              "item_add": "onItemAdd",
              "item_remove": "onItemRemove",
              "item_select": "onItemSelect",
              "clear": "onClear",
              "option_add": "onOptionAdd",
              "option_remove": "onOptionRemove",
              "option_clear": "onOptionClear",
              "optgroup_add": "onOptionGroupAdd",
              "optgroup_remove": "onOptionGroupRemove",
              "optgroup_clear": "onOptionGroupClear",
              "dropdown_open": "onDropdownOpen",
              "dropdown_close": "onDropdownClose",
              "type": "onType",
              "load": "onLoad",
              "focus": "onFocus",
              "blur": "onBlur"
            };
            for (key in callbacks) {
              fn = this.settings[callbacks[key]];
              if (fn)
                this.on(key, fn);
            }
          }
          /**
           * Sync the Tom Select instance with the original input or select
           *
           */
          sync(get_settings = true) {
            const self2 = this;
            const settings = get_settings ? getSettings(self2.input, {
              delimiter: self2.settings.delimiter
            }) : self2.settings;
            self2.setupOptions(settings.options, settings.optgroups);
            self2.setValue(settings.items || [], true);
            self2.lastQuery = null;
          }
          /**
           * Triggered when the main control element
           * has a click event.
           *
           */
          onClick() {
            var self2 = this;
            if (self2.activeItems.length > 0) {
              self2.clearActiveItems();
              self2.focus();
              return;
            }
            if (self2.isFocused && self2.isOpen) {
              self2.blur();
            } else {
              self2.focus();
            }
          }
          /**
           * @deprecated v1.7
           *
           */
          onMouseDown() {
          }
          /**
           * Triggered when the value of the control has been changed.
           * This should propagate the event to the original DOM
           * input / select element.
           */
          onChange() {
            triggerEvent(this.input, "input");
            triggerEvent(this.input, "change");
          }
          /**
           * Triggered on <input> paste.
           *
           */
          onPaste(e) {
            var self2 = this;
            if (self2.isInputHidden || self2.isLocked) {
              preventDefault2(e);
              return;
            }
            if (!self2.settings.splitOn) {
              return;
            }
            setTimeout(() => {
              var pastedText = self2.inputValue();
              if (!pastedText.match(self2.settings.splitOn)) {
                return;
              }
              var splitInput = pastedText.trim().split(self2.settings.splitOn);
              iterate$1(splitInput, (piece) => {
                const hash = hash_key2(piece);
                if (hash) {
                  if (this.options[piece]) {
                    self2.addItem(piece);
                  } else {
                    self2.createItem(piece);
                  }
                }
              });
            }, 0);
          }
          /**
           * Triggered on <input> keypress.
           *
           */
          onKeyPress(e) {
            var self2 = this;
            if (self2.isLocked) {
              preventDefault2(e);
              return;
            }
            var character = String.fromCharCode(e.keyCode || e.which);
            if (self2.settings.create && self2.settings.mode === "multi" && character === self2.settings.delimiter) {
              self2.createItem();
              preventDefault2(e);
              return;
            }
          }
          /**
           * Triggered on <input> keydown.
           *
           */
          onKeyDown(e) {
            var self2 = this;
            self2.ignoreHover = true;
            if (self2.isLocked) {
              if (e.keyCode !== KEY_TAB2) {
                preventDefault2(e);
              }
              return;
            }
            switch (e.keyCode) {
              case KEY_A:
                if (isKeyDown(KEY_SHORTCUT, e)) {
                  if (self2.control_input.value == "") {
                    preventDefault2(e);
                    self2.selectAll();
                    return;
                  }
                }
                break;
              case KEY_ESC2:
                if (self2.isOpen) {
                  preventDefault2(e, true);
                  self2.close();
                }
                self2.clearActiveItems();
                return;
              case KEY_DOWN:
                if (!self2.isOpen && self2.hasOptions) {
                  self2.open();
                } else if (self2.activeOption) {
                  let next = self2.getAdjacent(self2.activeOption, 1);
                  if (next)
                    self2.setActiveOption(next);
                }
                preventDefault2(e);
                return;
              case KEY_UP:
                if (self2.activeOption) {
                  let prev = self2.getAdjacent(self2.activeOption, -1);
                  if (prev)
                    self2.setActiveOption(prev);
                }
                preventDefault2(e);
                return;
              case KEY_RETURN:
                if (self2.canSelect(self2.activeOption)) {
                  self2.onOptionSelect(e, self2.activeOption);
                  preventDefault2(e);
                } else if (self2.settings.create && self2.createItem()) {
                  preventDefault2(e);
                } else if (document.activeElement == self2.control_input && self2.isOpen) {
                  preventDefault2(e);
                }
                return;
              case KEY_LEFT:
                self2.advanceSelection(-1, e);
                return;
              case KEY_RIGHT:
                self2.advanceSelection(1, e);
                return;
              case KEY_TAB2:
                if (self2.settings.selectOnTab) {
                  if (self2.canSelect(self2.activeOption)) {
                    self2.onOptionSelect(e, self2.activeOption);
                    preventDefault2(e);
                  }
                  if (self2.settings.create && self2.createItem()) {
                    preventDefault2(e);
                  }
                }
                return;
              case KEY_BACKSPACE:
              case KEY_DELETE:
                self2.deleteSelection(e);
                return;
            }
            if (self2.isInputHidden && !isKeyDown(KEY_SHORTCUT, e)) {
              preventDefault2(e);
            }
          }
          /**
           * Triggered on <input> keyup.
           *
           */
          onInput(e) {
            var self2 = this;
            if (self2.isLocked) {
              return;
            }
            var value = self2.inputValue();
            if (self2.lastValue !== value) {
              self2.lastValue = value;
              if (self2.settings.shouldLoad.call(self2, value)) {
                self2.load(value);
              }
              self2.refreshOptions();
              self2.trigger("type", value);
            }
          }
          /**
           * Triggered when the user rolls over
           * an option in the autocomplete dropdown menu.
           *
           */
          onOptionHover(evt, option) {
            if (this.ignoreHover)
              return;
            this.setActiveOption(option, false);
          }
          /**
           * Triggered on <input> focus.
           *
           */
          onFocus(e) {
            var self2 = this;
            var wasFocused = self2.isFocused;
            if (self2.isDisabled) {
              self2.blur();
              preventDefault2(e);
              return;
            }
            if (self2.ignoreFocus)
              return;
            self2.isFocused = true;
            if (self2.settings.preload === "focus")
              self2.preload();
            if (!wasFocused)
              self2.trigger("focus");
            if (!self2.activeItems.length) {
              self2.showInput();
              self2.refreshOptions(!!self2.settings.openOnFocus);
            }
            self2.refreshState();
          }
          /**
           * Triggered on <input> blur.
           *
           */
          onBlur(e) {
            if (document.hasFocus() === false)
              return;
            var self2 = this;
            if (!self2.isFocused)
              return;
            self2.isFocused = false;
            self2.ignoreFocus = false;
            var deactivate = () => {
              self2.close();
              self2.setActiveItem();
              self2.setCaret(self2.items.length);
              self2.trigger("blur");
            };
            if (self2.settings.create && self2.settings.createOnBlur) {
              self2.createItem(null, deactivate);
            } else {
              deactivate();
            }
          }
          /**
           * Triggered when the user clicks on an option
           * in the autocomplete dropdown menu.
           *
           */
          onOptionSelect(evt, option) {
            var value, self2 = this;
            if (option.parentElement && option.parentElement.matches("[data-disabled]")) {
              return;
            }
            if (option.classList.contains("create")) {
              self2.createItem(null, () => {
                if (self2.settings.closeAfterSelect) {
                  self2.close();
                }
              });
            } else {
              value = option.dataset.value;
              if (typeof value !== "undefined") {
                self2.lastQuery = null;
                self2.addItem(value);
                if (self2.settings.closeAfterSelect) {
                  self2.close();
                }
                if (!self2.settings.hideSelected && evt.type && /click/.test(evt.type)) {
                  self2.setActiveOption(option);
                }
              }
            }
          }
          /**
           * Return true if the given option can be selected
           *
           */
          canSelect(option) {
            if (this.isOpen && option && this.dropdown_content.contains(option)) {
              return true;
            }
            return false;
          }
          /**
           * Triggered when the user clicks on an item
           * that has been selected.
           *
           */
          onItemSelect(evt, item) {
            var self2 = this;
            if (!self2.isLocked && self2.settings.mode === "multi") {
              preventDefault2(evt);
              self2.setActiveItem(item, evt);
              return true;
            }
            return false;
          }
          /**
           * Determines whether or not to invoke
           * the user-provided option provider / loader
           *
           * Note, there is a subtle difference between
           * this.canLoad() and this.settings.shouldLoad();
           *
           *	- settings.shouldLoad() is a user-input validator.
           *	When false is returned, the not_loading template
           *	will be added to the dropdown
           *
           *	- canLoad() is lower level validator that checks
           * 	the Tom Select instance. There is no inherent user
           *	feedback when canLoad returns false
           *
           */
          canLoad(value) {
            if (!this.settings.load)
              return false;
            if (this.loadedSearches.hasOwnProperty(value))
              return false;
            return true;
          }
          /**
           * Invokes the user-provided option provider / loader.
           *
           */
          load(value) {
            const self2 = this;
            if (!self2.canLoad(value))
              return;
            addClasses2(self2.wrapper, self2.settings.loadingClass);
            self2.loading++;
            const callback = self2.loadCallback.bind(self2);
            self2.settings.load.call(self2, value, callback);
          }
          /**
           * Invoked by the user-provided option provider
           *
           */
          loadCallback(options, optgroups) {
            const self2 = this;
            self2.loading = Math.max(self2.loading - 1, 0);
            self2.lastQuery = null;
            self2.clearActiveOption();
            self2.setupOptions(options, optgroups);
            self2.refreshOptions(self2.isFocused && !self2.isInputHidden);
            if (!self2.loading) {
              removeClasses(self2.wrapper, self2.settings.loadingClass);
            }
            self2.trigger("load", options, optgroups);
          }
          preload() {
            var classList = this.wrapper.classList;
            if (classList.contains("preloaded"))
              return;
            classList.add("preloaded");
            this.load("");
          }
          /**
           * Sets the input field of the control to the specified value.
           *
           */
          setTextboxValue(value = "") {
            var input = this.control_input;
            var changed = input.value !== value;
            if (changed) {
              input.value = value;
              triggerEvent(input, "update");
              this.lastValue = value;
            }
          }
          /**
           * Returns the value of the control. If multiple items
           * can be selected (e.g. <select multiple>), this returns
           * an array. If only one item can be selected, this
           * returns a string.
           *
           */
          getValue() {
            if (this.is_select_tag && this.input.hasAttribute("multiple")) {
              return this.items;
            }
            return this.items.join(this.settings.delimiter);
          }
          /**
           * Resets the selected items to the given value.
           *
           */
          setValue(value, silent) {
            var events = silent ? [] : ["change"];
            debounce_events(this, events, () => {
              this.clear(silent);
              this.addItems(value, silent);
            });
          }
          /**
           * Resets the number of max items to the given value
           *
           */
          setMaxItems(value) {
            if (value === 0)
              value = null;
            this.settings.maxItems = value;
            this.refreshState();
          }
          /**
           * Sets the selected item.
           *
           */
          setActiveItem(item, e) {
            var self2 = this;
            var eventName;
            var i, begin, end, swap;
            var last;
            if (self2.settings.mode === "single")
              return;
            if (!item) {
              self2.clearActiveItems();
              if (self2.isFocused) {
                self2.showInput();
              }
              return;
            }
            eventName = e && e.type.toLowerCase();
            if (eventName === "click" && isKeyDown("shiftKey", e) && self2.activeItems.length) {
              last = self2.getLastActive();
              begin = Array.prototype.indexOf.call(self2.control.children, last);
              end = Array.prototype.indexOf.call(self2.control.children, item);
              if (begin > end) {
                swap = begin;
                begin = end;
                end = swap;
              }
              for (i = begin; i <= end; i++) {
                item = self2.control.children[i];
                if (self2.activeItems.indexOf(item) === -1) {
                  self2.setActiveItemClass(item);
                }
              }
              preventDefault2(e);
            } else if (eventName === "click" && isKeyDown(KEY_SHORTCUT, e) || eventName === "keydown" && isKeyDown("shiftKey", e)) {
              if (item.classList.contains("active")) {
                self2.removeActiveItem(item);
              } else {
                self2.setActiveItemClass(item);
              }
            } else {
              self2.clearActiveItems();
              self2.setActiveItemClass(item);
            }
            self2.hideInput();
            if (!self2.isFocused) {
              self2.focus();
            }
          }
          /**
           * Set the active and last-active classes
           *
           */
          setActiveItemClass(item) {
            const self2 = this;
            const last_active = self2.control.querySelector(".last-active");
            if (last_active)
              removeClasses(last_active, "last-active");
            addClasses2(item, "active last-active");
            self2.trigger("item_select", item);
            if (self2.activeItems.indexOf(item) == -1) {
              self2.activeItems.push(item);
            }
          }
          /**
           * Remove active item
           *
           */
          removeActiveItem(item) {
            var idx = this.activeItems.indexOf(item);
            this.activeItems.splice(idx, 1);
            removeClasses(item, "active");
          }
          /**
           * Clears all the active items
           *
           */
          clearActiveItems() {
            removeClasses(this.activeItems, "active");
            this.activeItems = [];
          }
          /**
           * Sets the selected item in the dropdown menu
           * of available options.
           *
           */
          setActiveOption(option, scroll = true) {
            if (option === this.activeOption) {
              return;
            }
            this.clearActiveOption();
            if (!option)
              return;
            this.activeOption = option;
            setAttr(this.focus_node, {
              "aria-activedescendant": option.getAttribute("id")
            });
            setAttr(option, {
              "aria-selected": "true"
            });
            addClasses2(option, "active");
            if (scroll)
              this.scrollToOption(option);
          }
          /**
           * Sets the dropdown_content scrollTop to display the option
           *
           */
          scrollToOption(option, behavior) {
            if (!option)
              return;
            const content = this.dropdown_content;
            const height_menu = content.clientHeight;
            const scrollTop = content.scrollTop || 0;
            const height_item = option.offsetHeight;
            const y = option.getBoundingClientRect().top - content.getBoundingClientRect().top + scrollTop;
            if (y + height_item > height_menu + scrollTop) {
              this.scroll(y - height_menu + height_item, behavior);
            } else if (y < scrollTop) {
              this.scroll(y, behavior);
            }
          }
          /**
           * Scroll the dropdown to the given position
           *
           */
          scroll(scrollTop, behavior) {
            const content = this.dropdown_content;
            if (behavior) {
              content.style.scrollBehavior = behavior;
            }
            content.scrollTop = scrollTop;
            content.style.scrollBehavior = "";
          }
          /**
           * Clears the active option
           *
           */
          clearActiveOption() {
            if (this.activeOption) {
              removeClasses(this.activeOption, "active");
              setAttr(this.activeOption, {
                "aria-selected": null
              });
            }
            this.activeOption = null;
            setAttr(this.focus_node, {
              "aria-activedescendant": null
            });
          }
          /**
           * Selects all items (CTRL + A).
           */
          selectAll() {
            const self2 = this;
            if (self2.settings.mode === "single")
              return;
            const activeItems = self2.controlChildren();
            if (!activeItems.length)
              return;
            self2.hideInput();
            self2.close();
            self2.activeItems = activeItems;
            iterate$1(activeItems, (item) => {
              self2.setActiveItemClass(item);
            });
          }
          /**
           * Determines if the control_input should be in a hidden or visible state
           *
           */
          inputState() {
            var self2 = this;
            if (!self2.control.contains(self2.control_input))
              return;
            setAttr(self2.control_input, {
              placeholder: self2.settings.placeholder
            });
            if (self2.activeItems.length > 0 || !self2.isFocused && self2.settings.hidePlaceholder && self2.items.length > 0) {
              self2.setTextboxValue();
              self2.isInputHidden = true;
            } else {
              if (self2.settings.hidePlaceholder && self2.items.length > 0) {
                setAttr(self2.control_input, {
                  placeholder: ""
                });
              }
              self2.isInputHidden = false;
            }
            self2.wrapper.classList.toggle("input-hidden", self2.isInputHidden);
          }
          /**
           * Hides the input element out of view, while
           * retaining its focus.
           * @deprecated 1.3
           */
          hideInput() {
            this.inputState();
          }
          /**
           * Restores input visibility.
           * @deprecated 1.3
           */
          showInput() {
            this.inputState();
          }
          /**
           * Get the input value
           */
          inputValue() {
            return this.control_input.value.trim();
          }
          /**
           * Gives the control focus.
           */
          focus() {
            var self2 = this;
            if (self2.isDisabled)
              return;
            self2.ignoreFocus = true;
            if (self2.control_input.offsetWidth) {
              self2.control_input.focus();
            } else {
              self2.focus_node.focus();
            }
            setTimeout(() => {
              self2.ignoreFocus = false;
              self2.onFocus();
            }, 0);
          }
          /**
           * Forces the control out of focus.
           *
           */
          blur() {
            this.focus_node.blur();
            this.onBlur();
          }
          /**
           * Returns a function that scores an object
           * to show how good of a match it is to the
           * provided query.
           *
           * @return {function}
           */
          getScoreFunction(query) {
            return this.sifter.getScoreFunction(query, this.getSearchOptions());
          }
          /**
           * Returns search options for sifter (the system
           * for scoring and sorting results).
           *
           * @see https://github.com/orchidjs/sifter.js
           * @return {object}
           */
          getSearchOptions() {
            var settings = this.settings;
            var sort = settings.sortField;
            if (typeof settings.sortField === "string") {
              sort = [{
                field: settings.sortField
              }];
            }
            return {
              fields: settings.searchField,
              conjunction: settings.searchConjunction,
              sort,
              nesting: settings.nesting
            };
          }
          /**
           * Searches through available options and returns
           * a sorted array of matches.
           *
           */
          search(query) {
            var result, calculateScore;
            var self2 = this;
            var options = this.getSearchOptions();
            if (self2.settings.score) {
              calculateScore = self2.settings.score.call(self2, query);
              if (typeof calculateScore !== "function") {
                throw new Error('Tom Select "score" setting must be a function that returns a function');
              }
            }
            if (query !== self2.lastQuery) {
              self2.lastQuery = query;
              result = self2.sifter.search(query, Object.assign(options, {
                score: calculateScore
              }));
              self2.currentResults = result;
            } else {
              result = Object.assign({}, self2.currentResults);
            }
            if (self2.settings.hideSelected) {
              result.items = result.items.filter((item) => {
                let hashed = hash_key2(item.id);
                return !(hashed && self2.items.indexOf(hashed) !== -1);
              });
            }
            return result;
          }
          /**
           * Refreshes the list of available options shown
           * in the autocomplete dropdown menu.
           *
           */
          refreshOptions(triggerDropdown = true) {
            var i, j, k, n, optgroup, optgroups, html, has_create_option, active_group;
            var create;
            const groups = {};
            const groups_order = [];
            var self2 = this;
            var query = self2.inputValue();
            const same_query = query === self2.lastQuery || query == "" && self2.lastQuery == null;
            var results = self2.search(query);
            var active_option = null;
            var show_dropdown = self2.settings.shouldOpen || false;
            var dropdown_content = self2.dropdown_content;
            if (same_query) {
              active_option = self2.activeOption;
              if (active_option) {
                active_group = active_option.closest("[data-group]");
              }
            }
            n = results.items.length;
            if (typeof self2.settings.maxOptions === "number") {
              n = Math.min(n, self2.settings.maxOptions);
            }
            if (n > 0) {
              show_dropdown = true;
            }
            for (i = 0; i < n; i++) {
              let item = results.items[i];
              if (!item)
                continue;
              let opt_value = item.id;
              let option = self2.options[opt_value];
              if (option === void 0)
                continue;
              let opt_hash = get_hash2(opt_value);
              let option_el = self2.getOption(opt_hash, true);
              if (!self2.settings.hideSelected) {
                option_el.classList.toggle("selected", self2.items.includes(opt_hash));
              }
              optgroup = option[self2.settings.optgroupField] || "";
              optgroups = Array.isArray(optgroup) ? optgroup : [optgroup];
              for (j = 0, k = optgroups && optgroups.length; j < k; j++) {
                optgroup = optgroups[j];
                if (!self2.optgroups.hasOwnProperty(optgroup)) {
                  optgroup = "";
                }
                let group_fragment = groups[optgroup];
                if (group_fragment === void 0) {
                  group_fragment = document.createDocumentFragment();
                  groups_order.push(optgroup);
                }
                if (j > 0) {
                  option_el = option_el.cloneNode(true);
                  setAttr(option_el, {
                    id: option.$id + "-clone-" + j,
                    "aria-selected": null
                  });
                  option_el.classList.add("ts-cloned");
                  removeClasses(option_el, "active");
                  if (self2.activeOption && self2.activeOption.dataset.value == opt_value) {
                    if (active_group && active_group.dataset.group === optgroup.toString()) {
                      active_option = option_el;
                    }
                  }
                }
                group_fragment.appendChild(option_el);
                groups[optgroup] = group_fragment;
              }
            }
            if (self2.settings.lockOptgroupOrder) {
              groups_order.sort((a, b) => {
                const grp_a = self2.optgroups[a];
                const grp_b = self2.optgroups[b];
                const a_order = grp_a && grp_a.$order || 0;
                const b_order = grp_b && grp_b.$order || 0;
                return a_order - b_order;
              });
            }
            html = document.createDocumentFragment();
            iterate$1(groups_order, (optgroup2) => {
              let group_fragment = groups[optgroup2];
              if (!group_fragment || !group_fragment.children.length)
                return;
              let group_heading = self2.optgroups[optgroup2];
              if (group_heading !== void 0) {
                let group_options = document.createDocumentFragment();
                let header = self2.render("optgroup_header", group_heading);
                append(group_options, header);
                append(group_options, group_fragment);
                let group_html = self2.render("optgroup", {
                  group: group_heading,
                  options: group_options
                });
                append(html, group_html);
              } else {
                append(html, group_fragment);
              }
            });
            dropdown_content.innerHTML = "";
            append(dropdown_content, html);
            if (self2.settings.highlight) {
              removeHighlight(dropdown_content);
              if (results.query.length && results.tokens.length) {
                iterate$1(results.tokens, (tok) => {
                  highlight(dropdown_content, tok.regex);
                });
              }
            }
            var add_template = (template) => {
              let content = self2.render(template, {
                input: query
              });
              if (content) {
                show_dropdown = true;
                dropdown_content.insertBefore(content, dropdown_content.firstChild);
              }
              return content;
            };
            if (self2.loading) {
              add_template("loading");
            } else if (!self2.settings.shouldLoad.call(self2, query)) {
              add_template("not_loading");
            } else if (results.items.length === 0) {
              add_template("no_results");
            }
            has_create_option = self2.canCreate(query);
            if (has_create_option) {
              create = add_template("option_create");
            }
            self2.hasOptions = results.items.length > 0 || has_create_option;
            if (show_dropdown) {
              if (results.items.length > 0) {
                if (!active_option && self2.settings.mode === "single" && self2.items[0] != void 0) {
                  active_option = self2.getOption(self2.items[0]);
                }
                if (!dropdown_content.contains(active_option)) {
                  let active_index = 0;
                  if (create && !self2.settings.addPrecedence) {
                    active_index = 1;
                  }
                  active_option = self2.selectable()[active_index];
                }
              } else if (create) {
                active_option = create;
              }
              if (triggerDropdown && !self2.isOpen) {
                self2.open();
                self2.scrollToOption(active_option, "auto");
              }
              self2.setActiveOption(active_option);
            } else {
              self2.clearActiveOption();
              if (triggerDropdown && self2.isOpen) {
                self2.close(false);
              }
            }
          }
          /**
           * Return list of selectable options
           *
           */
          selectable() {
            return this.dropdown_content.querySelectorAll("[data-selectable]");
          }
          /**
           * Adds an available option. If it already exists,
           * nothing will happen. Note: this does not refresh
           * the options list dropdown (use `refreshOptions`
           * for that).
           *
           * Usage:
           *
           *   this.addOption(data)
           *
           */
          addOption(data, user_created = false) {
            const self2 = this;
            if (Array.isArray(data)) {
              self2.addOptions(data, user_created);
              return false;
            }
            const key = hash_key2(data[self2.settings.valueField]);
            if (key === null || self2.options.hasOwnProperty(key)) {
              return false;
            }
            data.$order = data.$order || ++self2.order;
            data.$id = self2.inputId + "-opt-" + data.$order;
            self2.options[key] = data;
            self2.lastQuery = null;
            if (user_created) {
              self2.userOptions[key] = user_created;
              self2.trigger("option_add", key, data);
            }
            return key;
          }
          /**
           * Add multiple options
           *
           */
          addOptions(data, user_created = false) {
            iterate$1(data, (dat) => {
              this.addOption(dat, user_created);
            });
          }
          /**
           * @deprecated 1.7.7
           */
          registerOption(data) {
            return this.addOption(data);
          }
          /**
           * Registers an option group to the pool of option groups.
           *
           * @return {boolean|string}
           */
          registerOptionGroup(data) {
            var key = hash_key2(data[this.settings.optgroupValueField]);
            if (key === null)
              return false;
            data.$order = data.$order || ++this.order;
            this.optgroups[key] = data;
            return key;
          }
          /**
           * Registers a new optgroup for options
           * to be bucketed into.
           *
           */
          addOptionGroup(id, data) {
            var hashed_id;
            data[this.settings.optgroupValueField] = id;
            if (hashed_id = this.registerOptionGroup(data)) {
              this.trigger("optgroup_add", hashed_id, data);
            }
          }
          /**
           * Removes an existing option group.
           *
           */
          removeOptionGroup(id) {
            if (this.optgroups.hasOwnProperty(id)) {
              delete this.optgroups[id];
              this.clearCache();
              this.trigger("optgroup_remove", id);
            }
          }
          /**
           * Clears all existing option groups.
           */
          clearOptionGroups() {
            this.optgroups = {};
            this.clearCache();
            this.trigger("optgroup_clear");
          }
          /**
           * Updates an option available for selection. If
           * it is visible in the selected items or options
           * dropdown, it will be re-rendered automatically.
           *
           */
          updateOption(value, data) {
            const self2 = this;
            var item_new;
            var index_item;
            const value_old = hash_key2(value);
            const value_new = hash_key2(data[self2.settings.valueField]);
            if (value_old === null)
              return;
            const data_old = self2.options[value_old];
            if (data_old == void 0)
              return;
            if (typeof value_new !== "string")
              throw new Error("Value must be set in option data");
            const option = self2.getOption(value_old);
            const item = self2.getItem(value_old);
            data.$order = data.$order || data_old.$order;
            delete self2.options[value_old];
            self2.uncacheValue(value_new);
            self2.options[value_new] = data;
            if (option) {
              if (self2.dropdown_content.contains(option)) {
                const option_new = self2._render("option", data);
                replaceNode(option, option_new);
                if (self2.activeOption === option) {
                  self2.setActiveOption(option_new);
                }
              }
              option.remove();
            }
            if (item) {
              index_item = self2.items.indexOf(value_old);
              if (index_item !== -1) {
                self2.items.splice(index_item, 1, value_new);
              }
              item_new = self2._render("item", data);
              if (item.classList.contains("active"))
                addClasses2(item_new, "active");
              replaceNode(item, item_new);
            }
            self2.lastQuery = null;
          }
          /**
           * Removes a single option.
           *
           */
          removeOption(value, silent) {
            const self2 = this;
            value = get_hash2(value);
            self2.uncacheValue(value);
            delete self2.userOptions[value];
            delete self2.options[value];
            self2.lastQuery = null;
            self2.trigger("option_remove", value);
            self2.removeItem(value, silent);
          }
          /**
           * Clears all options.
           */
          clearOptions(filter) {
            const boundFilter = (filter || this.clearFilter).bind(this);
            this.loadedSearches = {};
            this.userOptions = {};
            this.clearCache();
            const selected = {};
            iterate$1(this.options, (option, key) => {
              if (boundFilter(option, key)) {
                selected[key] = option;
              }
            });
            this.options = this.sifter.items = selected;
            this.lastQuery = null;
            this.trigger("option_clear");
          }
          /**
           * Used by clearOptions() to decide whether or not an option should be removed
           * Return true to keep an option, false to remove
           *
           */
          clearFilter(option, value) {
            if (this.items.indexOf(value) >= 0) {
              return true;
            }
            return false;
          }
          /**
           * Returns the dom element of the option
           * matching the given value.
           *
           */
          getOption(value, create = false) {
            const hashed = hash_key2(value);
            if (hashed === null)
              return null;
            const option = this.options[hashed];
            if (option != void 0) {
              if (option.$div) {
                return option.$div;
              }
              if (create) {
                return this._render("option", option);
              }
            }
            return null;
          }
          /**
           * Returns the dom element of the next or previous dom element of the same type
           * Note: adjacent options may not be adjacent DOM elements (optgroups)
           *
           */
          getAdjacent(option, direction, type = "option") {
            var self2 = this, all;
            if (!option) {
              return null;
            }
            if (type == "item") {
              all = self2.controlChildren();
            } else {
              all = self2.dropdown_content.querySelectorAll("[data-selectable]");
            }
            for (let i = 0; i < all.length; i++) {
              if (all[i] != option) {
                continue;
              }
              if (direction > 0) {
                return all[i + 1];
              }
              return all[i - 1];
            }
            return null;
          }
          /**
           * Returns the dom element of the item
           * matching the given value.
           *
           */
          getItem(item) {
            if (typeof item == "object") {
              return item;
            }
            var value = hash_key2(item);
            return value !== null ? this.control.querySelector(`[data-value="${addSlashes(value)}"]`) : null;
          }
          /**
           * "Selects" multiple items at once. Adds them to the list
           * at the current caret position.
           *
           */
          addItems(values, silent) {
            var self2 = this;
            var items = Array.isArray(values) ? values : [values];
            items = items.filter((x) => self2.items.indexOf(x) === -1);
            const last_item = items[items.length - 1];
            items.forEach((item) => {
              self2.isPending = item !== last_item;
              self2.addItem(item, silent);
            });
          }
          /**
           * "Selects" an item. Adds it to the list
           * at the current caret position.
           *
           */
          addItem(value, silent) {
            var events = silent ? [] : ["change", "dropdown_close"];
            debounce_events(this, events, () => {
              var item, wasFull;
              const self2 = this;
              const inputMode = self2.settings.mode;
              const hashed = hash_key2(value);
              if (hashed && self2.items.indexOf(hashed) !== -1) {
                if (inputMode === "single") {
                  self2.close();
                }
                if (inputMode === "single" || !self2.settings.duplicates) {
                  return;
                }
              }
              if (hashed === null || !self2.options.hasOwnProperty(hashed))
                return;
              if (inputMode === "single")
                self2.clear(silent);
              if (inputMode === "multi" && self2.isFull())
                return;
              item = self2._render("item", self2.options[hashed]);
              if (self2.control.contains(item)) {
                item = item.cloneNode(true);
              }
              wasFull = self2.isFull();
              self2.items.splice(self2.caretPos, 0, hashed);
              self2.insertAtCaret(item);
              if (self2.isSetup) {
                if (!self2.isPending && self2.settings.hideSelected) {
                  let option = self2.getOption(hashed);
                  let next = self2.getAdjacent(option, 1);
                  if (next) {
                    self2.setActiveOption(next);
                  }
                }
                if (!self2.isPending && !self2.settings.closeAfterSelect) {
                  self2.refreshOptions(self2.isFocused && inputMode !== "single");
                }
                if (self2.settings.closeAfterSelect != false && self2.isFull()) {
                  self2.close();
                } else if (!self2.isPending) {
                  self2.positionDropdown();
                }
                self2.trigger("item_add", hashed, item);
                if (!self2.isPending) {
                  self2.updateOriginalInput({
                    silent
                  });
                }
              }
              if (!self2.isPending || !wasFull && self2.isFull()) {
                self2.inputState();
                self2.refreshState();
              }
            });
          }
          /**
           * Removes the selected item matching
           * the provided value.
           *
           */
          removeItem(item = null, silent) {
            const self2 = this;
            item = self2.getItem(item);
            if (!item)
              return;
            var i, idx;
            const value = item.dataset.value;
            i = nodeIndex(item);
            item.remove();
            if (item.classList.contains("active")) {
              idx = self2.activeItems.indexOf(item);
              self2.activeItems.splice(idx, 1);
              removeClasses(item, "active");
            }
            self2.items.splice(i, 1);
            self2.lastQuery = null;
            if (!self2.settings.persist && self2.userOptions.hasOwnProperty(value)) {
              self2.removeOption(value, silent);
            }
            if (i < self2.caretPos) {
              self2.setCaret(self2.caretPos - 1);
            }
            self2.updateOriginalInput({
              silent
            });
            self2.refreshState();
            self2.positionDropdown();
            self2.trigger("item_remove", value, item);
          }
          /**
           * Invokes the `create` method provided in the
           * TomSelect options that should provide the data
           * for the new item, given the user input.
           *
           * Once this completes, it will be added
           * to the item list.
           *
           */
          createItem(input = null, callback = () => {
          }) {
            if (arguments.length === 3) {
              callback = arguments[2];
            }
            if (typeof callback != "function") {
              callback = () => {
              };
            }
            var self2 = this;
            var caret = self2.caretPos;
            var output;
            input = input || self2.inputValue();
            if (!self2.canCreate(input)) {
              callback();
              return false;
            }
            self2.lock();
            var created = false;
            var create = (data) => {
              self2.unlock();
              if (!data || typeof data !== "object")
                return callback();
              var value = hash_key2(data[self2.settings.valueField]);
              if (typeof value !== "string") {
                return callback();
              }
              self2.setTextboxValue();
              self2.addOption(data, true);
              self2.setCaret(caret);
              self2.addItem(value);
              callback(data);
              created = true;
            };
            if (typeof self2.settings.create === "function") {
              output = self2.settings.create.call(this, input, create);
            } else {
              output = {
                [self2.settings.labelField]: input,
                [self2.settings.valueField]: input
              };
            }
            if (!created) {
              create(output);
            }
            return true;
          }
          /**
           * Re-renders the selected item lists.
           */
          refreshItems() {
            var self2 = this;
            self2.lastQuery = null;
            if (self2.isSetup) {
              self2.addItems(self2.items);
            }
            self2.updateOriginalInput();
            self2.refreshState();
          }
          /**
           * Updates all state-dependent attributes
           * and CSS classes.
           */
          refreshState() {
            const self2 = this;
            self2.refreshValidityState();
            const isFull = self2.isFull();
            const isLocked = self2.isLocked;
            self2.wrapper.classList.toggle("rtl", self2.rtl);
            const wrap_classList = self2.wrapper.classList;
            wrap_classList.toggle("focus", self2.isFocused);
            wrap_classList.toggle("disabled", self2.isDisabled);
            wrap_classList.toggle("required", self2.isRequired);
            wrap_classList.toggle("invalid", !self2.isValid);
            wrap_classList.toggle("locked", isLocked);
            wrap_classList.toggle("full", isFull);
            wrap_classList.toggle("input-active", self2.isFocused && !self2.isInputHidden);
            wrap_classList.toggle("dropdown-active", self2.isOpen);
            wrap_classList.toggle("has-options", isEmptyObject(self2.options));
            wrap_classList.toggle("has-items", self2.items.length > 0);
          }
          /**
           * Update the `required` attribute of both input and control input.
           *
           * The `required` property needs to be activated on the control input
           * for the error to be displayed at the right place. `required` also
           * needs to be temporarily deactivated on the input since the input is
           * hidden and can't show errors.
           */
          refreshValidityState() {
            var self2 = this;
            if (!self2.input.validity) {
              return;
            }
            self2.isValid = self2.input.validity.valid;
            self2.isInvalid = !self2.isValid;
          }
          /**
           * Determines whether or not more items can be added
           * to the control without exceeding the user-defined maximum.
           *
           * @returns {boolean}
           */
          isFull() {
            return this.settings.maxItems !== null && this.items.length >= this.settings.maxItems;
          }
          /**
           * Refreshes the original <select> or <input>
           * element to reflect the current state.
           *
           */
          updateOriginalInput(opts = {}) {
            const self2 = this;
            var option, label;
            const empty_option = self2.input.querySelector('option[value=""]');
            if (self2.is_select_tag) {
              let AddSelected = function(option_el, value, label2) {
                if (!option_el) {
                  option_el = getDom2('<option value="' + escape_html2(value) + '">' + escape_html2(label2) + "</option>");
                }
                if (option_el != empty_option) {
                  self2.input.append(option_el);
                }
                selected.push(option_el);
                if (option_el != empty_option || has_selected > 0) {
                  option_el.selected = true;
                }
                return option_el;
              };
              const selected = [];
              const has_selected = self2.input.querySelectorAll("option:checked").length;
              self2.input.querySelectorAll("option:checked").forEach((option_el) => {
                option_el.selected = false;
              });
              if (self2.items.length == 0 && self2.settings.mode == "single") {
                AddSelected(empty_option, "", "");
              } else {
                self2.items.forEach((value) => {
                  option = self2.options[value];
                  label = option[self2.settings.labelField] || "";
                  if (selected.includes(option.$option)) {
                    const reuse_opt = self2.input.querySelector(`option[value="${addSlashes(value)}"]:not(:checked)`);
                    AddSelected(reuse_opt, value, label);
                  } else {
                    option.$option = AddSelected(option.$option, value, label);
                  }
                });
              }
            } else {
              self2.input.value = self2.getValue();
            }
            if (self2.isSetup) {
              if (!opts.silent) {
                self2.trigger("change", self2.getValue());
              }
            }
          }
          /**
           * Shows the autocomplete dropdown containing
           * the available options.
           */
          open() {
            var self2 = this;
            if (self2.isLocked || self2.isOpen || self2.settings.mode === "multi" && self2.isFull())
              return;
            self2.isOpen = true;
            setAttr(self2.focus_node, {
              "aria-expanded": "true"
            });
            self2.refreshState();
            applyCSS(self2.dropdown, {
              visibility: "hidden",
              display: "block"
            });
            self2.positionDropdown();
            applyCSS(self2.dropdown, {
              visibility: "visible",
              display: "block"
            });
            self2.focus();
            self2.trigger("dropdown_open", self2.dropdown);
          }
          /**
           * Closes the autocomplete dropdown menu.
           */
          close(setTextboxValue = true) {
            var self2 = this;
            var trigger = self2.isOpen;
            if (setTextboxValue) {
              self2.setTextboxValue();
              if (self2.settings.mode === "single" && self2.items.length) {
                self2.hideInput();
              }
            }
            self2.isOpen = false;
            setAttr(self2.focus_node, {
              "aria-expanded": "false"
            });
            applyCSS(self2.dropdown, {
              display: "none"
            });
            if (self2.settings.hideSelected) {
              self2.clearActiveOption();
            }
            self2.refreshState();
            if (trigger)
              self2.trigger("dropdown_close", self2.dropdown);
          }
          /**
           * Calculates and applies the appropriate
           * position of the dropdown if dropdownParent = 'body'.
           * Otherwise, position is determined by css
           */
          positionDropdown() {
            if (this.settings.dropdownParent !== "body") {
              return;
            }
            var context = this.control;
            var rect = context.getBoundingClientRect();
            var top = context.offsetHeight + rect.top + window.scrollY;
            var left = rect.left + window.scrollX;
            applyCSS(this.dropdown, {
              width: rect.width + "px",
              top: top + "px",
              left: left + "px"
            });
          }
          /**
           * Resets / clears all selected items
           * from the control.
           *
           */
          clear(silent) {
            var self2 = this;
            if (!self2.items.length)
              return;
            var items = self2.controlChildren();
            iterate$1(items, (item) => {
              self2.removeItem(item, true);
            });
            self2.showInput();
            if (!silent)
              self2.updateOriginalInput();
            self2.trigger("clear");
          }
          /**
           * A helper method for inserting an element
           * at the current caret position.
           *
           */
          insertAtCaret(el) {
            const self2 = this;
            const caret = self2.caretPos;
            const target = self2.control;
            target.insertBefore(el, target.children[caret] || null);
            self2.setCaret(caret + 1);
          }
          /**
           * Removes the current selected item(s).
           *
           */
          deleteSelection(e) {
            var direction, selection, caret, tail;
            var self2 = this;
            direction = e && e.keyCode === KEY_BACKSPACE ? -1 : 1;
            selection = getSelection(self2.control_input);
            const rm_items = [];
            if (self2.activeItems.length) {
              tail = getTail(self2.activeItems, direction);
              caret = nodeIndex(tail);
              if (direction > 0) {
                caret++;
              }
              iterate$1(self2.activeItems, (item) => rm_items.push(item));
            } else if ((self2.isFocused || self2.settings.mode === "single") && self2.items.length) {
              const items = self2.controlChildren();
              let rm_item;
              if (direction < 0 && selection.start === 0 && selection.length === 0) {
                rm_item = items[self2.caretPos - 1];
              } else if (direction > 0 && selection.start === self2.inputValue().length) {
                rm_item = items[self2.caretPos];
              }
              if (rm_item !== void 0) {
                rm_items.push(rm_item);
              }
            }
            if (!self2.shouldDelete(rm_items, e)) {
              return false;
            }
            preventDefault2(e, true);
            if (typeof caret !== "undefined") {
              self2.setCaret(caret);
            }
            while (rm_items.length) {
              self2.removeItem(rm_items.pop());
            }
            self2.showInput();
            self2.positionDropdown();
            self2.refreshOptions(false);
            return true;
          }
          /**
           * Return true if the items should be deleted
           */
          shouldDelete(items, evt) {
            const values = items.map((item) => item.dataset.value);
            if (!values.length || typeof this.settings.onDelete === "function" && this.settings.onDelete(values, evt) === false) {
              return false;
            }
            return true;
          }
          /**
           * Selects the previous / next item (depending on the `direction` argument).
           *
           * > 0 - right
           * < 0 - left
           *
           */
          advanceSelection(direction, e) {
            var last_active, adjacent, self2 = this;
            if (self2.rtl)
              direction *= -1;
            if (self2.inputValue().length)
              return;
            if (isKeyDown(KEY_SHORTCUT, e) || isKeyDown("shiftKey", e)) {
              last_active = self2.getLastActive(direction);
              if (last_active) {
                if (!last_active.classList.contains("active")) {
                  adjacent = last_active;
                } else {
                  adjacent = self2.getAdjacent(last_active, direction, "item");
                }
              } else if (direction > 0) {
                adjacent = self2.control_input.nextElementSibling;
              } else {
                adjacent = self2.control_input.previousElementSibling;
              }
              if (adjacent) {
                if (adjacent.classList.contains("active")) {
                  self2.removeActiveItem(last_active);
                }
                self2.setActiveItemClass(adjacent);
              }
            } else {
              self2.moveCaret(direction);
            }
          }
          moveCaret(direction) {
          }
          /**
           * Get the last active item
           *
           */
          getLastActive(direction) {
            let last_active = this.control.querySelector(".last-active");
            if (last_active) {
              return last_active;
            }
            var result = this.control.querySelectorAll(".active");
            if (result) {
              return getTail(result, direction);
            }
          }
          /**
           * Moves the caret to the specified index.
           *
           * The input must be moved by leaving it in place and moving the
           * siblings, due to the fact that focus cannot be restored once lost
           * on mobile webkit devices
           *
           */
          setCaret(new_pos) {
            this.caretPos = this.items.length;
          }
          /**
           * Return list of item dom elements
           *
           */
          controlChildren() {
            return Array.from(this.control.querySelectorAll("[data-ts-item]"));
          }
          /**
           * Disables user input on the control. Used while
           * items are being asynchronously created.
           */
          lock() {
            this.isLocked = true;
            this.refreshState();
          }
          /**
           * Re-enables user input on the control.
           */
          unlock() {
            this.isLocked = false;
            this.refreshState();
          }
          /**
           * Disables user input on the control completely.
           * While disabled, it cannot receive focus.
           */
          disable() {
            var self2 = this;
            self2.input.disabled = true;
            self2.control_input.disabled = true;
            self2.focus_node.tabIndex = -1;
            self2.isDisabled = true;
            this.close();
            self2.lock();
          }
          /**
           * Enables the control so that it can respond
           * to focus and user input.
           */
          enable() {
            var self2 = this;
            self2.input.disabled = false;
            self2.control_input.disabled = false;
            self2.focus_node.tabIndex = self2.tabIndex;
            self2.isDisabled = false;
            self2.unlock();
          }
          /**
           * Completely destroys the control and
           * unbinds all event listeners so that it can
           * be garbage collected.
           */
          destroy() {
            var self2 = this;
            var revertSettings = self2.revertSettings;
            self2.trigger("destroy");
            self2.off();
            self2.wrapper.remove();
            self2.dropdown.remove();
            self2.input.innerHTML = revertSettings.innerHTML;
            self2.input.tabIndex = revertSettings.tabIndex;
            removeClasses(self2.input, "tomselected", "ts-hidden-accessible");
            self2._destroy();
            delete self2.input.tomselect;
          }
          /**
           * A helper method for rendering "item" and
           * "option" templates, given the data.
           *
           */
          render(templateName, data) {
            var id, html;
            const self2 = this;
            if (typeof this.settings.render[templateName] !== "function") {
              return null;
            }
            html = self2.settings.render[templateName].call(this, data, escape_html2);
            if (!html) {
              return null;
            }
            html = getDom2(html);
            if (templateName === "option" || templateName === "option_create") {
              if (data[self2.settings.disabledField]) {
                setAttr(html, {
                  "aria-disabled": "true"
                });
              } else {
                setAttr(html, {
                  "data-selectable": ""
                });
              }
            } else if (templateName === "optgroup") {
              id = data.group[self2.settings.optgroupValueField];
              setAttr(html, {
                "data-group": id
              });
              if (data.group[self2.settings.disabledField]) {
                setAttr(html, {
                  "data-disabled": ""
                });
              }
            }
            if (templateName === "option" || templateName === "item") {
              const value = get_hash2(data[self2.settings.valueField]);
              setAttr(html, {
                "data-value": value
              });
              if (templateName === "item") {
                addClasses2(html, self2.settings.itemClass);
                setAttr(html, {
                  "data-ts-item": ""
                });
              } else {
                addClasses2(html, self2.settings.optionClass);
                setAttr(html, {
                  role: "option",
                  id: data.$id
                });
                data.$div = html;
                self2.options[value] = data;
              }
            }
            return html;
          }
          /**
           * Type guarded rendering
           *
           */
          _render(templateName, data) {
            const html = this.render(templateName, data);
            if (html == null) {
              throw "HTMLElement expected";
            }
            return html;
          }
          /**
           * Clears the render cache for a template. If
           * no template is given, clears all render
           * caches.
           *
           */
          clearCache() {
            iterate$1(this.options, (option) => {
              if (option.$div) {
                option.$div.remove();
                delete option.$div;
              }
            });
          }
          /**
           * Removes a value from item and option caches
           *
           */
          uncacheValue(value) {
            const option_el = this.getOption(value);
            if (option_el)
              option_el.remove();
          }
          /**
           * Determines whether or not to display the
           * create item prompt, given a user input.
           *
           */
          canCreate(input) {
            return this.settings.create && input.length > 0 && this.settings.createFilter.call(this, input);
          }
          /**
           * Wraps this.`method` so that `new_fn` can be invoked 'before', 'after', or 'instead' of the original method
           *
           * this.hook('instead','onKeyDown',function( arg1, arg2 ...){
           *
           * });
           */
          hook(when, method, new_fn) {
            var self2 = this;
            var orig_method = self2[method];
            self2[method] = function() {
              var result, result_new;
              if (when === "after") {
                result = orig_method.apply(self2, arguments);
              }
              result_new = new_fn.apply(self2, arguments);
              if (when === "instead") {
                return result_new;
              }
              if (when === "before") {
                result = orig_method.apply(self2, arguments);
              }
              return result;
            };
          }
        }
        return TomSelect3;
      });
    }
  });

  // node_modules/@orchidjs/unicode-variants/dist/umd/index.js
  var require_umd = __commonJS({
    "node_modules/@orchidjs/unicode-variants/dist/umd/index.js"(exports, module) {
      (function(global, factory) {
        typeof exports === "object" && typeof module !== "undefined" ? factory(exports) : typeof define === "function" && define.amd ? define(["exports"], factory) : (global = typeof globalThis !== "undefined" ? globalThis : global || self, factory(global.diacritics = {}));
      })(exports, function(exports2) {
        "use strict";
        const arrayToPattern = (chars) => {
          chars = chars.filter(Boolean);
          if (chars.length < 2) {
            return chars[0] || "";
          }
          return maxValueLength(chars) == 1 ? "[" + chars.join("") + "]" : "(?:" + chars.join("|") + ")";
        };
        const sequencePattern = (array) => {
          if (!hasDuplicates(array)) {
            return array.join("");
          }
          let pattern = "";
          let prev_char_count = 0;
          const prev_pattern = () => {
            if (prev_char_count > 1) {
              pattern += "{" + prev_char_count + "}";
            }
          };
          array.forEach((char, i) => {
            if (char === array[i - 1]) {
              prev_char_count++;
              return;
            }
            prev_pattern();
            pattern += char;
            prev_char_count = 1;
          });
          prev_pattern();
          return pattern;
        };
        const setToPattern = (chars) => {
          let array = toArray(chars);
          return arrayToPattern(array);
        };
        const hasDuplicates = (array) => {
          return new Set(array).size !== array.length;
        };
        const escape_regex = (str) => {
          return (str + "").replace(/([\$\(\)\*\+\.\?\[\]\^\{\|\}\\])/gu, "\\$1");
        };
        const maxValueLength = (array) => {
          return array.reduce((longest, value) => Math.max(longest, unicodeLength(value)), 0);
        };
        const unicodeLength = (str) => {
          return toArray(str).length;
        };
        const toArray = (p) => Array.from(p);
        const allSubstrings = (input) => {
          if (input.length === 1)
            return [[input]];
          let result = [];
          const start = input.substring(1);
          const suba = allSubstrings(start);
          suba.forEach(function(subresult) {
            let tmp = subresult.slice(0);
            tmp[0] = input.charAt(0) + tmp[0];
            result.push(tmp);
            tmp = subresult.slice(0);
            tmp.unshift(input.charAt(0));
            result.push(tmp);
          });
          return result;
        };
        const code_points = [[0, 65535]];
        const accent_pat = "[\u0300-\u036F\xB7\u02BE\u02BC]";
        exports2.unicode_map = void 0;
        let multi_char_reg;
        const max_char_length = 3;
        const latin_convert = {};
        const latin_condensed = {
          "/": "\u2044\u2215",
          "0": "\u07C0",
          "a": "\u2C65\u0250\u0251",
          "aa": "\uA733",
          "ae": "\xE6\u01FD\u01E3",
          "ao": "\uA735",
          "au": "\uA737",
          "av": "\uA739\uA73B",
          "ay": "\uA73D",
          "b": "\u0180\u0253\u0183",
          "c": "\uA73F\u0188\u023C\u2184",
          "d": "\u0111\u0257\u0256\u1D05\u018C\uABB7\u0501\u0266",
          "e": "\u025B\u01DD\u1D07\u0247",
          "f": "\uA77C\u0192",
          "g": "\u01E5\u0260\uA7A1\u1D79\uA77F\u0262",
          "h": "\u0127\u2C68\u2C76\u0265",
          "i": "\u0268\u0131",
          "j": "\u0249\u0237",
          "k": "\u0199\u2C6A\uA741\uA743\uA745\uA7A3",
          "l": "\u0142\u019A\u026B\u2C61\uA749\uA747\uA781\u026D",
          "m": "\u0271\u026F\u03FB",
          "n": "\uA7A5\u019E\u0272\uA791\u1D0E\u043B\u0509",
          "o": "\xF8\u01FF\u0254\u0275\uA74B\uA74D\u1D11",
          "oe": "\u0153",
          "oi": "\u01A3",
          "oo": "\uA74F",
          "ou": "\u0223",
          "p": "\u01A5\u1D7D\uA751\uA753\uA755\u03C1",
          "q": "\uA757\uA759\u024B",
          "r": "\u024D\u027D\uA75B\uA7A7\uA783",
          "s": "\xDF\u023F\uA7A9\uA785\u0282",
          "t": "\u0167\u01AD\u0288\u2C66\uA787",
          "th": "\xFE",
          "tz": "\uA729",
          "u": "\u0289",
          "v": "\u028B\uA75F\u028C",
          "vy": "\uA761",
          "w": "\u2C73",
          "y": "\u01B4\u024F\u1EFF",
          "z": "\u01B6\u0225\u0240\u2C6C\uA763",
          "hv": "\u0195"
        };
        for (let latin in latin_condensed) {
          let unicode = latin_condensed[latin] || "";
          for (let i = 0; i < unicode.length; i++) {
            let char = unicode.substring(i, i + 1);
            latin_convert[char] = latin;
          }
        }
        const convert_pat = new RegExp(Object.keys(latin_convert).join("|") + "|" + accent_pat, "gu");
        const initialize = (_code_points) => {
          if (exports2.unicode_map !== void 0)
            return;
          exports2.unicode_map = generateMap(_code_points || code_points);
        };
        const normalize = (str, form = "NFKD") => str.normalize(form);
        const asciifold2 = (str) => {
          return toArray(str).reduce(
            /**
             * @param {string} result
             * @param {string} char
             */
            (result, char) => {
              return result + _asciifold(char);
            },
            ""
          );
        };
        const _asciifold = (str) => {
          str = normalize(str).toLowerCase().replace(convert_pat, (char) => {
            return latin_convert[char] || "";
          });
          return normalize(str, "NFC");
        };
        function* generator(code_points2) {
          for (const [code_point_min, code_point_max] of code_points2) {
            for (let i = code_point_min; i <= code_point_max; i++) {
              let composed = String.fromCharCode(i);
              let folded = asciifold2(composed);
              if (folded == composed.toLowerCase()) {
                continue;
              }
              if (folded.length > max_char_length) {
                continue;
              }
              if (folded.length == 0) {
                continue;
              }
              yield {
                folded,
                composed,
                code_point: i
              };
            }
          }
        }
        const generateSets = (code_points2) => {
          const unicode_sets = {};
          const addMatching = (folded, to_add) => {
            const folded_set = unicode_sets[folded] || /* @__PURE__ */ new Set();
            const patt = new RegExp("^" + setToPattern(folded_set) + "$", "iu");
            if (to_add.match(patt)) {
              return;
            }
            folded_set.add(escape_regex(to_add));
            unicode_sets[folded] = folded_set;
          };
          for (let value of generator(code_points2)) {
            addMatching(value.folded, value.folded);
            addMatching(value.folded, value.composed);
          }
          return unicode_sets;
        };
        const generateMap = (code_points2) => {
          const unicode_sets = generateSets(code_points2);
          const unicode_map = {};
          let multi_char = [];
          for (let folded in unicode_sets) {
            let set = unicode_sets[folded];
            if (set) {
              unicode_map[folded] = setToPattern(set);
            }
            if (folded.length > 1) {
              multi_char.push(escape_regex(folded));
            }
          }
          multi_char.sort((a, b) => b.length - a.length);
          const multi_char_patt = arrayToPattern(multi_char);
          multi_char_reg = new RegExp("^" + multi_char_patt, "u");
          return unicode_map;
        };
        const mapSequence = (strings, min_replacement = 1) => {
          let chars_replaced = 0;
          strings = strings.map((str) => {
            if (exports2.unicode_map[str]) {
              chars_replaced += str.length;
            }
            return exports2.unicode_map[str] || str;
          });
          if (chars_replaced >= min_replacement) {
            return sequencePattern(strings);
          }
          return "";
        };
        const substringsToPattern = (str, min_replacement = 1) => {
          min_replacement = Math.max(min_replacement, str.length - 1);
          return arrayToPattern(allSubstrings(str).map((sub_pat) => {
            return mapSequence(sub_pat, min_replacement);
          }));
        };
        const sequencesToPattern = (sequences, all = true) => {
          let min_replacement = sequences.length > 1 ? 1 : 0;
          return arrayToPattern(sequences.map((sequence) => {
            let seq = [];
            const len = all ? sequence.length() : sequence.length() - 1;
            for (let j = 0; j < len; j++) {
              seq.push(substringsToPattern(sequence.substrs[j] || "", min_replacement));
            }
            return sequencePattern(seq);
          }));
        };
        const inSequences = (needle_seq, sequences) => {
          for (const seq of sequences) {
            if (seq.start != needle_seq.start || seq.end != needle_seq.end) {
              continue;
            }
            if (seq.substrs.join("") !== needle_seq.substrs.join("")) {
              continue;
            }
            let needle_parts = needle_seq.parts;
            const filter = (part) => {
              for (const needle_part of needle_parts) {
                if (needle_part.start === part.start && needle_part.substr === part.substr) {
                  return false;
                }
                if (part.length == 1 || needle_part.length == 1) {
                  continue;
                }
                if (part.start < needle_part.start && part.end > needle_part.start) {
                  return true;
                }
                if (needle_part.start < part.start && needle_part.end > part.start) {
                  return true;
                }
              }
              return false;
            };
            let filtered = seq.parts.filter(filter);
            if (filtered.length > 0) {
              continue;
            }
            return true;
          }
          return false;
        };
        class Sequence {
          constructor() {
            this.parts = [];
            this.substrs = [];
            this.start = 0;
            this.end = 0;
          }
          /**
           * @param {TSequencePart|undefined} part
           */
          add(part) {
            if (part) {
              this.parts.push(part);
              this.substrs.push(part.substr);
              this.start = Math.min(part.start, this.start);
              this.end = Math.max(part.end, this.end);
            }
          }
          last() {
            return this.parts[this.parts.length - 1];
          }
          length() {
            return this.parts.length;
          }
          /**
           * @param {number} position
           * @param {TSequencePart} last_piece
           */
          clone(position, last_piece) {
            let clone = new Sequence();
            let parts = JSON.parse(JSON.stringify(this.parts));
            let last_part = parts.pop();
            for (const part of parts) {
              clone.add(part);
            }
            let last_substr = last_piece.substr.substring(0, position - last_part.start);
            let clone_last_len = last_substr.length;
            clone.add({
              start: last_part.start,
              end: last_part.start + clone_last_len,
              length: clone_last_len,
              substr: last_substr
            });
            return clone;
          }
        }
        const getPattern = (str) => {
          initialize();
          str = asciifold2(str);
          let pattern = "";
          let sequences = [new Sequence()];
          for (let i = 0; i < str.length; i++) {
            let substr = str.substring(i);
            let match = substr.match(multi_char_reg);
            const char = str.substring(i, i + 1);
            const match_str = match ? match[0] : null;
            let overlapping = [];
            let added_types = /* @__PURE__ */ new Set();
            for (const sequence of sequences) {
              const last_piece = sequence.last();
              if (!last_piece || last_piece.length == 1 || last_piece.end <= i) {
                if (match_str) {
                  const len = match_str.length;
                  sequence.add({
                    start: i,
                    end: i + len,
                    length: len,
                    substr: match_str
                  });
                  added_types.add("1");
                } else {
                  sequence.add({
                    start: i,
                    end: i + 1,
                    length: 1,
                    substr: char
                  });
                  added_types.add("2");
                }
              } else if (match_str) {
                let clone = sequence.clone(i, last_piece);
                const len = match_str.length;
                clone.add({
                  start: i,
                  end: i + len,
                  length: len,
                  substr: match_str
                });
                overlapping.push(clone);
              } else {
                added_types.add("3");
              }
            }
            if (overlapping.length > 0) {
              overlapping = overlapping.sort((a, b) => {
                return a.length() - b.length();
              });
              for (let clone of overlapping) {
                if (inSequences(clone, sequences)) {
                  continue;
                }
                sequences.push(clone);
              }
              continue;
            }
            if (i > 0 && added_types.size == 1 && !added_types.has("3")) {
              pattern += sequencesToPattern(sequences, false);
              let new_seq = new Sequence();
              const old_seq = sequences[0];
              if (old_seq) {
                new_seq.add(old_seq.last());
              }
              sequences = [new_seq];
            }
          }
          pattern += sequencesToPattern(sequences, true);
          return pattern;
        };
        exports2._asciifold = _asciifold;
        exports2.asciifold = asciifold2;
        exports2.code_points = code_points;
        exports2.escape_regex = escape_regex;
        exports2.generateMap = generateMap;
        exports2.generateSets = generateSets;
        exports2.generator = generator;
        exports2.getPattern = getPattern;
        exports2.initialize = initialize;
        exports2.mapSequence = mapSequence;
        exports2.normalize = normalize;
        exports2.substringsToPattern = substringsToPattern;
        Object.defineProperty(exports2, "__esModule", { value: true });
      });
    }
  });

  // client/django-tomselect.js
  var import_tom_select_base = __toESM(require_tom_select_base());

  // node_modules/tom-select/src/utils.ts
  var hash_key = (value) => {
    if (typeof value === "undefined" || value === null)
      return null;
    return get_hash(value);
  };
  var get_hash = (value) => {
    if (typeof value === "boolean")
      return value ? "1" : "0";
    return value + "";
  };
  var escape_html = (str) => {
    return (str + "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
  };
  var preventDefault = (evt, stop = false) => {
    if (evt) {
      evt.preventDefault();
      if (stop) {
        evt.stopPropagation();
      }
    }
  };
  var addEvent = (target, type, callback, options) => {
    target.addEventListener(type, callback, options);
  };

  // node_modules/@orchidjs/sifter/lib/utils.ts
  var import_unicode_variants = __toESM(require_umd());
  var iterate = (object, callback) => {
    if (Array.isArray(object)) {
      object.forEach(callback);
    } else {
      for (var key in object) {
        if (object.hasOwnProperty(key)) {
          callback(object[key], key);
        }
      }
    }
  };

  // node_modules/tom-select/src/vanilla.ts
  var getDom = (query) => {
    if (query.jquery) {
      return query[0];
    }
    if (query instanceof HTMLElement) {
      return query;
    }
    if (isHtmlString(query)) {
      var tpl = document.createElement("template");
      tpl.innerHTML = query.trim();
      return tpl.content.firstChild;
    }
    return document.querySelector(query);
  };
  var isHtmlString = (arg) => {
    if (typeof arg === "string" && arg.indexOf("<") > -1) {
      return true;
    }
    return false;
  };
  var addClasses = (elmts, ...classes) => {
    var norm_classes = classesArray(classes);
    elmts = castAsArray(elmts);
    elmts.map((el) => {
      norm_classes.map((cls) => {
        el.classList.add(cls);
      });
    });
  };
  var classesArray = (args) => {
    var classes = [];
    iterate(args, (_classes) => {
      if (typeof _classes === "string") {
        _classes = _classes.trim().split(/[\11\12\14\15\40]/);
      }
      if (Array.isArray(_classes)) {
        classes = classes.concat(_classes);
      }
    });
    return classes.filter(Boolean);
  };
  var castAsArray = (arg) => {
    if (!Array.isArray(arg)) {
      arg = [arg];
    }
    return arg;
  };

  // node_modules/tom-select/src/plugins/checkbox_options/plugin.ts
  function plugin_default() {
    var self2 = this;
    var orig_onOptionSelect = self2.onOptionSelect;
    self2.settings.hideSelected = false;
    var UpdateCheckbox = function(option) {
      setTimeout(() => {
        var checkbox = option.querySelector("input");
        if (checkbox instanceof HTMLInputElement) {
          if (option.classList.contains("selected")) {
            checkbox.checked = true;
          } else {
            checkbox.checked = false;
          }
        }
      }, 1);
    };
    self2.hook("after", "setupTemplates", () => {
      var orig_render_option = self2.settings.render.option;
      self2.settings.render.option = (data, escape_html2) => {
        var rendered = getDom(orig_render_option.call(self2, data, escape_html2));
        var checkbox = document.createElement("input");
        checkbox.addEventListener("click", function(evt) {
          preventDefault(evt);
        });
        checkbox.type = "checkbox";
        const hashed = hash_key(data[self2.settings.valueField]);
        if (hashed && self2.items.indexOf(hashed) > -1) {
          checkbox.checked = true;
        }
        rendered.prepend(checkbox);
        return rendered;
      };
    });
    self2.on("item_remove", (value) => {
      var option = self2.getOption(value);
      if (option) {
        option.classList.remove("selected");
        UpdateCheckbox(option);
      }
    });
    self2.on("item_add", (value) => {
      var option = self2.getOption(value);
      if (option) {
        UpdateCheckbox(option);
      }
    });
    self2.hook("instead", "onOptionSelect", (evt, option) => {
      if (option.classList.contains("selected")) {
        option.classList.remove("selected");
        self2.removeItem(option.dataset.value);
        self2.refreshOptions();
        preventDefault(evt, true);
        return;
      }
      orig_onOptionSelect.call(self2, evt, option);
      UpdateCheckbox(option);
    });
  }

  // node_modules/tom-select/src/plugins/clear_button/plugin.ts
  function plugin_default2(userOptions) {
    const self2 = this;
    const options = Object.assign({
      className: "clear-button",
      title: "Clear All",
      html: (data) => {
        return `<div class="${data.className}" title="${data.title}">&#10799;</div>`;
      }
    }, userOptions);
    self2.on("initialize", () => {
      var button = getDom(options.html(options));
      button.addEventListener("click", (evt) => {
        if (self2.isDisabled) {
          return;
        }
        self2.clear();
        if (self2.settings.mode === "single" && self2.settings.allowEmptyOption) {
          self2.addItem("");
        }
        evt.preventDefault();
        evt.stopPropagation();
      });
      self2.control.appendChild(button);
    });
  }

  // node_modules/tom-select/src/plugins/dropdown_header/plugin.ts
  function plugin_default3(userOptions) {
    const self2 = this;
    const options = Object.assign({
      title: "Untitled",
      headerClass: "dropdown-header",
      titleRowClass: "dropdown-header-title",
      labelClass: "dropdown-header-label",
      closeClass: "dropdown-header-close",
      html: (data) => {
        return '<div class="' + data.headerClass + '"><div class="' + data.titleRowClass + '"><span class="' + data.labelClass + '">' + data.title + '</span><a class="' + data.closeClass + '">&times;</a></div></div>';
      }
    }, userOptions);
    self2.on("initialize", () => {
      var header = getDom(options.html(options));
      var close_link = header.querySelector("." + options.closeClass);
      if (close_link) {
        close_link.addEventListener("click", (evt) => {
          preventDefault(evt, true);
          self2.close();
        });
      }
      self2.dropdown.insertBefore(header, self2.dropdown.firstChild);
    });
  }

  // node_modules/tom-select/src/constants.ts
  var KEY_ESC = 27;
  var KEY_TAB = 9;
  var IS_MAC = typeof navigator === "undefined" ? false : /Mac/.test(navigator.userAgent);

  // node_modules/tom-select/src/plugins/dropdown_input/plugin.ts
  function plugin_default4() {
    const self2 = this;
    self2.settings.shouldOpen = true;
    self2.hook("before", "setup", () => {
      self2.focus_node = self2.control;
      addClasses(self2.control_input, "dropdown-input");
      const div = getDom('<div class="dropdown-input-wrap">');
      div.append(self2.control_input);
      self2.dropdown.insertBefore(div, self2.dropdown.firstChild);
      const placeholder = getDom('<input class="items-placeholder" tabindex="-1" />');
      placeholder.placeholder = self2.settings.placeholder || "";
      self2.control.append(placeholder);
    });
    self2.on("initialize", () => {
      self2.control_input.addEventListener("keydown", (evt) => {
        switch (evt.keyCode) {
          case KEY_ESC:
            if (self2.isOpen) {
              preventDefault(evt, true);
              self2.close();
            }
            self2.clearActiveItems();
            return;
          case KEY_TAB:
            self2.focus_node.tabIndex = -1;
            break;
        }
        return self2.onKeyDown.call(self2, evt);
      });
      self2.on("blur", () => {
        self2.focus_node.tabIndex = self2.isDisabled ? -1 : self2.tabIndex;
      });
      self2.on("dropdown_open", () => {
        self2.control_input.focus();
      });
      const orig_onBlur = self2.onBlur;
      self2.hook("instead", "onBlur", (evt) => {
        if (evt && evt.relatedTarget == self2.control_input)
          return;
        return orig_onBlur.call(self2);
      });
      addEvent(self2.control_input, "blur", () => self2.onBlur());
      self2.hook("before", "close", () => {
        if (!self2.isOpen)
          return;
        self2.focus_node.focus({ preventScroll: true });
      });
    });
  }

  // node_modules/tom-select/src/plugins/remove_button/plugin.ts
  function plugin_default5(userOptions) {
    const options = Object.assign({
      label: "&times;",
      title: "Remove",
      className: "remove",
      append: true
    }, userOptions);
    var self2 = this;
    if (!options.append) {
      return;
    }
    var html = '<a href="javascript:void(0)" class="' + options.className + '" tabindex="-1" title="' + escape_html(options.title) + '">' + options.label + "</a>";
    self2.hook("after", "setupTemplates", () => {
      var orig_render_item = self2.settings.render.item;
      self2.settings.render.item = (data, escape) => {
        var item = getDom(orig_render_item.call(self2, data, escape));
        var close_button = getDom(html);
        item.appendChild(close_button);
        addEvent(close_button, "mousedown", (evt) => {
          preventDefault(evt, true);
        });
        addEvent(close_button, "click", (evt) => {
          preventDefault(evt, true);
          if (self2.isLocked)
            return;
          if (!self2.shouldDelete([item], evt))
            return;
          self2.removeItem(item);
          self2.refreshOptions(false);
          self2.inputState();
        });
        return item;
      };
    });
  }

  // node_modules/tom-select/src/plugins/virtual_scroll/plugin.ts
  function plugin_default6() {
    const self2 = this;
    const orig_canLoad = self2.canLoad;
    const orig_clearActiveOption = self2.clearActiveOption;
    const orig_loadCallback = self2.loadCallback;
    var pagination = {};
    var dropdown_content;
    var loading_more = false;
    var load_more_opt;
    var default_values = [];
    if (!self2.settings.shouldLoadMore) {
      self2.settings.shouldLoadMore = () => {
        const scroll_percent = dropdown_content.clientHeight / (dropdown_content.scrollHeight - dropdown_content.scrollTop);
        if (scroll_percent > 0.9) {
          return true;
        }
        if (self2.activeOption) {
          var selectable = self2.selectable();
          var index = Array.from(selectable).indexOf(self2.activeOption);
          if (index >= selectable.length - 2) {
            return true;
          }
        }
        return false;
      };
    }
    if (!self2.settings.firstUrl) {
      throw "virtual_scroll plugin requires a firstUrl() method";
    }
    self2.settings.sortField = [{ field: "$order" }, { field: "$score" }];
    const canLoadMore = (query) => {
      if (typeof self2.settings.maxOptions === "number" && dropdown_content.children.length >= self2.settings.maxOptions) {
        return false;
      }
      if (query in pagination && pagination[query]) {
        return true;
      }
      return false;
    };
    const clearFilter = (option, value) => {
      if (self2.items.indexOf(value) >= 0 || default_values.indexOf(value) >= 0) {
        return true;
      }
      return false;
    };
    self2.setNextUrl = (value, next_url) => {
      pagination[value] = next_url;
    };
    self2.getUrl = (query) => {
      if (query in pagination) {
        const next_url = pagination[query];
        pagination[query] = false;
        return next_url;
      }
      pagination = {};
      return self2.settings.firstUrl.call(self2, query);
    };
    self2.hook("instead", "clearActiveOption", () => {
      if (loading_more) {
        return;
      }
      return orig_clearActiveOption.call(self2);
    });
    self2.hook("instead", "canLoad", (query) => {
      if (!(query in pagination)) {
        return orig_canLoad.call(self2, query);
      }
      return canLoadMore(query);
    });
    self2.hook("instead", "loadCallback", (options, optgroups) => {
      if (!loading_more) {
        self2.clearOptions(clearFilter);
      } else if (load_more_opt) {
        const first_option = options[0];
        if (first_option !== void 0) {
          load_more_opt.dataset.value = first_option[self2.settings.valueField];
        }
      }
      orig_loadCallback.call(self2, options, optgroups);
      loading_more = false;
    });
    self2.hook("after", "refreshOptions", () => {
      const query = self2.lastValue;
      var option;
      if (canLoadMore(query)) {
        option = self2.render("loading_more", { query });
        if (option) {
          option.setAttribute("data-selectable", "");
          load_more_opt = option;
        }
      } else if (query in pagination && !dropdown_content.querySelector(".no-results")) {
        option = self2.render("no_more_results", { query });
      }
      if (option) {
        addClasses(option, self2.settings.optionClass);
        dropdown_content.append(option);
      }
    });
    self2.on("initialize", () => {
      default_values = Object.keys(self2.options);
      dropdown_content = self2.dropdown_content;
      self2.settings.render = Object.assign({}, {
        loading_more: () => {
          return `<div class="loading-more-results">Loading more results ... </div>`;
        },
        no_more_results: () => {
          return `<div class="no-more-results">No more results</div>`;
        }
      }, self2.settings.render);
      dropdown_content.addEventListener("scroll", () => {
        if (!self2.settings.shouldLoadMore.call(self2)) {
          return;
        }
        if (!canLoadMore(self2.lastValue)) {
          return;
        }
        if (loading_more)
          return;
        loading_more = true;
        self2.load.call(self2, self2.lastValue);
      });
    });
  }

  // client/plugins/dropdown_footer/plugin.ts
  function plugin_default7(userOptions) {
    const self2 = this;
    const options = Object.assign({
      title: "Autocomplete Footer",
      footerClass: "mt-1 px-2 flex-wrap border-top dropdown-footer",
      html: (data) => {
        return '<div title="' + data.title + '" class="' + data.footerClass + '"></div>';
      }
    }, userOptions);
    self2.hook("after", "setup", () => {
      var footer = getDom(options.html(options));
      self2.dropdown.appendChild(footer);
    });
  }

  // client/django-tomselect.js
  import_tom_select_base.default.define("checkbox_options", plugin_default);
  import_tom_select_base.default.define("clear_button", plugin_default2);
  import_tom_select_base.default.define("dropdown_header", plugin_default3);
  import_tom_select_base.default.define("dropdown_input", plugin_default4);
  import_tom_select_base.default.define("remove_button", plugin_default5);
  import_tom_select_base.default.define("virtual_scroll", plugin_default6);
  import_tom_select_base.default.define("dropdown_footer", plugin_default7);
  window.TomSelect = require_tom_select_base();
})();
/*! Bundled license information:

tom-select/dist/js/tom-select.base.js:
  (*! @orchidjs/unicode-variants | https://github.com/orchidjs/unicode-variants | Apache License (v2) *)
  (*! sifter.js | https://github.com/orchidjs/sifter.js | Apache License (v2) *)

@orchidjs/unicode-variants/dist/umd/index.js:
  (*! @orchidjs/unicode-variants | https://github.com/orchidjs/unicode-variants | Apache License (v2) *)
*/
