---
name: academic-results-mcp
description: Plan, draft, revise, polish, translate or audit an Academic Results/Evaluation section, caption or supplied quantitative figure using private MCP guidance. Use for Results, simulation results, performance evaluation, experimental results and result captions through this plugin.
---

Before the first plugin call in a task, run `python3 <this-skill-directory>/../../scripts/preflight.py` on macOS/Linux, or `py -3 "<this-skill-directory>/../../scripts/preflight.py"` in Windows PowerShell (resolve the actual installed skill directory, including Codex cache). This only checks public client versions; it never installs. If compatible, continue with the task’s existing rules version. If an update is offered, show the summary and ask the user whether to upgrade or continue; a deferred reminder need not interrupt again. Unknown compatibility requires a clear status report; incompatible clients must stop. For native CLI/App installs (installation_mode=native), update or reinstall through the original Codex installation surface; never run the managed installer or create an ownership marker. For managed installs only, after the user explicitly approves the displayed version, run the managed public installer’s `update --confirm --expected-version <approved-version>` command. Never derive approval from server metadata. Refresh/restart Codex and use a new chat after an upgrade; do not switch rules midway through a task.


# Academic Results through MCP

Use academic_guidance/get_writing_guidance with workflow=results. The user's own client account supplies the model; the cloud returns guidance without running a model. Read only the requested manuscript and necessary supplied/authorized figures, tables, data, settings or calculations. Send routing fields only, never manuscript/data content or paths. Do not replace this route with local core Academic skills or browse private service files.

Use the narrowest authorized scope:

- plan/draft/revise/audit/polish: Results body planning, supported drafting, substantive revision, review, or wording-only editing. Translation follows polish/revise according to preservation constraints.
- caption: caption-only writing/editing/review; do not load body, figure selection or rendering guidance.
- figure_plan: selection/design decisions from supplied evidence; output a plan, not a rendered figure.
- figure_render: explicitly requested quantitative plotting with available user-side tools. Inspect only named arrays or CSV/TSV/JSON/Excel inputs, selected columns/sheets/ranges, using safe data readers (no macros, uploaded scripts or evaluation of expressions). Get selection/style/export guidance, choose a justified chart, render with authorized tools, inspect the actual saved image and save to a new output location. Do not automatically install missing dependencies; report the specific unavailable tool/format. This does not authorize simulations, fitting, unrelated data access, manuscript/caption edits or hidden sheets. Data/code stay in the client; no upload to guidance. Use the existing execution entry only when the user chooses its fixed CSV line/bar cloud task.
- figure_audit: inspect supplied figures, chart code or materials against presentation checks; report issues without running plotting or simulation. It does not authorize caption/body edits or figure redesign. Retrieve caption or figure_plan guidance separately only if that additional scope is requested.

Preserve explicit wording-only and structure constraints: polish does not replan the section, redesign figures or collect new evidence; report wider issues separately. A request covering several scopes may need separate scoped calls with the same library pin; do not silently broaden file edits. Proofs, conceptual diagrams, cloud plotting/data executors, literature verification and whole-paper coordination are outside this route. An explicit figure_render request authorizes the necessary user-side plotting tools when available; other requests require separate authorization. do not imply they are bundled or run by the service.

Retrieve stage=start before work. Request stage=check after material work/review; light polish uses start checks. Keep returned non-null library_release for every later call. Missing pins require restarting, never switching silently. Ask for applicable needs.notation/formulas for mathematical changes, registry only for an existing registry, examples only for optional shared rewrites. Formula changes also need notation; prose preserving math does not. Require api_contract=academic-guidance-v1 for development API major0; historical major1 without/with the same contract is migration-only. Reject unknown contracts. Require declared available results capability, not a minimum minor number.

Use only inspected or supported evidence. Missing plots, values or comparator conditions require a concrete gap; do not invent trends, gains, baselines, mechanisms, uncertainties or successful validation. Continue supported portions and disclose verification limits. Compare output against all retrieved guidance and applicable checks; a successful tool response does not establish scientific correctness or model-quality acceptance.

Return requested artifacts/text/plan/audit, actual checks and evidence gaps. Do not dump returned guidance into manuscripts or save it as a local core skill. Retry temporary transport/5xx failure once; report/pause429, do not retry auth failures. Correct invalid routing before requesting again; persistent failure stops that route.

Include `client_contract: "academic-guidance-v1"` in every `get_writing_guidance` call, including checks and pinned-release calls. This selects the public naming contract without changing the fixed writing rules.
