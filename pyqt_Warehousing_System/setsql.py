import psycopg2
import subprocess
import sys
import update
from contextlib import contextmanager

# --- 全域設定區 ---
DB_CONFIG = {
    "user": "mct",
    "password": "mct123",
    "host": "localhost",
    "port": "5432",
    "dbname": "armconfig"
}
POSTGRES_ADMIN_USER = "postgres"
POSTGRES_ADMIN_PASS = "00123"

# --- 連線管理工具 (Context Manager) ---
@contextmanager
def get_db_connection(db_name=None, user=None, password=None):
    """
    建立資料庫連線的 Context Manager。
    用法: with get_db_connection() as conn: ...
    """
    # 如果沒指定參數，使用預設設定
    target_db = db_name if db_name else DB_CONFIG["dbname"]
    target_user = user if user else DB_CONFIG["user"]
    target_pass = password if password else DB_CONFIG["password"]

    conn = None
    try:
        conn = psycopg2.connect(
            dbname=target_db,
            user=target_user,
            password=target_pass,
            host=DB_CONFIG["host"],
            port=DB_CONFIG["port"]
        )
        conn.autocommit = True # 設定自動提交
        yield conn
    except psycopg2.Error as e:
        # 這裡可以決定要拋出錯誤還是只印出訊息
        print(f"Database connection error: {e}")
        raise e 
    finally:
        if conn:
            conn.close()

# --- 初始化與檢查函式 ---

def check_user_exists():
    """設定 PostgreSQL 使用者"""
    print("Configuring database user...")
    try:
        # 修改 postgres 預設密碼
        subprocess.check_call(["sudo", "-u", "postgres", "psql", "-c", f"ALTER USER postgres WITH PASSWORD '{POSTGRES_ADMIN_PASS}';"])
        
        # 連線到 postgres 預設資料庫來建立 mct 使用者
        with get_db_connection(db_name="postgres", user=POSTGRES_ADMIN_USER, password=POSTGRES_ADMIN_PASS) as conn:
            with conn.cursor() as cursor:
                try:
                    cursor.execute("CREATE USER mct WITH PASSWORD 'mct123';")
                    cursor.execute("ALTER USER mct SUPERUSER;")
                    print("User 'mct' created/configured.")
                except psycopg2.errors.DuplicateObject:
                    print("User 'mct' already exists.")
                except Exception as e:
                    print(f"Warning during user creation: {e}")

    except Exception as e:
        sys.exit(f"An error occurred while configuring the user: {e}")

def check_database():
    """檢查並建立 armconfig 資料庫"""
    print("Configuring database...")
    try:
        # 使用 mct 連線到 postgres 資料庫來檢查 armconfig 是否存在
        with get_db_connection(db_name="postgres") as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'armconfig';")
                if not cursor.fetchone():
                    cursor.execute("CREATE DATABASE armconfig;")
                    print("Database 'armconfig' created successfully!")
                else:
                    print("Database 'armconfig' already exists.")
    except Exception as e:
        sys.exit(f"An error occurred while configuring the database: {e}")

def check_table():
    """檢查並建立必要的表格與初始資料"""
    print("Configuring database tables...")
    
    # 定義初始表格結構與資料，避免重複程式碼
    # 格式: (Table Name, Create SQL, Insert SQL)
    initial_tables = [
        (
            "tableName", 
            "CREATE TABLE tableName (names VARCHAR(20));",
            "INSERT INTO tableName (names) VALUES ('MotorRange'),('prepare'),('A'),('B'),('C');"
        ),
        (
            "MotorRange",
            "CREATE TABLE MotorRange (pwm0 int,pwm1 int,pwm2 int,pwm3 int);",
            "INSERT INTO MotorRange (pwm0, pwm1, pwm2, pwm3) VALUES (900, 1250, 650, 1350);"
        ),
        (
            "prepare",
            "CREATE TABLE prepare (pwm0 int,pwm1 int,pwm2 int,pwm3 int);",
            "INSERT INTO prepare (pwm0, pwm1, pwm2, pwm3) VALUES (0, 0, 0, 90), (-10, 100, 60, 90), (10, 100, 75, 90), (10, 100, 75, 20),(0, 100, 0, 20);"
        ),
        (
            "A", "CREATE TABLE A (pwm0 int,pwm1 int,pwm2 int,pwm3 int);",
            "INSERT INTO A (pwm0, pwm1, pwm2, pwm3) VALUES (90, 10, -10, 20), (90, 10, 20, 20), (90, 10, 20, 90), (90, 10, -10, 90), (0, 0, 0, 90);"
        ),
        (
            "B", "CREATE TABLE B (pwm0 int,pwm1 int,pwm2 int,pwm3 int);",
            "INSERT INTO B (pwm0, pwm1, pwm2, pwm3) VALUES (25, 10, 0, 20), (50, 10, 50, 20), (50, 10, 50, 90), (50, 10, 0, 90), (0, 0, 0, 90);"
        ),
        (
            "C", "CREATE TABLE C (pwm0 int,pwm1 int,pwm2 int,pwm3 int);",
            "INSERT INTO C (pwm0, pwm1, pwm2, pwm3) VALUES (0, 10, 70, 20), (10, 10, 95, 20), (10, 10, 95, 90), (0, 10, 70, 90), (0, 0, 0, 90);"
        ),
        (
            "machine",
            "CREATE TABLE machine (machine_id VARCHAR(20) PRIMARY KEY, machine_name VARCHAR(20) NOT NULL, machine_location VARCHAR(20) NOT NULL, machine_ip VARCHAR(30) NOT NULL, machine_addtime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP, machine_state INT NOT NULL);",
            "INSERT INTO machine (machine_id, machine_name, machine_location, machine_ip, machine_state) VALUES ('test001','mct001','ksu','mct001.local','100');"
        )
    ]

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                for name, create_sql, insert_sql in initial_tables:
                    try:
                        # 嘗試建立表格
                        cursor.execute(create_sql)
                        # 只有在建立成功時 (代表表格原本不存在) 才插入初始資料
                        cursor.execute(insert_sql)
                        print(f"Table '{name}' configured successfully!")
                    except psycopg2.errors.DuplicateTable:
                        # 如果表格已存在，psycopg2 會拋出 DuplicateTable 錯誤
                        # 這裡我們捕捉它並忽略，不做任何事
                        print(f"Table '{name}' already exists.")
                    except Exception as inner_e:
                         # 捕捉其他特定表格的錯誤，但不中斷整個迴圈
                        print(f"Warning configuring table '{name}': {inner_e}")
                        
    except Exception as e:
        sys.exit(f"An error occurred while configuring tables: {e}")

# --- 資料讀寫函式 ---

def take_names():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM tablename;")
                # 這裡簡化 List Comprehension
                return [item[0] for item in cursor.fetchall()]
    except Exception as e:
        sys.exit(f"Error retrieving names: {e}")

def take_range():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT * FROM MotorRange;")
                data = cursor.fetchone() # MotorRange 應該只有一行設定
                if data:
                    return list(data)
                return [0,0,0,0] # 預設值防呆
    except Exception as e:
        sys.exit(f"Error retrieving MotorRange: {e}")

def read_sql(tableName):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 注意：Table name 不能參數化，需確保 tableName 來源安全
                cursor.execute(f"SELECT * FROM {tableName};")
                return [list(item) for item in cursor.fetchall()]
    except Exception as e:
        print(f"Error reading data from {tableName}: {e}")
        return [] # 回傳空陣列避免 UI 崩潰

def write_sql(tableName, array):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"TRUNCATE TABLE {tableName};")
                if not array:
                    return
                
                # 建構 VALUES 字串: (val1, val2, val3, val4), (val...)
                # 這裡沿用原本的字串拼接邏輯
                values_str = ", ".join(f"({', '.join(map(str, row))})" for row in array)
                cursor.execute(f"INSERT INTO {tableName} (pwm0, pwm1, pwm2, pwm3) VALUES {values_str};")
    except Exception as e:
        print(f"Error saving data to {tableName}: {e}")

def drop_table(tableName):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # 先刪除 tablename 表中的紀錄
                cursor.execute(f"DELETE FROM tablename WHERE names = '{tableName}';")
                # 再刪除實際表格
                cursor.execute(f"DROP TABLE {tableName};")
    except Exception as e:
        print(f"Error deleting table {tableName}: {e}")

def add_table(tableName):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"INSERT INTO tablename VALUES ('{tableName}');")
                cursor.execute(f"CREATE TABLE {tableName} (pwm0 int,pwm1 int,pwm2 int,pwm3 int);")
                cursor.execute(f"INSERT INTO {tableName} (pwm0, pwm1, pwm2, pwm3) VALUES (0, 0, 0, 90);")
    except Exception as e:
        print(f"Error creating table {tableName}: {e}")

def state_update(value):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(f"UPDATE machine SET machine_state = '{value}';")
    except Exception as e:
        print(f"Error updating machine state locally: {e}")
    
    # 呼叫 update.py 上傳到伺服器
    update.update_to_server(value)