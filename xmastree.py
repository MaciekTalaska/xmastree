import tornado.ioloop
import tornado.web
import tornado.options
import tornado.autoreload
import threading
import time
import Queue
import uuid
import json

lightThread = None
queue = Queue.Queue()
programs = dict()

class LightChanger():
    @staticmethod
    def turn_all_ligths_off():
        pass

    @staticmethod
    def change_light_state(light):        
        pass

class LightThread(threading.Thread):
    def __init__(self, threadId, name, counter):
        pass
    
    def run(self):
        pass

class JSONHelper():
    def is_proper_program(self, program):
        pass
    
class RequestHandlerBase(tornado.web.RequestHandler):
    def set_all_headers(self):
        self.set_header("Content-Type", "application/json")

class XmasLines(RequestHandlerBase):
    def put(self, line):
        self.set_all_headers()
        LightChanger.change_light_state(line)

class XmasStdProgramLister(tornado.web.RequestHandler):
    def get(self):
        self.write("listing all standard programs...")
        
class XmasStdProgram(RequestHandlerBase):    
    def get(self, program):
        self.write("standard program " +str(program) + " requested")
        
    def put(self):
        self.write("starting pre-defined program")
        
class XmasCustomProgramLister(RequestHandlerBase):
    def get(self):
        self.set_all_headers()
        #self.write(str(programs.items()))
        l = list()
        for k in programs.iterkeys():
            skey = str(k)
            value = programs[k]
            l.append(dict(skey, value))
        output = json.dumps(l)
        self.write(output)

    def post(self):
        id = uuid.uuid1()
        self.write("{id:"+str(id)+"}")
        global programs
        programs[id]= self.request.body

class XmasCustomProgram(RequestHandlerBase):
    def get(self,id):  
        newid = uuid.UUID(id)
        self.write(programs[newid])

application = tornado.web.Application([
    (r"/line/([0-7]{1})",XmasLines),
    (r"/stdprogram",XmasStdProgramLister),
    (r"/stdprogram/([0-9]{1})",XmasStdProgram),
    (r"/program",XmasCustomProgramLister),
    (r"/program/([0-9A-Fa-f-]*)",XmasCustomProgram),
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

if __name__ == "__main__":
    tornado.options.parse_command_line()
    # register main file for changes
    tornado.autoreload.watch("xmastree.py")
    application.listen(8888)
    tornado.autoreload.start(io_loop=None,check_time=500)
    lightThread = threading.Thread(target = InnerThread)
    # worker thread is temporarily disabled
    #lightThread.start()
    tornado.ioloop.IOLoop.instance().start()
    #lightThread.join();