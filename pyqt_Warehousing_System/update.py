import requests
import urllib3

def update_to_server(state):
    url = "https://mct.local/static/update.php"
    payload = {
        "machine_id": "test001",
        "machine_state": state
    }
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    requests.post(url, data=payload, verify=False)