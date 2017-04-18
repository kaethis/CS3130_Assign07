#!/usr/bin/env python3

import socket

import threading

import argparse

import dbmgr

import cachemgr

import ui


err = {  'NOFILE'  : 'FILE NOT FOUND!',
         'NOCONF'  : 'DATABASE NOT CONFIGURED!',
         'TIMEOUT' : 'CONNECTION TIMED OUT!',
         'CONNREF' : 'CONNECTION REFUSED!',
         'INVREQ'  : 'INVALID REQUEST!',
         'INVKEY'  : 'INVALID OR EXISTING KEY!',
         'NOREC'   : 'NO RECORDS FOUND!',
         'DEBUG'   : 'AS ABOVE SO BELOW!' }

reqs = { 'GETUPD'  : 'FETCH TIME LAST UPDATED...',
         'GETSCH'  : 'FETCH SCHEMA...',
         'GETRECS' : 'FETCH ALL RECORDS...',
         'ADDREC'  : 'ADD RECORD...',
         'DELREC'  : 'DELETE RECORD...',
         'CONNEND' : 'END CONNECTION... GOODBYE!' }

succ = { 'ADDOK'   : 'RECORD ADDED.',
         'DELOK'   : 'RECORD DELETED.',
         'ENDOK'   : 'GOOBYE.' }


MAX_BYTES = 1024

def worker(sock, address, db):


    while True:

        data, tmp = sock.recvfrom(MAX_BYTES)

        if not data: break


        output = '\nREQUEST FROM [{}] [{}]'

        output = output.format(address[0], address[1])

        print(output)


        text = data.decode('ascii').split('#')

        req = text[0]

        if req in reqs.keys():

            if req == 'CONNEND':

                print(reqs[req])

                ret = 'ENDOK'


            elif req == 'GETUPD':

                ret = repr(db.getUpdated())

                print(reqs[req], ret)


            elif req == 'GETSCH':

                ret = repr(db.getSchema())

                print(reqs[req])


            elif req == 'GETRECS':

                ret = repr(db.getRecords())

                print(reqs[req])


            elif req == 'ADDREC':

                attrs = eval(text[1])

                key = attrs[0]

                print('{} {}:{}'.format(reqs[req], key, attrs))


                if db.add(key, attrs):

                    db.setUpdated()

                    ret = 'ADDOK'

                    print(succ[ret])

                else:

                    ret = 'INVKEY'

                    print(err[ret])


            elif req == 'DELREC':

                key = eval(text[1])

                print('{} {}'.format(reqs[req], key))


                if db.delete(key):

                    db.setUpdated()

                    ret = 'DELOK'

                    print(succ[ret])

                else:

                    ret = 'INVKEY'

                    print(err[ret])

        else:

            ret = 'INVREQ'

            print(err[ret])


        sock.sendto(ret.encode('ascii'), address)


    output = '\nCONNECTION CLOSED [{}] [{}]'

    output = output.format(address[0], address[1])

    print(output)


    sock.close()


def server(args):

    db = dbmgr.Database(host='localhost', port=6379, index=1)


    if args.csv:

        try:

            with open(args.csv, 'r') as file:

                db.load(file.read())

        except FileNotFoundError:

            print(err['NOFILE'])

            quit()


    if not db.getConfig():

        print(err['NOCONF'])

        quit()


    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    sock.bind((args.host, args.p))

    sock.listen(1)


    output = '\nLISTENING AT [{}] [{}]'

    output = output.format(args.host, args.p)

    print(output)


    while True:

        sc, sockname = sock.accept()


        t = threading.Thread(target=worker, args=(sc, sockname, db))

        t.is_daemon = True;

        t.start()


        output = '\nCONNECTION ESTABLISHED [{}] [{}]'

        output = output.format(sockname[0], sockname[1])

        print(output)


    sock.close()


def request(sock, data):

    timeout = 10  # seconds

    while True:

        sock.send(data)

        sock.settimeout(timeout)

        try:

            data = sock.recv(MAX_BYTES)

        except socket.timeout as exc: return 'TIMEOUT'

        except:                       return 'CONNREF'

        else:                         return data.decode('ascii')


def client(args):

    def fetchUpdated(sock):

        ret = request(sock, 'GETUPD'.encode('ascii'))

        if str(ret) in err:

            y, x = 1, 2

            ui.alert(y, x, err[ret])

            ui.exit()


            quit()

        else: return eval(ret)


    def fetchSchema(sock):

        ret = request(sock, 'GETSCH'.encode('ascii'))

        if str(ret) in err:

            y, x = 1, 2

            ui.alert(y, x, err[ret])

            ui.exit()


            quit()

        else: return eval(ret)


    def fetchRecords(sock):
 
        ret = request(sock, 'GETRECS'.encode('ascii'))

        if str(ret) in err:

            y, x = 1, 2

            ui.alert(y, x, err[ret])

            ui.exit()


            quit()

        else: return eval(ret)


    ui.init()


    cache = cachemgr.Cache(host='localhost', port=11211)
    

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try: sock.connect((args.host, args.p))

    except:

        y, x = 1, 2

        ui.alert(y, x, err['CONNREF'])

        ui.exit()

        quit()


    server_time = fetchUpdated(sock)

    schema = fetchSchema(sock)

    collect = fetchRecords(sock)

    cache.consolidate(server_time, schema, collect)


    schema = cache.getSchema()

    collect = cache.getRecords()

    sel = 0

    while True:

        y, x = 1, 2

        height = 13

        ret = ui.menuwin(y, x, height, sel, schema, collect) 


        if ui.keyboard['ESC'] in ret:

            sel = ret[1]

            y, x = 1, 2

            if ui.confirm(y, x, 'EXIT?'):

                ret = request(sock, 'CONNEND'.encode('ascii'))

                if str(ret) in err:

                    y, x = 1, 2

                    ui.alert(y, x, err[ret])

                elif str(ret) in succ:

                    y, x = 1, 2

                    ui.alert(y, x, succ[ret])

                ui.exit()

                quit()


        elif ui.keyboard['S'] in ret:

            sel = ret[1]


            y, x = 1, 2

            title = 'SEARCH'

            length = 30

            typech = 'VARCHAR'

            ret = ui.textwin(y, x, typech, length, title, False)

            if not ret == ui.keyboard['ESC']:

                sel = 0

 
                if not cache.getUpdated() == server_time:

                    y, x = 1, 2

                    ui.alert(y, x, 'CONSOLIDATING...')


                    collect = fetchRecords(sock)

                    cache.consolidate(server_time, schema, collect)
               

                search = cache.search(ret)

                if not search:

                    y, x = 1, 2

                    ui.alert(y, x, err['NOREC'])

                else:

                    y, x, 1, 2

                    ui.alert(y, x, '{} RECORD(S) FOUND.'.format(len(search)))


                    collect = search

                    
        elif ui.keyboard['A'] in ret:

            sel = ret[1]


            attrs, lens, typechs, is_hiddens = [], [], [], []

            for s in schema:

                attrs.append(str(s[0]))

                lens.append(int(s[1]))

                typechs.append(str(s[2]))

                is_hiddens.append(False)


            y, x = 1, 2

            ret = ui.multitextwinv(y, x, typechs, lens, attrs, is_hiddens)

            if not ret == ui.keyboard['ESC']:

                req = '{}#{}'.format('ADDREC', repr(ret))

                ret = request(sock, req.encode('ascii'))

                if str(ret) in err:

                    y, x = 1, 2

                    ui.alert(y, x, err[ret])

                elif str(ret) in succ:

                    y, x = 1, 2

                    ui.alert(y, x, succ[ret])

                    sel = 0

                server_time = fetchUpdated(sock)


        elif ui.keyboard['D'] in ret and collect:

            sel = ret[1]

            for i, rec in enumerate(collect):

                if i == sel: key = rec[schema[0][0]]


            y, x = 1, 2

            if ui.confirm(y, x, 'DELETE {}?'.format(key)):

                req = '{}#{}'.format('DELREC', repr(key))

                ret = request(sock, req.encode('ascii'))

                if str(ret) in err:

                    y, x = 1, 2

                    ui.alert(y, x, err[ret])

                elif str(ret) in succ:

                    y, x = 1, 2

                    ui.alert(y, x, succ[ret])

                    sel = 0

                server_time = fetchUpdated(sock)


        elif ui.keyboard['R'] in ret:

            y, x = 1, 2

            if ui.confirm(y, x, 'REFRESH?'):

                server_time = fetchUpdated(sock)

                collect = fetchRecords(sock)

                cache.consolidate(server_time, schema, collect)


        if not cache.getUpdated() == server_time:

            y, x = 1, 2

            ui.alert(y, x, 'CONSOLIDATING...')


            collect = fetchRecords(sock)

            cache.consolidate(server_time, schema, collect)


if __name__ == '__main__':

    description = '''
                  '''

    parser = argparse.ArgumentParser(description=description)


    choices = { 'client' : client,
                'server' : server }

    parser.add_argument('role',
                        choices=choices,
                        help='which role to take')

    parser.add_argument('host',
                        help='''if client, host the client connects to;
                                else if server, interface the server
                                listens at''')

    parser.add_argument('-p',
                        metavar='port',
                        type=int,
                        default=2001,
                        help='TCP port (default 2001)')

    parser.add_argument('-csv',
                        metavar='csv',
                        type=str,
                        help='comma-separated-value file')

    args = parser.parse_args()


    function = choices[args.role]

    function(args)
