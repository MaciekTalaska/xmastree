import unittest

try:
    import http.client as httpclient
except ImportError:
    import httplib as httpclient
import uuid
import json
import config
import xmastree


class TestBase(unittest.TestCase):
    port = config.web_server_port

    def create_connection(self):
        return httpclient.HTTPConnection("localhost", self.port)

    @staticmethod
    def get_body_content(body):
        return json.loads(body.decode("utf-8"))

    def check_content_type(self, response):
        status = response.status
        if status == httpclient.OK:
            content_type = response.getheader("Content-Type")
            self.assertEqual("application/json", content_type)

    def execute(self, method, resource, body=None):
        conn = self.create_connection()
        conn.request(method, resource, body)
        response = conn.getresponse()
        status = response.status
        body = response.read()
        response.close()
        conn.close()
        self.check_content_type(response)
        return body, status

    def execute_get(self, resource):
        return self.execute("GET", resource)

    def execute_post(self, resource, body):
        return self.execute("POST", resource, body)

    def execute_delete(self, resource):
        return self.execute("DELETE", resource)

    def execute_put(self, resource, body=None):
        return self.execute("PUT", resource, body)


class TestDirectLightControl(TestBase):
    def test_after_reset_all_lights_should_be_switched_off(self):
        resource = "/tree"
        self.execute_delete(resource)
        (body, status) = self.execute_get(resource)
        self.assertEqual(httpclient.OK, status)
        j = self.get_body_content(body)
        self.assertEqual(8, j.count(0))

    def test_after_reset_lights_could_be_turned_on(self):
        resource = "/tree"
        (body, status) = self.execute_delete(resource)
        self.assertEqual(httpclient.OK, status)
        for i in range(0, 8):
            (body, status) = self.execute_put("/line/" + str(i))
            self.assertEqual(httpclient.OK, status)
        (body, status) = self.execute_get("/tree")
        self.assertEqual(httpclient.OK, status)
        j = self.get_body_content(body)
        self.assertEqual(8, j.count(1))

    def test_after_reset_lights_could_be_turned_on_2(self):
        resource = "/tree"
        (body, status) = self.execute_delete(resource)
        self.assertEqual(httpclient.OK, status)
        for i in range(0, 8):
            (body, status) = self.execute_put("/line/" + str(i) + "/1")
            self.assertEqual(httpclient.OK, status)
        (body, status) = self.execute_get("/tree")
        self.assertEqual(httpclient.OK, status)
        j = self.get_body_content(body)
        self.assertEqual(8, j.count(1))
        for i in range(0, 8):
            (body, status) = self.execute_put("/line/" + str(i) + "/0")
            self.assertEqual(httpclient.OK, status)
        (body, status) = self.execute_get("/tree")
        self.assertEqual(httpclient.OK, status)
        j = self.get_body_content(body)
        self.assertEqual(8, j.count(0))

    def test_toggle(self):
        resource = "/tree"
        (body, status) = self.execute_delete(resource)
        self.assertEqual(httpclient.OK, status)
        for i in range(0, 8):
            (body, status) = self.execute_put("/line/" + str(i))
            self.assertEqual(httpclient.OK, status)
        (body, status) = self.execute_get("/tree")
        self.assertEqual(httpclient.OK, status)
        j = self.get_body_content(body)
        self.assertEqual(8, j.count(1))
        for i in range(0, 8):
            (body, status) = self.execute_put("/line/" + str(i))
            self.assertEqual(httpclient.OK, status)
        (body, status) = self.execute_get("/tree")
        self.assertEqual(httpclient.OK, status)
        j = self.get_body_content(body)
        self.assertEqual(8, j.count(0))

    def test_toggle_many(self):
        resource = "/tree"
        (body, status) = self.execute_delete(resource)
        self.assertEqual(httpclient.OK, status)
        (body, status) = self.execute_put(resource, "[0,1,2,3,4,5,6,7]")
        self.assertEqual(httpclient.OK, status)
        (body, status) = self.execute_get(resource)
        self.assertEqual(httpclient.OK, status)
        (body, status) = self.execute_get("/tree")
        self.assertEqual(httpclient.OK, status)
        j = self.get_body_content(body)
        self.assertEqual(8, j.count(1))

    def test_switch_on_many(self):
        resource = "/tree"
        (body, status) = self.execute_delete(resource)
        self.assertEqual(httpclient.OK, status)
        (body, status) = self.execute_post(resource, "[0,1,2,3,4,5,6,7]")
        self.assertEqual(httpclient.OK, status)
        (body, status) = self.execute_get(resource)
        self.assertEqual(httpclient.OK, status)
        (body, status) = self.execute_get("/tree")
        self.assertEqual(httpclient.OK, status)
        j = self.get_body_content(body)
        self.assertEqual(8, j.count(1))


class TestStandardProgram(TestBase):
    def test_there_should_be_standard_programms(self):
        response = self.execute_get("/stdprogram")
        status = response[1]
        self.assertEqual(httpclient.OK, status)

    def test_asking_for_non_existing_program_should_result_in_404(self):
        sid = str(uuid.uuid4())
        response = self.execute_get("/stdprogram/" + sid)
        status = response[1]
        self.assertEqual(404, status)


class TestCustomProgram(TestBase):
    @staticmethod
    def program_string_from_components(author, name, content, loop_from):
        return '{"author":"' + author + \
               '","name":"' + name + \
               '","content":"' + content + \
               '", "loop_from":' + loop_from + '}'

    def test_asking_for_non_existing_program_should_result_in_404(self):
        sid = str(uuid.uuid4())
        response = self.execute_get("/program/" + sid)
        status = response[1]
        self.assertEqual(404, status)

    def test_when_program_is_created_it_could_be_retrieved(self):
        author = "author"
        content = "on:1,2,3;wait:300;off:1,2,3;on:4,5,6;wait:300"
        name = "a simple name for a test program"
        loop_from = "1"
        request_body = self.program_string_from_components(author, name, content, loop_from)
        (body, status) = self.execute_post("/program", request_body)
        self.assertTrue(len(body) > 0)
        self.assertEqual(httpclient.OK, status)
        j = self.get_body_content(body)
        sid = j['id']
        (response_body, status) = self.execute_get("/program/" + sid)
        self.assertEqual(httpclient.OK, status)
        json_object = self.get_body_content(response_body)
        self.assertEqual(author, json_object['author'])
        self.assertEqual(name, json_object['name'])
        self.assertEqual(content, json_object['content'])


class TestProgram(unittest.TestCase):
    def test_proper_program_should_be_parsed(self):
        author = "author1"
        name = "proper program"
        content = "on:1,2,3;wait:300;off:1,2,3;on:4,5,6;wait:300"
        loop_from = "0"
        id = str(uuid.uuid4())
        program = xmastree.Program(author, name, id, content, loop_from)
        seq = program.create_sequence()
        self.assertEqual(6, len(seq))
        self.assertEqual((xmastree.ON_INSTRUCTION, [1, 2, 3]), seq[0])
        self.assertEqual((xmastree.WAIT_INSTRUCTION, 300), seq[1])
        self.assertEqual((xmastree.OFF_INSTRUCTION, [1, 2, 3]), seq[2])
        self.assertEqual((xmastree.ON_INSTRUCTION, [4, 5, 6]), seq[3])
        self.assertEqual((xmastree.WAIT_INSTRUCTION, 300), seq[4])
        self.assertEqual((xmastree.LOOP_INSTRUCTION, 0), seq[5])

    def test_proper_program_ending_with_semicolon_should_be_parsed(self):
        author = "author1"
        name = "proper program"
        content = "on:1,2,3;wait:300;off:1,2,3;on:4,5,6;wait:300;"
        loop_from = "0"
        id = str(uuid.uuid4())
        program = xmastree.Program(author, name, id, content, loop_from)
        seq = program.create_sequence()
        self.assertEqual(6, len(seq))
        self.assertEqual((xmastree.ON_INSTRUCTION, [1, 2, 3]), seq[0])
        self.assertEqual((xmastree.WAIT_INSTRUCTION, 300), seq[1])
        self.assertEqual((xmastree.OFF_INSTRUCTION, [1, 2, 3]), seq[2])
        self.assertEqual((xmastree.ON_INSTRUCTION, [4, 5, 6]), seq[3])
        self.assertEqual((xmastree.WAIT_INSTRUCTION, 300), seq[4])
        self.assertEqual((xmastree.LOOP_INSTRUCTION, 0), seq[5])


if __name__ == '__main__':
    unittest.main()
