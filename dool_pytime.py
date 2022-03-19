### python time
import time

class dstat_plugin(dstat):
    def __init__(self):
        self.name = 'pytime'
        self.type = 'f'
        self.width = len(str(int(time.time())))+1
        self.nick = ('time',)
        self.vars = self.nick

    def check(self):
        pass

    def extract(self):
        self.val['time'] = int(time.time())


# vim:ts=4:sw=4:et
