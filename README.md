# Academic Writing

Academic writing, prose polishing, reference checks and figure tools for Codex CLI and Codex App. Uses the same plugin and remote MCP service on both surfaces. Local helper scripts require Python 3.9+ (Python 3.11 or newer recommended).

Client version: **0.1.11**. Installation and actual writing, reference-check and plotting workflows have passed acceptance.

## Native CLI installation

With Codex CLI installed, register the public repository and add the plugin:

```sh
codex plugin marketplace add TerryZhang95/academic-writing-plugin
codex plugin add academic-writing@academic-writing-public
```

These commands also work in Windows PowerShell. To install from the ZIP instead, pass the extracted `academic-writing` folder to `codex plugin marketplace add`.

Start a new Codex session after installation. Native installation does not require the Python managed installer. Python is needed for version checks and explicit reference/figure helpers.

## Codex App installation

Open the App's plugin management page and add a custom marketplace with the GitHub source `TerryZhang95/academic-writing-plugin`. Select **Academic Writing**, install and enable it, then open a new chat. For a local ZIP installation, use the extracted `academic-writing` folder as the marketplace source. If the custom-source control is unavailable, update Codex App before continuing.

The App and CLI must use the same local Codex home to share installation state. A custom `CODEX_HOME` creates a separate installation context: set it consistently for the surface you use. Do not run the managed installer over an existing native marketplace with the same name.

## Optional managed installation

Download `academic-writing-public-0.1.11.zip` from [Releases](https://github.com/TerryZhang95/academic-writing-plugin/releases/latest) and extract it. Run from the extracted `academic-writing` folder.

macOS:

```sh
python3 scripts/manage.py install
python3 scripts/manage.py check
```

Windows PowerShell:

```powershell
py -3 scripts/manage.py install
py -3 scripts/manage.py check
```

The managed route also requires Codex CLI. If it is not on PATH, pass `--codex "C:\path\to\codex.exe"`, or set `CODEX_CLI_PATH`. The client uses the native executable, including a uniquely discovered binary behind an npm wrapper, without executing shell wrappers. Refresh/restart the App and open a new chat afterward.

The plugin identifier is `academic-writing`, marketplace is `academic-writing-public`, and directory is `plugins/academic-writing`. Installation is per user and requires no administrator rights. Ordinary local directories with Chinese characters or spaces are supported; symlinks and Windows junction/reparse paths are rejected. Avoid redirected/cloud-only folders for the managed installation.

## Use

Ask Codex to use Academic Writing with the relevant text or files:

- “Polish this paragraph with Academic Writing, keeping its meaning and structure.”
- “Use Academic Writing to revise the Introduction in paper.tex.”
- “Check refs.bib and the citations in paper.tex, including DOI verification.”
- “Plot these data with Academic Writing; use load for x and throughput for y.”

Use `py -3 "path\to\script.py"` in Windows PowerShell and `python3 "path/to/script.py"` on macOS. Local scripts need no extra Python packages or model API key. Quote file paths containing spaces. Sample inputs are in `examples/`.

## Update and uninstall

**Native CLI/App installations:** use the install surface's update command/control, if available, or remove and reinstall from a refreshed marketplace source. Start a new chat afterward. Version preflight checks the plugin's own manifest and public compatibility metadata; it never creates an ownership marker or takes over native installs. Unknown/incompatible versions stop with an explicit report.

For a CLI reinstall, remove the plugin, remove its marketplace registration, and add the repository again before reinstalling. This refreshes the source instead of reusing an old local marketplace:

```sh
codex plugin remove academic-writing@academic-writing-public
codex plugin marketplace remove academic-writing-public
codex plugin marketplace add TerryZhang95/academic-writing-plugin
codex plugin add academic-writing@academic-writing-public
```

For App installations, refresh the marketplace through the App's source controls, then update or reinstall **Academic Writing**. If installing from a ZIP folder, download the new release first and use its newly extracted folder as the source. Pushing a repository update does not automatically upgrade an installed copy.

CLI removal:

```sh
codex plugin remove academic-writing@academic-writing-public
```

**Managed installations:** run `check-update`, review its summary, then approve a particular version with `update --confirm --expected-version VERSION`. On Windows run from your user home, outside the managed installation directory, to avoid holding it open:

```powershell
Set-Location $env:USERPROFILE
$manager = Join-Path $env:USERPROFILE '.codex\academic-writing-distribution\scripts\manage.py'
py -3 $manager check-update
py -3 $manager update --confirm --expected-version VERSION
py -3 $manager check
# When you want to remove the managed installation:
py -3 $manager uninstall
```

For custom `CODEX_HOME`, use that directory consistently for installation and later actions:

```powershell
$env:CODEX_HOME = Join-Path $env:USERPROFILE 'codex-academic'
# From the freshly extracted academic-writing folder:
py -3 scripts/manage.py install
Set-Location $env:USERPROFILE
$manager = Join-Path $env:CODEX_HOME 'academic-writing-distribution\scripts\manage.py'
py -3 $manager check-update
```

Set `CODEX_HOME` before launching Codex and restart an already running App so it can use the intended context. For native CLI installation, set the same variable before running the marketplace/plugin commands above. On macOS use `python3` and the same managed script/actions. Native installations cannot be updated or uninstalled by this tool. Concurrent upgrades are refused; a failed replacement restores the previous installation. If Windows reports files in use, close affected shells/App sessions and retry. Upgrading never silently switches the rules version of an existing task.

For old `ieee-writing` installations, uninstall with the old installer before installing the renamed plugin. If a request returns HTTP 429, wait and explicitly retry. Restart Codex when an installed tool is missing; connection checks do not measure writing quality.
