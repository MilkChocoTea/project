from flask import Flask
from flask_socketio import SocketIO
import psycopg2
import time

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# 連接 PostgreSQL
conn = psycopg2.connect("dbname=arm_user user=mct password=00123 host=localhost port=5432")
cursor = conn.cursor()
cursor.execute("LISTEN database_change;")  # 監聽 `database_change`
conn.commit()

def listen_for_changes():
    """ 在背景監聽 PostgreSQL 變更 """
    print("📡 開始監聽資料庫變更...")
    while True:
        try:
            conn.poll()
            while conn.notifies:
                notify = conn.notifies.pop(0)
                socketio.emit("update", {"message": "🔄 資料庫發生變更！"})
        except Exception as e:
            print(f"⚠️ 監聽資料庫變更時發生錯誤: {e}")
        time.sleep(1)

@socketio.on("connect")
def handle_connect():
    print("📡 客戶端已連線！")
    socketio.start_background_task(listen_for_changes)

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5000, )
