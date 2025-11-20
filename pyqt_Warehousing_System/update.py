import requests
import urllib3
#import setsql  # 引入 setsql 來讀取機器設定

def update_to_server(state):
    # 1. 從資料庫讀取設定，而不是寫死
    # 假設您在 machine 表格裡有存 machine_ip 或 server_url
    # machine_info = setsql.read_machine_config() 
    # url = machine_info['server_url']
    # machine_id = machine_info['id']
    
    # 目前先沿用您的，但建議改掉：
    url = "https://192.168.1.103/static/update.php"
    payload = {
        "machine_id": "test001", 
        "machine_state": state
    }
    
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

    try:
        # 設定 Timeout
        response = requests.post(url, data=payload, verify=False, timeout=2)
        if response.status_code != 200:
            print(f"Server returned error: {response.status_code}")
    except Exception as e:
        # 建議只印出簡短錯誤，不要印出一大串 Traceback 嚇到使用者
        print(f"無法上傳狀態 ({state}) 至伺服器 (忽略)")