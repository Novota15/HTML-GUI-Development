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
# alarm limits
temp_min_limit = 30.0
temp_max_limit = 80.0
humid_min_limit = 30.0
humid_max_limit = 70.0

# alarms
temp_min_alarm = False
temp_max_alarm = False
humid_min_alarm = False
humid_max_alarm = False

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
        op = self.get_argument('op', None)

        global temp_min_limit, temp_max_limit, humid_min_limit, humid_max_limit
        global temp_min_alarm, temp_max_alarm, humid_min_alarm, humid_max_alarm

        #received a "checkup" operation command from the browser:
        if op == "checkup":
            print("checkup called")
            #make a dictionary
            status = {"server": True }
            #turn it to JSON and send it to the browser
            self.write( json.dumps(status) )

        elif op == "sample once":
            print("sample once called")
            single_sample()
            #make a dictionary
            global current_temp, current_humidity
            status = {"server": True, "current_temp": current_temp, "current_humidity": current_humidity,
                "temp_max_limit": temp_max_limit, "humid_max_limit": humid_max_limit,
                "temp_min_limit": temp_min_limit, "humid_min_limit": humid_min_limit,
                "temp_max_alarm": temp_max_alarm, "humid_max_alarm": humid_max_alarm,
                "temp_min_alarm": temp_min_alarm, "humid_min_alarm": humid_min_alarm}
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
            status = {"server": True, "current_temp": current_temp, "current_humidity": current_humidity,
                "temp_max_limit": temp_max_limit, "humid_max_limit": humid_max_limit,
                "temp_min_limit": temp_min_limit, "humid_min_limit": humid_min_limit,
                "temp_max_alarm": temp_max_alarm, "humid_max_alarm": humid_max_alarm,
                "temp_min_alarm": temp_min_alarm, "humid_min_alarm": humid_min_alarm}
            #turn it to JSON and send it to the browser
            self.write( json.dumps(status) )

        elif op == "calc metrics":
            print("calc metrics called")
            metrics = calc_metrics()
            metrics["server"] = True
            status = metrics
            #turn it to JSON and send it to the browser
            self.write( json.dumps(status) )

        elif op == "set max temp":
            value = self.get_argument('value', None)
            temp_max_limit = float(value)
            print("max temp value:", value)

        elif op == "set max humidity":
            value = self.get_argument('value', None)
            humid_max_limit = float(value)
            print("max humidity value:", value)

        elif op == "set min temp":
            value = self.get_argument('value', None)
            temp_min_limit = float(value)
            print("min temp value:", value)

        elif op == "set min humidity":
            value = self.get_argument('value', None)
            humid_min_limit = float(value)
            print("min humidity value:", value)

        elif op == "create error":
            status = {}
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

    # check if we hit an alarm
    global temp_min_limit, temp_max_limit, humid_min_limit, humid_max_limit
    global temp_min_alarm, temp_max_alarm, humid_min_alarm, humid_max_alarm

    # reset alarms
    temp_min_alarm = False
    temp_max_alarm = False
    humid_min_alarm = False
    humid_max_alarm = False
    
    # set alarms
    if temp_f > temp_max_limit:
        temp_max_alarm = True
    elif temp_f < temp_min_limit:
        temp_min_alarm = True
    elif h > humid_max_limit:
        humid_max_alarm = True
    elif h < humid_min_limit:
        humid_min_alarm = True

    return h, temp_f

def single_sample():
    h,t = sample_data()
    global current_temp, current_humidity
    current_temp = t
    current_humidity = h
    print('sample', 'temp:', t, 'humidity:', h)
    return

def calc_metrics():
        temp_list, temp_times = db.get_all_temps(session, "f")
        humid_list, humid_times = db.get_all_humids(session)
        metrics = {}
        # set total samples
        metrics["total_samples"] = str(len(temp_list))
        # min temp
        metrics["min_temp"] = str(min(temp_list))
        # min humidity
        metrics["min_humidity"] = str(min(humid_list))
        # max temp
        metrics["max_temp"] = str(max(temp_list))
        # max humidity
        metrics["max_humidity"] = str(max(humid_list))
        # avg temp
        metrics["avg_temp"] = str(sum(temp_list)/len(temp_list))
        # avg humidity
        metrics["avg_humidity"] = str(sum(humid_list)/len(humid_list))
        return metrics

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