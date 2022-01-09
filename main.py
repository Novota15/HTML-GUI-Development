# main code
import sys
import time
import numpy as np
from datetime import datetime
import tornado.ioloop
import tornado.web
import os
import json

# my libraries
import db
from psuedoSensor import PseudoSensor

# init database
session = db.init_session()

tornadoPort = 8888
cwd = os.getcwd() # used by static file server

current_temp = 0.0
current_humidity = 0.0

# allow cross-origin requests
class BaseHandler(tornado.web.RequestHandler):
    def set_default_headers(self):
        print("setting headers!!!")
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "x-requested-with")
        self.set_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        # HEADERS!
        self.set_header("Access-Control-Allow-Headers", "access-control-allow-origin,authorization,content-type")

    def options(self):
        # no body
        self.set_status(204)
        self.finish()

# send the index file
class IndexHandler(BaseHandler):
    def get(self, url = '/'):
        self.render('index.html')
    def post(self, url ='/'):
        self.render('index.html')

# handle commands sent from the web browser
class CommandHandler(BaseHandler):
    #both GET and POST requests have the same responses
    def get(self, url = '/'):
        print("get")
        self.handleRequest()
        
    def post(self, url = '/'):
        print("post")
        self.handleRequest()
    
    # handle both GET and POST requests with the same function
    def handleRequest(self):
        # is op to decide what kind of command is being sent
        op = self.get_argument('op',None)
        
        #received a "checkup" operation command from the browser:
        if op == "checkup":
            print("checkup called")
            #make a dictionary
            status = {"server": True, "mostRecentSerial": "success" }
            #turn it to JSON and send it to the browser
            self.write( json.dumps(status) )

        elif op == "sample once":
            print("sample once called")
            single_sample()
            #make a dictionary
            global current_temp, current_humidity
            status = {"server": True, "current_temp": current_temp, "current_humidity": current_humidity }
            #turn it to JSON and send it to the browser
            self.write( json.dumps(status) )

        elif op == "sample multi":
            print("multi sample called")
            max = 10
            print("take 10 samples:")
            for i in range(max):
                print('sample', i+1)
                single_sample()
                time.sleep(1)
            global current_temp, current_humidity
            status = {"server": True, "current_temp": current_humidity, "current_humidity": current_humidity }
            #turn it to JSON and send it to the browser
            self.write( json.dumps(status) )

        elif op == "stop server":
            stop_tornado()

        #operation was not one of the ones that we know how to handle
        else:
            print(op)
            print(self.request)
            raise tornado.web.HTTPError(404, "Missing argument 'op' or not recognized")

    def send_update(self):
        global current_temp, current_humidity
        status = {"current_temp": current_humidity, "current_humidity": current_humidity }
        self.write( json.dumps(status) )

# adds event handlers for commands and file requests
application = tornado.web.Application([
    #all commands are sent to http://*:port/com
    #each command is differentiated by the "op" (operation) JSON parameter
    (r"/(com.*)", CommandHandler ),
    (r"/", IndexHandler),
    (r"/(index\.html)", tornado.web.StaticFileHandler,{"path": cwd}),
    (r"/(.*\.png)", tornado.web.StaticFileHandler,{"path": cwd }),
    (r"/(.*\.jpg)", tornado.web.StaticFileHandler,{"path": cwd }),
    (r"/(.*\.js)", tornado.web.StaticFileHandler,{"path": cwd }),
    (r"/(.*\.css)", tornado.web.StaticFileHandler,{"path": cwd }),
])

# END OF WEB APP FUNCTIONS


# get sample of data from pseudo sensor
def sample_data():
    ps = PseudoSensor()
    h,temp_f = ps.generate_values()
    temp_c = (temp_f - 32) * 5.0/9.0
    now = datetime.now()
    db.add_temp(session, temp_f, temp_c, now)
    db.add_humidity(session, h, now)
    return h, temp_f

def single_sample():
    h,t = sample_data()
    global current_temp, current_humidity
    current_temp = t
    current_humidity = h
    print('sample', 'temp:', t, 'humidity:', h)
    return

def start_tornado():
    application.listen(tornadoPort)
    tornado.ioloop.IOLoop.instance().start()

def stop_tornado():
    tornado.ioloop.IOLoop.instance().stop()

if __name__ == "__main__":    
    #start tornado
    print("Starting server on port number %i..." % tornadoPort )
    print("Open at http://127.0.0.1:%i/index.html" % tornadoPort )
    start_tornado()