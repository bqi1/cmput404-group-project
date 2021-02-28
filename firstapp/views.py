from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.http import HttpResponseNotFound, HttpResponseForbidden, HttpResponseBadRequest
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .form import UserForm
from django.urls import reverse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.datastructures import MultiValueDictKeyError
import sqlite3
import os
from random import randrange as rand
from datetime import datetime

from rest_framework.decorators import api_view, permission_classes, authentication_classes
#from rest_framework.permissions import IsAuthenticated
from .permissions import EditPermission
from rest_framework.authentication import BasicAuthentication, SessionAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token

FILEPATH = os.path.dirname(os.path.abspath(__file__)) + "/"

ADD_QUERY = "INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
EDIT_QUERY = "UPDATE posts SET post_id=?, user_id=?, title=?, description=?, contenttype=?, content=?, image=?, tstamp=? WHERE post_id=? AND user_id =?;"

# Create your views here.
def index(request):
    #if request.user.is_authenticated:
    return render(request, 'index.html')

def homepage(request):
    if request.user.is_authenticated:
        conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
        cursor = conn.cursor()
        cursor.execute('SELECT u.id,t.key FROM authtoken_token t, auth_user u WHERE u.id = t.user_id AND u.username = "%s";' % request.user)
        data = cursor.fetchall()[0]
        user_id,token = data[0], data[1]
        conn.close()
        return render(request, 'homepage.html', {'user_id':user_id,'token':token})
    
def signup(request):
    success = False
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
            new_username = form.cleaned_data.get('username')
            new_password = form.cleaned_data.get('password1')
            user = authenticate(username = new_username, password=new_password)
            auth_login(request, user)
            Token(user=user).save()
            user.save()

            success = True
            messages.success(request, "congrat!successful signup!")
           # return render(request, 'index.html')
            return HttpResponseRedirect(reverse('home'))
        else:
            context = {'form':form}
            return render(request, 'signup.html', context)
    else:
        form = UserForm()
        context = {'form':form}
        return render(request, 'signup.html', context)

def login(request):
    
    if request.method == 'POST':
        new_username = request.POST.get('username')
        new_password = request.POST.get('password')
        user = authenticate(request, username = new_username, password = new_password)
        if user is not None:
            auth_login(request, user)
          #  return HttpResponseRedirect(reverse('index'))
            return HttpResponseRedirect(reverse('home'))
        else:
         #   form = AuthenticationForm()
            #context = {'form':form}
         #   return render(request, 'signup.html', context)
            print("Invalid account!")
            return HttpResponseRedirect(reverse('login'))
    else:
        form = AuthenticationForm()
        context = {'form':form}
        return render(request, 'login.html', context)



@api_view(['GET','POST','PUT','DELETE'])
@authentication_classes([BasicAuthentication, SessionAuthentication, TokenAuthentication])
@permission_classes([EditPermission])
def post(request,user_id,post_id):
    resp = ""
    method = request.META["REQUEST_METHOD"]
    token = str(request.auth)
    conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM auth_user WHERE id=%d'%user_id)
    data = cursor.fetchall()
    if len(data)==0: return HttpResponseNotFound("The user you requested does not exist\n")
    cursor.execute('SELECT * FROM posts p WHERE p.post_id=%d AND p.user_id=%d'%(post_id,user_id))
    data = cursor.fetchall()
    if len(data)==0 and method != 'PUT': return HttpResponseNotFound("The post you requested does not exist\n")
    elif len(data) > 0 and method == 'PUT': return HttpResponse("The post with id %d already exists! Maybe try POST?\n"%post_id,status=409)

    if method == 'GET':
        pretty_template = '{\n\t"post_id":%d,\n\t"user_id":%d,\n\t"title":%s,\n\t"description":%s,\n\t"content-type":%s,\n\t"content":%s,\n\t"image":%a,\n\t"timestamp":%s,\n}\n'
        resp = pretty_template % data[0]
    else:
        cursor.execute('SELECT t.key FROM authtoken_token t, auth_user u WHERE u.id = t.user_id AND u.id = "%d";'%user_id)
        user_token = cursor.fetchall()[0][0]
        if token != user_token: return HttpResponseForbidden("Invalid token for the requested user!\n")

        if method == 'POST':
            p = request.POST
            try: image = p["image"] # image is an optional param!
            except MultiValueDictKeyError: image = '0'
            try:
                cursor.execute(EDIT_QUERY, (post_id,user_id,p["title"],p["description"],p["contenttype"],p["content"],sqlite3.Binary(bytes(image,encoding="utf-8")),str(datetime.now()),post_id,user_id))
                conn.commit()
                resp = "Succesfully modified post: %d\n" % post_id
            except MultiValueDictKeyError:
                resp = "Failed to modify post:\nInvalid parameters\n"  
        elif method == 'PUT':
            p = request.POST
            try: image = p["image"] # image is an optional param!
            except MultiValueDictKeyError: image = '0'
            try:
                cursor.execute(ADD_QUERY, (post_id,user_id,p["title"],p["description"],p["contenttype"],p["content"],sqlite3.Binary(bytes(image,encoding="utf-8")),str(datetime.now())))
                conn.commit()
                resp = "Succesfully added post: %d\n" % post_id
            except MultiValueDictKeyError:
                resp = "Failed to modify post:\nInvalid parameters\n"  
        elif method == 'DELETE':
            cursor.execute("DELETE FROM posts WHERE post_id=%d AND user_id=%d"%(post_id,user_id))
            conn.commit()
            resp = "Successfully deleted post: %d\n" %post_id
        else:
            conn.close()
            return HttpResponseBadRequest("Error: invalid method used\n")
    conn.close()
    return HttpResponse(resp)

@api_view(['GET','POST'])
@authentication_classes([BasicAuthentication, SessionAuthentication, TokenAuthentication])
@permission_classes([EditPermission])
def allposts(request,user_id):
    resp = ""
    method = request.META["REQUEST_METHOD"]
    conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM auth_user WHERE id=%d'%user_id)
    data = cursor.fetchall()
    if len(data)==0: return HttpResponseNotFound("The user you requested does not exist\n")
    cursor.execute('SELECT t.key FROM authtoken_token t, auth_user u WHERE u.id = t.user_id AND u.id = "%d";'%user_id)
    user_token = cursor.fetchall()[0][0]
    if method == "POST":
        token = request.META["HTTP_AUTHORIZATION"].split("Token ")[1]
        # Check to see if supplied token matches the user in question!
        print(token)
        print(user_token)
        if token != user_token: return HttpResponseForbidden("Invalid token for the requested user!\n")
        p = request.POST
        while True:
            post_id = rand(2**63)
            cursor.execute("SELECT post_id FROM posts WHERE post_id=%d;" % post_id)
            data = cursor.fetchall()
            if len(data) == 0 : break
        
        try: image = p["image"] # image is an optional param!
        except MultiValueDictKeyError: image = '0'

        try:
            cursor.execute(ADD_QUERY, (post_id,user_id,p["title"],p["description"],p["contenttype"],p["content"],sqlite3.Binary(bytes(image,encoding="utf-8")),str(datetime.now())))
            conn.commit()
            resp = "Succesfully created post: %d\n" % post_id
        except MultiValueDictKeyError:
            resp = "Failed to create post:\nInvalid parameters\n"   
    elif method == "GET":
        cursor.execute("SELECT * FROM posts WHERE user_id=%d;" % user_id)
        data = cursor.fetchall()
        pretty_template = '{\n\t"post_id":%d,\n\t"user_id":%d,\n\t"title":%s,\n\t"description":%s,\n\t"content-type":%s,\n\t"content":%s,\n\t"image":%a,\n\t"timestamp":%s\n}\n'
        for d in data: resp += pretty_template % d
    else:
        conn.close()
        return HttpResponseBadRequest("Error: invalid method used\n")
    conn.close()
    agent = request.META["HTTP_USER_AGENT"]
    if "Mozilla" in agent or "Chrome" in agent or "Edge" in agent or "Safari" in agent:
        with open(FILEPATH+"static/allposts.js","r") as f: script = f.read() % user_token
        return render(request,'allposts.html',{'resp':resp,'true_auth':(request.user.is_authenticated and request.user.id == user_id),'postscript':script})
    else: return HttpResponse(resp)
