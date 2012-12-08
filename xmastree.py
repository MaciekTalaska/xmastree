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
sequences = dict()
WAIT_INSTRUCTION    = 0
ON_INSTRUCTION      = 1
OFF_INSTRUCTION     = 2
LOOP_INSTRUCTION    = 3

class LightController():
    @staticmethod
    def reset_lights():
        for i in range(0,8):
            LightController.set_light(i, "0")

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
    def __init__(self, sid):
        self.sid = sid
        self.index = 0
        self.sequence = sequences.get(sid)
    
    def execute(self):
        while True:
            instruction = self.sequence[self.index]
            self.index+=1
            #self.execute_instruction(instruction)
            (operation, value) = instruction
            if operation == ON_INSTRUCTION:
                for i in value:
                    LightController.light_on(i)
            if operation == OFF_INSTRUCTION:
                for i in value:
                    LightController.light_off(i)
            if operation == WAIT_INSTRUCTION:
                if self.index < len(self.sequence):
                    next_instruction = self.sequence[self.index]
                    next_operation, next_value = next_instruction
                    if next_operation == LOOP_INSTRUCTION:
                        return value
                else:
                    self.index = 0
                    return 300 # default wait time
        
    @staticmethod
    def run(self,id):
        queue.put(id)
        

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
    def __init__(self, author, name, id, content, loop_from):
        self.author = author
        self.name = name
        self.id = id
        self.content = content
        self.loop_from = loop_from
        
#    def to_json(self):
#        json.dumps(self.__dict__)
        
    @staticmethod
    def from_json(json_object):
        if ('author' in json_object) and ('name' in json_object) and ('content' in json_object) and ('loop_from' in json_object):
            author = json_object['author']
            name = json_object['name']
            content = json_object['content']
            loop_from = json_object['loop_from']
            return Program(author, name, id, content, loop_from)
            
    def create_sequence(self):
        seq = list()
        operations = self.content.split(';')
        for op in operations:
            if len(op) == 0:
                break
            pcs = op.split(':')
            operation = pcs[0]
            value = pcs[1]
            if operation == 'on' or operation == 'off':
                value = "["+value+"]"
                instruction = ON_INSTRUCTION if len(operation)==2 else OFF_INSTRUCTION
                lights = json.loads(value)
                seq.append((instruction,lights))
            if operation == 'wait':
                waittime = int(value)
                seq.append((WAIT_INSTRUCTION,waittime))
        seq.append((LOOP_INSTRUCTION,int(self.loop_from)))
        return seq

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
        
    def delete(self):
        LightController.reset_lights()
        
    def post(self):
        body = self.request.body
        if len(body) < 3:
            raise tornado.web.HTTPError(400)
        lights = json.loads(body)
        if lights is None:
            raise tornado.web.HTTPError(400)
        if not isinstance(lights, list):
            raise tornado.web.HTTPError(400)
        for i in lights:
            LightController.light_on(i)
    
    def put(self):
        body = self.request.body
        if len(body) < 3:
            raise tornado.web.HTTPError(400)
        lights = json.loads(self.request.body)
        if lights is None:
            raise tornado.web.HTTPError(400)
        if not isinstance(lights, list):
            raise tornado.web.HTTPError(400)
        for i in lights:
            LightController.toggle(i)            
        

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
            ProgramLauncher.run(id)
            
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
        seq = program.create_sequence()
        global sequences
        sequences[sid] = seq
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
        program = programs.get(id)
        if program is None:
            raise tornado.web.HTTPError(404)
        else:
            ProgramLauncher.run(id)

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
    while True:
        processing = False
        launcher = None
        if (queue.empty()):
            if True == processing:
                print("processing...")
                launcher.execute()
            time.sleep(1)
            print("queue is empty")
        else:
            print("queue populated!")
            global queue
            item = queue.get(block=True)
            print("current item: " + str(item))
            processing = True
            launcher = ProgramLauncher(item)
            time.sleep(1)
            
def populate_programs():
    global stdprograms
    sid1 = '8c702c94-12c8-4843-adb4-73b4806d1d47'
    sid2 = 'cd6934bc-4bd5-4f13-994d-bcc386126f74'
    content1 = "off:0,1,2,3,4,5,6,7;wait:500;on:1;wait:500;off:1;on:2;wait:500;off:2;on:3;wait:500;off:3;on:4;wait:500;off:4;on:5;wait:500;off:5;on:6;wait:500;off:6;on:7;wait:500;"
    content2 = "off:0,1,2,3,4,5,6,7;wait:500;on:0,7;wait:500;off:0,7;on:1,6;wait:500;off:1,6;on:2,5;wait:500;off:2,5;on:3,4;wait:500;"
    loop1 = "1"
    loop2 = "0"
    program1 = Program('Maciek', 'Blinker', '8c702c94-12c8-4843-adb4-73b4806d1d47', content1, loop1)
    program2 = Program('Maciek', 'Blinker v2', 'cd6934bc-4bd5-4f13-994d-bcc386126f74', content2, loop2)
    stdprograms[sid1] = program1
    stdprograms[sid2] = program2
    global sequences
    sequences[sid1] = program1.create_sequence()
    sequences[sid2] = program2.create_sequence()

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
