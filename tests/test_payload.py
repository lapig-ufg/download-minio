from requests import post
import json

URL = 'https://s3.lapig.iesa.ufg.br:9001/api/download'

def rename(newname):
    def decorator(f):
        f.__name__ = newname
        return f
    return decorator




def test_payload_pasture():
    with open('tests/payloads/pasture_col6.json') as file:
        dataset = json.load(file)
    
    for payload in dataset:
        @rename(f'teste_{payload}')
        def validate_payload(data):
            request = post(URL,data=data)
            print(request.text)
            assert request.status_code == 200
        validate_payload(dataset[payload])
        
def test_pytest():
    assert 1 == 1

