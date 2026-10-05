# Academic Writing

Academic Writing helps you plan, draft, revise and review research manuscripts in Codex App and Codex CLI. It provides section-specific guidance for Introductions, Related Work, System Models, Methods/Algorithms and Results, alongside whole-manuscript review, language polishing, reference checks, data plotting and schematic figure prompts.

## Install

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

Download [academic-writing-public-0.1.13.zip](https://github.com/TerryZhang95/academic-writing-plugin/releases/download/v0.1.13/academic-writing-public-0.1.13.zip), extract it, and open a terminal in the extracted `academic-writing` folder.

```sh
python3 scripts/manage.py install
python3 scripts/manage.py check
```

In PowerShell, use `py -3` in place of `python3`:

```powershell
py -3 scripts/manage.py install
py -3 scripts/manage.py check
```

A successful check lists the nine skill entries and confirms the MCP connection. Restart Codex and open a new chat after installation.

If Codex CLI is outside your `PATH`, pass its executable with `--codex "/path/to/codex"` or set `CODEX_CLI_PATH`. Quote paths that contain spaces. Install into a regular local folder.

## Use

Each guidance request uses the service’s current rules, including requests from work already in progress. Updates preserve the supported interfaces and existing functions. Returned version metadata records the rules used; historical versions are reserved for release records and operator rollback.

Ask Codex to use **Academic Writing** and provide the text or files for the task.

The plugin provides multiple skills with agents for section writing, whole-manuscript review, language polishing, schematic figure prompts, reference checks and data plotting. Section-specific guidance covers Introductions, Related Work, Models, Methods/Algorithms and Results.

For Methods/Algorithms, provide the algorithm steps, inputs, outputs and stopping conditions. The algorithm skill explains the method and checks pseudocode; new blocks use `algorithm` with `algpseudocode`, while existing manuscript packages are preserved. Experimental evaluation stays in Results.

Provide the text or files you want to work on. Request DOI verification explicitly when checking references. For plotting, provide a data file (e.g., csv or json) and specify the data columns and chart type.

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

For installations from 0.1.12 or earlier, download and extract the new release, then run the **newly downloaded** `scripts/manage.py update --confirm --expected-version VERSION` against the same Codex home (pass `--home` if you used a custom home). Older installed updaters cannot accept the changed file list. The new manager preserves unrelated settings and restores the previous bundle if its installation check fails.

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
