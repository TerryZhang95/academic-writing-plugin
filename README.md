# Academic Writing Plugin for Codex

Academic Writing is an open-source academic writing plugin for Codex App and Codex CLI. It helps you plan, draft, revise and review research papers, with dedicated workflows for manuscript sections, language polishing, reference checks and scientific figures.

Codex has strong writing and revision capabilities and can work directly with manuscript files. This plugin builds on those capabilities with academic writing guidance that connects the research motivation, claims, methods and results. The goal is to make Codex a more useful writing partner throughout manuscript preparation, from an initial outline to a full-paper review.

The plugin brings writing skills and a connected guidance service together in one installation. You can move between section writing, manuscript review, references and figures in the same Codex chat, without configuring each skill and tool separately. Codex uses your existing account and selected model to carry out the work.

## Functions

| Function | What it helps you do |
| --- | --- |
| Section writing | Plan, draft and revise Introductions, Related Work, System Models and Results with guidance tailored to each section. |
| Whole-paper writing and review | Coordinate sections, revise the manuscript's argument and check consistency across claims, notation and terminology. Support also covers Abstracts, Conclusions, Problem Formulations, Analysis and Appendices. |
| Language polishing | Polish English and Chinese prose for clear, natural academic or professional expression while preserving meaning and technical content. |
| Reference checks | Check supplied BibTeX entries and LaTeX citation keys for missing keys, duplicates and metadata issues. Verify DOI metadata when requested. |
| Data plotting and Results figures | Plot supplied quantitative data, review figures and write Results text and captions based on the provided evidence. |
| Schematic figures | Plan architecture, workflow, protocol and system diagrams, prepare image-generation prompts and review supplied diagrams. |

The plugin is under active development. Suggestions for additional writing workflows, checks or figure tools are welcome through [GitHub Issues](https://github.com/TerryZhang95/academic-writing-plugin/issues). Describe the task you want to complete and the output you need.

## Installation

### Codex App

1. Open plugin management and add a custom marketplace.
2. Enter `TerryZhang95/academic-writing-plugin` as the GitHub source.
3. Install and enable **Academic Writing**.
4. Open a new chat.

You can also download the [release ZIP](https://github.com/TerryZhang95/academic-writing-plugin/releases/latest), extract it, and select the extracted `academic-writing` folder as the local marketplace source. If the App does not show the custom marketplace control, update the App.

### Codex CLI

Run these commands in your terminal:

```sh
codex plugin marketplace add TerryZhang95/academic-writing-plugin
codex plugin add academic-writing@academic-writing-public
```

The commands also work in PowerShell. Start a new Codex session after installation.

To install from a ZIP, replace the GitHub source in the first command with the path to the extracted `academic-writing` folder.

### Python installer

Use this method if you want to manage installation, checks, updates and removal with the included script. It requires Codex CLI. Python 3.11 or newer is recommended.

Download the ZIP asset from the [latest release](https://github.com/TerryZhang95/academic-writing-plugin/releases/latest), extract it, and open a terminal in the extracted `academic-writing` folder.

```sh
python3 scripts/manage.py install
python3 scripts/manage.py check
```

In PowerShell, use `py -3` in place of `python3`:

```powershell
py -3 scripts/manage.py install
py -3 scripts/manage.py check
```

A successful check lists the eight skill entries and confirms the MCP connection. Restart Codex and open a new chat after installation.

If Codex CLI is outside your `PATH`, pass its executable with `--codex "/path/to/codex"` or set `CODEX_CLI_PATH`. Quote paths that contain spaces. Install into a regular local folder.

## How to use

Ask Codex to use **Academic Writing** and provide the text or files you want to work on. State the task, the section or files in scope, and any requirements such as the target venue, language or output format. Codex selects the relevant writing workflow from your request.

For drafting, provide your research notes, methods and available results. For revision or review, provide the current manuscript and identify the parts you want changed or checked. If you want wording changes only, specify that the structure and technical meaning should be preserved.

For reference checks, provide the relevant `.bib` and `.tex` files and request DOI verification explicitly if needed. For plotting, provide the data file, selected columns, units and intended comparison. For schematic figures, describe the components and their relationships, and specify whether you need a plan, a generation prompt or a rendered image.

Writing guidance is retrieved without uploading manuscript text. When you request the cloud reference checker or CSV plotting tool, the selected files are uploaded for that task.

## Update

Use the method you installed with, then restart Codex and open a new chat.

### App

Refresh the marketplace source in plugin management, then update or reinstall **Academic Writing**. For a local ZIP source, download the current release and select its extracted folder.

### CLI

Refresh the repository source and reinstall:

```sh
codex plugin remove academic-writing@academic-writing-public
codex plugin marketplace remove academic-writing-public
codex plugin marketplace add TerryZhang95/academic-writing-plugin
codex plugin add academic-writing@academic-writing-public
```

### Python installer

Run the installed manager from outside the installation folder. With the default Codex home, its path is `~/.codex/academic-writing-distribution/scripts/manage.py`.

```sh
cd ~
python3 ~/.codex/academic-writing-distribution/scripts/manage.py check-update
```

Read the reported version and update summary. To install that version, replace `VERSION` below with the version shown by the check:

```sh
python3 ~/.codex/academic-writing-distribution/scripts/manage.py update --confirm --expected-version VERSION
python3 ~/.codex/academic-writing-distribution/scripts/manage.py check
```

In PowerShell:

```powershell
Set-Location $env:USERPROFILE
$manager = Join-Path $env:USERPROFILE '.codex\academic-writing-distribution\scripts\manage.py'
py -3 $manager check-update
py -3 $manager update --confirm --expected-version VERSION
py -3 $manager check
```

## Uninstall

In the App, remove **Academic Writing** through plugin management.

For a CLI installation:

```sh
codex plugin remove academic-writing@academic-writing-public
```

For a Python-managed installation:

```sh
cd ~
python3 ~/.codex/academic-writing-distribution/scripts/manage.py uninstall
```

In PowerShell, set `$manager` as shown above and run `py -3 $manager uninstall`.
