import json
from org.apache.commons.io import IOUtils
from java.nio.charset import StandardCharsets
from org.apache.nifi.processor.io import StreamCallback

class ModJSON(StreamCallback):
    def __init__(self):
        self.error_occurred = False

    def process(self, inputStream, outputStream):
        try:
            text = IOUtils.toString(inputStream, StandardCharsets.UTF_8)
            reply = json.loads(text)
            reply['coords'] = f"{reply['lat']},{reply['lng']}"
            reply['opendate'] = reply['created_at'].split('T')[0]
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
