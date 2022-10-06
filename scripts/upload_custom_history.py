import json
from pathlib import Path
import requests
from uuid import uuid4


DOMAIN = 'https://fedot.onti.actcognitive.org'
# DOMAIN = 'http://127.0.0.1:5000'
BASE_PATH = Path(r"...")
FILE_NAME = '... .json'

if __name__ == '__main__':
    case_id = FILE_NAME.replace('.json', '') + str(uuid4())
    history_url = f'{DOMAIN}/ws/sandbox/custom_{case_id}/history'
    post_url = f"{DOMAIN}/api/showcase/add"

    history_json = json.load(open(BASE_PATH.joinpath(FILE_NAME)))
    new_case = {
            'case': {
                'case_id': case_id,
            },
            'history': history_json
    }
    response = requests.post(post_url, json=new_case)

    print(response.text, response.status_code, )
    print(f'IMPORTANT! Save this url.\n{history_url}')
