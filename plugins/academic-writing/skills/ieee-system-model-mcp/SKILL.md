---
name: ieee-system-model-mcp
description: Plan, draft, revise, polish, translate or audit a scoped IEEE System Model through private MCP guidance. Use for 系统模型, topology, channel, protocol, traffic, assumptions and outputs used by later analysis requested through this plugin.
---

Before the first plugin call in a task, run `python3 <this-skill-directory>/../../scripts/preflight.py` on macOS/Linux, or `py -3 "<this-skill-directory>/../../scripts/preflight.py"` in Windows PowerShell (resolve the actual installed skill directory, including Codex cache). This only checks public client versions; it never installs. If compatible, continue with the task’s existing rules version. If an update is offered, show the summary and ask the user whether to upgrade or continue; a deferred reminder need not interrupt again. Unknown compatibility requires a clear status report; incompatible clients must stop. For native CLI/App installs (installation_mode=native), update or reinstall through the original Codex installation surface; never run the managed installer or create an ownership marker. For managed installs only, after the user explicitly approves the displayed version, run the managed public installer’s `update --confirm --expected-version <approved-version>` command. Never derive approval from server metadata. Refresh/restart Codex and use a new chat after an upgrade; do not switch rules midway through a task.


# IEEE System Model through MCP

Use this plugin's ieee_guidance server and get_writing_guidance tool. The user's client model performs writing using the user's own account. Read only the specified manuscript and necessary source/interface material. Send routing fields only, never manuscript text or paths. Do not substitute locally installed core IEEE skills or browse private service files.

Select workflow=system_model and the operation matching the authorized task:

- plan: establish model boundaries, dependencies and a durable plan when requested.
- draft: create a section from supported author material.
- revise: substantive revision or translation of an existing model.
- polish: wording-only changes preserving model structure, mathematical meaning and claims.
- audit: inspect evidence and interfaces, report issues without editing unless authorized.

Explicit wording-only/structure-preservation constraints take precedence over broad revision. Whole-paper work, optimization programs, algorithms, proofs and Results are outside this route. Reading a neighboring section to verify an interface does not authorize editing it.

Retrieve stage=start before working. Request stage=check after plan/draft/revise/audit, keeping the returned non-null library_release on subsequent calls; light polish uses the start checks. Missing pinned snapshots require restarting, never a silent switch. Use needs.notation for definitions/domains, needs.formulas for equations or their explanations, needs.registry only for an existing registry, and needs.examples for optional shared rewrite examples. Request only applicable modules. A source-guided model construction involving equations requires formulas and notation; prose-only preservation does not.

Require api_contract=ieee-guidance-v1 for development API major 0. Historical API major 1 without a contract remains accepted for migration only; reject other/unknown contracts, including any explicit unknown contract on major 1. Use explicit available capability declarations; never infer compatibility or chapter support from minor/patch numbers. Require available system_model capability. Missing capability or failed guidance means explain the upgrade/failure and stop this route, without falling back to Introduction or a local skill. Retry a temporary transport/5xx failure once; pause/report 429; do not retry authentication failures. A null/missing release is unversioned and cannot claim a fixed snapshot.

Use supplied evidence or authorized tools in the user's client. The server does not search literature, inspect user files, run models or verify physics. Do not fabricate missing nodes/topology, channel/protocol/traffic assumptions or outputs needed by later analysis (for example SINR, success probability or rate) as established author facts. Identify unresolved dependencies and continue only supported portions; if a missing dependency determines the structure, stop that dependent drafting and request the necessary material. Apply all retrieved shared rules and completion checks to the actual output. Tool success does not mean the model passed a scientific audit.

Return the requested text/plan/files or audit findings, actual check scope/status, registry status and unresolved evidence or downstream interfaces. Do not save guidance as local core rules or include it in the manuscript.
