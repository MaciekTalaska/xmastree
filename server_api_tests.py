import unittest
import httplib
import uuid
import json

class TestStandardProgram(unittest.TestCase):
    def test_there_should_be_2_standard_programms(self):
        conn = httplib.HTTPConnection("localhost:8888")
        conn.request("GET", "/stdprogram")
        response = conn.getresponse()
        status = response.status
        response.read()
        response.close()
        self.assertEqual(200, status)
        
    
    def test_asking_for_non_existing_program_should_result_in_404(self):
        sid = str(uuid.uuid4())
        conn = httplib.HTTPConnection("localhost:8888")
        conn.request("GET", "/stdprogram/"+sid)
        response = conn.getresponse()
        status = response.status
        response.read()
        response.close()
        self.assertEqual(404, status)
    
class TestCustomProgram(unittest.TestCase):
    def test_asking_for_non_existing_program_should_result_in_404(self):
        sid = str(uuid.uuid4())
        conn = httplib.HTTPConnection("localhost:8888")
        conn.request("GET", "/program/"+sid)
        response = conn.getresponse()
        status = response.status
        response.read()
        response.close()
        self.assertEqual(404, status)

    def test_when_program_is_created_it_could_be_retrieved(self):
        author="Maciek"
        content="doesnt really matter"
        name="a simple name for a test program"
        conn = httplib.HTTPConnection("localhost:8888")
        conn.request("POST", "/program",'{"author":"'+author+'","name":"'+name+'","content":"'+content+'"}')
        response = conn.getresponse()
        status = response.status
        body=response.read()
        response.close()
        self.assertTrue(len(body)>0)
        self.assertEqual(200, status)
        j=json.loads(body)
        sid=j['id']
        conn = httplib.HTTPConnection("localhost:8888")
        conn.request("GET", "/program/"+sid)
        response = conn.getresponse()
        status = response.status
        response_body=response.read()
        response.close()
        self.assertEqual(200, status)
        json_object = json.loads(response_body)
        self.assertEqual(author, json_object['author'])
        self.assertEqual(name, json_object['name'])
        self.assertEqual(content, json_object['content'])
        
        

suite = unittest.TestLoader().loadTestsFromTestCase(TestStandardProgram)
unittest.TextTestRunner(verbosity=2).run(suite)
suite = unittest.TestLoader().loadTestsFromTestCase(TestCustomProgram)
unittest.TextTestRunner(verbosity=2).run(suite)