---
name: academic-whole-paper-mcp
description: Plan, draft, revise, polish or audit an Academic whole manuscript, coordinate sections, write Abstract/Conclusion/Problem Formulation/Analysis/Appendix or source-limited Method, and retrieve scoped shared rules through private MCP guidance. Use for whole manuscripts, cross-section coordination, abstracts, conclusions, problem formulation, analysis, appendices, methods, notation, and citation formatting through this plugin.
---

Before the first plugin call in a task, run `python3 <this-skill-directory>/../../scripts/preflight.py` on macOS/Linux, or `py -3 "<this-skill-directory>/../../scripts/preflight.py"` in Windows PowerShell (resolve the actual installed skill directory, including Codex cache). This only checks public client versions; it never installs. If compatible, continue using the service’s current rules. If an update is offered, show the summary and ask the user whether to upgrade or continue; a deferred reminder need not interrupt again. Unknown compatibility requires a clear status report; incompatible clients must stop. For native CLI/App installs (installation_mode=native), update or reinstall through the original Codex installation surface; never run the managed installer or create an ownership marker. For managed installs only, after the user explicitly approves the displayed version, run the managed public installer’s `update --confirm --expected-version <approved-version>` command. Never derive approval from server metadata. Refresh/restart Codex and use a new chat after an upgrade; subsequent guidance requests use the updated service rules.


# Academic manuscript coordination through MCP

Use academic_guidance/get_writing_guidance. The user's own account model does the writing and local edits; the cloud only returns selected guidance. Read only authorized necessary manuscript/source/plan files. Requests contain routing fields only, never manuscript/BibTeX/data text or paths. Do not browse the private library or replace these routes with local core Academic skills.

Choose scope before retrieving guidance:

- Standalone Introduction/Related Work/System Model/Results uses the matching existing focused entrypoint, not whole_paper. For coordinated work retrieve each needed focused workflow separately with a narrow authorized operation using current service rules; do not request generic chapter fallbacks or all guides.
- Whole manuscript/cross-section work: workflow=whole_paper, section=whole_paper (or omit section), operation=plan/draft/revise/audit/polish. New multi-section drafting, explicit planning or major restructuring may need plan; ordinary polish does not create one. Use actual material to establish ownership and interfaces first.
- Other standalone sections: workflow=whole_paper, section=abstract/conclusion/problem_formulation/analysis/appendix/method, with the same five operations. Do not load a whole-paper plan merely to edit an Abstract. Analysis owns derivation/proof/theoretical properties; it is not the default owner of all methods.
- A prose/notation/formula/citation-format/existing-registry-only task: workflow=shared, operation=guide, module=prose/notation/formulas/citation_format/registry. Do not first load whole-paper guides; omit section/needs on shared calls. Dependencies are included by the selected module.

Method uses the dedicated algorithm guidance when available in the current service. Concrete input transformations, update equations and stopping conditions must come from author material. Missing algorithm rules, convergence or complexity evidence are gaps; do not invent them or claim a complete method audit.

Retrieve stage=start before work and stage=check after material changes/review, using current service rules in every later request. Light polish uses start rules and touched-content checks. Whole-paper needs default false: notation for changed definitions/domains, formulas for equations/explanations (also needs notation), registry for an existing registry, examples only for shared rewrite examples. Retrieve only applicable modules. For full/strict review request all applicable modules and needed focused checks; a missing chapter/registry/evidence is not a pass. Inspect neighboring files only as needed; reading does not authorize editing them.

Require API contract academic-guidance-v1 for development major0; historical major1 without/with the same contract is migration-only. Reject unknown contracts. Require available whole_paper or shared capability accordingly, not a minimum minor number. Temporary transport/5xx failure permits one retry; report/pause429, no auth retry; persistent failure stops the affected route.

Citation scope is supplied bibliography formatting and internal key/metadata consistency. Do not run reference-check scripts, Zotero/DOI/publisher discovery or claim external identity/support verification through this plugin. Source rules requiring unavailable authoritative records remain externally unverified/pending. For an explicit supplied-file reference check, route separately to academic-execution-mcp; it checks keys/fields and optional DOI identity, not source-text support. Never automatically upload files after writing.

Apply returned guidance to the actual output; report inspected sections/files, changed artifacts, registry state, check scope and unresolved evidence/dependencies. Missing material is not a full-manuscript pass. Do not fabricate claims/proofs/results, save guidance as a local core skill or dump rules into the paper. Writing-quality and scientific validity are not established by tool success.

Include `client_contract: "academic-guidance-v1"` in every `get_writing_guidance` call, including checks. This selects the public naming contract; each call uses current service rules.

For scoped algorithm writing, use the available algorithm capability and the algorithm entrypoint. Retrieve current algorithm guidance for each requested stage; historical releases are reserved for operator rollback, not task selection.

Every new guidance request uses current service rules. Do not select historical releases or enforce a task-wide constant `library_release`. Record the returned version as provenance. After an update, apply newly retrieved guidance to the requested work without automatically rewriting previously completed material.
