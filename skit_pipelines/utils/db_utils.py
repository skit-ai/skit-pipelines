
import psycopg2

def get_connections(dbname, user, password, host, port):
    conn = ''
    conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port)
    return conn