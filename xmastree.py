#!/usr/bin/python
import tornado.ioloop
import tornado.web
import tornado.options
import tornado.autoreload
import threading
import time
import uuid
import json
import config

try:
    import RPi.GPIO as GPIO
except ImportError:
    import FakeGPIO as GPIO

from stdprograms import stdprograms

lightThread = None
programs = dict()
portMap = [0, 1, 4, 17, 21, 22, 10, 9]
lightState = [0, 0, 0, 0, 0, 0, 0, 0]
sequences = dict()
WAIT_INSTRUCTION = '0'
ON_INSTRUCTION = '1'
OFF_INSTRUCTION = '2'
LOOP_INSTRUCTION = '3'
STOP_MARKER = '9'
current_operation = '9'


class LightController:
    @staticmethod
    def reset_lights():
        for i in range(0, 8):
            LightController.set_light(i, "0")

    @staticmethod
    def light_on(light):
        GPIO.output(portMap[light], True)
        lightState[light] = 1

    @staticmethod
    def light_off(light):
        GPIO.output(portMap[light], False)
        lightState[light] = 0

    @staticmethod
    def set_light(light, state):
        light_num = int(light)
        if state == "0":
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


class ProgramLauncher(object):
    def __init__(self, sid):
        self.sid = sid
        self.index = 0
        self.sequence = sequences.get(sid)

    def execute(self):
        while True:
            instruction = self.sequence[self.index]
            self.index += 1
            (operation, value) = instruction
            if operation == ON_INSTRUCTION:
                for i in value:
                    LightController.light_on(i)
                print(("executing - on" + str(value)))
            if operation == OFF_INSTRUCTION:
                for i in value:
                    LightController.light_off(i)
                print(("executing - off" + str(value)))
            if operation == WAIT_INSTRUCTION:
                if self.index < len(self.sequence):
                    next_instruction = self.sequence[self.index]
                    next_operation, next_value = next_instruction
                    if next_operation == LOOP_INSTRUCTION:
                        print(("executing - wait & loop: " + str(value)))
                        self.index = next_value
                    return value
                else:
                    self.index = 0
                    return 300  # default wait time

    @staticmethod
    def run(operation_id):
        global current_operation
        current_operation = operation_id

    @staticmethod
    def stop_program():
        global current_operation
        current_operation = STOP_MARKER


class XmasJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Program):
            return obj.__dict__
        return json.JSONEncoder().default(obj)


class Program(object):
    def __init__(self, author, name, program_id, content, loop_from):
        self.author = author
        self.name = name
        self.id = program_id
        self.content = content
        self.loop_from = loop_from

    #    def to_json(self):
    #        json.dumps(self.__dict__)

    @staticmethod
    def from_json(json_object):
        if ('author' in json_object) and ('name' in json_object) and ('content' in json_object) and (
                'loop_from' in json_object):
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
                value = "[" + value + "]"
                instruction = ON_INSTRUCTION if len(operation) == 2 else OFF_INSTRUCTION
                lights = json.loads(value)
                seq.append((instruction, lights))
            if operation == 'wait':
                wait_time = int(value)
                seq.append((WAIT_INSTRUCTION, wait_time))
        seq.append((LOOP_INSTRUCTION, int(self.loop_from)))
        return seq


class RequestHandlerBase(tornado.web.RequestHandler):
    def set_all_headers(self):
        self.set_header("Content-Type", "application/json")


class LinesHandler(RequestHandlerBase):
    def put(self, line, state):
        self.set_all_headers()
        LightController.set_light(line, state)
        ProgramLauncher.stop_program()


class LinesStatusHandler(RequestHandlerBase):
    def get(self, line):
        self.set_all_headers()
        self.write(str(lightState[int(line)]))
        ProgramLauncher.stop_program()

    def delete(self, line):
        LightController.reset_lights()
        self.set_all_headers()
        ProgramLauncher.stop_program()

    def put(self, line):
        LightController.toggle(line)
        self.set_all_headers()
        ProgramLauncher.stop_program()


class TreeStatusHandler(RequestHandlerBase):
    def get(self):
        self.set_all_headers()
        self.write(str(json.dumps(lightState)))
        ProgramLauncher.stop_program()

    def delete(self):
        LightController.reset_lights()
        self.set_all_headers()
        ProgramLauncher.stop_program()

    def post(self):
        body = self.request.body
        if len(body) < 3:
            raise tornado.web.HTTPError(400)
        lights = json.loads(body.decode("utf-8"))
        if lights is None:
            raise tornado.web.HTTPError(400)
        if not isinstance(lights, list):
            raise tornado.web.HTTPError(400)
        for i in lights:
            LightController.light_on(i)
        self.set_all_headers()
        ProgramLauncher.stop_program()

    def put(self):
        body = self.request.body
        if len(body) < 3:
            raise tornado.web.HTTPError(400)
        lights = json.loads(self.request.body.decode("utf-8"))
        if lights is None:
            raise tornado.web.HTTPError(400)
        if not isinstance(lights, list):
            raise tornado.web.HTTPError(400)
        for i in lights:
            LightController.toggle(i)
        self.set_all_headers()
        ProgramLauncher.stop_program()


class StandardProgramHandlerLister(RequestHandlerBase):
    def get(self):
        if len(stdprograms) > 0:
            self.set_all_headers()
            body = json.dumps(list(stdprograms.values()), cls=XmasJSONEncoder)
            self.write(body)
            ProgramLauncher.stop_program()
        else:
            raise tornado.web.HTTPError(404)


class StandardProgramHandler(RequestHandlerBase):
    def get(self, program_id):
        program = stdprograms.get(program_id)
        if program is None:
            raise tornado.web.HTTPError(404)
        else:
            self.set_all_headers()
            self.write(XmasJSONEncoder().encode(program))
            ProgramLauncher.stop_program()

    def put(self, program_id):
        program = stdprograms.get(program_id)
        if program is None:
            raise tornado.web.HTTPError(404)
        else:
            self.set_all_headers()
            ProgramLauncher.run(program_id)


class CustomProgramListerHandler(RequestHandlerBase):
    def get(self):
        if len(programs) > 0:
            body = json.dumps(list(programs.values()), cls=XmasJSONEncoder)
            self.set_all_headers()
            self.write(body)
        else:
            raise tornado.web.HTTPError(404)
            ProgramLauncher.stop_program()

    def post(self):
        sid = str(uuid.uuid1())
        strprogram = self.request.body
        program = json.loads(strprogram.decode("utf-8"), object_hook=Program.from_json)
        program.__dict__['id'] = sid
        programs[sid] = program
        seq = program.create_sequence()
        sequences[sid] = seq
        self.set_all_headers()
        self.write('{"id":"' + sid + '"}')
        ProgramLauncher.stop_program()


class CustomProgramHandler(RequestHandlerBase):
    def get(self, program_id):
        program = programs.get(program_id)
        if program is None:
            raise tornado.web.HTTPError(404)
        else:
            self.set_all_headers()
            self.write(json.dumps(program, cls=XmasJSONEncoder))
            ProgramLauncher.stop_program()

    def put(self, program_id):
        program = programs.get(program_id)
        if program is None:
            raise tornado.web.HTTPError(404)
        else:
            ProgramLauncher.run(program_id)


application = tornado.web.Application([
    (r"/tree", TreeStatusHandler),
    (r"/line/([0-7]{1})", LinesStatusHandler),
    (r"/line/([0-7]{1})/([0-1]{1})", LinesHandler),
    (r"/stdprogram", StandardProgramHandlerLister),
    (r"/stdprogram/([0-9A-Fa-f-]*)", StandardProgramHandler),
    (r"/program", CustomProgramListerHandler),
    (r"/program/([0-9A-Fa-f-]*)", CustomProgramHandler),
])


def inner_thread():
    launcher = None
    last_operation = None
    while True:
        if current_operation == STOP_MARKER:
            time.sleep(1)
        else:
            if launcher is None or (last_operation != current_operation):
                # print('creating launcher with id: '+str(current_operation))
                launcher = ProgramLauncher(current_operation)
                last_operation = current_operation
                time.sleep(1)
            else:
                # print('executing launcher id: ' +str(current_operation))
                sleep_time = launcher.execute()
                time.sleep(sleep_time / 1000)


def create_worker_thread():
    global lightThread
    lightThread = threading.Thread(target=inner_thread)
    lightThread.daemon = True
    lightThread.start()


def initialize_rpi():
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    for i in portMap:
        GPIO.setup(i, GPIO.OUT)


def initialize():
    create_worker_thread()
    initialize_rpi()


if __name__ == "__main__":
    initialize()
    tornado.options.parse_command_line()
    # register main file for changes
    tornado.autoreload.watch("xmastree.py")
    application.listen(config.web_server_port)
    tornado.autoreload.start(check_time=500)
    tornado.ioloop.IOLoop.instance().start()
    # lightThread.join();
