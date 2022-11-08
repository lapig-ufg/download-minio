from requests import post
import json

URL = 'localhost:8282/api/download'

def rename(newname):
    def decorator(f):
        f.__name__ = newname
        return f
    return decorator




def test_payload_pasture():
    with open('test/payloads/pasture_col6.json') as file:
        dataset = json.load(file)
    
    for payload in dataset:
        @rename(f'teste_{payload}')
        def validate_payload(data):
            request = post(URL,data=data)
            assert request.status_code == 200
        validate_payload(dataset[payload])
        
