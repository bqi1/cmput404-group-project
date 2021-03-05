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
import json
import sqlite3

def validate_post(expected, actual, user_id, post_id,image='0'):

    actual["user_id"] = user_id
    actual["post_id"] = post_id
    actual["image"] = image
    for col in actual.keys():
        if col != "timestamp" and actual[col] != expected[col]:
            return False
    return True

class PostTests(unittest.TestCase):
    # Initialize some variables

    def setUp(self):
        self.allposts_url = "http://localhost:8000/author/%s/posts/"
        self.post_url = "http://localhost:8000/author/%s/posts/%d"
        self.post_id2 = 12345
        self.data1 = {"title":"title_one","description":"desc_one","markdown":0,"content":"content_one"}
        self.data2 = {"title":"title_two","description":"desc_two","markdown":1,"content":"content_three"}
        self.auth_header = {"Authorization": "Token 9ea7039bf3a3e547be6d07b31070239e6489111a" }
        self.unauth_header = {"Authorization": "Token 5a3739ccb2dc7fa54bb5596bcd6e234223f8dc99" }
        self.image_url = "https://miro.medium.com/max/1200/1*mk1-6aYaf_Bes1E3Imhc0A.jpeg"

    # Tasks that should work

    def test_create_POST(self):
        r = requests.post(self.allposts_url % 8, headers = self.auth_header, data = self.data1)
        self.assertTrue(r.status_code == 200,"Status code expected to be 200, got %d" % r.status_code)
        self.assertTrue("Successfully created post:" in r.text, "Expected a successful post creation, got %s" % r.text)
        with open("post_tests.txt","w") as f: f.write(r.text.split(": ")[-1])

    def test_create_PUT(self):
        with open("post_tests.txt","r") as f: self.post_id1 = int(f.read())

        r = requests.put(self.post_url % (8,self.post_id2), headers = self.auth_header, data = self.data2)
        self.assertTrue(r.status_code == 200,"Status code expected to be 200, got %d" % r.status_code)
        self.assertTrue(r.text == "Successfully created post: %d\n" % self.post_id2, "Expected a successful post creation, got %s" % r.text)

        r = requests.get(self.allposts_url % 8)
        self.assertTrue(r.status_code == 200, "Status code expected to be 200, got %d" % r.status_code)
        post_list = json.loads(r.text)
        self.assertTrue(len(post_list) == 2, "Expected 2 posts to be returned, got %d" % len(post_list))
        self.assertTrue(validate_post(post_list[0],self.data1,8,self.post_id1), "Expected the first post to be %s, got %s" % (str(self.data1),str(post_list[0])) )
        self.assertTrue(validate_post(post_list[1],self.data2,8,self.post_id2), "Expected the second post to be %s, got %s" % (str(self.data1),str(post_list[1])) )

    def test_modify_POST(self):
        self.data2["content"] = "content_two"
        self.data2["image"] = self.image_url
        r = requests.post(self.post_url % (8,self.post_id2), headers = self.auth_header, data = self.data2)
        self.assertTrue(r.status_code == 200,"Status code expected to be 200, got %d" % r.status_code)
        self.assertTrue(r.text == "Successfully modified post: %d\n" % self.post_id2, "Expected a successful post modification, got %s" % r.text)

        r = requests.get(self.post_url % (8,self.post_id2))
        self.assertTrue(r.status_code == 200, "Status code expected to be 200, got %d" % r.status_code)
        post_list = json.loads(r.text)
        self.assertTrue(len(post_list) == 1, "Expected 1 post to be returned, got %d" % len(post_list))
        self.assertTrue(validate_post(post_list[0],self.data2,8,self.post_id2,image=self.image_url), "Expected the first post to be %s, got %s" % (str(self.data2),str(post_list[0])) )

    def test_delete_DELETE(self):
        with open("post_tests.txt","r") as f: self.post_id1 = int(f.read())
        r = requests.delete(self.post_url %(8,self.post_id1),headers = self.auth_header)
        self.assertTrue(r.status_code == 200,"Status code expected to be 200, got %d" % r.status_code)
        self.assertTrue(r.text == "Successfully deleted post: %d\n" % self.post_id1, "Expected a successful post deletion, got %s" % r.text)

        r = requests.get(self.allposts_url % 8)
        self.assertTrue(r.status_code == 200, "Status code expected to be 200, got %d" % r.status_code)
        post_list = json.loads(r.text)
        self.assertTrue(len(post_list) == 1, "Expected 2 posts to be returned, got %d" % len(post_list))
        self.assertTrue(validate_post(post_list[0],self.data2,8,self.post_id2), "Expected the first post to be %s, got %s" % (str(self.data2),str(post_list[0])) )


    # Tasks that should not work (not working means pass)
    
    def test_not_AUTH(self):
        r = requests.post(self.allposts_url % 8, data = self.data1)
        self.assertTrue(r.status_code == 401,"Status code expected to be 401, got %d" % r.status_code)

        r = requests.post(self.post_url % (8,self.post_id2), data = self.data2)
        self.assertTrue(r.status_code == 401,"Status code expected to be 401, got %d" % r.status_code)

        r = requests.put(self.post_url % (8,self.post_id2), data = self.data2)
        self.assertTrue(r.status_code == 401,"Status code expected to be 401, got %d" % r.status_code)

        r = requests.delete(self.post_url %(8,self.post_id2))
        self.assertTrue(r.status_code == 401,"Status code expected to be 401, got %d" % r.status_code)

        r = requests.post(self.allposts_url % 8, headers = self.unauth_header, data = self.data1)
        self.assertTrue(r.status_code == 401,"Status code expected to be 401, got %d" % r.status_code)

        r = requests.post(self.post_url % (8,self.post_id2), headers = self.unauth_header, data = self.data2)
        self.assertTrue(r.status_code == 401,"Status code expected to be 401, got %d" % r.status_code)

        r = requests.put(self.post_url % (8,self.post_id2 + 1), headers = self.unauth_header, data = self.data2)
        self.assertTrue(r.status_code == 401,"Status code expected to be 401, got %d" % r.status_code)

        r = requests.delete(self.post_url %(8,self.post_id2), headers = self.unauth_header,)
        self.assertTrue(r.status_code == 401,"Status code expected to be 401, got %d" % r.status_code)


    def test_invalid_METHOD(self):
        r = requests.put(self.allposts_url % (8,), headers=self.auth_header,data = self.data2)
        self.assertTrue(r.status_code == 405,"Status code expected to be 405, got %d" % r.status_code)
    
        r = requests.delete(self.allposts_url %(8,), headers=self.auth_header)
        self.assertTrue(r.status_code == 405,"Status code expected to be 405, got %d" % r.status_code)

        r = requests.head(self.post_url %(8,self.post_id2),headers = self.auth_header)
        self.assertTrue(r.status_code == 405,"Status code expected to be 405, got %d" % r.status_code)

        r = requests.put(self.post_url % (8,self.post_id2),headers=self.auth_header,data=self.data2)
        self.assertTrue(r.status_code == 409,"Status code expected to be 409, got %d" % r.status_code)



    def test_invalid_PARAMS(self):
        r = requests.post(self.allposts_url % 8, headers = self.auth_header, data = {"title":"not-working"})
        self.assertTrue(r.status_code == 400,"Status code expected to be 400, got %d" % r.status_code)

        r = requests.post(self.post_url % (8,self.post_id2), headers = self.auth_header, data = {"title":"not-working"})
        self.assertTrue(r.status_code == 400,"Status code expected to be 400, got %d" % r.status_code)

        r = requests.put(self.post_url % (8,self.post_id2+1), headers = self.auth_header, data = {"title":"not-working"})
        self.assertTrue(r.status_code == 400,"Status code expected to be 400, got %d" % r.status_code)

        self.data2["markdown"] = "invalid value"

        r = requests.post(self.allposts_url % 8, headers = self.auth_header, data = self.data2)
        self.assertTrue(r.status_code == 400,"Status code expected to be 400, got %d" % r.status_code)

        r = requests.post(self.post_url % (8,self.post_id2), headers = self.auth_header, data = self.data2)
        self.assertTrue(r.status_code == 400,"Status code expected to be 400, got %d" % r.status_code)

        r = requests.put(self.post_url % (8,self.post_id2+1), headers = self.auth_header, data = self.data2)
        self.assertTrue(r.status_code == 400,"Status code expected to be 400, got %d" % r.status_code)

    def test_not_FOUND(self):
        r = requests.get(self.allposts_url % 0)
        self.assertTrue(r.status_code == 404,"Status code expected to be 404, got %d" % r.status_code)

        r = requests.get(self.post_url % (0,self.post_id2))
        self.assertTrue(r.status_code == 404,"Status code expected to be 404, got %d" % r.status_code)

        r = requests.get(self.post_url % (8,self.post_id2+1))
        self.assertTrue(r.status_code == 404,"Status code expected to be 404, got %d" % r.status_code)

        # Delete remaining post to clean up the database!
        r = requests.delete(self.post_url % (8,self.post_id2),headers=self.auth_header)

if __name__ == "__main__":
    # Run tests
    unittest.main()

    # Clean up any leftover posts that may still linger if tests fail!
    conn = sqlite3.connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM posts WHERE user_id = 8;")
    conn.commit()
    conn.close()