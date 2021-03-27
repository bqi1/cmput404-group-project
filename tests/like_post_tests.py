'''

Note: this test assumes that two users, ltest1 and ltest2 exists
userids: 12, 13
passwords: Testuser1234 , Testuser5678
api tokens: c93c48f80577cfa577bc7d63f8b3403f4aa301e3, 3e7d456b246310c6dabcab12c89c28b5a3eb2994
first/last names: test user, test user
emails: jacky@gmail.com, jacky@gmail.com

'''

import unittest
import requests
import json
import sqlite3
import os

class LikeTests(unittest.TestCase):

    # Initialize some variables
    def setUp(self):
        self.allposts_url = "http://localhost:8000/author/%s/posts/"
        self.post_url = "http://localhost:8000/author/%s/posts/%d"
        self.view_like_post_url = "http://localhost:8000/author/%s/posts/%d/likes/"
        self.like_post_url = "http://localhost:8000/author/%s/posts/%d/likepost/"
        self.post_id = 12345
        self.data1 = {"title":"title_one","description":"desc_one","markdown":0,"content":"content_one"}
        self.auth_header = {"Authorization": "Token 9ea7039bf3a3e547be6d07b31070239e6489111a" }
        self.unauth_header = {"Authorization": "Token 5a3739ccb2dc7fa54bb5596bcd6e234223f8dc99" }


    # Tasks that should work
    def test_create_POST(self):
        r = requests.post(self.allposts_url % 8, headers = self.auth_header, data = self.data1)
        self.assertTrue(r.status_code == 200,"Status code expected to be 200, got %d" % r.status_code)
        self.assertTrue("Successfully created post:" in r.text, "Expected a successful post creation, got %s" % r.text)
        with open("post_tests.txt","w") as f: f.write(r.text.split(": ")[-1])

    # this is a bad test, it uses the code from the actual likepost() function in views.py so when the code changes there, this test will have to change too
    def test_like_POST(self):
        with open("post_tests.txt","r") as f: self.post_id = int(f.read())
        r = requests.post(self.like_post_url % (12, self.post_id))
        FILEPATH = os.path.dirname(os.path.abspath(__file__)) + "/"
        conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO postlikes VALUES(123456,12,12,%d);"%self.post_id)
        conn.commit()
        cursor.execute('SELECT * FROM postlikes WHERE from_user = %d AND post_id = %d'% (12, self.post_id))
        self.assertEqual(len(cursor.fetchall()), 1, "The postlike was not added to the database")

    def test_view_likes_post(self):
        r=requests.get(self.view_like_post_url % (12, self.post_id))
        self.assertTrue("likes on this post" in r.text, "Expected to see likes page but got %s"%r.text)

    def tearDown(self):
        # Clean up any leftover posts and likes that may still linger if tests fail!
        FILEPATH = os.path.dirname(os.path.abspath(__file__)) + "/"
        conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM postlikes WHERE like_id = 123456;")
        cursor.execute("DELETE FROM posts WHERE user_id = 12;")
        conn.commit()
        conn.close()
        
if __name__ == "__main__":
    # Run tests
    unittest.main()

