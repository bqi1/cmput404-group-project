import unittest
import requests
import json
import sqlite3
import os

class CommentTests(unittest.TestCase):

    def setUp(self):
        self.allposts_url = "http://localhost:8000/author/%s/posts/"
        self.post_url = "http://localhost:8000/author/%s/posts/%d"
        self.view_comment_post_url = "http://localhost:8000/author/%s/posts/%d/vieComment/"
        self.comment_post_url = "http://localhost:8000/author/%s/posts/%d/commentpost/"
        self.comment_id = 12345
        self.data1 = {"comment_id":"comment_id","content":"comment_text"}
        self.auth_header = {"Authorization": "Token 9ea7039bf3a3e547be6d07b31070239e6489111a" }
        self.unauth_header = {"Authorization": "Token 5a3739ccb2dc7fa54bb5596bcd6e234223f8dc99" }
    
    def test_make_POST(self):
        r = requests.post(self.allposts_url % 8, headers = self.auth_header, data = self.data1)
        self.assertTrue(r.status_code == 200,"Status code expected to be 200, got %d" % r.status_code)
        self.assertTrue("Successfully created post:" in r.text, "Expected a successful post creation, got %s" % r.text)
        with open("comment_tests.txt","w") as f: f.write(r.text.split(": ")[-1])
    
    def test_comment_POST(self):
        with open("comment_tests.txt","r") as f: self.post_id = int(f.read())
        r = requests.post(self.comment_post_url % (12, self.post_id))
        FILEPATH = os.path.dirname(os.path.abspath(__file__)) + "/"
        conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO postlikes VALUES(123456,12,12,%d);"%self.post_id)
        conn.commit()
        cursor.execute('SELECT * FROM firstapp_comment WHERE from_user = %d AND post_id = %d'% (12, self.post_id))
        self.assertEqual(len(cursor.fetchall()), 1, "The comment was not added to the database")
    
    def test_view_comment_post(self):
        r = requests.get(self.view_comment_post_url % (7, self.post_id))
        self.assertTrue("comment on the post" in r.text, "expected to see comments but got %s"%r.text)
    
    def tearDown(self):
        FILEPATH = os.path.dirname(os.path.abspath(__file__)) + "/"
        conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM firstapp_comment WHERE comment_id = 123456;")
        cursor.execute("DELETE FROM firstapp_comment WHERE from_user = 7;")
        conn.commit()
        conn.close()

if __name__=="__main__":
    unittest.main()

    
