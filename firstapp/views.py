from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from django.http import HttpResponseNotFound, HttpResponseBadRequest
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
import json
from markdown import Markdown as Md

from rest_framework.decorators import api_view, permission_classes, authentication_classes
#from rest_framework.permissions import IsAuthenticated
from .permissions import EditPermission
from rest_framework.authentication import BasicAuthentication, SessionAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from .models import Author


FILEPATH = os.path.dirname(os.path.abspath(__file__)) + "/"

ADD_QUERY = "INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
EDIT_QUERY = "UPDATE posts SET post_id=?, user_id=?, title=?, description=?, markdown=?, content=?, image=?, tstamp=? WHERE post_id=? AND user_id =?;"

# Create your views here.
def index(request):
    #if request.user.is_authenticated:
    return render(request, 'index.html')

def homepage(request):
    if request.user.is_authenticated:
        conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
        cursor = conn.cursor()
        cursor.execute('SELECT u.id,t.key FROM authtoken_token t, auth_user u WHERE u.id = t.user_id AND u.username = "%s";' % request.user)
        try:
            data = cursor.fetchall()[0]
        except IndexError: # No token exists, must create a new one!
            token = Token.objects.create(user=request.user)
            cursor.execute('SELECT u.id,t.key FROM authtoken_token t, auth_user u WHERE u.id = t.user_id AND u.username = "%s";' % request.user)
            data = cursor.fetchall()[0]
        user_id,token = data[0], data[1]
        conn.close()
        return render(request, 'homepage.html', {'user_id':user_id,'token':token})
    
def signup(request):
    success = False
    if request.method == 'POST':
        form = UserForm(request.POST) # A form consisting of username, password, email, and name
        if form.is_valid():
            user = form.save()
            new_username = form.cleaned_data.get('username')
            new_password = form.cleaned_data.get('password1')
            user = authenticate(username = new_username, password=new_password) # Attempt to authenticate user after using checks. Returns User object if succesful, else None
            auth_login(request, user) # Save user ID for further sessions
            Token(user=user).save()
            user.save()
            success = True
            # Check if UsersNeedAuthentication is True. If it is, redirect to login and set Authorized to False for that user
            # Else, let the use in the homepage, set Authorized to True
            conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
            cursor = conn.cursor()
            cursor.execute('SELECT UsersNeedAuthentication from firstapp_setting;')
            try:
                needs_authentication = cursor.fetchall()[0][0]
            except:
                messages.add_message(request,messages.INFO, 'The server admin needs to implement settings. Please come back later.')
                return HttpResponseRedirect(reverse('register'))
            finally:
                conn.close()

            if needs_authentication: # If users need an OK from server admin, create the user, but set authorized to False, preventing them from logging in.
                user = Author.objects.create(username=new_username,userid=request.user.id,authorized=False,email=form.cleaned_data['email'],name=f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}")
                # If the flag, UsersNeedAuthentication is True, redirect to Login Page with message
                messages.add_message(request,messages.INFO, 'Please wait to be authenticated by a server admin.')
                return HttpResponseRedirect(reverse('login'))
            # Else, let them in homepage.
            user = Author.objects.create(username=new_username,userid=request.user.id, authorized=True,email=form.cleaned_data['email'],name=f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}")
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
            # Check if Authorized. If so, proceed. Else, display an error message and redirect back to login page.
            conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
            cursor = conn.cursor()
            cursor.execute('SELECT Authorized FROM firstapp_usercreation WHERE Userid = ? and User = ?;',(request.user.id,new_username))
            try:
                authenticated = cursor.fetchall()[0][0]
                conn.close()
            except:
                conn.close()
                messages.add_message(request,messages.INFO, 'This user does not exist.')
                return HttpResponseRedirect(reverse('login'))
            if not authenticated:
                messages.add_message(request,messages.INFO, 'Please wait to be authenticated by a server admin.')
                return HttpResponseRedirect(reverse('login'))
            else:
                auth_login(request, user)
                return HttpResponseRedirect(reverse('home'))
        else:
            print("Invalid account!")
            return HttpResponseRedirect(reverse('login'))
    else:
        form = AuthenticationForm()
        context = {'form':form}
        return render(request, 'login.html', context)



def validate_int(p,optional=[]):
    try:
        int(p["markdown"])
        for i in optional: int(i)
        return 1
    except ValueError: return 0

def make_post_html(data,allposts=False):
    resp = ""
    start = '<div class="post" style="border:solid;" '+('onclick="viewPost(\'%d\')"' if allposts else '')+'><p class="title">%s</p><p class="desc">%s</p></br><p class="content">%s</p></br>'
    endimage = '<img src="%s"/><span class="md" style="display:none" value="%s"></div>'
    endnoimage = '<span class="md" style="display:none" value="%s"></div>'
    for d in data:
        image = str(d[-2],encoding="utf-8")
        content = d[5]
        if d[4]: # use markdown!
            md = Md()
            content = md.convert(content)
        starttag = start % (d[0],d[2],d[3],content) if allposts else start % (d[2],d[3],content)
        if image == '0': resp += starttag + endnoimage % (d[4],)
        else: resp += starttag + endimage % (image,d[4])
        resp += "</br>"
    return resp

def make_post_list(data):
    post_list = []
    for d in data:
        post_dict = {
            "post_id":d[0],
            "user_id":d[1],
            "title":d[2],
            "description":d[3],
            "markdown":d[4],
            "content":d[5],
            "image":str(d[6],encoding="utf-8"),
            "timestamp":d[7]
        }
        post_list.append(post_dict)
    return json.dumps(post_list,indent=4)



@api_view(['GET','POST','PUT','DELETE'])
@authentication_classes([BasicAuthentication, SessionAuthentication, TokenAuthentication])
@permission_classes([EditPermission])
def post(request,user_id,post_id):
    resp = ""
    method = request.META["REQUEST_METHOD"]
    conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM auth_user WHERE id=%d'%user_id)
    data = cursor.fetchall()
    if len(data)==0: return HttpResponseNotFound("The user you requested does not exist\n")
    cursor.execute('SELECT * FROM posts p WHERE p.post_id=%d AND p.user_id=%d'%(post_id,user_id))
    data = cursor.fetchall()
    if len(data)==0 and method != 'PUT': return HttpResponseNotFound("The post you requested does not exist\n")
    elif len(data) > 0 and method == 'PUT': return HttpResponse("The post with id %d already exists! Maybe try POST?\n"%post_id,status=409)
    cursor.execute('SELECT t.key FROM authtoken_token t, auth_user u WHERE u.id = t.user_id AND u.id = "%d";'%user_id)
    user_token = cursor.fetchall()[0][0]

    if method == 'GET':
        resp = make_post_list(data)
    else:
        token = request.META["HTTP_AUTHORIZATION"].split("Token ")[1]
        if token != user_token: return HttpResponse('{"detail":"Authentication credentials were not provided."}',status=401)

        if method == 'POST':
            p = request.POST
            try: image = p["image"] # image is an optional param!
            except MultiValueDictKeyError: image = '0'
            try:
                if not validate_int(p,[post_id,user_id]): return HttpResponseBadRequest("Error: you have submitted non integer values to integer fields.")
                cursor.execute(EDIT_QUERY, (post_id,user_id,p["title"],p["description"],p["markdown"],p["content"],sqlite3.Binary(bytes(image,encoding="utf-8")),str(datetime.now()),post_id,user_id))
                conn.commit()
                resp = "Successfully modified post: %d\n" % post_id
            except MultiValueDictKeyError:
                return HttpResponseBadRequest("Failed to modify post:\nInvalid parameters\n")  
        elif method == 'PUT':
            p = request.POST
            try: image = p["image"] # image is an optional param!
            except MultiValueDictKeyError: image = '0'
            try:
                if not validate_int(p,[post_id,user_id]): return HttpResponseBadRequest("Error: you have submitted non integer values to integer fields.")
                cursor.execute(ADD_QUERY, (post_id,user_id,p["title"],p["description"],p["markdown"],p["content"],sqlite3.Binary(bytes(image,encoding="utf-8")),str(datetime.now())))
                conn.commit()
                resp = "Successfully created post: %d\n" % post_id
            except MultiValueDictKeyError:
                return HttpResponseBadRequest("Failed to modify post:\nInvalid parameters\n")  
        elif method == 'DELETE':
            cursor.execute("DELETE FROM posts WHERE post_id=%d AND user_id=%d"%(post_id,user_id))
            conn.commit()
            resp = "Successfully deleted post: %d\n" %post_id
        else:
            conn.close()
            return HttpResponseBadRequest("Error: invalid method used\n")
    conn.close()
    agent = request.META["HTTP_USER_AGENT"]
    if "Mozilla" in agent or "Chrome" in agent or "Edge" in agent or "Safari" in agent:
        if method == "GET": resp = make_post_html(data)
        with open(FILEPATH+"static/post.js","r") as f: script = f.read() % (user_token, user_token)
        return render(request,'post.html',{'post_list':resp,'true_auth':(request.user.is_authenticated and request.user.id == user_id),'postscript':script})
    else: return HttpResponse(resp)

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
        if token != user_token: return HttpResponse('{"detail":"Authentication credentials were not provided."}',status=401)
        p = request.POST
        while True:
            post_id = rand(2**63)
            cursor.execute("SELECT post_id FROM posts WHERE post_id=%d;" % post_id)
            data = cursor.fetchall()
            if len(data) == 0 : break
        
        try: image = p["image"] # image is an optional param!
        except MultiValueDictKeyError: image = '0'

        try:
            if not validate_int(p): return HttpResponseBadRequest("Error: you have submitted non integer values to integer fields.")
            cursor.execute(ADD_QUERY, (post_id,user_id,p["title"],p["description"],p["markdown"],p["content"],sqlite3.Binary(bytes(image,encoding="utf-8")),str(datetime.now())))
            conn.commit()
            resp = "Successfully created post: %d\n" % post_id
        except MultiValueDictKeyError:
            return HttpResponseBadRequest("Failed to create post:\nInvalid parameters\n")
    elif method == "GET":
        cursor.execute("SELECT * FROM posts WHERE user_id=%d;" % user_id)
        data = cursor.fetchall()
        resp = make_post_list(data)
    else:
        conn.close()
        return HttpResponseBadRequest("Error: invalid method used\n")
    conn.close()
    agent = request.META["HTTP_USER_AGENT"]
    if "Mozilla" in agent or "Chrome" in agent or "Edge" in agent or "Safari" in agent:
        with open(FILEPATH+"static/allposts.js","r") as f: script = f.read() % user_token
        if method == "GET": resp = make_post_html(data,allposts=True)
        return render(request,'allposts.html',{'post_list':resp,'true_auth':(request.user.is_authenticated and request.user.id == user_id),'postscript':script})
    else: return HttpResponse(resp)
