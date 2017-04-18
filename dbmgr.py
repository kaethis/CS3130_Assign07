import time

import redis


class Database():

    def __init__(self, host, port, index):

        self.meta = [ 'SCHEMA', 'UPDATED', 'CONFIG', 'KEYS' ]


        self.redis = redis.StrictRedis(host=host, port=port, db=index)


    def load(self, csv):

        self.redis.flushdb()


        csv = csv.split('\n')[:-1]

        attrs = csv[0].rstrip().split(',')

        lens = csv[1].rstrip().split(',')

        typechs = csv[2].rstrip().split(',')


        schema = []

        for i, attr in enumerate(attrs):

            schema.append([ attr, lens[i], typechs[i] ])

        self.redis.set('SCHEMA', repr(schema))


        csv = csv[3:]

        for line in csv:

            attrs = line.rstrip().split(',')

            key = attrs[0]

            self.add(key, attrs)


        self.setUpdated()

        self.redis.set('CONFIG', repr(True))


        return True


    def exists(self, key):

        for k in self.getKeys():

            if k in self.meta:   pass

            elif k == repr(key): return True

        return False


    def add(self, key, attrs):

        if self.exists(key):   return False

        elif key in self.meta: return False

        else:

            rec = {}

            for i, s in enumerate(self.getSchema()): rec[s[0]] = attrs[i]

            self.redis.set(repr(key), repr(rec))

            return True


    def delete(self, key):

        if not self.exists(key): return False

        elif key in self.meta:   return False

        else:

            self.redis.delete(repr(key))

            return True


    def getSchema(self):

        return eval(self.redis.get('SCHEMA').decode('ascii'))


    def getConfig(self):

        if not self.redis.get('CONFIG'): return False

        else:                            return True


    def getKeys(self):

        keys = []

        for k in self.redis.keys(): keys.append(k.decode('ascii'))

        return keys


    def getRecords(self):

        collect = []

        for k in self.getKeys():

            if k in self.meta: pass

            else:

                rec = eval(self.redis.get(k).decode('ascii'))

                collect.append(rec)

        return collect


    def getUpdated(self):

        return eval(self.redis.get('UPDATED').decode('ascii'))


    def setUpdated(self):

        self.redis.set('UPDATED', time.time())

        return self.getUpdated()
