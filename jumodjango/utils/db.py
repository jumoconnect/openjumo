from django.db import connections

def db_time(db='default'):
    cur = connections[db].cursor()
    cur.execute('select utc_timestamp()')
    return cur.fetchone()[0]