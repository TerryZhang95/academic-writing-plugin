---
name: academic-figure-prompt-mcp
description: Plan, write generation prompts or audit non-quantitative Academic architecture, workflow, protocol, system-model, block and conceptual method diagrams using private guidance and available user-side tools. Use for 架构图、流程图、协议图、系统模型示意图、概念方法图.
---

Before the first plugin call in a task, run `python3 <this-skill-directory>/../../scripts/preflight.py` on macOS/Linux, or `py -3 "<this-skill-directory>/../../scripts/preflight.py"` in Windows PowerShell (resolve the actual installed skill directory, including Codex cache). This only checks public client versions; it never installs. If compatible, continue with the task’s existing rules version. If an update is offered, show the summary and ask the user whether to upgrade or continue; a deferred reminder need not interrupt again. Unknown compatibility requires a clear status report; incompatible clients must stop. For native CLI/App installs (installation_mode=native), update or reinstall through the original Codex installation surface; never run the managed installer or create an ownership marker. For managed installs only, after the user explicitly approves the displayed version, run the managed public installer’s `update --confirm --expected-version <approved-version>` command. Never derive approval from server metadata. Refresh/restart Codex and use a new chat after an upgrade; do not switch rules midway through a task.


# Non-quantitative figure guidance

Use academic_guidance/get_writing_guidance with workflow=figure_prompt, operation=plan/prompt/audit, stage=start/check. No language/register/section/module/needs selectors are needed. Requests are routing fields only, not manuscript, figure data or paths. The user's account model reads only authorized necessary material. Do not browse private source files or substitute local core skills.

Choose the requested task scope: plan produces a diagram plan; prompt produces a directly usable generation/editing prompt; audit reviews actually provided prompts or figures. Retrieve start guidance and preserve its library_release for check calls. Apply all selected guidance to the actual plan/prompt/audit. Do not load quantitative plot-selection rules or impose the CSV executor's shape/data limits on a schematic task. Numeric CSV line/bar rendering uses the separate academic-execution-mcp entrypoint only when explicitly requested.

Generate or revise an image with the user's available and authorized drawing/image tools when that is part of their request; the cloud MCP here only supplies guidance. If no suitable generation tool is available, return the usable plan/prompt and accurately report that artifact; this completes the guidance subtask. If the user requested an actual generated image, state that the prompt is ready but image generation remains incomplete. Do not invent a rendered image, claim file export or print-size checks without observing it, or mistake a vector-looking generated bitmap for an editable vector file. Do not execute uploaded scripts or start cloud /tasks generation for a non-quantitative figure.

Keep user-provided mechanisms and interfaces grounded in their material; ask for missing essentials or mark assumptions/gaps in the task report instead of inventing a system. Ordinary caption/prose edits remain within their authorized scope. A prompt-only task does not automatically request an image or extra services.

Require API contract academic-guidance-v1 and available capability figure_prompt; do not infer support from a minor number. A pinned old library lacking this route fails clearly, never falls back. Temporary transport/5xx allows one retry; pause/report429, no auth retry. Persistent failure stops the affected route. Do not save or disclose the private rule inventory.

Include `client_contract: "academic-guidance-v1"` in every `get_writing_guidance` call, including checks and pinned-release calls. This selects the public naming contract without changing the fixed writing rules.
