from django.shortcuts import render, HttpResponse, HttpResponseRedirect, get_object_or_404
from django.http import HttpResponseNotFound, HttpResponseForbidden, HttpResponseBadRequest
from django.contrib.auth import authenticate
from django.contrib.auth import login as auth_login
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from .form import UserForm, CommentForm
# from .form import UserForm
from django.urls import reverse
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.http import QueryDict
from django.utils.datastructures import MultiValueDictKeyError
from django.db import connection
import sqlite3
import os
from random import randrange as rand
from datetime import datetime
import json
from django.conf import settings
from markdown import Markdown as Md
from django.core.mail import send_mail

from rest_framework.decorators import api_view, permission_classes, authentication_classes
#from rest_framework.permissions import IsAuthenticated
from .permissions import EditPermission
from rest_framework.authentication import BasicAuthentication, SessionAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from friend.request_status import RequestStatus
from friend.models import FriendList, FriendRequest,FriendShip
from friend.is_friend import get_friend_request_or_false
from firstapp.models import Author, Post, Author_Privacy, Comment, PostLikes, Node
from django.contrib.auth import get_user_model
import uuid
import requests
import base64
from .remote_friend import get_all_remote_user
FILEPATH = os.path.dirname(os.path.abspath(__file__)) + "/"

ADD_QUERY = "INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
EDIT_QUERY = "UPDATE posts SET post_id=?, user_id=?, title=?, description=?, markdown=?, content=?, image=?, tstamp=? WHERE post_id=? AND user_id =?;"

PRIV_ADD_QUERY = "INSERT INTO author_privacy VALUES (?,?);"
STR2BOOL = lambda x: bool(int(x))

# Create your views here.
def index(request):
    #if request.user.is_authenticated:
    return render(request, 'index.html')

def homepage(request):
    if request.user.is_authenticated:
        author = Author.objects.get(username=request.user)
        user_id,author_uuid = author.userid,author.consistent_id


        ourURL = "http://"+request.META['HTTP_HOST']+"/posts"
        ourRequest = requests.get(url=ourURL)
        ourData = ourRequest.json()

        # Get all public posts from another server, from the admin panel
        servers = Node.objects.all()
        theirData = []
        for server in servers: # Iterate through each server, providing authentication if necessary
            try:
                postsRequest = requests.get(url=f"{server.hostserver}/posts", auth = (f"{server.authusername}",f"{server.authpassword}"))
                if postsRequest.status_code == 200:
                    theirData.extend(postsRequest.json())
            except:
                continue



        return render(request, 'homepage.html', {'user_id':user_id,'author_uuid':author_uuid, 'our_server_posts':ourData,'other_server_posts':theirData})
    
def signup(request):
    # Called when user accesses the signup page
    success = False
    if request.method == 'POST': # When a user wants to sign up, first validate:
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
            conn = connection
            cursor = conn.cursor()
            cursor.execute('SELECT UsersNeedAuthentication from firstapp_setting;')
            try:
                needs_authentication = cursor.fetchall()[0][0]
            except:
                messages.add_message(request,messages.INFO, 'The server admin needs to implement settings. Please come back later.')
                return HttpResponseRedirect(reverse('login'))
            finally:
                conn.close()

            if needs_authentication: # If users need an OK from server admin, create the user, but set authorized to False, preventing them from logging in.
                user = Author.objects.create(host=f"http://{request.get_host()}",username=new_username,userid=request.user.id,\
                    authorized=False,email=form.cleaned_data['email'],\
                        name=f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}",\
                            consistent_id=f"{uuid.uuid4().hex}")
                # If the flag, UsersNeedAuthentication is True, redirect to Login Page with message
                user.save()
                messages.add_message(request,messages.INFO, 'Please wait to be authenticated by a server admin.')
                return HttpResponseRedirect(reverse('login'))
            # Else, let them in homepage.
            user = Author.objects.create(host=f"http://{request.get_host()}",username=new_username,\
                userid=request.user.id, authorized=True,email=form.cleaned_data['email'],\
                    name=f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}",\
                        consistent_id=f"{uuid.uuid4().hex}")
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
            conn = connection
            cursor = conn.cursor()
            cursor.execute("SELECT Authorized FROM firstapp_author WHERE username = '%s';"%new_username)
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

# This function will return all visible posts, and return them in html to be displayed in broswer
# data - the list of tuples returned from sql
# user_id - used to check to see if the current user can view the post (is it private to specific authors, or public?)
# canaedit - true if the current user is allowed to edit the post
def make_post_html(data,user_id,isowner=False):
    resp = ""
  #  resp1 = ""
    with open(FILEPATH+"static/like.js","r") as f: script = f.read()
  #  with open(FILEPATH+"static/comment.js","r") as f1: script1 = f1.read()
    #add javascript likePost function and the jquery library for ajax
    jscript = '<script>' + script + '</script>' + '<script src="http://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js"></script>'
    start = '<div class="post" style="border:solid;" ><p class="title">%s</p><p class="desc">%s</p></br><p class="content">%s</p></br>'
    endimage = '<img src="%s"/><span class="md" style="display:none" value="%s"></span></br>'+('<input type = "button" value="Edit" onclick="viewPost(\'{0}\')">' if isowner else '')
    endnoimage = '<span class="md" style="display:none" value="%s"></span></br>'+('<input type = "button" value="Edit" onclick="viewPost(\'{0}\')">' if isowner else '')

    for d in data:
        priv = Author_Privacy.objects.filter(post_id=d.post_id)
        image = str(d.image,encoding="utf-8")
        content = d.content
        if d.markdown: # use markdown!
            md = Md()
            content = md.convert(content)
        starttag = jscript
        starttag += start % (d.title,d.description,content)
        if len(priv) == 0: # post is not private
            if image == '0':
                resp += starttag
                resp += endnoimage.format(d.post_id) % (d.markdown,)
                resp += '<button onclick="likePost(\'{}\')">Like</button>'.format(d.post_id)
                resp += '<button onclick="viewLikes(\'{}\')">View Likes</button>'.format(d.post_id)
                resp += '<button onclick="commentPost(\'{}\')">Comment</button>'.format(d.post_id)
                resp += '<button onclick="viewComment(\'{}\')">View Comment</button>'.format(d.post_id)
            else: 
                resp += starttag + endimage.format(d.post_id) % (image,d.markdown)
                resp += '<button onclick="likePost(\'{}\')">Like</button>'.format(d.post_id)
                resp += '<button onclick="viewLikes(\'{}\')">View Likes</button>'.format(d.post_id)
                resp += '<button onclick="commentPost(\'{}\')">Comment</button>'.format(d.post_id)
                resp += '<button onclick="viewComment(\'{}\')">View Comment</button>'.format(d.post_id)

            resp += "</br>"
        else: # post is private
            show_post = False
            for p in priv:
                if p.user_id == user_id or isowner:
                    show_post = True
                    break
            if show_post and user_id != None: # show post only if this variable is true, and a user is logged in!
                if image == '0': resp += starttag + endnoimage.format(d.post_id,d.post_id) % (d.markdown,)
                else: resp += starttag + endimage.format(d.post_id,d.post_id) % (image,d.markdown)
                resp += "</br>"
    return resp

# This function will return all visible posts, and return them in a list to be displayed to non-browser user agents
# data - the list of tuples returned from sql
# user_id - used to check to see if the current user can view the post (is it private to specific authors, or public?)
def make_post_list(data,user_id,isowner=False):
    post_list = []
    for d in data:

        # This block assigns the author object to each post object.
        author = Author.objects.get(consistent_id=d.user_id)
        author_dict = {
            "id": f"http://{author.host}/author/{author.consistent_id}",
            "host": f"{author.host}/",
            "displayName": author.username,
            "url": f"{author.host}/firstapp/{author.userid}",
            "github": author.github,
        }

        priv = Author_Privacy.objects.filter(post_id=d.post_id)
        post_dict = {
            "post_id":d.post_id,
            "user_id":d.user_id,
            "title":d.title,
            "description":d.description,
            "markdown":d.markdown,
            "content":d.content,
            "image":str(d.image,encoding="utf-8"),
            "privfriends":d.privfriends,
            "timestamp":d.tstamp,
            "id":d.id,
            "author":author_dict,
        }
        # post is public or post belongs to user
        if len(priv) == 0 or user_id == d.user_id: post_list.append(post_dict)
        else:
            show_post = False
            # Determine if requesting author is among privacy list
            for p in priv:
                if p.user_id == user_id or isowner:
                    show_post = True
                    break
            if show_post and user_id != None: post_list.append(post_dict)
    return json.dumps(post_list,indent=4)

# The api view for looking at a specific post for a user
# GET - view that specific post (not auth)
# POST - edit that specific post (auth)
# PUT - create post with specific id (auth)
# DELETE - delte specific post (auth)
@api_view(['GET','POST','PUT','DELETE'])
@authentication_classes([BasicAuthentication, SessionAuthentication, TokenAuthentication])
@permission_classes([EditPermission])
def post(request,user_id,post_id):
    resp = ""
    method = request.META["REQUEST_METHOD"]
    conn = connection
    cursor = conn.cursor()
    data = Author.objects.filter(consistent_id=user_id)
    if len(data)==0: return HttpResponseNotFound("The user you requested does not exist\n")
    data = Post.objects.filter(post_id=post_id,user_id=user_id)
    if len(data)==0 and method != 'PUT': return HttpResponseNotFound("The post you requested does not exist\n") # Check to see if post in url exists (not for PUT)
    data = Post.objects.filter(post_id=post_id)
    if len(data) > 0 and method == 'PUT': return HttpResponse("The post with id %d already exists! Maybe try POST?\n"%post_id,status=409) # check to see if post already exists (for PUT)
    cursor.execute("SELECT t.key FROM authtoken_token t, auth_user u, firstapp_author a WHERE u.id = t.user_id AND u.id = a.userid AND a.consistent_id = '%s';"%user_id)
    user_token = cursor.fetchall()[0][0]
    cursor.execute("SELECT a.userid FROM firstapp_author a WHERE a.consistent_id= '%s';"%user_id)
    author_id = cursor.fetchall()[0][0]
    trueauth = (request.user.is_authenticated and author_id == request.user.id) # Check if the user is authenticated AND their id is the same as the author they are viewing posts of. If all true, then they can edit
    if method == 'GET':
        resp = make_post_list(data,request.user.id,isowner=trueauth)
    else:
        token = request.META["HTTP_AUTHORIZATION"].split("Token ")[1]
        if token != user_token: return HttpResponse('{"detail":"Authentication credentials were not provided."}',status=401) # Incorrect or missing token

        if method == 'POST':

            p = request.POST
            if request.META["CONTENT_TYPE"] == "application/json": # Allows clients to send JSON requests
                p = QueryDict('',mutable=True)
                p.update(request.data)
            try: image = p["image"] # image is an optional param!
            except MultiValueDictKeyError: image = '0'
            try: # if all mandatory fields are passed
                if not validate_int(p,[post_id]): return HttpResponseBadRequest("Error: you have submitted non integer values to integer fields.") # non integer markdown field (0-1)
                new_post = Post.objects.get(post_id=post_id,user_id=user_id)
                new_post.title = p["title"]
                new_post.description = p["description"]
                new_post.markdown = p["markdown"]
                new_post.content = p["content"]
                new_post.image = sqlite3.Binary(bytes(image,encoding="utf-8"))
                new_post.privfriends = p["privfriends"]
                new_post.tstamp = str(datetime.now())
                resp = "Successfully modified post: %d\n" % post_id

            except MultiValueDictKeyError:
                return HttpResponseBadRequest("Failed to modify post:\nInvalid parameters\n")

            # Modify the author privacy table in the database
            if "priv_author" in p.keys() or "priv_author[]" in p.keys():
                if "priv_author" in p.keys(): private_authors = p.getlist("priv_author")
                else: private_authors = p.getlist("priv_author[]")
                for pa in private_authors:
                    data = Author.objects.filter(userid=pa)
                    if len(data) == 0: return HttpResponseNotFound("One or more user ids entered into the author privacy field are not valid user ids.") # check if author ids are valid
                for pa in private_authors:
                    new_private_author = Author_Privacy(post_id=post_id,user_id=pa)
                    new_private_author.save()
            else:
                author_privacies = Author_Privacy.objects.filter(post_id=post_id)
                for ap in author_privacies: ap.delete()
            new_post.save()

 
        elif method == 'PUT':

            p = request.POST
            if request.META["CONTENT_TYPE"] == "application/json": # Allows clients to send JSON requests
                p = QueryDict('',mutable=True)
                p.update(request.data)
            try: image = p["image"] # image is an optional param!
            except MultiValueDictKeyError: image = '0'
            try: # if all mandatory fields are passed
                if not validate_int(p,[post_id]): return HttpResponseBadRequest("Error: you have submitted non integer values to integer fields.") # non integer markdown field (0-1)
                new_post = Post(id = f"http://{request.get_host()}/author/{user_id}/posts/{post_id}",post_id=post_id,user_id=user_id,title=p["title"],description=p["description"],markdown=STR2BOOL(p["markdown"]),content=p["content"],image=sqlite3.Binary(bytes(image,encoding="utf-8")),privfriends=STR2BOOL(p["privfriends"]),tstamp=str(datetime.now()))
                resp = "Successfully created post: %d\n" % post_id
            except MultiValueDictKeyError:
                return HttpResponseBadRequest("Failed to modify post:\nInvalid parameters\n")

            # Modify the author privacy table in the database
            if "priv_author" in p.keys() or "priv_author[]" in p.keys():
                if "priv_author" in p.keys(): private_authors = p.getlist("priv_author")
                else: private_authors = p.getlist("priv_author[]")
                for pa in private_authors:
                    data = Author.objects.filter(userid=pa)
                    if len(data) == 0: return HttpResponseNotFound("One or more user ids entered into the author privacy field are not valid user ids.")
                for pa in private_authors:
                    new_private_author = Author_Privacy(post_id=post_id,user_id=pa)
                    new_private_author.save()
            new_post.save()

        elif method == 'DELETE':
            author_privacies = Author_Privacy.objects.filter(post_id=post_id)
            for ap in author_privacies: ap.delete()
            new_post = Post.objects.get(post_id=post_id,user_id=user_id)
            new_post.delete()
            resp = "Successfully deleted post: %d\n" %post_id
        else:
            conn.close()
            return HttpResponseBadRequest("Error: invalid method used\n")
    conn.close()
    agent = request.META["HTTP_USER_AGENT"]
    if "Mozilla" in agent or "Chrome" in agent or "Edge" in agent or "Safari" in agent: # is the agent a browser? If yes, show html, if no, show regular post list
        if method == "GET": resp = make_post_html(data,request.user.id,isowner=trueauth)
        with open(FILEPATH+"static/post.js","r") as f: script = f.read() % (user_token, user_token)
        # true_auth: is user logged in, and are they viewing their own post? (determines if they can edit /delete the post or not)
        return render(request,'post.html',{'post_list':resp,'true_auth':trueauth,'postscript':script})
    else: return HttpResponse(resp)

# Api view for looking at all posts for a specific user
# GET - get all posts for auser (not auth)
# POST - create post with random id (auth)
@api_view(['GET','POST'])
@authentication_classes([BasicAuthentication, SessionAuthentication, TokenAuthentication])
@permission_classes([EditPermission])
def allposts(request,user_id):
    resp = ""
    method = request.META["REQUEST_METHOD"]

    conn = connection
    cursor = conn.cursor()
    data = Author.objects.filter(consistent_id=user_id)

    if len(data)==0: return HttpResponseNotFound("The user you requested does not exist\n")

    cursor.execute("SELECT t.key FROM firstapp_author a, authtoken_token t WHERE a.userid = t.user_id AND a.consistent_id= '%s';"%user_id)
    user_token = cursor.fetchall()[0][0]

    cursor.execute("SELECT a.userid FROM firstapp_author a WHERE a.consistent_id= '%s';"%user_id)
    author_id = cursor.fetchall()[0][0]

    trueauth = (request.user.is_authenticated and author_id == request.user.id) # Check if the user is authenticated AND their id is the same as the author they are viewing posts of. If all true, then they can edit

    if method == "POST":
        token = request.META["HTTP_AUTHORIZATION"].split("Token ")[1]
        if token != user_token: return HttpResponse('{"detail":"Authentication credentials were not provided."}',status=401) # Incorrect or missing token
        p = request.POST
        if request.META["CONTENT_TYPE"] == "application/json": # Allows clients to send JSON requests
            p = QueryDict('',mutable=True)
            p.update(request.data)
        while True:
            post_id = rand(2**28)
            data = Post.objects.filter(post_id=post_id)
            if len(data) == 0 : break
        try: image = p["image"] # image is an optional param!
        except MultiValueDictKeyError: image = '0'

        try: # if all mandatory fields are passed
            if not validate_int(p): return HttpResponseBadRequest("Error: you have submitted non integer values to integer fields.")
            new_post = Post(id = f"http://{request.get_host()}/author/{user_id}/posts/{post_id}",post_id=post_id,user_id=user_id,title=p["title"],description=p["description"],markdown=STR2BOOL(p["markdown"]),content=p["content"],image=sqlite3.Binary(bytes(image,encoding="utf-8")),privfriends=STR2BOOL(p["privfriends"]),tstamp=str(datetime.now()))
            resp = "Successfully created post: %d\n" % post_id
        except MultiValueDictKeyError:
            return HttpResponseBadRequest("Failed to create post:\nInvalid parameters\n")

        # Modify the author privacy table in the database
        if "priv_author" in p.keys() or "priv_author[]" in p.keys():
            if"priv_author" in p.keys(): private_authors = p.getlist("priv_author")
            else: private_authors = p.getlist("priv_author[]")
            for pa in private_authors:
                data = Author.objects.filter(userid=pa)
                if len(data) == 0: return HttpResponseNotFound("One or more user ids entered into the author privacy field are not valid user ids.")
            for pa in private_authors:
                new_private_author = Author_Privacy(post_id=post_id,user_id=pa)
                new_private_author.save()
        new_post.save()
    elif method == "GET":
        data = Post.objects.filter(user_id=user_id)
        resp = make_post_list(data,request.user.id,trueauth)
    else:
        conn.close()
        return HttpResponseBadRequest("Error: invalid method used\n")
    conn.close()
    agent = request.META["HTTP_USER_AGENT"]
    if "Mozilla" in agent or "Chrome" in agent or "Edge" in agent or "Safari" in agent: # is the agent a browser? If yes, show html, if no, show regular post list
        with open(FILEPATH+"static/allposts.js","r") as f: script = f.read() % (user_token)
        if method == "GET": resp = make_post_html(data,user_id,isowner=trueauth)
        # true_auth: is user logged in, and are they viewing their own posts? (determines if they can create a new post or not)
        return render(request,'allposts.html',{'post_list':resp,'true_auth':trueauth,'postscript':script})
    else: return HttpResponse(resp)

#like a post
@api_view(['POST'])
def likepost(request, user_id, post_id):
    resp = ""
    conn = connection
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM firstapp_postlikes WHERE from_user = %d AND post_id = %d"% (request.user.id, post_id))
    data = cursor.fetchall()
    # if post has already been liked
    if len(data) > 0:
        return HttpResponse("Post already liked", status=409)
    else:
        while True:
            like_id = rand(2**31-1)
            cursor.execute('SELECT * FROM firstapp_postlikes WHERE like_id = %d'% (like_id))
            if len(cursor.fetchall()) == 0:
                print(post_id)

                like = PostLikes(like_id=like_id, from_user =request.user.id, to_user = user_id, post_id = post_id)
                like.save()
                break
        # cursor.execute('INSERT INTO postlikes VALUES(%d, %d, %d, %d);'% (like_id, request.user.id, user_id, post_id))
        # conn.commit()
        #TODO send like object to author's inbox
        url = request.get_full_path()
        # make_like_object(url, author)
        return HttpResponse("Post liked successfully") # #TODO send to inbox here

def make_like_object(object, user_id, make_json = True):
    like_dict = {}
    like_dict["type"] = "like"
    try:
        author = Author.objects.get(consistent_id=user_id)
        url = 'http://c404-project.herokuapp.com/author/' + author.consistent_id
        r = requests.get(url)
        like_dict["author"] = r.json()
    except:
        return HttpResponseNotFound("The account you requested does not exist\n")
    like_dict["object"] = object
    if make_json:
        return json.dumps(like_dict)
    else:
        return like_dict

#get a list of likes from other authors on the post id
@api_view(['GET'])
def postlikes(request, user_id, post_id):
    conn = connection
    cursor = conn.cursor()
    agent = request.META["HTTP_USER_AGENT"]

    if "Mozilla" in agent or "Chrome" in agent or "Edge" in agent or "Safari" in agent: #if using browser
        cursor.execute("SELECT u.username FROM firstapp_postlikes l, auth_user u WHERE l.post_id=%d AND l.from_user = u.id;"%post_id)
        data = cursor.fetchall()
        author_list = []
        for d in data:
            author = d[0]
            author_list.append(author)
        num_likes = len(author_list)
    
        return render(request, "likes.html", {"author_list":author_list,"num_likes":num_likes})
    else: 
        #return a list of like objects
        cursor.execute('SELECT a.consistent_id FROM firstapp_postlikes l, firstapp_author a WHERE l.post_id=%d AND l.from_user = a.userid;'%post_id)
        data = cursor.fetchall()
        url = request.get_full_path()
        json_post_likes = make_post_likes_object(data, url)
        return HttpResponse(json.dumps(json_post_likes))

def make_post_likes_object(data, url):
    #Get list of likes from other authors on author_ids's post post_id
    post_likes_dict = {}
    json_like_object_list = []

    post_likes_dict["type"] = "post likes"
    for like in data:
        like_object = make_like_object(url, like[0], make_json=False)
        json_like_object_list.append(like_object)
    post_likes_dict["items"] = json_like_object_list
    return post_likes_dict


#get a list of posts and comments that the author has liked
@api_view(['GET'])
def liked(request,user_id):
    conn = connection
    cursor = conn.cursor()
    agent = request.META["HTTP_USER_AGENT"]

    if "Mozilla" in agent or "Chrome" in agent or "Edge" in agent or "Safari" in agent: #if using browser
        cursor.execute("SELECT * FROM firstapp_postlikes l, firstapp_author a WHERE l.from_user = a.userid AND a.consistent_id = '%s';"%(user_id))
        data = cursor.fetchall()
        liked_posts_list = []
        for id in data:
            post_id = id[0]
            liked_posts_list.append(post_id)
        return render(request, "liked.html", {"liked_posts_list":liked_posts_list})

    #TODO get comments that author has liked
    # cursor.execute('SELECT * FROM commentlikes WHERE from_id=%d;'%user_id)
    # data = cursor.fetchall()
    
    else:
        cursor.execute("SELECT a.consistent_id, l.post_id, l.to_user FROM firstapp_postlikes l, firstapp_author a WHERE a.consistent_id='%s' AND l.from_user=a.userid;"%(user_id))
        data = cursor.fetchall()
        liked_object_list = make_liked_object(data)

        return HttpResponse(json.dumps(liked_object_list))

def make_liked_object(data):
    liked_dict = {}
    json_like_object_list = []
    liked_dict["type"] = "liked"

    for like in data:
        url = "http://c404-project.herokuapp.com/author/" + like[2] + "/posts/" + str(like[1])
        like_object = make_like_object(url,like[0], make_json=False)
        json_like_object_list.append(like_object)
    liked_dict["items"] = json_like_object_list
    
    return liked_dict

@api_view(['GET'])
# This function retrieves all public posts.
def publicposts(request):
    # This method can GET all public posts based on their privacy
    resp = ""
    post_list = []
    posts = Post.objects.filter() # First get all posts, regardless of privacy
    for post in posts:
        if not post.privfriends: # If it's not privage to only friends, AKA public, display
            # Each post has an author object
            author = Author.objects.get(consistent_id = post.user_id)
            author_dict = {
                "id": f"http://{author.host}/author/{author.consistent_id}",
                "host": f"{author.host}/",
                "displayName": author.username,
                "url": f"{author.host}/firstapp/{author.userid}",
                "github": author.github,
            }

            post_dict = {
                "post_id":post.post_id,
                "user_id":post.user_id,
                "title":post.title,
                "description":post.description,
                "markdown":post.markdown,
                "content":post.content,
                "image":str(post.image,encoding="utf-8"),
                "privfriends":post.privfriends,
                "timestamp":post.tstamp,
                "id":post.id,
                "author":author_dict,
            }
            post_list.append(post_dict)
    return HttpResponse(json.dumps(post_list))
    



@api_view(['GET','POST'])
def commentpost(request, user_id, post_id):
    resp = ""
  #  conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
    conn = connection
    cursor = conn.cursor()
    try:
        request.user.id = int(request.user.id)
    except:
        request.user.id = 0
    cursor.execute('SELECT * FROM firstapp_comment WHERE from_user = %s AND post_id = %d;'% (request.user.id, post_id))
    data = cursor.fetchall()
    if request.method == "POST":
        while True:
            
            comment_id = rand(2**31)
            byte_data = request.data
         #   data = byte_data.decode("utf-8")
           # json_object = json.loads(request.data)
          #  print(json_object)
          #  comment = byte_data.split("&comment=")[1]
            comment = byte_data.get('comment')
          #  comment = request.POST.get('comment_text')
         #   new_comment = Comment.objects.create(comment_text=comment, comment_id=comment_id)
            
            cursor.execute('SELECT comment_text FROM firstapp_comment WHERE comment_id=%d'%(comment_id))
            data1 = cursor.fetchall()
            if len(data1)==0:
                new_comment = Comment(post_id=post_id, comment_id=comment_id, from_user=request.user.id, to_user=user_id, comment_text=comment)
                new_comment.save()
                break
              #  return HttpResponse("Comment created sucessfully!")
        #print(json_object)
        url = request.get_full_path()
        return render(request, "comments.html")
    else:
        return render(request, "comments.html")

@api_view(['GET'])
def viewComments(request, user_id, post_id):
   # conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
    conn = connection
    cursor = conn.cursor()
    agent = request.META["HTTP_USER_AGENT"]
    
    if "Mozilla" in agent or "Chrome" in agent or "Edge" in agent or "Safari" in agent:
     #   cursor.execute('SELECT comment_id FROM firstapp_comment WHERE to_user = ? AND post_id = ?;',(user_id,post_id))
        cursor.execute("SELECT comment_text FROM firstapp_comment WHERE to_user = '%s' AND post_id = '%d';" %(user_id,post_id))
        data = cursor.fetchall()
        comment_list = []
        for d in data:
            comment_text = d[0]
            comment_list.append(comment_text)
        num_comments = len(comment_list)
        return render(request, "comment_list.html", {"comment_list":comment_list, "num_comments":num_comments})

    
def search_user(request, *args, **kwargs):
    context = {}
    noresult = False
    user_id = request.user.id
    
    remote_author_list = get_all_remote_user()
        
    if request.method == "GET":
        search_query = request.GET.get("q")
        if len(search_query) > 0:
            accounts = []
            conn = connection
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM authtoken_token t, firstapp_author a WHERE a.username LIKE %s', ("%" + search_query + "%",))
            duplicate = []

            # Search for the local author 
            try:

                data = cursor.fetchall()
                Author = get_user_model()
                account = Author.objects.filter(username = search_query)
            except IndexError: # No token exists, must create a new one!
                noresult = True 
            user = request.user
                    # account.append((user[0]))

            if not noresult:
                for user in data:
                    if(user[8] not in duplicate):
                        print(user[8])
                        print(user)
                        accounts.append((user,False))
                        duplicate.append(user[8])
                        # print('user3')
                        # print(user[3]

            context['searchResult'] = accounts
            
    conn.close()
    return render(request,"search_user.html",context)

@api_view(['GET','POST'])
@authentication_classes([BasicAuthentication, SessionAuthentication, TokenAuthentication])
@permission_classes([EditPermission])
def account(request,user_id):
    # This method can GET and POST an author by their UUID
    # GET retrieves the account's information. POST updates the account's information if authenticated
    resp = ""
    method = request.META["REQUEST_METHOD"]
    conn = connection
    cursor = conn.cursor()
    try: 
        author = Author.objects.get(consistent_id=user_id) # Try to retrieve the author. If not, give error HTTP response
    except:
        return HttpResponseNotFound("The account you requested does not exist\n")
    if method == "GET": # We want to return a JSON object of the Author requested
        author_dict = {
            "id": f"http://{author.host}/author/{author.consistent_id}",
            "host": f"{author.host}/",
            "displayName": author.username,
            "url": f"{author.host}/firstapp/{author.userid}",
            "github": author.github,
        }
        return HttpResponse(json.dumps(author_dict))
    else: # It's a POST request
        try: # First see if the user exists
            cursor.execute("SELECT t.key FROM authtoken_token t, auth_user u, firstapp_author a WHERE u.id = t.user_id AND u.id = a.userid AND a.consistent_id = '%s';"%user_id)
            user_token = cursor.fetchall()[0][0]
        except IndexError:
            return HttpResponse("User does not exist.")
        token = request.META["HTTP_AUTHORIZATION"].split("Token ")[1] # Retrieve the API token. If it does not match the user's token, cannot update
        if token != user_token: return HttpResponse('{"detail":"Authentication credentials were incorrectly provided."}',status=401) # Incorrect or missing token
        p = request.POST
        try: # You can only edit your github and display name.
            author = Author.objects.get(consistent_id=user_id)
            author.github = p["github"]
            author.username = p["displayName"]
            author.save()
        except MultiValueDictKeyError:
            return HttpResponseBadRequest("Failed to modify post:\nInvalid/not enough parameters\n")
        return HttpResponse("Updated profile")
@api_view(['GET','POST'])
def account_view(request, *args, **kwargs):


    context = {}
    user_id = kwargs.get("user_id")
    conn = connection

    # Receive request method from profile page. One possibility is having to change git username and user
    method = request.META["REQUEST_METHOD"]
    if method == "POST":
        data = request.POST

        from firstapp.models import Author
        author = Author.objects.get(userid = user_id)
        author.github = data["git_url"]
        author.github_username = data["git_username"]
        author.save()


    cursor = conn.cursor()
    # print("*****************")
    # print(user_id)
    cursor.execute("SELECT * FROM authtoken_token t, auth_user u WHERE u.id = '%s';" % user_id)
    try:
        data = cursor.fetchall()[0]
        Author = get_user_model()
        account = Author.objects.get(id = user_id)
    except IndexError: # No token exists, must create a new one!
        return HttpResponse("user doesn't exist") 
    # print("here is data")
    # print(data)
    
    # print(len(data))
    if data:

        context['id'] = data[3]
        context['username'] = data[7]
        context['email'] = data[9]

        try:
            friend_list = FriendList.objects.get(user=account)
        except FriendList.DoesNotExist:
            friend_list = FriendList(user=account)
            friend_list.save()


        friends = friend_list.friends.all()
        context['friends'] = friends
        is_self = True 
        is_friend = False

        request_sent = RequestStatus.NO_REQUEST_SENT.value # range: ENUM -> friend/friend_request_status.FriendRequestStatus
        friend_requests = None
        user = request.user
         # define the variable
        if user.is_authenticated and user != account:
            is_self = False
            if friends.filter(pk=user.id):
                is_friend = True
            else:
                is_friend = False
                # CASE1: Request has been sent from THEM to YOU: FriendRequestStatus.THEM_SENT_TO_YOU
                if get_friend_request_or_false(sender=account, receiver=user) != False:
                    request_sent = RequestStatus.THEM_SENT_TO_YOU.value
                    context['pending_friend_request_id'] = get_friend_request_or_false(sender=account, receiver=user).id
                # CASE2: Request has been sent from YOU to THEM: FriendRequestStatus.YOU_SENT_TO_THEM
                elif get_friend_request_or_false(sender=user, receiver=account) != False:
                    request_sent = RequestStatus.YOU_SENT_TO_THEM.value
                # CASE3: No request sent from YOU or THEM: FriendRequestStatus.NO_REQUEST_SENT
                else:
                    request_sent = RequestStatus.NO_REQUEST_SENT.value
        
        elif not user.is_authenticated:
            is_self = False
        else:
            try:
                print("friend request")
                friend_requests = FriendRequest.objects.filter(receiver=user, is_active=True)
            except:
                pass

        user = request.user
        if not (request.user.is_authenticated and str(request.user.id) == str(user_id)):
            is_self = False

        context['is_self'] =is_self
        context['is_friend'] = is_friend
        context['request_sent'] = request_sent
        context['friend_requests'] = friend_requests
        context['BASE_URL'] = settings.BASE_DIR
        context['Author'] = getAuthor(user_id)
        return render(request,"profile.html",context)

def getAuthor(userid):
    # This function gets the Author object associated with the userid. Returns None
    my_user = Author.objects.get(userid=userid) # Will change it to include the uuid rather than userid
    return my_user
        

        

    
    
    
    
