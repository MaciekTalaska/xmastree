import tornado.ioloop
import tornado.web
import tornado.options
import tornado.autoreload

class XmasLines(tornado.web.RequestHandler):
    def get(self, line):
        self.write("state for line " + str(line) + " requested")
    
    def put(self, line):
        self.write("line " +str(line) + " changed")

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

if __name__ == "__main__":
    tornado.options.parse_command_line()
    # register main file for changes
    tornado.autoreload.watch("xmastree.py")
    application.listen(8888)
    tornado.autoreload.start(io_loop=None,check_time=500)
    tornado.ioloop.IOLoop.instance().start()