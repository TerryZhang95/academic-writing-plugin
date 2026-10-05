---
name: academic-algorithm-mcp
description: Write, revise, polish or audit an Academic Method/Algorithm section through MCP. Use when requests concern algorithm sections, method sections or pseudocode; experimental evaluation belongs to Results.
---


Before the first plugin call in a task, run `python3 <this-skill-directory>/../../scripts/preflight.py` on macOS/Linux, or `py -3 "<this-skill-directory>/../../scripts/preflight.py"` in Windows PowerShell (resolve the actual installed skill directory, including Codex cache). This only checks public client versions; it never installs. If compatible, continue using the service’s current rules. If an update is offered, show the summary and ask the user whether to upgrade or continue; a deferred reminder need not interrupt again. Unknown compatibility requires a clear status report; incompatible clients must stop. For native CLI/App installs (installation_mode=native), update or reinstall through the original Codex installation surface; never run the managed installer or create an ownership marker. For managed installs only, after the user explicitly approves the displayed version, run the managed public installer’s `update --confirm --expected-version <approved-version>` command. Never derive approval from server metadata. Refresh/restart Codex and use a new chat after an upgrade; subsequent guidance requests use the updated service rules.


# Academic Algorithm through MCP

Use this plugin's academic_guidance server and get_writing_guidance tool with
workflow=algorithm and client_contract="academic-guidance-v1". The user's model
writes using the user's own account. Send routing fields only, never manuscript
text or paths. Read authorized author material and necessary problem interfaces
in the client; do not install core skills or browse private service files.

Select operation=plan for requested planning, draft for a supported new section,
revise for substantive edits or translation, polish for wording-only edits, or
audit for findings without edits unless authorized. Obtain stage=start; after
plan/draft/revise/audit request stage=check using current service rules.
Polish uses the light checks without expanding scope. The returned library_release
records the version actually used; do not send it to select historical rules.
Use needs.notation for changed definitions, needs.formulas for equations, and
needs.registry only for affected existing registries. Request only needed modules.

Require the explicit available algorithm capability and the supported
academic-guidance-v1 contract (API major 0; historical major 1 migration follows
the existing plugin contract). If the current service lacks algorithm capability, explain the missing capability
and stop rather than falling back to a different section or local skill.
Retry a temporary transport/5xx error once; report/pause on 429; do not retry
authentication failures.

Apply retrieved writing and algorithm-block rules to the actual output. Preserve
existing structure, mathematical meaning, labels and algorithm package for polish.
Missing initialization, updates, stopping conditions or outputs remain specific
author decisions; never invent steps, guarantees, proofs or numerical results.
Experimental settings and measured performance belong to Results. A neighbor
read does not authorize rewriting it. The server supplies guidance, not a solver,
compiler or verification executor. Return the requested artifact, actual check
scope, name/registry status and concrete gaps; tool success is not scientific
or writing-quality acceptance. Do not save guidance as local core rules.

Every new guidance request uses current service rules. Do not select historical releases or enforce a task-wide constant `library_release`. Record the returned version as provenance. After an update, apply newly retrieved guidance to the requested work without automatically rewriting previously completed material.
