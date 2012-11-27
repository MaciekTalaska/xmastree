import tornado.ioloop
import tornado.web
import tornado.options
import tornado.autoreload
import threading
import time
import Queue

lightThread = None
queue = Queue.Queue()
programs = dict()

class LightThread(threading.Thread):
    def __init__(self, threadId, name, counter):
        pass
    
    def run(self):
        pass

class XmasLines(tornado.web.RequestHandler):
    def get(self, line):
        self.set_header("Content-Type", "application/json")
        self.write("state for line " + str(line) + " requested")
    
    def put(self, line):
        self.set_header("Content-Type", "application/json")
        self.write("line " +str(line) + " changed")
        global queue
        queue.put("a very new item in the queue", block=True)

class XmasStdProgramLister(tornado.web.RequestHandler):
    def get(self):
        self.write("listing all standard programs...")
        
class XmasStdProgram(tornado.web.RequestHandler):    
    def get(self, program):
        self.write("standard program " +str(program) + " requested")
        
    def put(self):
        self.write("starting pre-defined program")
        
class XmasCustomProgramLister(tornado.web.RequestHandler):
    def get(self):
        self.write("listing all CUSTOM programs...")

class XmasCustomProgram(tornado.web.RequestHandler):
    def get(self):
        self.write("custom program")
        
    def put(self):
        self.write("uploading custom program")

application = tornado.web.Application([
    (r"/line/([0-7]{1})",XmasLines),
    (r"/stdprogram",XmasStdProgramLister),
    (r"/stdprogram/([0-9]{1})",XmasStdProgram),
    (r"/program",XmasCustomProgramLister),
    #(r"/program",XmasCustomProgram),
])

def InnerThread():
    while( 1 == 1):    
        #print("inner thread ;)")
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
    lightThread.start()
    tornado.ioloop.IOLoop.instance().start()
    lightThread.join();