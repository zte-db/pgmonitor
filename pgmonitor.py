import os
import psycopg2
import time
import argparse
from queries import *

# close psycopg2 connection safely
def safeclosec(conn):
    try:
        conn.close()
    except:
        pass

# args:
# config: database connection config
# progress: how many metrics have been collected
# info: information of this monitoring process, never change as a recursive function
# chances: number of re-connection chances
# results: a dict for results, int keys, list values
# return:
# if time up or no more chances, return 1; else return 0
def monitor(config, progress, info, chances, results):
    host, port, user, pwd = config
    pos, curr = progress
    ddl, valid, prev, elapsed, functions, ftypes = info

    # connect or re-connect
    conn = psycopg2.connect(host=host, port=port, user=user, password=pwd)
    cursor = conn.cursor()
    now = time.time()
    if now >= ddl:
        return 1
    cursor.execute('SET statement_timeout = \'{}s\''.format((ddl-now)/(chances+1)))

    # check all metrics
    for i in range(len(ftypes)):
        try:
            if pos <= i and valid[i] == 1:
                if ftypes[i] == 0:
                    val = functions[i](cursor)
                else:
                    val, cu = functions[i](cursor, prev[i], elapsed)
                    curr[i] = cu
                results[i] = val
        except KeyboardInterrupt:
            print('Interrupted by Ctrl+C')
            exit()
        except:
            print('Failed at', functions[i])
            safeclosec(conn)
            if time.time() >= ddl or chances == 0:
                return 1
            return monitor(config, (i, curr), info, chances-1, results)
        if time.time() >= ddl:
            return 1

    safeclosec(conn)
    return 0

def parseargs():
    parser = argparse.ArgumentParser(description='args')
    parser.add_argument('--interval',type=int,default=5,help='interval of data collection')
    parser.add_argument('--omit',type=str,default='time',help='metrics to omit, separated by comma')
    parser.add_argument('--host',type=str,default='localhost',help='host IP of the PG server')
    parser.add_argument('--port',type=int,default=5432,help='port of the PG server')
    parser.add_argument('--user',type=str,default='postgres',help='user name of PG')
    parser.add_argument('--pwd',type=str,default='postgres',help='password of the PG user')
    parser.add_argument('--chances',type=int,default=4,help='number of maximum re-connection allowed')
    parser.add_argument('--printall',action='store_true',default=False,help='print all monitoring data')
    parser.add_argument('--check',action='store_true',default=False,help='check the first piece of data, if invalid then exit')
    parser.add_argument('--output',type=str,default='metrics.csv',help='output csv file name')
    args = parser.parse_args()
    interval = args.interval
    omit = args.omit
    host = args.host
    port = args.port
    user = args.user
    pwd = args.pwd
    chances = args.chances
    printall = args.printall
    check = args.check
    fname = args.output
    return interval, omit, host, port, user, pwd, chances, printall, check, fname

def get_valid(omit, metrics):
    try:
        valid = [1] * len(metrics)
        for x in omit.split(','):
            if x != '':
                valid[metrics.index(x)] = 0
        return valid
    except:
        print('Initialization error, please check the \'--omit\' argument and the metrics.')
        exit()

def run_monitor(interval, valid, config, fname, printall, chances, check):
    functions = get_functions()
    ftypes = get_ftypes()

    f = open(fname, 'w')
    vars = ','.join(get_vars(valid))
    vars = 'time,'+vars
    f.writelines([vars, '\n'])
    f.flush()

    if printall:
        print(vars)

    st = time.time()
    prev = get_init_prev()
    curr = {}
    # ddl, valid, prev, elapsed, functions, ftypes
    info = (st+interval*0.8, valid, prev, interval, functions, ftypes)
    results = {}
    x = monitor(config, (0, curr), info, chances, results)
    now = time.time()
    if x != 0 or now - st > interval:
        print('First piece of data invalid, please check the database system!')
        if check:
            exit()
        else:
            curr = prev

    while True:
        prev = curr
        curr = {}
        results = {}
        st1 = st + interval

        # get next timestamp
        now = time.time()
        while st1 <= now:
            st1 += interval
        
        try:
            time.sleep(st1 - now)
            x = monitor(config, (0, curr), (st1+interval*0.8, valid, prev, st1-st, functions, ftypes), chances, results)
        except KeyboardInterrupt:
            print('Interrupted by Ctrl+C')
            exit()
        except:
            x = 2
            
        now = time.time()
        if x != 0 or now - st1 > interval:
            print('Missing data at {} with error {}'.format(st1, x))
        else:
            strs = []
            for i in range(len(valid)):
                if valid[i]:
                    strs.append(','.join([str(x) for x in results[i]]))
            allstrs = ','.join(strs)
            allstrs = str(int(st1))+','+allstrs
            f.writelines([allstrs, '\n'])
            f.flush()
            if printall:
                print(allstrs)
        st = st1

if __name__=='__main__':
    interval, omit, host, port, user, pwd, chances, printall, check, fname = parseargs()
    metrics = get_metrics()
    valid = get_valid(omit, metrics)
    config = (host, port, user, pwd)
    run_monitor(interval, valid, config, fname, printall, chances, check)
        

    

