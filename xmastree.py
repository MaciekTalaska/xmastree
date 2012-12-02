import tornado.ioloop
import tornado.web
import tornado.options
import tornado.autoreload
import threading
import time
import Queue
import uuid
import json
from lightcontroller import *

lightThread = None
queue = Queue.Queue()
programs = dict()
stdprograms = dict()

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
    
    @property
    def Author(self):
        return self.author
    
    @property
    def Name(self):
        return self.name
        
    @property
    def Id(self):
        return self.id
        
    @property
    def Content(self):
        return self.content
        
    def to_json():
        json.dumps(self.__dict__)
        
    @staticmethod
    def from_json(json_object):
        if ('author' in json_object) and ('name' in json_object) and ('content' in json_object):
            author = json_object['author']
            name = json_object['name']
            content = json_object['content']
            return Program(author, name, id, content)

class JSONHelper():
    @staticmethod
    def program_from_json(json_object):
        if ('program_name' in json_object):
            pass
            
    def is_proper_program(self, program):
        pass
    
class RequestHandlerBase(tornado.web.RequestHandler):
    def set_all_headers(self):
        self.set_header("Content-Type", "application/json")

class LinesHandler(RequestHandlerBase):
    def put(self, line):
        self.set_all_headers()
        LightController.change_light_state(line)

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
    (r"/line/([0-7]{1})",LinesHandler),
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
    #print("prepopulating programms...")
    global stdprograms
    stdprograms['8c702c94-12c8-4843-adb4-73b4806d1d47'] = Program('Maciek', 'Blinker', '8c702c94-12c8-4843-adb4-73b4806d1d47', 'ala ma kota')
    stdprograms['cd6934bc-4bd5-4f13-994d-bcc386126f74'] = Program('Maciek', 'Blinker v2', 'cd6934bc-4bd5-4f13-994d-bcc386126f74', 'kot ma ale')

if __name__ == "__main__":
    # initialize
    populate_programs()
    tornado.options.parse_command_line()
    # register main file for changes
    tornado.autoreload.watch("xmastree.py")
    application.listen(8808)
    tornado.autoreload.start(io_loop=None,check_time=500)
    lightThread = threading.Thread(target = InnerThread)
    # worker thread is temporarily disabled
    #lightThread.start()
    tornado.ioloop.IOLoop.instance().start()
    #lightThread.join();