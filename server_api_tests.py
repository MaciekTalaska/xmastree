import unittest
import httplib
import uuid
import json
import config

class TestBase(unittest.TestCase):
    port = config.web_server_port
    def create_connection(self):
        return httplib.HTTPConnection("localhost", self.port)
        
    def execute_get(self, resource):
        conn = self.create_connection()
        conn.request("GET", resource)
        response = conn.getresponse()
        status = response.status
        body = response.read()
        response.close()
        return (body,status)
        
    def execute_post(self, resource, body):
        conn = self.create_connection()
        conn.request("POST", resource, body)
        response = conn.getresponse()
        status = response.status
        body = response.read()
        response.close()
        return (body,status)
        
    def execute_delete(self, resource):
        conn = self.create_connection()
        conn.request("DELETE", resource)
        response = conn.getresponse()
        status = response.status
        body = response.read()
        response.close()
        return (body,status)
        
    def execute_put(self, resource, body=None):
        conn = self.create_connection()
        conn.request("PUT", resource, body)
        response = conn.getresponse()
        status = response.status
        body = response.read()
        response.close()
        return (body,status)
        

class TestDirectLightControl(TestBase):
    def test_after_reset_all_lights_should_be_switched_off(self):
        resource = "/tree"
        self.execute_delete(resource)
        (body, status) = self.execute_get(resource)
        self.assertEqual(200, status)
        j = json.loads(body)
        self.assertEqual(8, j.count(0))
        
    def test_after_reset_lights_could_be_turned_on(self):
        resource = "/tree"
        (body, status) = self.execute_delete(resource)
        self.assertEqual(200,status)
        for i in range(0,8):
            (body, status) = self.execute_put("/line/"+str(i))
            self.assertEqual(200, status)
        (body, status) = self.execute_get("/tree")
        self.assertEqual(200, status)
        j = json.loads(body)
        self.assertEqual(8, j.count(1))
            
    def test_after_reset_lights_could_be_turned_on_2(self):
        resource = "/tree"
        (body, status) = self.execute_delete(resource)
        self.assertEqual(200,status)
        for i in range(0,8):
            (body, status) = self.execute_put("/line/"+str(i)+"/1")
            self.assertEqual(200, status)
        (body, status) = self.execute_get("/tree")
        self.assertEqual(200, status)
        j = json.loads(body)
        self.assertEqual(8, j.count(1))
        for i in range(0,8):
            (body, status) = self.execute_put("/line/"+str(i)+"/0")
            self.assertEqual(200, status)
        (body, status) = self.execute_get("/tree")
        self.assertEqual(200, status)
        j = json.loads(body)
        self.assertEqual(8, j.count(0))
        
    def test_toggle(self):
        resource = "/tree"
        (body, status) = self.execute_delete(resource)
        self.assertEqual(200,status)
        for i in range(0,8):
            (body, status) = self.execute_put("/line/"+str(i))
            self.assertEqual(200, status)
        (body, status) = self.execute_get("/tree")
        self.assertEqual(200, status)
        j = json.loads(body)
        self.assertEqual(8, j.count(1))
        for i in range(0,8):
            (body, status) = self.execute_put("/line/"+str(i))
            self.assertEqual(200, status)
        (body, status) = self.execute_get("/tree")
        self.assertEqual(200, status)
        j = json.loads(body)
        self.assertEqual(8, j.count(0))
        
    def test_toggle_many(self):
        resource = "/tree"
        (body, status) = self.execute_delete(resource)
        (body, status) = self.execute_put(resource, "[0,1,2,3,4,5,6,7]")
        self.assertEqual(200, status)
        (body, status) = self.execute_get(resource)
        (body, status) = self.execute_get("/tree")
        self.assertEqual(200, status)
        j = json.loads(body)
        self.assertEqual(8, j.count(1))
        
    
    def test_switch_on_many(self):
        resource = "/tree"
        (body, status) = self.execute_delete(resource)
        (body, status) = self.execute_post(resource, "[0,1,2,3,4,5,6,7]")
        self.assertEqual(200, status)
        (body, status) = self.execute_get(resource)
        (body, status) = self.execute_get("/tree")
        self.assertEqual(200, status)
        j = json.loads(body)
        self.assertEqual(8, j.count(1))

class TestStandardProgram(TestBase):
    def test_there_should_be_standard_programms(self):
        response = self.execute_get("/stdprogram")
        status = response[1]
        self.assertEqual(200, status)
    
    def test_asking_for_non_existing_program_should_result_in_404(self):
        sid = str(uuid.uuid4())
        response = self.execute_get("/stdprogram/"+sid)
        status = response[1]
        self.assertEqual(404, status)
    
class TestCustomProgram(TestBase):
    def test_asking_for_non_existing_program_should_result_in_404(self):
        sid = str(uuid.uuid4())
        response = self.execute_get("/program/"+sid)
        status = response[1]
        self.assertEqual(404, status)

    def test_when_program_is_created_it_could_be_retrieved(self):
        author = "Maciek"
        content = "doesnt really matter"
        name = "a simple name for a test program"
        request_body = '{"author":"'+author+'","name":"'+name+'","content":"'+content+'"}'
        response = self.execute_post("/program", request_body)
        body, status = response
        self.assertTrue(len(body)>0)
        self.assertEqual(200, status)
        j = json.loads(body)
        sid = j['id']
        response = self.execute_get("/program/"+sid)
        response_body, status = response
        self.assertEqual(200, status)
        json_object = json.loads(response_body)
        self.assertEqual(author, json_object['author'])
        self.assertEqual(name, json_object['name'])
        self.assertEqual(content, json_object['content'])

if __name__=='__main__':
    unittest.main()