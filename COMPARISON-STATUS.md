# Literature comparison implementation status

Client 0.1.15 candidate adds coverage and method comparison tables through the
academic-literature-comparison-mcp entrypoint. The current published release is
0.1.14; candidate source availability does not mean the service is deployed or a
new client release is published. The entrypoint checks both the tool schema and
an explicit available capability before using the new route.

The plugin includes its public v2 data format, structural validator, deterministic
Markdown/LaTeX exports and optional PDF transcription checks. One installation
provides the entrypoint and helpers. Python 3.10+ is required and is not bundled.
PDF transcription checks also require pdftotext. LaTeX compilation is optional.

The current agent completed two real-paper comparisons using four fixed arXiv v1
PDFs. Coverage: three assessed cells and one explicit unknown. Method: four
assessed cells. Seven short excerpts matched their recorded physical PDF pages
and source hashes. Both standalone tables compiled and received visual inspection.
These results cover the inspected sections, not full-paper assessments.

Content acceptance used the current agent. It is not a claim that a fresh model
with no prior private-library exposure performed an independent task. Native CLI
installation/discovery checks and managed update/rollback tests are separate from
content acceptance; desktop UI and Windows runs need their own recorded evidence.
No external model invocation is required to use the plugin in the current chat.

Source authenticity, semantic entailment, comparison fairness and negative-search
adequacy require local reading and review. Helper success and service rule
retrieval do not establish those conclusions. The public package contains the
interface and execution steps; task-specific guidance is retrieved from the
service, without a private-library browser or full-guide export.

For a managed upgrade from 0.1.14, use the installer in the newly downloaded
candidate/release bundle. The old updater deliberately rejects the expanded file
inventory. Native App/CLI installations update through their original channel.
The new installer checks the exact entrypoint set for the installed version, so a
rollback can validate the previous nine-entrypoint package as well as the new
ten-entrypoint package. It also checks that comparison helpers match the cached
plugin files. Published archives remain unchanged. After review, deploy a compatible service
before publishing the corresponding client.

## Review fixes — 2026-11-23

LaTeX exports now budget the full column padding against the surrounding
linewidth. Tables split into at most six comparison columns per part by default;
--columns-per-part accepts 1–6 for narrower layouts. Parts preserve all columns,
repeat paper labels, wrap group headers and keep global condition-note numbers.
The bundled comparison_layout.py provides the same display logic to fragment
and standalone exports without adding an external Python package.

The two-row, twelve-feature regression now retains F1–F12 across two readable
parts. Compilation checks also cover ordinary/two-column article fragments,
long group names, mixed states and the four previously inspected real-paper
artifacts. Compiler diagnostics, extracted PDF text/bounds and visual review are
separate from structural export. Unbreakable text, oversized floats and missing
characters are failures requiring adjustment; a zero compiler exit code alone
does not establish layout acceptance. A dedicated Linux CI job installs LaTeX and
Poppler and cannot silently skip these compilation regressions.

Installation guidance now distinguishes nine entrypoints in published 0.1.14
from ten in candidate 0.1.15. The candidate version is unchanged and remains
unpublished. Scientific assessments, source evidence and private guidance are
unchanged by these display fixes.
