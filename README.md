# Academic Writing

A small academic writing plugin, currently optimized for Codex. Installation has been tested on macOS. Requires Python 3.9+ and the Codex CLI (`codex --version`).

## Install

Download `ieee-writing-public-0.1.8.zip` from [Releases](https://github.com/TerryZhang95/academic-writing-plugin/releases/latest), unzip it, and open a terminal in the extracted `ieee-writing` folder:

```sh
python3 scripts/manage.py install
python3 scripts/manage.py check
```

Refresh or restart Codex, then open a new chat. The plugin appears as **Academic Writing**; its internal identifier remains `ieee-writing`.

## Use

Ask Codex to use Academic Writing and specify the text or files:

- “Polish this paragraph with Academic Writing, keeping its meaning and structure.”
- “Use Academic Writing to revise the Introduction in paper.tex.”
- “Check refs.bib and the citations in paper.tex, including DOI verification.”
- “Plot these data with Academic Writing; use load for x and throughput for y.”
- “Create an architecture-diagram prompt from these system notes.”

Sample writing inputs are in `examples/`. For file tasks, specify the files and a new output directory.

## Update

Run these commands from the downloaded folder, or from `~/.codex/ieee-writing-distribution` after installation:

```sh
python3 scripts/manage.py check-update
# After reviewing and accepting the displayed version:
python3 scripts/manage.py update --confirm --expected-version VERSION
python3 scripts/manage.py check
```

Replace `VERSION` with the displayed version. Refresh or restart Codex and open a new chat after upgrading. To postpone a reminder, run `python3 scripts/manage.py check-update --defer`.

Existing installations can upgrade to 0.1.8 using their previous update tool. This version adds GitHub updates. If the old installation has no update command, download this release and use its tool to upgrade the managed installation.

## Uninstall

```sh
python3 scripts/manage.py uninstall
```

If a request reports HTTP 429, wait and retry. If installation succeeds but a tool is missing, restart Codex and run `check` again. Connection self-check does not evaluate writing quality.
