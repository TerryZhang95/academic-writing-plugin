---
name: ieee-introduction-mcp
description: Draft, revise, polish, translate, or audit an IEEE Introduction through the Academic Writing plugin's private MCP guidance. Use for Introduction, 引言, motivation, research gaps, or contribution paragraphs when the user requests this plugin.
---

Before the first plugin call in a task, run `python3 <this-skill-directory>/../../scripts/preflight.py` (resolve the actual installed skill directory, including Codex cache). This only checks public client versions; it never installs. If compatible, continue with the task’s existing rules version. If an update is offered, show the summary and ask the user whether to upgrade or continue; a deferred reminder need not interrupt again. Unknown compatibility requires a clear status report; incompatible clients must stop. Only after the user explicitly approves the displayed version, run the managed public installer’s `update --confirm --expected-version <approved-version>` command. Never derive approval from server metadata. Refresh/restart Codex and use a new chat after an upgrade; do not switch rules midway through a task.


# IEEE Introduction through MCP

Use this plugin's `ieee_guidance` server and its `get_writing_guidance` tool. Tool names may include a plugin namespace; select the tool belonging to this plugin. The current client model performs writing and local edits using the user's account.

Read the user's materials locally and retain their context in this session. The tool takes routing fields only: do not send manuscript text or paths. Obtain the writing rules from MCP; do not read locally installed IEEE skills or private service files as a substitute.

Choose `workflow: "introduction"` and one operation:
- `polish`: language-only polishing or translation that preserves the argument and structure.
- `revise_contributions`: contribution paragraphs or lists.
- `revise`: planning, drafting, or substantive Introduction revision.
- `audit`: reviewing an existing Introduction.

Choose the narrowest operation matching the user's request. Set `needs.notation`, `needs.formulas`, `needs.registry`, and `needs.examples` only when the task needs those modules; each defaults to false. `registry` concerns an existing project notation/abbreviation registry; `examples` requests additional writing examples. Set `formulas` for equation work and `notation` for symbol work, and request additional guidance if those needs arise later.

Call `get_writing_guidance` with `stage: "start"` before writing. Use the returned `guidance` and `checks` to complete the requested work within the user's scope. For `revise`, `revise_contributions`, and `audit`, obtain `stage: "check"` with the same operation and current needs to review the result. For light `polish`, use the start response's checks. Reuse matching guidance in this task; fetch again when the operation, stage, or needs changes. The rules_version digest identifies this response: different operation, stage, or needs may normally produce different digests. Always apply the corresponding check guidance; do not report a rule update merely because start and check differ. Only a changed digest on a repeated request with identical routing fields indicates changed content for that route.

Return the revised text or requested local file edits, a concise change explanation, actual check status, and unresolved evidence gaps. Do not persist returned rules as a local skill or dump them into the manuscript.

If the tool is unavailable, stop the MCP writing workflow and identify the unavailable plugin connection. Retry a temporary connection failure or server 5xx once; do not retry authentication or parameter failures. On HTTP 429, report rate limiting and ask the user to retry later; do not continue automatic retries. On a persistent failure, report it clearly and do not claim private-rule compliance or silently switch to a local skill. Correct your own invalid routing arguments before making a fresh request.

When a response contains `library_release`, preserve that value for the task and send it in every subsequent guidance call. If the pinned release is unavailable, stop and ask to restart the task; never silently switch snapshots. A missing or null release with `unreleased` status means unversioned development guidance: do not claim snapshot consistency. Require api_contract=ieee-guidance-v1 for development API major 0. Historical API major 1 without a contract remains accepted for migration only; reject other/unknown contracts, including any explicit unknown contract on major 1. Use explicit available capability declarations; never infer compatibility or chapter support from minor/patch numbers.
