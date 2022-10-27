import psycopg
import time
import os
import urllib.parse as urlparse

url = urlparse.urlparse(os.getenv('DATABASE_URL'))
dbname = url.path[1:]
user = url.username
password = url.password
host = url.hostname
port = url.port

conn = psycopg.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
            )

def check_table_existence(table_name):
    with conn.cursor() as cur:
        cur.execute("select * from information_schema.tables where table_name=%s", (table_name,))
        return bool(cur.rowcount)

def create_job_table(table_name):
    with conn.cursor() as cur:
        query = """
        CREATE TABLE {} (
            id serial PRIMARY KEY,
            job_id bigint,
            department_id bigint,
            office_id bigint,
            job_name text,
            location text,
            fetched_time integer)
        """.format(table_name) 
        executed_query = cur.execute(query)
        conn.commit()
        return executed_query

def enter_job(table_name,job):
    with psycopg.ClientCursor(conn) as cur:
        query = """
        INSERT INTO {} (job_id, department_id, office_id, job_name, location, fetched_time) VALUES (%s, %s, %s, %s, %s, %s);
        """.format(table_name)
        entry_params = (job['job_id'],job['department_id'],job['office_id'],job['name'],job['location'],int(time.time()))
        query = cur.execute(query,entry_params)
        conn.commit()
    return query

def fetch_all_jobs(table_name):
    '''Returns a set of job IDs'''
    eph_jobset = set()
    with psycopg.ClientCursor(conn) as cur:
        query = cur.execute("""
        SELECT job_id FROM {}
        """.format(table_name))
        for item in query.fetchall():
            eph_jobset.add(str(item[0]))
        return eph_jobset

def clear_all_jobs(table_name):
    query = "DELETE FROM {};".format(table_name)
    with psycopg.ClientCursor(conn) as cur:
        exec_query = cur.execute(query)
        conn.commit()
    return True

if __name__ == "__main__":
    pass