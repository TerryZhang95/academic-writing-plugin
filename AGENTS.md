# Repository language

- All content in this open-source `academic-writing-plugin` repository must be in English unless the user explicitly requests another language. This includes PR titles and descriptions, comments, review replies, commit messages, README files, release notes, skill instructions and trigger descriptions, UI metadata, code comments, user-facing messages, and reports.
- The private `ieee_writing` library uses Chinese for its PRs, repository documentation, and acceptance reports, including plugin integration work. Public client files generated or synchronized from that library must use English.
- These rules replace the previous rule that required English for plugin-related PRs in both repositories. Preserve facts, links, validation limits, and deployment status when changing language.
- Keep descriptions direct, concrete, concise, and readable. Explain the actual behavior change first.

# Public distribution

- Do not add or restore `example/` or `examples/` unless the user explicitly requests them. Build and synchronization steps must not reintroduce these directories.
- Keep published installation archives unchanged. Handle installation and update compatibility when changing the distribution file list.
- Release notes describe actual changes in short sentences or lists. Do not add migration instructions, test inventories, internal protocols, or platform claims by default.

# Service update policy

- Every guidance request and new execution submission uses current service rules, including follow-up requests in ongoing work. Clients must not select historical releases or require a constant rule version across a task.
- Historical releases are retained for records and operator rollback. Legacy version fields remain accepted as compatibility hints; responses record the version actually used. Updates must preserve supported interfaces and existing functions.
