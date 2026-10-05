# Plugin pull request language

- Use English for every plugin-related pull request unless the user explicitly requests another language. This applies to the public plugin repository and plugin-related changes in the private library.
- Write PR titles, descriptions, comments, review replies, and acceptance reports attached to the PR in English. Use English for new commit messages for plugin changes as well.
- This specific rule takes precedence over a general preference for Chinese PR text in the private library or a writing skill. Preserve facts, links, validation limits, and deployment status when translating existing PR text.
- Keep user-facing descriptions direct, concrete, concise, and readable. Explain the actual behavior change first.

# Public distribution

- Do not add or restore `example/` or `examples/` unless the user explicitly requests them. Build and synchronization steps must not reintroduce these directories.
- Keep published installation archives unchanged. Handle installation and update compatibility when changing the distribution file list.
- Release notes describe actual changes in short sentences or lists. Do not add migration instructions, test inventories, internal protocols, or platform claims by default.
