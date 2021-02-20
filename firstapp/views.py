from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.datastructures import MultiValueDictKeyError
import sqlite3
import os
from random import randrange as rand
from datetime import datetime

FILEPATH = os.path.dirname(os.path.abspath(__file__)) + "/"

POST_QUERY = "INSERT INTO posts VALUES (%d, %d, '%s', '%s', '%s', ?, '%s');"

# Create your views here.
def index(reqeuest):
    return HttpResponse("Hello, this is our first web app")

# CSRF Exempt stops the browser from authenticating when submitting a form, when users are required to login, this decorator will need to be deleted!
@csrf_exempt
def post(request,post_id):
    return HttpResponse("Specific post of author will go here")

@csrf_exempt
def allposts(request):
    resp = ""
    method = request.META["REQUEST_METHOD"]
    conn = sqlite3.connect(FILEPATH+"social.db")
    cursor = conn.cursor()
    if method == "POST":
        p = request.POST
        while True:
            post_id = rand(2**63)
            cursor.execute("SELECT post_id FROM posts WHERE post_id=%d;" % post_id)
            data = cursor.fetchall()
            if len(data) == 0 : break
        try:
            cursor.execute(POST_QUERY % (post_id,12345,p["title"],p["description"],p["contenttype"],str(datetime.now())),(sqlite3.Binary(bytes(p["content"],encoding="utf-8")),))
            conn.commit()
            resp = "Succesfully created post: %d\n" % post_id
        except MultiValueDictKeyError:
            resp = "Failed to create post:\nInvalid parameters\n"   
    elif method == "GET":
        cursor.execute("SELECT * FROM posts;")
        data = cursor.fetchall()
        pretty_template = '{\n\t"post_id":%d,\n\t"user_id":%d,\n\t"title":%s,\n\t"description":%s,\n\t"content-type":%s,\n\t"content":%a,\n\t"timestamp":%s,\n}\n'
        for d in data: resp += pretty_template % d
    else: resp = "Error: invalid method used"
    conn.close()
    return HttpResponse(resp)