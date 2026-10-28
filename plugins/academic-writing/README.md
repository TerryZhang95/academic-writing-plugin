# Academic Writing

Use the installed writing entrypoints for your selected text, references or figures.
After an update, refresh or restart Codex and open a new chat.

MIT License

Copyright (c) 2026 TerryZhang95

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Algorithm writing uses the algorithm entrypoint for section prose, pseudocode and checks. Experimental evaluation remains with Results.

## Content-guided writing

Text-writing tasks send the authorized passage and necessary plan to MCP for transient context analysis. The service automatically includes formula and notation rules when mathematics is present or planned, without a formulas flag. It does not run a model, retain manuscript content or log text. Generation and a separate review run in the current Codex session using the user’s account. A local scanner inventories displays and flags candidates for semantic review; its output is not a correctness verdict.

The updated client requires the service’s `context_preparation` capability. Light polish also checks the actual draft. Explicit editing limits are preserved; unresolved issues are reported separately from author prose. A passed review covers only the inspected content and does not prove scientific correctness.

For the first managed update from a client without the context files, use `scripts/manage.py update --confirm --expected-version 0.1.14` from the new downloaded bundle. The older updater rejects the expanded inventory. Native installations update through their original Codex installation surface. Released packages remain unchanged.

## Local execution and abbreviation review

MCP returns a scoped execution prompt and symbolic tasks; the current Codex session performs the file operations and review. Existing directories and user targets take precedence. New manuscript sections and plans use the supplied layout rules; wording polish does not move files or split sections.

Academic writing includes the full abbreviation checks. The local scanner keeps Abstract and body definitions separate, follows the final body reading order and reports unresolved macro/registry evidence. Full strict manuscript checks may create an internal abbreviation table from supported definitions; local polish does not create one automatically. Explicit read-only limits take precedence.

The bundled artifact checker compares actual files, authorized changes, references and the last checked text digests. Its evidence-consistent result confirms correspondence between artifacts and review records, not scientific correctness. Use the service's declared local_execution and abbreviation_review capabilities; missing support requires an upgrade rather than a silent fallback.
