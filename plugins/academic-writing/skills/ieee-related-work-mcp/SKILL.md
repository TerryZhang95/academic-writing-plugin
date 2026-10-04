---
name: ieee-related-work-mcp
description: Plan, revise, polish, translate, or audit a scoped IEEE Related Work section through the Academic Writing plugin's private MCP guidance. Use for 相关工作, research-track organization and prior-work evidence comparisons requested through this plugin.
---

Before the first plugin call in a task, run `python3 <this-skill-directory>/../../scripts/preflight.py` on macOS/Linux, or `py -3 "<this-skill-directory>/../../scripts/preflight.py"` in Windows PowerShell (resolve the actual installed skill directory, including Codex cache). This only checks public client versions; it never installs. If compatible, continue with the task’s existing rules version. If an update is offered, show the summary and ask the user whether to upgrade or continue; a deferred reminder need not interrupt again. Unknown compatibility requires a clear status report; incompatible clients must stop. For native CLI/App installs (installation_mode=native), update or reinstall through the original Codex installation surface; never run the managed installer or create an ownership marker. For managed installs only, after the user explicitly approves the displayed version, run the managed public installer’s `update --confirm --expected-version <approved-version>` command. Never derive approval from server metadata. Refresh/restart Codex and use a new chat after an upgrade; do not switch rules midway through a task.


# IEEE Related Work through MCP

Use this plugin's `ieee_guidance` server and `get_writing_guidance` tool. The user's current client model performs writing and local edits using the user's account. Read only the local manuscript and source material needed for the user's task. Send routing fields only; never upload manuscript text or paths in a guidance request. Obtain rules from MCP, without substituting locally installed IEEE skills or browsing private service files.

Choose `workflow: "related_work"` and the narrowest operation matching the request:

- `polish`: local wording or translation, preserving structure and technical meaning.
- `revise`: planning from supplied evidence, drafting or authorized structural revision.
- `audit`: scoped argument/evidence review; apply edits only if requested.

Select by the requested scope, not by the word "polish" alone. A request to repair overall logic, organization, or readability uses `revise` when structural work is authorized, even if the user calls it polishing. Explicit instructions to preserve structure or limit changes to wording take precedence: use `polish` and report wider issues separately. Do not silently expand the requested passage or edit neighboring sections.

This route owns a dedicated Related Work section/subsection. Brief prior-work comparisons inside Introduction use the Introduction entrypoint. Whole-paper coordination is not yet connected.

Call with `stage: "start"` before working. Use returned guidance and checks. For revise and audit, request `stage: "check"` afterward with the same workflow, operation and task pin; for light polish, use the start checks. `needs` flags default to false: use notation/formulas for mathematical changes, registry for project notation/abbreviation maintenance, and examples for optional fictional chapter worked examples plus shared sentence examples. Retrieve added needs only when they arise.

Preserve the returned non-null `library_release` in all later requests in the task. Missing pinned releases require restarting; never silently switch snapshots. Null/missing metadata means unversioned guidance and cannot guarantee a fixed task. Require api_contract=ieee-guidance-v1 for development API major 0. Historical API major 1 without a contract remains accepted for migration only; reject other/unknown contracts, including any explicit unknown contract on major 1. Use explicit available capability declarations; never infer compatibility or chapter support from minor/patch numbers. Require available `related_work` capability. If the service lacks these or rejects this workflow, explain that Related Work requires a service upgrade and stop this route; do not switch to Introduction or a local skill. Older servers remain usable through the Introduction entrypoint only.

The `rules_version` identifies one response; operation/stage/needs differences normally change it. Apply the appropriate check guidance instead of inferring a library update from different start/check digests.

Literature search and bibliography tools are optional user-client capabilities, not included or executed by this server. Use supplied evidence when sufficient; perform scoped discovery only when authorized and suitable tools exist. If unavailable, finish only supported work and disclose missing verification. Do not imply original sources, bibliographic identity or coverage were checked from titles/notes alone. Never insert the teaching examples as real papers.

Before returning, compare the actual draft against all retrieved guidance and applicable checks, including selected shared prose and mathematical rules. Correct supported deviations within the authorized scope; identify unresolved deviations explicitly. A successful MCP request alone does not establish that the draft passed these checks.

Return the requested text or file edits, brief changes, actual check status and unresolved evidence limits. Do not save returned rules as a local skill or dump them into the manuscript. Retry temporary transport/5xx failure once; HTTP 429 requires pausing and reporting rate limiting. Do not retry auth failures or continue after persistent tool failure. Correct invalid routing before a new request. Report unavailable capability accurately; do not claim rule compliance without a successful response.
