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

class LikeTests(unittest.TestCase):

    # Initialize some variables
    def setUp(self):
        self.allposts_url = "http://localhost:8000/author/%s/posts/"
        self.post_url = "http://localhost:8000/author/%s/posts/%d"
        self.like_post_url = "http://localhost:8000/author/%s/posts/%d/likepost/"
        self.post_id2 = 12345
        self.data1 = {"title":"title_one","description":"desc_one","markdown":0,"content":"content_one"}
        self.data2 = {"title":"title_two","description":"desc_two","markdown":1,"content":"content_three"}
        self.auth_header = {"Authorization": "Token 9ea7039bf3a3e547be6d07b31070239e6489111a" }
        self.unauth_header = {"Authorization": "Token 5a3739ccb2dc7fa54bb5596bcd6e234223f8dc99" }


    # Tasks that should work
    def test_create_POST(self):
        r = requests.post(self.allposts_url % 8, headers = self.auth_header, data = self.data1)
        self.assertTrue(r.status_code == 200,"Status code expected to be 200, got %d" % r.status_code)
        print(r.text)
        self.assertTrue("Successfully created post:" in r.text, "Expected a successful post creation, got %s" % r.text)

    def test_like_POST(self):
        r = requests.post(self.like_post_url % (12,self.post_id2))
        self.assertTrue(r.status_code == 200,"Status code expected to be 200, got %d" % r.status_code)
        self.assertTrue("Successfully liked post:%d" % self.post_id2, "Expected a like, got %s" % r.text)


if __name__ == "__main__":
    # Run tests
    unittest.main()

    # Clean up any leftover posts and likes that may still linger if tests fail!
    conn = sqlite3.connect()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM postlikes WHERE user_id = 12;")
    cursor.execute("DELETE FROM posts WHERE user_id = 12;")
    conn.commit()
    conn.close()