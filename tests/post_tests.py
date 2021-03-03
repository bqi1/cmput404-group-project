'''

Note: this test assumes that two users, ptest1 and ptest2 exists
userids: 8, 9
passwords: Testuser1234 , Testuser5678
api tokens: 9ea7039bf3a3e547be6d07b31070239e6489111a, 5a3739ccb2dc7fa54bb5596bcd6e234223f8dc99
first/last names: test user, test user
emails: kandrosc98@gmail.com, kandrosc98@gmail.com

'''

import unittest
import requests


class PostTests(unittest.TestCase):
    # Initialize some variables

    def setUp(self):
        self.allposts_url = "http://localhost:8000/author/%s/posts"
        self.post_url = "http://localhost:8000/author/%s/posts/%d"
        self.post_id1 = 0
        self.post_id2 = 12345
        self.data1 = {"title":"title_one","description":"desc_one","markdown":0,"content":"content_one"}
        self.data2 = {"title":"title_two","description":"desc_two","markdown":1,"content":"content_two"}
        self.auth_header = {"Authorization": "Token 9ea7039bf3a3e547be6d07b31070239e6489111a" }

    # Tasks that should work


    def test_create_POST(self):
        r = requests.post(self.allposts_url % 8, headers = self.auth_header, data = self.data1)
        self.assertTrue(r.status_code == 200,"Status code expected to be 200, got %d" % r.status_code)
        self.assertTrue("Successfully created post:" in r.text, "Expected a successful post creation, got %s" % r.text)
        self.post_id1 = int(r.text.split(": ")[-1])

    def test_create_PUT(self):
        r = requests.put(self.post_url % (8,self.post_id2), headers = self.auth_header, data = self.data2)
        self.assertTrue(r.status_code == 200,"Status code expected to be 200, got %d" % r.status_code)
        self.assertTrue(r.text == "Successfully created post: %d\n" % self.post_id2, "Expected a successful post creation, got %s" % r.text)

    def test_modify_POST(self):
        r = requests.post(self.post_url % (8,self.post_id2), headers = self.auth_header, data = self.data2)
        self.assertTrue(r.status_code == 200,"Status code expected to be 200, got %d" % r.status_code)
        self.assertTrue(r.text == "Successfully modified post: %d\n" % self.post_id2, "Expected a successful post modification, got %s" % r.text)

    '''
    def allposts_GET(self):
        pass
    def delete_DELETE(self):
        pass
    def singepost_GET(self):
        pass

    # Tasks that should not work
    
    def not_AUTH(self):
        pass
    def invalid_PARAM(self):
        pass
    def invalid_METHOD(self):
        pass
    def not_FOUND(self):
        pass
    '''

if __name__ == "__main__":
    unittest.main()