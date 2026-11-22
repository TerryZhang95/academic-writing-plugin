# Public comparison format: academic-comparison-v2

This format describes data exchange and display, not rules for judging papers.
Python 3.10+ and the bundled comparison_io.py/comparison_render.py are required.
Use UTF-8 JSON. Unknown fields and duplicate keys/IDs are rejected. Limits:
2 MB JSON, 200 sources/rows/columns, 20 excerpts/cell, 600 characters/excerpt.

Required root fields: schema_version=2, mode=coverage|method, title, label,
sources, columns, papers. Optional: synthetic (boolean; labels all previews),
verified_cite_keys (unique already verified citation keys). IDs match
[A-Za-z0-9][A-Za-z0-9_-]{0,63}. Table labels and citation keys permit ASCII
letters/digits/colon/underscore/hyphen; labels begin with a letter. Citation-key
declarations record user verification, not external verification by the helper.

Each source requires id, title, version, availability=full|partial|unavailable,
and read_scope (actual inspected pages/sections, or an explicit unread statement).
Optional: public HTTPS url without credentials/query/fragment, sha256 (64 lowercase
hex characters), page_count (positive integer). Real local paths belong only in a
separate private source map and must never appear in shareable outputs.

Each column requires id, label, kind and definition; optional group names must
form consecutive runs. Coverage kinds: coverage/text. Method: binary/value/text.
Each paper requires id, label, nonempty unique source_ids and cells (object keyed
by every column ID exactly once). Optional cite_key must be in verified_cite_keys;
is_ours is a boolean highlighting flag only.

Each cell requires status, reason and evidence (list). Assessed cells require
basis=explicit|inference and at least one excerpt. Unknown cells can have no
excerpts. An excerpt requires source_id registered to that row, locator, quote;
optional pdf_pages are physical positive PDF pages bounded by source page_count.
Unavailable sources cannot supply excerpts. Evidence is a short original passage,
not a generated synopsis. A quote match/hash check is not a semantic check.

| Kind | Assessed status | Display |
|---|---|---|
| coverage | full / partial / none | ● / ◐ / ○ |
| binary | yes / partial / no | ● / ◐ / ○ |
| value or text | value | plain-text value |
| all | unknown / nr / na | ? / NR / N/A |

Value status requires a string value; numeric value-kind cells also require unit
and conditions. Other optional cell fields: conditions (string), notes (nonempty
string list), review. Conditions/notes become numbered publication notes and do
not alter the support glyph. Negative no/none/nr with basis=inference requires
review with nonempty sections/terms lists and note. Numeric value-kind nr also
requires this review regardless of basis. The helper checks presence,
not adequacy of searches. Detailed judgment rules come from scoped private MCP
guidance. Do not use a 50% numerical interpretation for the partial glyph.

## Requests

Use comparison_context only with workflow=literature_comparison. Required mode
and goal; optional sources (id/title/version/availability/read_scope), columns
(id/label/kind/definition), evidence (source_id/column_id/locator/quote/reason),
summary (string), batch (index/total/source_ids). Every listed record field is
required. Limits: 24,000 UTF-8 bytes total, 40 records/list, 1,000 characters per
record value, goal 2,000, summary 4,000. Logical IDs only. Each batch retains full
column definitions and records covered source IDs; track complete coverage locally.
Response execution_context identifies this contract and local semantic-review
requirement. The service never executes source/semantic review.

## Export and migration

Run comparison_render.py input.json --criteria criteria.md --out unused-directory.
The new directory contains canonical comparison.json, criteria.md, comparison.md,
comparison.tex, comparison-standalone.tex, evidence.md. Existing directories are
never replaced. Markdown links each cell to evidence; both TeX outputs carry the
same values/conditions. Source strings are escaped as data. The TeX fragment uses
verified keys; standalone uses row labels and includes the required glyph macro.
Criteria is user-written project Markdown; keep it free of private rules/paths.

V1 is rejected explicitly. To convert, preserve source/row/column IDs and evidence,
set schema_version=2, replace location with public url or omit it, add availability
and actual read_scope, and declare only verified citation keys. Convert legacy
conditional to yes/full or partial according to its explicit support_level, retain
conditions, then remove support_level. Never guess missing support. Revalidate and
review converted outputs. This format does not promise byte-identical legacy output.

Optional PDF transcription check: run comparison_sources.py comparison.json
--source-map private-map.json --report unused-report.json. The map is a local JSON
object of source IDs to PDF paths; never share or upload it. Install pdftotext
separately if needed. Each excerpt needs pdf_pages and its source needs sha256.
Missing sources/pages/hashes, changed hashes and mismatched excerpts remain explicit
failures/pending checks. A text-match checks transcription/location only.
