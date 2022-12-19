import json
from glob import glob

import pytest
from requests import post

URL = 'https://download.lapig.iesa.ufg.br/api/download/'
# URL = 'http://localhost:8282/api/download/'
FILES = glob('tests/payloads/*.json')

TESTS = []
PAYLOAD = {}
for file in FILES:
    with open(file) as binfile:
        tmp_json = json.load(binfile)
        PAYLOAD[file] = tmp_json
        for payload_name in tmp_json:
            TESTS.append((file, payload_name))
# TESTS = [('tests/payloads/areas_especias.json', 'Areas_Publicas_Goiania_SHP')]


@pytest.mark.parametrize('file, payload_name', TESTS)
def test_payload(file, payload_name):
    request = post(URL, json=PAYLOAD[file][payload_name])
    if not request.status_code == 200 and not request.status_code == 415:
        try:
            text = request.json()['message']
            assert text in [
                'unable_filter_layer',
                'file_empty',
                'file_not_found',
            ]
        except:
            print(request.status_code, request.text)
            assert False
    elif request.status_code == 415:
        text = request.json()['message']
        assert (
            'Incongruity in the type of data entered, please enter valid data for this layer'
            in text
        )

    else:
        assert request.status_code == 200
