# Academic Writing

Academic Writing adds manuscript guidance, language polishing, reference checks and CSV plotting to Codex App and Codex CLI. Your Codex model writes and edits the manuscript using guidance from the remote MCP service.

## Install

Choose one installation method. Both the App and CLI use the same plugin.

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

To install from a ZIP, replace the GitHub source in the first command with the path to the extracted `academic-writing` folder. Keep the second command unchanged.

### Python installer

Use this method if you want to manage installation, checks, updates and removal with the included script. It requires Codex CLI and Python 3.9 or newer; Python 3.11 or newer is recommended.

Download [academic-writing-public-0.1.12.zip](https://github.com/TerryZhang95/academic-writing-plugin/releases/download/v0.1.12/academic-writing-public-0.1.12.zip), extract it, and open a terminal in the extracted `academic-writing` folder.

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

## Use

Ask Codex to use **Academic Writing** and provide the text or files for the task.

| Task | Example request |
| --- | --- |
| Introduction | “Use Academic Writing to revise the Introduction in paper.tex.” |
| Related Work | “Organize this Related Work around the research directions and gaps.” |
| System Model | “Check the System Model for missing assumptions and inconsistent notation.” |
| Results | “Revise the discussion of these results using the figures and data I provide.” |
| Whole manuscript | “Review the structure of this manuscript and revise the Abstract.” |
| Language polishing | “Polish this paragraph while preserving its meaning and structure.” |
| Schematics | “Prepare a figure prompt for this system architecture.” |
| References and plots | “Check refs.bib against paper.tex” or “Plot data.csv with load on the x-axis and throughput on the y-axis.” |

For DOI verification, ask for it explicitly. For a plot, specify the file, columns and chart type. Sample writing inputs are in `examples/`.

Python is required for the startup version check and reference/plot helpers, including when you install through the App or CLI. The local scripts use the Python standard library. Your Codex account supplies the writing model; no separate model API key is needed.

Manuscript writing uses your local text and remote writing guidance. Reference and plotting tasks send the explicitly selected BibTeX, LaTeX or CSV files to the remote service for processing.

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

## Codex home and troubleshooting

The App and CLI share installation state when they use the same Codex home. If you set `CODEX_HOME`, set it before installation and before launching Codex. Restart an App that is already running. Use one installation method for this marketplace within each Codex home.

For example, to use a separate home in PowerShell, run this from the extracted ZIP folder:

```powershell
$env:CODEX_HOME = Join-Path $env:USERPROFILE 'codex-academic'
py -3 scripts/manage.py install
Set-Location $env:USERPROFILE
$manager = Join-Path $env:CODEX_HOME 'academic-writing-distribution\scripts\manage.py'
py -3 $manager check
```

Use that `$manager` path for later checks, updates and removal. For a native CLI installation, set `CODEX_HOME` before running the marketplace commands instead.

If skills are missing, restart Codex and open a new chat. If a connection check fails, check Python, your internet connection and service availability. If the service returns HTTP 429, wait before retrying. If an update reports files in use, close terminals or App sessions using the installation folder and retry.
