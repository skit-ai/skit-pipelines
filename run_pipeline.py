

"""Pipelines Tester

Usage:
  run_pipeline --pipeline-name=<pipeline_name> --params-file=<request_params_json> [--port=<server_port_number>]
  run_pipeline (-h | --help)

Options:
  --pipeline-name=<pipeline_name>       Pipeline name which we want to test.
  --params-file=<request_params_json>   Path to json file which contains parameters for the pipeline.
  --port=<server_port_number>           Port number in which pipelines server is running [default: 9991].
  -h --help                             Show this screen.

"""

from docopt import docopt

if __name__ == "__main__":
    import json
    from requests.exceptions import ConnectionError
    from skit_pipelines.api.slack_bot import run_pipeline

    arguments = docopt(__doc__)
    PIPELINE_NAME = arguments['--pipeline-name']
    PAYLOAD_FILE = arguments['--params-file']
    server_port = arguments['--port']

    with open(PAYLOAD_FILE, "r") as f:
        payload = json.load(f)

    try:
        resp = run_pipeline(
            pipeline_name=PIPELINE_NAME,
            payload=payload,
            server_port=server_port
        )
        run_url = resp.split("|")[0].split("<")[-1]
        print(f"Run URL: {run_url}")
        
    except ConnectionError as e:
        print(f"{e}\n\nTIP: check if server is running\n")
