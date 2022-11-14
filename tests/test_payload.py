import json
from glob import glob

import pytest
from requests import post

from app.config import logger

URL = 'https://download.lapig.iesa.ufg.br//api/download/'
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


@pytest.mark.parametrize('file, payload_name', TESTS)
def test_payload_pasture(file, payload_name):
    request = post(URL, json=PAYLOAD[file][payload_name])
    if not request.status_code == 200:
        print(request.text)
        assert request.text == 'lapig'
    else:
        assert request.status_code == 200
