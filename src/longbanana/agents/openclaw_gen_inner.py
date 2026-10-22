"""Run the retained OpenClaw generation function inside an isolated task."""
import json
from pathlib import Path
import sys

sys.path.insert(0, '/opt/judge/src')


def run():
    from openclaw_longbanana.generation import run as generation
    from openclaw_longbanana.config import OpenClawModelConfig
    request = json.loads(Path('/input/request.json').read_text())
    provider = request['provider']
    generation.PROJECT_ROOT = Path('/opt/reference')
    model = provider['models'][0]
    generation.load_openclaw_model_config = lambda **kwargs: OpenClawModelConfig(
        provider='longbanana', model=model['id'], base_url=provider['baseUrl'],
        api_key_env='LONGBANANA_PLANNER_TOKEN', api=provider['api'], context_window=model['contextWindow'],
        max_tokens=kwargs.get('max_tokens', 8192), allow_private_network=True, headers=provider['headers'])
    import os
    os.environ['LONGBANANA_PLANNER_TOKEN'] = provider['apiKey']
    original = generation._write_openclaw_config

    def provision(**kwargs):
        original(**kwargs)
        path = kwargs['config_path']
        config = json.loads(path.read_text())
        mcp = config['mcp']['servers']['image-gen']
        mcp['env'].update(LONGBANANA_IMAGE_BRIDGE_URL=request['image_url'],
                          LONGBANANA_IMAGE_BRIDGE_TOKEN=request['image_token'],
                          MCP_TOOL_TIMEOUT=str(request['tool_timeout'] * 1000))
        mcp['requestTimeoutMs'] = request['tool_timeout'] * 1000
        path.write_text(json.dumps(config))
        # Save deployment evidence before the original runner removes temp state.
        Path('/output/runtime_config.json').write_text(json.dumps(config))

    generation._write_openclaw_config = provision
    result = generation.run_one(request['task'], request['strategy'], 'gemini', Path('/output'),
                                request['timeout_s'], request['pipe_mode'], Path('/input'))
    Path('/output/row.json').write_text(json.dumps(result))


if __name__ == '__main__':
    run()
