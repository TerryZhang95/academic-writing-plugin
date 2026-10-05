"""Small standard-library MCP connection check. No model inference or credentials."""
import json
import re
import ssl
import urllib.error
import urllib.request
from urllib.parse import urlsplit


class CheckError(RuntimeError):
    pass


class Connection:
    def __init__(self, url):
        parsed = urlsplit(url)
        if parsed.scheme != 'https' or not parsed.hostname or parsed.path != '/mcp' or parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise CheckError('Expected a credential-free HTTPS /mcp endpoint')
        self.url = url
        self.sequence = 0
        self.headers = {'Content-Type': 'application/json', 'Accept': 'application/json, text/event-stream'}

    def request(self, method, params=None, notification=False):
        if method == 'tools/call' and params.get('name') == 'get_writing_guidance':
            params = {**params, 'arguments': {**params['arguments'], 'client_contract': 'academic-guidance-v1'}}
        payload = {'jsonrpc': '2.0', 'method': method}
        if params is not None:
            payload['params'] = params
        if not notification:
            self.sequence += 1
            payload['id'] = self.sequence
        req = urllib.request.Request(self.url, data=json.dumps(payload).encode(), headers=self.headers)
        try:
            with urllib.request.urlopen(req, timeout=15, context=ssl.create_default_context()) as response:
                if response.headers.get('Mcp-Session-Id'):
                    self.headers['Mcp-Session-Id'] = response.headers['Mcp-Session-Id']
                if urlsplit(response.url).scheme != 'https':
                    raise CheckError('HTTPS endpoint redirected to an insecure connection')
                raw = response.read(150_001)
                if len(raw) > 150_000:
                    raise CheckError('MCP response exceeded the self-check size limit')
                if notification:
                    return None
                result = json.loads(raw)
        except urllib.error.HTTPError as error:
            if error.code == 429:
                raise CheckError('HTTP 429: rate limited; wait and retry later. No automatic retry was made.') from None
            if error.code == 401:
                raise CheckError('HTTP 401: endpoint still requires credentials; operator must enable public access.') from None
            raise CheckError(f'HTTP {error.code}: service request failed') from None
        except (OSError, ValueError):
            raise CheckError('HTTPS/MCP connection failed; check internet, endpoint availability and trusted certificate.') from None
        if not isinstance(result, dict) or result.get('jsonrpc') != '2.0' or type(result.get('id')) is not int or result.get('id') != self.sequence:
            raise CheckError('Invalid MCP response envelope')
        if 'error' in result:
            raise CheckError('MCP rejected the request')
        if not isinstance(result.get('result'), dict):
            raise CheckError('Invalid MCP result shape')
        return result['result']

    def initialize(self):
        result = self.request('initialize', {'protocolVersion': '2025-11-25', 'capabilities': {}, 'clientInfo': {'name': 'academic-writing-check', 'version': '0.1.0'}})
        if not isinstance(result.get('protocolVersion'), str):
            raise CheckError('Invalid MCP initialization response')
        self.headers['MCP-Protocol-Version'] = result['protocolVersion']
        self.request('notifications/initialized', notification=True)
        return result

    def check(self):
        self.initialize()
        tools = self.request('tools/list').get('tools')
        if not isinstance(tools, list) or any(not isinstance(tool, dict) for tool in tools):
            raise CheckError('Invalid MCP tool list')
        if [tool.get('name') for tool in tools] != ['get_writing_guidance']:
            raise CheckError('Unexpected MCP tools; expected only get_writing_guidance')
        for method, field in (('resources/list', 'resources'), ('resources/templates/list', 'resourceTemplates'), ('prompts/list', 'prompts')):
            if self.request(method).get(field):
                raise CheckError('Unexpected resources or prompts')
        result = self.request('tools/call', {'name': 'get_writing_guidance', 'arguments': {'workflow': 'introduction', 'operation': 'polish', 'stage': 'start'}})
        if result.get('isError'):
            raise CheckError('Rule retrieval failed; ask the operator to inspect private source availability')
        structured = result.get('structuredContent')
        if not isinstance(structured, dict) or not isinstance(structured.get('guidance'), str) or not structured['guidance'] or not isinstance(structured.get('rules_version'), str):
            raise CheckError('Invalid structured guidance result')
        api = structured.get('api_version')
        if not isinstance(api, str) or len(api) > 32 or not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', api):
            raise CheckError('Invalid guidance API metadata; upgrade the service')
        contract = structured.get('api_contract')
        major = int(api.split('.')[0])
        if not ((major == 0 and contract == 'academic-guidance-v1') or (major == 1 and contract in (None, 'academic-guidance-v1'))):
            raise CheckError('Unsupported guidance API contract; update the client before continuing')
        for field in ('mcp_version', 'library_release'):
            value = structured.get(field)
            if value is not None and (not isinstance(value, str) or len(value) > 32 or not re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)', value)):
                raise CheckError('Invalid service release metadata')
        if structured.get('release_status', 'legacy-unversioned') not in ('released', 'unreleased', 'legacy-unversioned'):
            raise CheckError('Invalid service release metadata')
        capabilities = structured.get('capabilities', [])
        if not isinstance(capabilities, list) or any(not isinstance(item, dict) or set(item) != {'id', 'status'} or type(item['id']) is not str or item['status'] not in ('available', 'planned') for item in capabilities):
            raise CheckError('Invalid service capability metadata')
        related = any(item == {'id': 'related_work', 'status': 'available'} for item in capabilities)
        related_digest = None
        if related:
            arguments = {'workflow': 'related_work', 'operation': 'polish', 'stage': 'start'}
            if structured.get('library_release') is not None:
                arguments['library_release'] = structured['library_release']
            related_result = self.request('tools/call', {'name': 'get_writing_guidance', 'arguments': arguments})
            response = related_result.get('structuredContent')
            if related_result.get('isError') or not isinstance(response, dict) or response.get('workflow') != 'related_work' or type(response.get('guidance')) is not str or not response['guidance'] or type(response.get('rules_version')) is not str or not re.fullmatch(r'[0-9a-f]{64}', response['rules_version']):
                raise CheckError('Related Work retrieval failed; service upgrade or operator review is required')
            if response.get('library_release') != structured.get('library_release') or response.get('api_version') != api or response.get('api_contract') != contract:
                raise CheckError('Related Work did not retain the requested task release')
            related_digest = response['rules_version']
        system = any(item == {'id': 'system_model', 'status': 'available'} for item in capabilities)
        system_digest = None
        if system:
            arguments = {'workflow': 'system_model', 'operation': 'polish', 'stage': 'start'}
            if structured.get('library_release') is not None:
                arguments['library_release'] = structured['library_release']
            system_result = self.request('tools/call', {'name': 'get_writing_guidance', 'arguments': arguments})
            response = system_result.get('structuredContent')
            if system_result.get('isError') or not isinstance(response, dict) or response.get('workflow') != 'system_model' or not response.get('guidance') or not re.fullmatch(r'[0-9a-f]{64}', str(response.get('rules_version', ''))):
                raise CheckError('System Model retrieval failed; service upgrade or operator review is required')
            if response.get('library_release') != structured.get('library_release') or response.get('api_version') != api or response.get('api_contract') != contract:
                raise CheckError('System Model did not retain the requested task release')
            system_digest = response['rules_version']
        results = any(item == {'id': 'results', 'status': 'available'} for item in capabilities)
        results_digest = None
        if results:
            arguments = {'workflow': 'results', 'operation': 'polish', 'stage': 'start'}
            if structured.get('library_release') is not None:
                arguments['library_release'] = structured['library_release']
            response_result = self.request('tools/call', {'name': 'get_writing_guidance', 'arguments': arguments})
            response = response_result.get('structuredContent')
            if response_result.get('isError') or not isinstance(response, dict) or response.get('workflow') != 'results' or not response.get('guidance') or not re.fullmatch(r'[0-9a-f]{64}', str(response.get('rules_version', ''))):
                raise CheckError('Results retrieval failed; service upgrade or operator review is required')
            if response.get('library_release') != structured.get('library_release') or response.get('api_version') != api or response.get('api_contract') != contract:
                raise CheckError('Results did not retain the requested task release/API identity')
            results_digest = response['rules_version']
        added_digests = {}
        for workflow, scope in [('algorithm', {'operation':'polish'}), ('whole_paper', {'operation':'polish', 'section':'abstract'}), ('shared', {'operation':'guide', 'module':'notation'}), ('language_polish', {'operation':'polish','language':'en','register':'academic'}), ('figure_prompt', {'operation':'prompt'})]:
            available = any(item == {'id':workflow, 'status':'available'} for item in capabilities)
            if not available:
                continue
            arguments = {'workflow':workflow, 'stage':'start', **scope}
            if structured.get('library_release') is not None:
                arguments['library_release'] = structured['library_release']
            retrieved = self.request('tools/call', {'name':'get_writing_guidance', 'arguments':arguments})
            response = retrieved.get('structuredContent')
            if retrieved.get('isError') or not isinstance(response,dict) or response.get('workflow') != workflow or not response.get('guidance') or not re.fullmatch(r'[0-9a-f]{64}', str(response.get('rules_version',''))):
                raise CheckError('Manuscript/shared guidance unavailable; upgrade or ask the operator')
            if any(response.get(field) != structured.get(field) for field in ['library_release','api_version','api_contract']):
                raise CheckError('Manuscript/shared guidance changed the task release/API identity')
            if any(response.get(field) != scope[field] for field in ('language','register') if field in scope):
                raise CheckError('Language selectors changed during retrieval')
            added_digests[workflow] = response['rules_version']
        return {'https': True, 'mcp_tool': 'get_writing_guidance', 'rules_version': structured['rules_version'],
                'api_version': api, 'api_contract': contract or 'legacy-major-1', 'mcp_version': structured.get('mcp_version'),
                'language_polish_available':'language_polish' in added_digests, 'figure_prompt_available':'figure_prompt' in added_digests,
                'algorithm_available':'algorithm' in added_digests, 'whole_paper_available':'whole_paper' in added_digests, 'shared_available':'shared' in added_digests,
                'added_rules_versions':added_digests, 'results_available': results, 'results_rules_version': results_digest,
                'system_model_available': system, 'system_model_rules_version': system_digest,
                'related_work_available': related, 'related_work_rules_version': related_digest,
                'library_release': structured.get('library_release'),
                'release_status': structured.get('release_status', 'legacy-unversioned'), 'model_calls': 0}
