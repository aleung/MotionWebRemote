#!/usr/bin/env python

import web
import urllib2
import re
import time
import os

urls = (
    '/homecam/status', 'status',
    '/homecam/snapshot', 'snapshot',
    '/homecam/disable', 'disable',
    '/homecam/enable', 'enable',
    '/homecam/ping', 'ping',
    '(.*)', 'help',
)
app = web.application(urls, globals())

MOTION_CONTROL_URL_BASE = 'http://localhost:8090'
MOTION_PAUSE_FILE = '/tmp/motion_pause'

class help:
    def GET(self, path):
        return "Unknown path {0}".format(path)

# Put into crontab:
# * * * * * /usr/bin/lwp-request http://localhost/homecam/ping >> /var/log/cron.log 2>&1
class ping:
    def GET(self):
        expire = read_expire()
        if expire <= time.time():
            enable_motion()
        
    
class disable:
    def GET(self):
        disable_motion(int(web.input().hours))
        return index(False)

class enable:
    def GET(self):
        enable_motion()
        return index(False)
        
class status:
    def GET(self):
        return index(False)
        
class snapshot:
    def GET(self):
        take_snapshot()
        return index(True)

def index(show_snapshot):
        status = get_motion_status()
        render = web.template.render('.')
        return render.index(status, show_snapshot)

def disable_motion(hours):
    urllib2.urlopen(MOTION_CONTROL_URL_BASE + '/0/detection/pause')
    expire = time.time() + 3600 * hours
    with open(MOTION_PAUSE_FILE, 'w') as f:
        f.write(str(expire))

def enable_motion():
    try:
        os.remove(MOTION_PAUSE_FILE)
    except:
        pass
    urllib2.urlopen(MOTION_CONTROL_URL_BASE + '/0/detection/start')

def get_motion_status():
    try:
        result = urllib2.urlopen(MOTION_CONTROL_URL_BASE + '/0/detection/status')
        status = re.match('Thread 0 Detection status (.*)', result.read()).group(1)
        if status == 'PAUSE':
            expire = read_expire()
            if expire > 0:
                return "%s till %s" % (status, time.strftime('%H:%M', time.localtime(expire)))
        return status
    except urllib2.URLError:
        return 'STOP'

def read_expire():
    try:
        with open(MOTION_PAUSE_FILE, 'r') as f:
            return float(f.readline())
    except:
        return 0
        
def take_snapshot():
    urllib2.urlopen(MOTION_CONTROL_URL_BASE + '/0/action/snapshot')
    time.sleep(1)

if __name__ == "__main__":
    app.run()
