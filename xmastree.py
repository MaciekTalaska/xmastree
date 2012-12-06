#!/usr/bin/python
import tornado.ioloop
import tornado.web
import tornado.options
import tornado.autoreload
import threading
import time
import Queue
import uuid
import json
import config
try:
    import RPi.GPIO as GPIO
except ImportError:
    import FakeGPIO as GPIO

lightThread = None
queue = Queue.Queue()
programs = dict()
stdprograms = dict()
portMap = [0,1,4,17,21,22,10,9]
lightState = [0,0,0,0,0,0,0,0]

class LightController():
    @staticmethod
    def reset_lights():
        for i in range(0,8):
            LightController.set_light(i, False)

    @staticmethod
    def light_on(light):
        GPIO.output(portMap[light], True)
        global lightState
        lightState[light] = 1

    @staticmethod
    def light_off(light):
        GPIO.output(portMap[light], False)
        global lightState
        lightState[light] = 0

    @staticmethod
    def set_light(light, state):
        light_num = int(light)
        if (state == "0"):
            LightController.light_off(light_num)
        else:
            LightController.light_on(light_num)

    @staticmethod
    def toggle(light):
        light_num = int(light)
        if lightState[light_num] == 0:
            LightController.light_on(light_num)
        else:
            LightController.light_off(light_num)
   
    @staticmethod
    def get_tree_state():
        acc = 0
        for i in range(0,8):
            acc = (acc << 1) | lightState[i]
        return acc

class ProgramLauncher(object):
    def __init__():
        pass
    
    @staticmethod
    def run(program):
        pass
        

class XmasJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Program):
            return obj.__dict__
        return json.JSONEncoder().default(obj)

class LightThread(threading.Thread):
    def __init__(self, threadId, name, counter):
        pass
    
    def run(self):
        pass

class Program(object):
    def __init__(self, author, name, id, content):
        self.author = author
        self.name = name
        self.id = id
        self.content = content
        
    def to_json():
        json.dumps(self.__dict__)
        
    @staticmethod
    def from_json(json_object):
        if ('author' in json_object) and ('name' in json_object) and ('content' in json_object):
            author = json_object['author']
            name = json_object['name']
            content = json_object['content']
            return Program(author, name, id, content)

class RequestHandlerBase(tornado.web.RequestHandler):
    def set_all_headers(self):
        self.set_header("Content-Type", "application/json")

class LinesHandler(RequestHandlerBase):
    def put(self, line, state):
        self.set_all_headers()
        LightController.set_light(line, state)

class LinesStatusHandler(RequestHandlerBase):
    def get(self, line):
        self.set_all_headers()
        self.write(str(lightState[int(line)]))

    def delete(self,line):
        LightController.reset_lights()
    
    def put(self, line):
        LightController.toggle(line)

class TreeStatusHandler(RequestHandlerBase):
    def get(self):
        self.write(str(json.dumps(lightState)))

class StandardProgramHandlerLister(RequestHandlerBase):
    def get(self):
        if len(stdprograms) > 0:
            body = json.dumps(stdprograms.values(), cls=XmasJSONEncoder)
            self.set_all_headers()
            self.write(body)
        else:
            raise tornado.web.HTTPError(404)
        
class StandardProgramHandler(RequestHandlerBase):    
    def put(self, id):
        program = stdprograms.get(id)
        if program is None:
            raise tornado.web.HTTPError(404)
        else:
            self.set_all_headers()
            ProgramLauncher.run()
            
    def get(self, id):
        program = stdprograms.get(id)
        if program is None:
            raise tornado.web.HTTPError(404)
        else:
            self.set_all_headers()
            self.write(XmasJSONEncoder().encode(program))
        
class CustomProgramListerHandler(RequestHandlerBase):
    def get(self):
        if len(programs) > 0:
            body = json.dumps(programs.values(), cls=XmasJSONEncoder)
            self.set_all_headers()
            self.write(body)
        else:
            raise tornado.web.HTTPError(404)

    def post(self):
        sid = str(uuid.uuid1())
        global programs
        strprogram = self.request.body
        program = json.loads(strprogram, object_hook=Program.from_json)
        program.__dict__['id']=sid
        programs[sid]= program
        self.write('{"id":"'+sid+'"}')

class CustomProgramHandler(RequestHandlerBase):
    def get(self,id):  
        program = programs.get(id)
        if program is None:
            raise tornado.web.HTTPError(404)
        else:
            self.set_all_headers()
            self.write(json.dumps(program, cls=XmasJSONEncoder))
        
    def put(self, id):
        program = programs.get[id]
        if program is None:
            raise tornado.web.HTTPError(404)
        else:
            ProgramLauncher.run(program)

application = tornado.web.Application([
    (r"/tree",TreeStatusHandler),
    (r"/line/([0-7]{1})",LinesStatusHandler),
    (r"/line/([0-7]{1})/([0-1]{1})",LinesHandler),
    (r"/stdprogram",StandardProgramHandlerLister),
    (r"/stdprogram/([0-9A-Fa-f-]*)",StandardProgramHandler),
    (r"/program",CustomProgramListerHandler),
    (r"/program/([0-9A-Fa-f-]*)",CustomProgramHandler),
])

def InnerThread():
    while( 1 == 1):    
        if (queue.empty()):
            time.sleep(5)
            print("queue is empty")
        else:
            print("queue populated!")
            global queue
            item = queue.get(block=True)
            print("current item: " + str(item))
            time.sleep(5)
            
def populate_programs():
    global stdprograms
    stdprograms['8c702c94-12c8-4843-adb4-73b4806d1d47'] = Program('Maciek', 'Blinker', '8c702c94-12c8-4843-adb4-73b4806d1d47', 'content of the first program')
    stdprograms['cd6934bc-4bd5-4f13-994d-bcc386126f74'] = Program('Maciek', 'Blinker v2', 'cd6934bc-4bd5-4f13-994d-bcc386126f74', 'content of the second program')

def create_worker_thread():
    global lightThread
    lightThread = threading.Thread(target = InnerThread)
    lightThread.daemon = True
    # worker thread is temporarily disabled
    #lightThread.start()
    global queue
    queue = Queue.Queue()

def initialize_RaspberryPi():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    for i in portMap:
        GPIO.setup(i, GPIO.OUT)

def initialize():
    populate_programs()
    create_worker_thread()
    initialize_RaspberryPi()

if __name__ == "__main__":
    initialize()
    tornado.options.parse_command_line()
    # register main file for changes
    tornado.autoreload.watch("xmastree.py")
    application.listen(config.web_server_port)
    tornado.autoreload.start(io_loop=None,check_time=500)
    tornado.ioloop.IOLoop.instance().start()
    #lightThread.join();
