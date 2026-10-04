#!/usr/bin/env python3
"""Run four writing cases with an already logged-in Codex account; never copy auth."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile
from connection import CheckError, Connection
from manage import PACKAGE, SELECTOR, manage
from platform_support import codex_binary

OPERATIONS = ('polish', 'revise_contributions', 'revise', 'audit')


def extract(events, operation):
    calls = []
    final = ''
    for event in events:
        item = event.get('item', {})
        if item.get('type') == 'agent_message' and item.get('text'):
            final = item['text']
        if item.get('type') != 'mcp_tool_call' or event.get('type') != 'item.completed':
            continue
        # Tool evidence comes from runtime events, not the model's prose.
        tool = item.get('tool', '')
        server = item.get('server', '')
        if tool != 'get_writing_guidance' or 'academic' not in server.lower():
            continue
        arguments = item.get('arguments', {})
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except ValueError:
                arguments = {}
        result = item.get('result') or {}
        structured = result.get('structuredContent', result.get('structured_content'))
        if not structured:
            for content in result.get('content', []):
                if content.get('type') == 'text':
                    try:
                        candidate = json.loads(content.get('text', ''))
                        if isinstance(candidate, dict) and 'rules_version' in candidate:
                            structured = candidate
                    except ValueError:
                        pass
        success = (item.get('status') == 'completed' and not result.get('isError', result.get('is_error', False))
                   and isinstance(structured, dict) and bool(structured.get('guidance')) and bool(structured.get('rules_version')))
        calls.append({'tool': tool, 'server': server, 'operation': arguments.get('operation'),
                      'stage': arguments.get('stage'), 'success': success,
                      'rules_version': structured.get('rules_version') if isinstance(structured, dict) else None})
    stages = {'start'} if operation == 'polish' else {'start', 'check'}
    observed = {call['stage'] for call in calls if call['success'] and call['operation'] == operation}
    return final, calls, stages <= observed


def diagnostic(events, stderr, returncode, evidence):
    """Classify known failures; never persist raw peer text or stderr."""
    messages = []
    for event in events:
        if event.get('type') == 'error':
            messages.append(str(event.get('message', '')))
        elif event.get('type') == 'turn.failed':
            error = event.get('error', {})
            if isinstance(error, dict):
                messages.append(str(error.get('message', '')))
    text = (' '.join(messages) + ' ' + stderr).lower()
    if 'not supported' in text and ('chatgpt' in text or 'model' in text):
        return 'Requested model is unsupported for this account; choose an available Codex model/list model.'
    if '429' in text or 'rate limit' in text:
        return 'Rate limited; wait and retry later. No automatic replay was made.'
    if '401' in text or 'not logged in' in text or 'authentication' in text:
        return 'Authentication failed; check the test account login and public endpoint access.'
    if returncode:
        return 'Codex execution failed; inspect account/model availability and local prerequisites.'
    if not evidence:
        return 'No successful required plugin MCP calls were observed; writing acceptance failed.'
    return 'Required runtime MCP calls observed; human content review remains.'


def run(output, *, codex='codex', model=None, home=None, package=PACKAGE, allow_local_skills_smoke=False):
    home = Path(home or os.environ.get('CODEX_HOME', Path.home() / '.codex')).expanduser().resolve()
    # Caller logs in independently. Do not create or populate a new auth home.
    if not home.is_dir():
        raise CheckError('Existing independently logged-in Codex home required')
    installed = home / 'academic-writing-distribution'
    if not (home / 'academic-writing-install.json').is_file():
        if not allow_local_skills_smoke:
            raise CheckError('Install the public bundle in this test account first')
        installed = package
    local_skills_detected = False
    for directory in (home / 'skills', home / 'plugins/cache'):
        if directory.is_dir():
            unwanted = [path for path in directory.rglob('SKILL.md')
                        if (path.parents[1].name == 'skills' or '-writing' in path.parent.name or 'paper-self-review' in path.as_posix().lower())
                        and path.parent.name not in {'academic-introduction-mcp', 'academic-related-work-mcp', 'academic-system-model-mcp', 'academic-results-mcp', 'academic-whole-paper-mcp', 'academic-execution-mcp', 'academic-language-polish-mcp', 'academic-figure-prompt-mcp'}]
            if unwanted:
                local_skills_detected = True
                if not allow_local_skills_smoke:
                    raise CheckError('Local Academic skills detected; use an independently logged-in clean test user/home')
    output = Path(output).resolve()
    if output.exists():
        raise CheckError('Report directory already exists; choose a new path')
    output.mkdir(parents=True)
    try:
        if allow_local_skills_smoke:
            endpoint = json.loads((installed / 'plugins/academic-writing/.mcp.json').read_text(encoding='utf-8'))['mcpServers']['academic_guidance']['url']
            connection = Connection(endpoint).check()
        else:
            connection = manage('check', codex=codex, home=home)
    except CheckError as error:
        (output / 'report.md').write_text('# Writing acceptance\n\nNot run: connection self-check failed.\n\n' + str(error) + '\n')
        return False
    manifest = json.loads((installed / 'plugins/academic-writing/.codex-plugin/plugin.json').read_text(encoding='utf-8'))
    context = (package / 'examples/context.md').read_text(encoding='utf-8')
    source = (package / 'examples/introduction.tex').read_text(encoding='utf-8')
    env = dict(os.environ, CODEX_HOME=str(home))
    for key in (set(os.environ) & {'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'CODEX_API_KEY'}) | {key for key in os.environ if key.endswith('_MCP_ACCESS_TOKEN')}:
        env.pop(key, None)
    reports = []
    with tempfile.TemporaryDirectory(prefix='academic-writing-case-') as workspace:
        for operation in OPERATIONS:
            prompt = (f'Use $academic-writing:academic-introduction-mcp from {SELECTOR}. Operation={operation}. '
                      'Obtain real plugin MCP rules: start, and check except polish. Use routing fields only. '
                      'Do not read local Academic skills, private repositories or service rules. '
                      'If MCP fails or returns 429 stop and report the failure; no fallback. '
                      'Return the revised Introduction as LaTeX (audit returns findings instead), actual check status and evidence gaps. '
                      'Preserve the approved two contributions. Do not add numerical evidence or sources.\n\n' + context + '\n\n' + source)
            command = [codex]
            if allow_local_skills_smoke:
                command += ['-c', 'marketplaces.academic-writing-public.source_type="local"',
                            '-c', 'marketplaces.academic-writing-public.source=' + json.dumps(str(installed)),
                            '-c', 'plugins."academic-writing@academic-writing-public".enabled=true']
            command += ['exec', '--json', '--ephemeral', '--skip-git-repo-check', '--sandbox', 'read-only', '-C', workspace]
            if model:
                command += ['--model', model]
            command += ['-']
            try:
                process = subprocess.run(command, input=prompt, text=True, env=env, capture_output=True, timeout=240)
                events = [json.loads(line) for line in process.stdout.splitlines() if line.startswith('{')]
                final, calls, evidence = extract(events, operation)
                passed = process.returncode == 0 and bool(final) and evidence
                execution = {'returncode': process.returncode, 'diagnostic': diagnostic(events, process.stderr, process.returncode, evidence)}
            except (OSError, ValueError, subprocess.TimeoutExpired):
                final, calls, passed = 'Execution failed or timed out; no writing compliance claimed.', [], False
                execution = {'returncode': None, 'diagnostic': 'Execution timed out or produced invalid events; no raw error data persisted.'}
            # Only final paper output and sanitized call metadata are persisted;
            # raw events can contain private guidance and must not be published.
            (output / (operation + '.md')).write_text(final + '\n')
            (output / (operation + '-calls.json')).write_text(json.dumps(calls, indent=2) + '\n')
            checks = {'runtime_rules_evidence': passed, 'nonempty_output': bool(final)}
            if operation != 'audit':
                checks['section_label_preserved'] = '\\label{sec:intro}' in final
                checks['two_contributions'] = len(re.findall(r'\\item\b', final)) == 2
                checks['percent_escape_preserved'] = '5\\%' in final
            reports.append((operation, checks, calls, execution))
    lines = ['# Real writing acceptance', '', f'Plugin version: {manifest["version"]}',
             f'Model: {model or "current account configured default (not resolved by script)"}',
             'Account: existing user login; no auth copied or inspected.',
             ('Environment: DEVELOPMENT SMOKE ONLY; local skills permitted/detected=' + str(local_skills_detected) + '; not independent-user acceptance.' if allow_local_skills_smoke else 'Environment: clean home scan passed; independent macOS user/desktop isolation still requires human confirmation.'),
             f'Connection rules version: {connection["rules_version"]}', '',
             'This report separates observed runtime calls from writing quality. Raw rule payloads and credentials are excluded.', '',
             '## Public input', '', '```markdown', context, '```', '', '```latex', source, '```', '', '## Cases', '']
    for operation, checks, calls, execution in reports:
        lines += [f'### {operation}', '', f'Output: [{operation}.md]({operation}.md)',
                  f'Runtime calls: [{operation}-calls.json]({operation}-calls.json)', '', '```json', json.dumps({'checks': checks, 'execution': execution}, indent=2), '```', '']
    lines += ['## Human review still required', '', '- Technical meaning, evidence scope and author contribution count.',
              '- Literature-gap logic and unsupported novelty/guarantees.', '- LaTeX completeness, touched interfaces and exact source constraints.',
              '- Plugin visibility after desktop restart and independent macOS-user acceptance.',
              '- No formula/citation preservation claimed: the synthetic fixture contains neither.', '']
    (output / 'report.md').write_text('\n'.join(lines))
    return all(all(checks.values()) for _, checks, _, _ in reports)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--model')
    parser.add_argument('--codex', default='codex')
    parser.add_argument('--home', type=Path)
    parser.add_argument('--allow-local-skills-smoke', action='store_true', help='Developer-only: use existing login and process-local plugin overrides; report non-isolated smoke, not new-user acceptance')
    args = parser.parse_args()
    try:
        passed = run(args.output, codex=args.codex, model=args.model, home=args.home, allow_local_skills_smoke=args.allow_local_skills_smoke)
    except (CheckError, OSError, ValueError) as error:
        parser.exit(1, str(error) if isinstance(error, CheckError) else 'Writing test failed; inspect prerequisites.\n')
    print('Report created. Automatic checks passed; human review remains.' if passed else 'Report created with failed/pending checks; no writing acceptance claimed.')
    raise SystemExit(0 if passed else 1)


if __name__ == '__main__':
    main()
