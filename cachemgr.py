import memcache


class Cache():

    def __init__(self, host, port):

        self.meta = [ 'SCHEMA', 'UPDATED', 'CONFIG', 'KEYS' ]

        self.cache = memcache.Client(['{}:{}'.format(host, port)], debug=0)


    def consolidate(self, time, schema, collect):

        self.cache.set('UPDATED', time)

        self.cache.set('SCHEMA', schema)


        schema = self.getSchema()

        keys = []

        for rec in collect:

            key = rec[schema[0][0]]

            keys.append(key)

            self.cache.set(key, rec)


        self.cache.set('KEYS', keys)


    def exists(self, key):

        for k in self.getKeys():

            if k in self.meta: pass

            elif k == key:     return True

        return False


    def search(self, attr):

        collect = []

        for rec in self.getRecords():

            for s in self.getSchema():

                if attr in rec[s[0]] and not rec in collect:

                    collect.append(rec)

        return collect


    def getSchema(self):

        return self.cache.get('SCHEMA')


    def getKeys(self):

        return self.cache.get('KEYS')


    def getRecords(self):

        collect = []

        for k in self.getKeys():

            if k in self.meta: pass

            else:

                rec = self.cache.get(k)

                collect.append(rec)

        return collect


    def getUpdated(self):

        return self.cache.get('UPDATED')
