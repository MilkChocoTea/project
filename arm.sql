\c arm
ALTER USER mct WITH PASSWORD '00123';
SET timezone = 'Asia/Taipei';

CREATE TABLE machines (machine_id VARCHAR(20) PRIMARY KEY,machine_name VARCHAR(20) NOT NULL,machine_location VARCHAR(20) NOT NULL,machine_ip VARCHAR(30) NOT NULL,machine_addtime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,machine_state INT NOT NULL,machine_statetime TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,machine_remark VARCHAR(50));
INSERT INTO machines (machine_id, machine_name, machine_location, machine_ip, machine_state, machine_remark) VALUES ('test001', 'mct001', 'ksu', 'mct001.local', 1, 'none'),('test002','mct002','R0509','mct002.local',0,'none');
CREATE TABLE staff (staff_id SERIAL PRIMARY KEY,staff_name VARCHAR(50) NOT NULL,username VARCHAR(30) UNIQUE NOT NULL,position VARCHAR(15),department VARCHAR(20),schedule TEXT,contact_info VARCHAR(30),password_hash TEXT NOT NULL,status INT DEFAULT 1,create_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP);
insert into staff (staff_name,username,position,department,schedule,contact_info,password_hash,status)values('test','KSUtest','none','ksu','none','line','$2y$10$qQJ0nlu/QNNjHsnaVLz8l./Se1lZYdYkC6d.Gfs2gNnLvtG46aFpK',1);
CREATE TABLE item (item_id SERIAL PRIMARY KEY,item_name VARCHAR(20) NOT NULL,category VARCHAR(20),quantity INT DEFAULT 1,location VARCHAR(10),unit_price INT DEFAULT 1,supplier VARCHAR(50),warehouse_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,shipping_time TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,remark VARCHAR(100),last_update TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP);
insert into item (item_name,category,quantity,location,unit_price,supplier,remark)values('001','test',10,'B',200,'ksu','none');

GRANT ALL PRIVILEGES ON DATABASE arm TO mct;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO mct;

CREATE OR REPLACE FUNCTION notify_database_change() RETURNS TRIGGER AS $$ BEGIN PERFORM pg_notify('database_change', 'refresh'); RETURN NEW; END; $$ LANGUAGE plpgsql;
CREATE TRIGGER staff_data_change AFTER INSERT OR UPDATE OR DELETE ON staff FOR EACH ROW EXECUTE FUNCTION notify_database_change();
CREATE TRIGGER machines_data_change AFTER INSERT OR UPDATE OR DELETE ON machines FOR EACH ROW EXECUTE FUNCTION notify_database_change();
CREATE TRIGGER item_data_change AFTER INSERT OR UPDATE OR DELETE ON item FOR EACH ROW EXECUTE FUNCTION notify_database_change();