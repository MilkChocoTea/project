import psycopg2
import subprocess
import sys

def check_user_exists():
    subprocess.check_call(["sudo", "-u", "postgres", "psql","-c","ALTER USER postgres WITH PASSWORD '00123';"])
    print("Configuring database user...")
    try:
        with psycopg2.connect(
            dbname="postgres",
            user="postgres",
            password="00123",
            host="localhost",
            port="5432"
        ) as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                try:
                    cursor.execute("CREATE USER mct WITH PASSWORD 'mct123';")
                    cursor.execute("ALTER USER mct SUPERUSER;")
                except:
                    pass
    except Exception as e:
        sys.exit(f"An error occurred while configuring the user：{e}")

def check_database():
    print("Configuring database...")
    try:
        connection = psycopg2.connect(
            dbname="postgres",
            user="mct",
            password="mct123",
            host="localhost",
            port="5432"
        )
        connection.autocommit = True
        cursor = connection.cursor()
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'armconfig';")
        exists = cursor.fetchone() is not None
        if exists==False:
            cursor.execute("CREATE DATABASE armconfig;")
            print("Database armconfig configured successfully！")
        cursor.close()
        connection.close()
    except Exception as e:
        sys.exit(f"An error occurred while configuring the database：{e}")

def check_table():
    print("Configuring database table...")
    try:
        with psycopg2.connect(
            dbname="armconfig",
            user="mct",
            password="mct123",
            host="localhost",
            port="5432"
        ) as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                try:
                    cursor.execute("CREATE TABLE tableName (names VARCHAR(20));")
                    cursor.execute("INSERT INTO tableName (names) VALUES ('MotorRange'),('prepare'),('A'),('B'),('C');")
                    print("Table tableName configured successfully！")
                except:
                    pass
                try:
                    cursor.execute("CREATE TABLE MotorRange (pwm0 int,pwm1 int,pwm2 int,pwm3 int);")
                    cursor.execute("INSERT INTO MotorRange (pwm0, pwm1, pwm2, pwm3) VALUES (900, 1250, 650, 1350);")
                    print("Table MotorRange configured successfully！")
                except:
                    pass
                try:
                    cursor.execute("CREATE TABLE prepare (pwm0 int,pwm1 int,pwm2 int,pwm3 int);")
                    cursor.execute("INSERT INTO prepare (pwm0, pwm1, pwm2, pwm3) VALUES (0, 0, 0, 90), (-10, 100, 60, 90), (10, 100, 75, 90), (10, 100, 75, 20),(0, 100, 0, 20);")
                    print("Table prepare configured successfully！")
                except:
                    pass
                try:
                    cursor.execute("CREATE TABLE A (pwm0 int,pwm1 int,pwm2 int,pwm3 int);")
                    cursor.execute("INSERT INTO A (pwm0, pwm1, pwm2, pwm3) VALUES (90, 10, -10, 20), (90, 10, 20, 20), (90, 10, 20, 90), (90, 10, -10, 90), (0, 0, 0, 90);")
                    print("Table A configured successfully！")
                except:
                    pass
                try:
                    cursor.execute("CREATE TABLE B (pwm0 int,pwm1 int,pwm2 int,pwm3 int);")
                    cursor.execute("INSERT INTO B (pwm0, pwm1, pwm2, pwm3) VALUES (25, 10, 0, 20), (50, 10, 50, 20), (50, 10, 50, 90), (50, 10, 0, 90), (0, 0, 0, 90);")
                    print("Table B configured successfully！")
                except:
                    pass
                try:
                    cursor.execute("CREATE TABLE C (pwm0 int,pwm1 int,pwm2 int,pwm3 int);")
                    cursor.execute("INSERT INTO C (pwm0, pwm1, pwm2, pwm3) VALUES (0, 10, 70, 20), (10, 10, 95, 20), (10, 10, 95, 90), (0, 10, 70, 90), (0, 0, 0, 90);")
                    print("Table C configured successfully！")
                except:
                    pass
    except Exception as e:
        sys.exit(f"An error occurred while configuring the table：{e}")

def take_names():
    try:
        with psycopg2.connect(
            dbname="armconfig",
            user="mct",
            password="mct123",
            host="localhost",
            port="5432"
        ) as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM tablename;")
                data = cursor.fetchall()
                result = [item[0] for item in data]
                return(result)
    except Exception as e:
        sys.exit(f"An error occurred while retrieving the name：{e}")

def take_range():
    try:
        with psycopg2.connect(
            dbname="armconfig",
            user="mct",
            password="mct123",
            host="localhost",
            port="5432"
        ) as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM MotorRange;")
                data = cursor.fetchall()
                result = [list(item) for item in data]
                return(result[0])
    except Exception as e:
        sys.exit(f"An error occurred while retrieving the initial PWM value：{e}")

def read_sql(tableName):
    try:
        with psycopg2.connect(
            dbname="armconfig",
            user="mct",
            password="mct123",
            host="localhost",
            port="5432"
        ) as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute(f"SELECT * FROM {tableName};")
                data = cursor.fetchall()
                result = [list(item) for item in data]
                return(result)
    except Exception as e:
        print(f"An error occurred while reading data：{e}")

def write_sql(tableName,array):
    try:
        with psycopg2.connect(
            dbname="armconfig",
            user="mct",
            password="mct123",
            host="localhost",
            port="5432"
        ) as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute(f"TRUNCATE TABLE {tableName};")
                data = ", ".join(f"({', '.join(map(str, row))})" for row in array)
                cursor.execute(f"INSERT INTO {tableName} (pwm0, pwm1, pwm2, pwm3) VALUES {data};")
    except Exception as e:
        print(f"An error occurred while saving data：{e}")

def drop_table(tableName):
    try:
        with psycopg2.connect(
            dbname="armconfig",
            user="mct",
            password="mct123",
            host="localhost",
            port="5432"
        ) as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute(f"DELETE FROM tablename WHERE names = ('{tableName}');")
                cursor.execute(f"DROP TABLE {tableName};")
    except Exception as e:
        print(f"An error occurred while deleting the table：{e}")

def add_table(tableName):
    try:
        with psycopg2.connect(
            dbname="armconfig",
            user="mct",
            password="mct123",
            host="localhost",
            port="5432"
        ) as connection:
            connection.autocommit = True
            with connection.cursor() as cursor:
                cursor.execute(f"INSERT INTO tablename VALUES ('{tableName}');")
                cursor.execute(f"CREATE TABLE {tableName} (pwm0 int,pwm1 int,pwm2 int,pwm3 int);")
                cursor.execute(f"INSERT INTO {tableName} (pwm0, pwm1, pwm2, pwm3) VALUES (0, 0, 0, 90);")
    except Exception as e:
        print(f"An error occurred while creating the table：{e}")
