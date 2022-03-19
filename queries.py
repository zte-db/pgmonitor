# use full names instead of nick names (i.e., vars instead of nick)
# if you want to add a metric, please add the pg_* function and modify the following functions:
# get_metrics, get_ftypes, get_init_prev, get_vars, get_functions
# notice: if you want to remove pg_time, please modify the default '--omit' in pgmonitor.py

def get_metrics():
    return ['time', 'dbsize', 'conn', 'lockwaits', 'transactions', 'buffer', 'settings']

# if need to remember previous result (for divided by time), then 1
def get_ftypes():
    return [0, 1, 0, 0, 1, 1, 0]

# init previous result never affects the output. set as 0
def get_init_prev():
    return {1:[0]*4, 4:[0]*2, 5:[0]*2}

def get_names(title, names):
    return [title + '-' + x for x in names]

def get_vars(valid):
    ans = []

    if valid[0]:
        vars = ('time_now',)
        ans += get_names('pg_time', vars)

    if valid[1]:
        vars = ('dbsize', 'grow_rate', 'inserted',
                'updated', 'deleted')
        ans += get_names('pg_dbsize', vars)

    if valid[2]:
        vars = ('conn_cnt', 'conn_cnt_rate',
                'conn_active_cnt', 'long_query_cnt',
                'long_transaction_cnt', 'idl_cnt',
                'long_idl_cnt', 'long_waiting_cnt',
                'sqls_1sec', 'sqls_3sec',
                'sqls_5sec',
                'transactions_1sec', 'transactions_3sec',
                )
        ans += get_names('pg_conn', vars)

    if valid[3]:
        vars = ('lock_num',)
        ans += get_names('pg_lockwaits', vars)

    if valid[4]:
        vars = ('commit', 'rollback')
        ans += get_names('pg_transactions', vars)

    if valid[5]:
        vars = ('clean', 'backend',
                'alloc',
                'heap_blks_read', 'heap_blks_hit', 'ratio_hit',
                )
        ans += get_names('pg_buffer', vars)
        
    if valid[6]:
        vars = ('shared_buffers',
                'work_mem', 'bgwriter_delay',
                'max_connections',
                'autovacuum_work_mem',
                'temp_buffers', 'autovacuum_max_workers',
                'maintenance_work_mem', 'checkpoint_timeout',
                'max_wal_size', 'checkpoint_completion_target',
                'wal_keep_segments', 'wal_segment_size')
        ans += get_names('pg_settings', vars)

    return ans


def pg_time(c):
    val = [0]
    c.execute('select ceil(extract(epoch from now()));')
    t = c.fetchone()[0]
    val[0] = int(t)
    return val

def pg_dbsize(c, prev, elapsed):
    val = [0]*5
    c.execute("select sum(pg_database_size(oid)) from pg_database;")
    dbsize = float(c.fetchone()[0])
    c.execute(
        'select sum(tup_inserted),sum(tup_updated),sum(tup_deleted) from pg_stat_database;')
    records = c.fetchone()
    curr = [dbsize, float(records[0]), float(records[1]), float(records[2])]

    val[0] = dbsize
    for i in range(4):
        val[i+1] = float(curr[i] - prev[i]) / elapsed
    return val, curr

# debug
# flagg = 0
def pg_conn(c):
    # global flagg
    # if flagg < 8:
    #     print(flagg)
    #     flagg += 1
    #     c.execute("select pg_sleep(0.5);")
    val = [0]*13
    c.execute("select count(*) used from pg_stat_activity")
    conn_cnt = c.fetchone()[0]
    c.execute(
        "select setting::int max_conn from pg_settings where name=$$max_connections$$")
    max_conn = c.fetchone()[0]
    c.execute(
        "select setting::int res_for_super from pg_settings where name=$$superuser_reserved_connections$$")
    res_for_super_conn = c.fetchone()[0]
    c.execute(
        "select count(*) from pg_stat_activity where state = 'active'")
    conn_cnt_activate = c.fetchone()[0]
    c.execute(
        "select count(*) from pg_stat_activity where state = 'active' and now()-query_start > interval '15 second';")
    long_query_cnt = c.fetchone()[0]
    c.execute(
        "select count(*) from pg_stat_activity where now()-xact_start > interval '15 second';")
    long_transaction_cnt = c.fetchone()[0]
    c.execute(
        "select count(*) from pg_stat_activity where state='idle in transaction'")
    idl_cnt = c.fetchone()[0]
    c.execute(
        "select count(*) from pg_stat_activity where state='idle in transaction' and now()-state_change > interval '15 second';")
    long_idl_cnt = c.fetchone()[0]
    c.execute(
        "select count(*) from pg_stat_activity where wait_event_type is not null and now()-state_change > interval '15 second';")
    long_waiting_cnt = c.fetchone()[0]
    c.execute("select count(*) from pg_stat_activity where date_part('epoch',now()-query_start)>1 and state<>'idle';")
    sqls_1sec = c.fetchone()[0]
    c.execute("select count(*) from pg_stat_activity where date_part('epoch',now()-query_start)>3 and state<>'idle';")
    sqls_3sec = c.fetchone()[0]
    c.execute("select count(*) from pg_stat_activity where date_part('epoch',now()-query_start)>5 and state<>'idle';")
    sqls_5sec = c.fetchone()[0]
    c.execute("select count(*) from pg_stat_activity where date_part('epoch',now()-xact_start)>1 and state<>'idle';")
    transactions_1sec = c.fetchone()[0]
    c.execute("select count(*) from pg_stat_activity where date_part('epoch',now()-xact_start)>3 and state<>'idle';")
    transactions_3sec = c.fetchone()[0]

    val[0] = conn_cnt
    val[1] = conn_cnt/max_conn
    val[2] = conn_cnt_activate
    val[3] = long_query_cnt
    val[4] = long_transaction_cnt
    val[5] = idl_cnt
    val[6] = long_idl_cnt
    val[7] = long_waiting_cnt
    val[8] = sqls_1sec
    val[9] = sqls_3sec
    val[10] = sqls_5sec
    val[11] = transactions_1sec
    val[12] = transactions_3sec
    return val

def pg_lockwaits(c):
    val = [0]
    c.execute('select count(1) from pg_locks where granted is false;')
    val[0] = c.fetchone()[0]
    return val

def pg_transactions(c, prev, elapsed):
    val = [0]*2
    c.execute('SELECT sum(xact_commit),sum(xact_rollback) FROM pg_stat_database;')
    curr = c.fetchone()
    for i in range(2):
        val[i] = float(curr[i] - prev[i]) / elapsed
    return val, curr

def pg_buffer(c, prev, elapsed):
    val = [0]*6
    
    c.execute("select buffers_clean,buffers_backend,buffers_alloc from pg_stat_bgwriter")
    clean, backend, alloc = c.fetchone()
    c.execute("select sum(heap_blks_read), sum(heap_blks_hit) FROM pg_statio_all_tables")
    curr = c.fetchone()

    val[0] = clean
    val[1] = backend
    val[2] = alloc
    rd = float(curr[0] - prev[0]) / elapsed
    val[3] = rd
    hd = float(curr[1] - prev[1]) / elapsed
    val[4] = hd
    val[5] = int(hd)*1.0 / (int(hd)+int(rd)+0.00001)
    return val, curr

def pg_settings(c):
    vars = ('shared_buffers',
            'work_mem', 'bgwriter_delay',
            'max_connections',
            'autovacuum_work_mem',
            'temp_buffers', 'autovacuum_max_workers',
            'maintenance_work_mem', 'checkpoint_timeout',
            'max_wal_size', 'checkpoint_completion_target',
            'wal_keep_segments', 'wal_segment_size')
    val = []
    c.execute('select name, setting from pg_settings where name in {};'.format(vars))
    res = c.fetchall()
    for _, v in res:
        v = float(v)
        val.append(v)
    return val

def get_functions():
    return (pg_time, pg_dbsize, pg_conn, pg_lockwaits, pg_transactions, pg_buffer, pg_settings)