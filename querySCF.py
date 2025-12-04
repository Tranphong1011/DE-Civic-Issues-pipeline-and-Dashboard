import json
from urllib.parse import urlencode
from urllib.request import urlopen
from org.apache.nifi.processor.io import StreamCallback

class ModJSON(StreamCallback):
    def __init__(self):
        self.error_occurred = False

    def process(self, inputStream, outputStream):
        try:
            params = {'place_url': 'bernalillo-county', 'per_page': '100'}
            url = f'https://seeclickfix.com/api/v2/issues?{urlencode(params)}'
            with urlopen(url) as response:
                reply = json.loads(response.read())
            outputStream.write(json.dumps(reply, indent=4).encode('utf-8'))
        except Exception:
            self.error_occurred = True
            outputStream.write(json.dumps({}, indent=4).encode('utf-8'))

error_occurred = False
flow_file = session.get()
if flow_file:
    mod_json = ModJSON()
    flow_file = session.write(flow_file, mod_json)
    error_occurred = mod_json.error_occurred
    session.transfer(flow_file, REL_FAILURE if error_occurred else REL_SUCCESS)
session.commit()
