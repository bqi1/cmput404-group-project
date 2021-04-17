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
from rest_framework.permissions import IsAuthenticated
from .permissions import EditPermission
from rest_framework.authentication import BasicAuthentication, SessionAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from friend.request_status import RequestStatus
from friend.follow_status import FollowStatus
from friend.models import FriendList, FriendRequest,FriendShip,FollowingList,Follow
from friend.is_friend import get_friend_request_or_false
from friend.is_following import Following_Or_Not
from firstapp.models import Author, Post, Author_Privacy, Comment, Like, Category, Node, Setting, Inbox
from django.contrib.auth import get_user_model
from django.contrib.auth.models import AnonymousUser
import uuid
import requests
import base64
from urllib.parse import urlparse
from html import escape
from .remote_friend import get_all_remote_user,get_all_remote_user_2
from django.contrib.auth.models import User
from django.core import serializers
from django.core.paginator import Paginator
from django.contrib.admin.views.decorators import staff_member_required
import subprocess
FILEPATH = os.path.dirname(os.path.abspath(__file__)) + "/"

ADD_QUERY = "INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
EDIT_QUERY = "UPDATE posts SET post_id=?, user_id=?, title=?, description=?, markdown=?, content=?, image=?, published=? WHERE post_id=? AND user_id =?;"

PRIV_ADD_QUERY = "INSERT INTO author_privacy VALUES (?,?);"
STR2BOOL = lambda x: bool(int(x))

# Create your views here.
def index(request):
    #if request.user.is_authenticated:
    return render(request, 'index.html')

#helper function for getting json author objects from our server's database
def get_our_author_object(host, author_uuid):
    print("entered get_our_author_object")
    try:
        url = "https://"+host+"/author/"+author_uuid
        print(url)
        r = requests.get(url)
        print("getting author succesfull")
        return r.json()
    except Exception as e:
        print(e)
        return HttpResponseNotFound("The account you requested does not exist\n")

def homepage(request):
    if request.user.is_authenticated:
        try:
            author = Author.objects.get(username=request.user)
            token = author.api_token
        except Author.DoesNotExist:
            return HttpResponseNotFound(f"In the homepage function, the user you requested does not exist!!{request.user}\n")
        if not author.authorized:
            messages.add_message(request,messages.INFO, 'Please wait to be authenticated by a server admin.')
            return HttpResponseRedirect(reverse('login'))
        user_id,author_uuid = author.userid,author.consistent_id
        ourURL = f"https://"+request.META['HTTP_HOST']+"/posts" # change this to https in heroku, http in local server
        print(f"\n\n\n\n{ourURL}\n\n\n")
        ourRequest = requests.get(url=ourURL)
        print(f"\n\n{ourRequest}\n\n")
        ourData = ourRequest.json()
        # print(ourRequest)
        print("\n")



        # Get all public posts from another server, from the admin panel
        servers = Node.objects.all()
        theirData = []
        auth_user = ""
        auth_pass = ""
        for server in servers: # Iterate through each server, providing authentication if necessary
            try:
                postsRequest = requests.get(url=f"{server.hostserver}/posts", auth = (f"{server.authusername}",f"{server.authpassword}"))
                auth_user = server.authusername
                auth_pass = server.authpassword
                if postsRequest.status_code == 200:
                    theirData.extend(postsRequest.json())
                    #TODO find a way to pass in auth info with post json
            except Exception as e:
                print(f"Could not connect to {server.hostserver} becuase: {e} :(")
                continue
        # print(ourData)
        # print(theirData)
        return render(request, 'homepage.html', {'user_id':user_id,'author_uuid':author_uuid, 'our_server_posts':ourData,'other_server_posts':theirData,"author":author})
    
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
            #Token(user=user).save()
            #user.save()
            success = True
            # Check if UsersNeedAuthentication is True. If it is, redirect to login and set Authorized to False for that user
            # Else, let the use in the homepage, set Authorized to True
            try:
                settings = Setting.objects.get()
            except Setting.DoesNotExist:
                print("make a setting")
                settings = Setting(usersneedauthentication=False)
            needs_authentication = settings.usersneedauthentication
            # print(f"AUTHENTICATE ME https://{request.get_host()}")
            if needs_authentication: # If users need an OK from server admin, create the user, but set authorized to False, preventing them from logging in.
                user = Author.objects.create(host=f"https://{request.get_host()}",username=new_username,userid=request.user.id,\
                    authorized=False,email=form.cleaned_data['email'],\
                        name=f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}",\
                            consistent_id=f"{uuid.uuid4().hex}",api_token = Token.objects.create(user=user))
                # If the flag, UsersNeedAuthentication is True, redirect to Login Page with message
                user.save()
                user_inbox = Inbox.objects.create(type="inbox", author=f"https://{request.get_host()}/author/{user.consistent_id}", items=[])
                user_inbox.save()
                messages.add_message(request,messages.INFO, 'Please wait to be authenticated by a server admin.')
                return HttpResponseRedirect(reverse('login'))
            # Else, let them in homepage.
            user = Author.objects.create(host=f"https://{request.get_host()}",username=new_username,\
                userid=request.user.id, authorized=True,email=form.cleaned_data['email'],\
                    name=f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}",\
                        consistent_id=f"{uuid.uuid4().hex}",api_token = Token.objects.create(user=user))
            user_inbox = Inbox.objects.create(type="inbox", author=f"https://{request.get_host()}/author/{user.consistent_id}", items=[])
            
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

        # print(Author.objects.get(username=request.user))
        user = authenticate(username = new_username, password = new_password)
        if user is not None:
            # Check if Authorized. If so, proceed. Else, display an error message and redirect back to login page.

            try:
                author = Author.objects.get(username=new_username)
            except Author.DoesNotExist:
                messages.add_message(request,messages.INFO, f'This user, {new_username}, does not exist.')
                return HttpResponseRedirect(reverse('login'))
            authenticated = author.authorized
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

# escapes instances of <script> and </script> tags from content
def clean_script(content):
    tags = ["<script>","</script>"]
    for t in tags:
        L = len(t)
        n = content.find(t)
        while n >= 0:
            content = content[:n] + escape(content[n:n+L]) + content[n+L:]
            n = content.find(t)
    return content

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
    jscript = '<script>' + script + '</script>' + '<script src="https://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js"></script>'
    start = '<div class="post" style="border:solid;" ><p class="title">%s</p><p class="desc">%s</p></br><p class="content">%s</p></br><p class="tags">%s</p></br>'
    endimage = '<img src="%s"/><span class="md" style="display:none" value="%s"></span></br>'+('<input type = "button" value="Edit" onclick="viewPost(\'{0}\')">' if isowner else '')
    endnoimage = '<span class="md" style="display:none" value="%s"></span></br>'+('<input type = "button" value="Edit" onclick="viewPost(\'{0}\')">' if isowner else '')

    for d in data:
        priv = Author_Privacy.objects.filter(post_id=d.post_id)
        tags = [c.tag for c in Category.objects.filter(post_id=d.post_id)]
        image = str(d.image,encoding="utf-8")
        content = d.content
        if d.markdown: # use markdown!
            md = Md()
            content = md.convert(content)
        starttag = jscript
        starttag += start % (clean_script(d.title),clean_script(d.description),clean_script(content),clean_script(",".join(tags)))
        if len(priv) == 0 and d.privfriends == False: # post is not private
            if image == '0':
                resp += starttag
                resp += endnoimage.format(d.post_id) % (d.markdown,)
                resp += '<button onclick="viewLikes(\'{}\')">View Likes</button>'.format(d.post_id)
                resp += '<button onclick="viewComment(\'{}\')">View Comment</button>'.format(d.post_id)
            else: 
                resp += starttag + endimage.format(d.post_id) % (image,d.markdown)
                resp += '<button onclick="viewLikes(\'{}\')">View Likes</button>'.format(d.post_id)
                resp += '<button onclick="viewComment(\'{}\')">View Comment</button>'.format(d.post_id)

            resp += "</br>"
        else: # post is private
            show_post = False
            for p in priv:
                if p.user_id == user_id or isowner:
                    show_post = True
                    break

            # If post is set to be private to friends, check to see if the user trying to see the post is the user's friend
            if d.privfriends == True:
                cons_id = Author.objects.get(consistent_id=d.user_id).userid
                try: friend_ids = [Author.objects.get(userid=f.id).consistent_id for f in FriendList.objects.get(user_id=cons_id).friends.all()]
                except FriendList.DoesNotExist: friend_ids = []
                if user_id in friend_ids or isowner: show_post = True
            if show_post and user_id != None: # show post only if this variable is true, and a user is logged in!
                if image == '0':
                    resp += starttag
                    resp += endnoimage.format(d.post_id) % (d.markdown,)
                    resp += '<button onclick="likePost(\'{}\')">Like</button>'.format(d.post_id)
                    resp += '<button onclick="viewLikes(\'{}\')">View Likes</button>'.format(d.post_id)
                else:
                    resp += starttag + endimage.format(d.post_id) % (image,d.markdown)
                    resp += '<button onclick="likePost(\'{}\')">Like</button>'.format(d.post_id)
                    resp += '<button onclick="viewLikes(\'{}\')">View Likes</button>'.format(d.post_id)
                resp += "</br>"
    return resp

# This function will return all visible posts, and return them in a list to be displayed to non-browser user agents
# data - the list of tuples returned from sql
# user_id - used to check to see if the current user can view the post (is it private to specific authors, or public?)
def make_post_list(data,user_id,isowner=False,uri=""):
    post_list = []
    for d in data:

        # This block assigns the author object to each post object.
        author = Author.objects.get(consistent_id=d.user_id)
        author_dict = {
            "id": f"{author.host}/author/{author.consistent_id}",
            "host": f"{author.host}/",
            "displayName": author.username,
            "url": f"{author.host}/firstapp/{author.userid}",
            "github": author.github,
            "type": "author",
        }


        priv = Author_Privacy.objects.filter(post_id=d.post_id)
        post_dict = {
            "type":"post",
            "title":d.title,
            "id":d.id,
            "source":d.source,
            "origin":d.origin,
            "description":d.description,
            "contentType":"text/markdown" if d.markdown else "text/plain",
            "content":d.content,
            "categories":[],
            "count":0,
            "size":0,
            "comments":f"{author.host}/author/{author.consistent_id}/posts/{d.post_id}/viewComments/",
            "comments":[],
            "visibility":[],
            "unlisted":False if not d.privfriends else True,
            "post_id":d.post_id,
            "user_id":d.user_id,
            "image":str(d.image,encoding="utf-8"),
            "markdown":d.markdown,
            "privfriends":d.privfriends,
            "visibility":[],
            "unlisted":d.unlisted,
            "published":d.published,
            "author":author_dict,
        }

        # retrieve all categories for post
        categories = Category.objects.filter(post_id=d.post_id)
        for ca in categories:post_dict["categories"].append(ca.tag)

        # post is public or post belongs to user
        if len(priv) == 0 and d.privfriends == False:
            post_dict["visibility"].append("PUBLIC")
            post_list.append(post_dict)
        else:
            show_post = False
            # Determine if requesting author is among privacy list
            if len(priv) > 0: post_dict["visibility"].append("SELECT AUTHOR(S)")
            for p in priv:
                if p.user_id == user_id or isowner:
                    show_post = True
                    break
            # If post is set to be private to friends, check to see if the user trying to see the post is the user's friend
            if d.privfriends == True:
                post_dict["visibility"].append("FRIENDS")
                cons_id = Author.objects.get(consistent_id=d.user_id).userid
                try: friend_ids = [Author.objects.get(userid=f.id).consistent_id for f in FriendList.objects.get(user_id=cons_id).friends.all()]
                except FriendList.DoesNotExist: friend_ids = []
                if user_id in friend_ids or isowner: show_post = True

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
    viewer_id = "0"
    if type(request.user) != AnonymousUser:
        viewer_id = Author.objects.get(username=request.user).consistent_id # consistent id of the user that is viewing the posts
    data = Author.objects.filter(consistent_id=user_id)
    if len(data)==0: return HttpResponseNotFound("The user you requested does not exist\n")
    user_token = data[0].api_token
    author_id = data[0].userid
    try: friend_ids = [Author.objects.get(userid=f.id).consistent_id for f in FriendList.objects.get(user_id=author_id).friends.all()]
    except FriendList.DoesNotExist: friend_ids = []
    try: follow_ids = [Author.objects.get(userid=f.follower.id).consistent_id for f in Follow.objects.filter(receiver=author_id)]
    except Follow.DoesNotExist: follow_ids = []
    data = Post.objects.filter(post_id=post_id,user_id=user_id)
    if len(data)==0 and method != 'PUT': return HttpResponseNotFound("The post you requested does not exist\n") # Check to see if post in url exists (not for PUT)
    data = Post.objects.filter(post_id=post_id)
    if len(data) > 0 and method == 'PUT': return HttpResponse("The post with id %d already exists! Maybe try POST?\n"%post_id,status=409) # check to see if post already exists (for PUT)
    trueauth = (request.user.is_authenticated and author_id == request.user.id) # Check if the user is authenticated AND their id is the same as the author they are viewing posts of. If all true, then they can edit
    if method == 'GET':
        resp = make_post_list(data,viewer_id,isowner=trueauth,uri=request.build_absolute_uri())
        if data[0].unlisted and not trueauth: return HttpResponseNotFound("The post you requested does not exist\n") # Unlisted posts will not be returned from this method!
    else:
        try: # Client is using token authentication
            token = request.META["HTTP_AUTHORIZATION"].split("Token ")[1]
            if token != user_token: return HttpResponse('{"detail":"Authentication credentials were not provided."}',status=401) # Incorrect or missing token
        except IndexError: # Client is using basic authentication
            enc = base64.b64decode(request.META["HTTP_AUTHORIZATION"].split(" ")[1]).decode("utf-8").split(":")
            uname, pword = enc[0], enc[1]
            user = User.objects.get(id=author_id)
            if user.username != uname or not user.check_password(pword):
                return HttpResponse('{"detail":"Invalid username/password."}',status=401) # A correct uname and pword supplied, but not for this specific user
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
                new_post.markdown = STR2BOOL(p["markdown"])
                new_post.content = p["content"]
                new_post.image = sqlite3.Binary(bytes(image,encoding="utf-8"))
                new_post.privfriends = STR2BOOL(p["privfriends"])
                new_post.unlisted = STR2BOOL(p["unlisted"])
                new_post.published = str(datetime.now())
                resp = "Successfully modified post: %d\n" % post_id

            except MultiValueDictKeyError:
                return HttpResponseBadRequest("Failed to modify post:\nInvalid parameters\n")

            # Modify the author privacy table in the database
            if "priv_author" in p.keys() or "priv_author[]" in p.keys():
                if "priv_author" in p.keys(): private_authors = p.getlist("priv_author")
                else: private_authors = p.getlist("priv_author[]")
                for pa in private_authors:
                    data = Author.objects.filter(username=pa)
                    if len(data) == 0: return HttpResponseNotFound("One or more user ids entered into the author privacy field are not valid user ids.") # check if author ids are valid
                for pa in private_authors:
                    consistent_id = Author.objects.get(username=pa).consistent_id
                    new_private_author = Author_Privacy(post_id=post_id,user_id=consistent_id)
                    new_private_author.save()
            else:
                author_privacies = Author_Privacy.objects.filter(post_id=post_id)
                for ap in author_privacies: ap.delete()
            # Modify the categories table in the database
            if "categories" in p.keys() or "categories[]" in p.keys():
                if "categories" in p.keys(): private_authors = p.getlist("categories")
                else: categories = p.getlist("categories[]")
                for ca in categories:
                    category = Category(post_id=post_id,tag=ca)
                    category.save()
            else:
                categories = Category.objects.filter(post_id=post_id)
                for ca in categories: ca.delete()
            new_post.save()
            author = Author.objects.get(consistent_id=user_id)
            author_dict = {
                "id": f"{author.host}/author/{author.consistent_id}",
                "host": f"{author.host}/",
                "displayName": author.username,
                "url": f"{author.host}/firstapp/{author.userid}",
                "github": author.github,
                "type": "author",
            }
            payload = {"type":"post","author":author_dict,"id" : f"https://{request.get_host()}/author/{user_id}/posts/{post_id}","post_id":post_id,"user_id":user_id,"title":p["title"],"description":p["description"],"markdown":STR2BOOL(p["markdown"]),"content":p["content"],"image":str(image),"privfriends":STR2BOOL(p["privfriends"]),"unlisted":STR2BOOL(p["unlisted"]),"published":str(datetime.now())}
            for f in friend_ids:
                r = requests.post(f"https://{request.get_host()}/author/{f}/inbox",headers={"Authorization":"Token %s"%user_token,"Content-Type":"application/json"},json=payload)
            for f in follow_ids:
                r = requests.post(f"https://{request.get_host()}/author/{f}/inbox",headers={"Authorization":"Token %s"%user_token,"Content-Type":"application/json"},json=payload)
 
        elif method == 'PUT':

            p = request.POST
            if request.META["CONTENT_TYPE"] == "application/json": # Allows clients to send JSON requests
                p = QueryDict('',mutable=True)
                p.update(request.data)
            try: image = p["image"] # image is an optional param!
            except MultiValueDictKeyError: image = '0'
            try: # if all mandatory fields are passed
                if not validate_int(p,[post_id]): return HttpResponseBadRequest("Error: you have submitted non integer values to integer fields.") # non integer markdown field (0-1)
                new_post = Post(source=f"https://{request.get_host()}/posts",origin=f"https://{request.get_host()}/posts",id = f"https://{request.get_host()}/author/{user_id}/posts/{post_id}",post_id=post_id,user_id=user_id,title=p["title"],description=p["description"],markdown=STR2BOOL(p["markdown"]),content=p["content"],image=sqlite3.Binary(bytes(image,encoding="utf-8")),privfriends=STR2BOOL(p["privfriends"]),unlisted=STR2BOOL(p["unlisted"]),published=str(datetime.now()))
                resp = "Successfully created post: %d\n" % post_id
            except MultiValueDictKeyError:
                return HttpResponseBadRequest("Failed to modify post:\nInvalid parameters\n")

            # Modify the author privacy table in the database
            if "priv_author" in p.keys() or "priv_author[]" in p.keys():
                if "priv_author" in p.keys(): private_authors = p.getlist("priv_author")
                else: private_authors = p.getlist("priv_author[]")
                for pa in private_authors:
                    data = Author.objects.filter(username=pa)
                    if len(data) == 0: return HttpResponseNotFound("One or more user ids entered into the author privacy field are not valid user ids.")
                for pa in private_authors:
                    consistent_id = Author.objects.get(username=pa).consistent_id
                    new_private_author = Author_Privacy(post_id=post_id,user_id=consistent_id)
                    new_private_author.save()
            # Modify the categories table in the database
            if "categories" in p.keys() or "categories[]" in p.keys():
                if "categories" in p.keys(): private_authors = p.getlist("categories")
                else: categories = p.getlist("categories[]")
                for ca in categories:
                    category = Category(post_id=post_id,tag=ca)
                    category.save()
            new_post.save()
            author = Author.objects.get(consistent_id=user_id)
            author_dict = {
                "id": f"{author.host}/author/{author.consistent_id}",
                "host": f"{author.host}/",
                "displayName": author.username,
                "url": f"{author.host}/firstapp/{author.userid}",
                "github": author.github,
                "type": "author",
            }
            payload = {"type":"post","author":author_dict,"id" : f"https://{request.get_host()}/author/{user_id}/posts/{post_id}","post_id":post_id,"user_id":user_id,"title":p["title"],"description":p["description"],"markdown":STR2BOOL(p["markdown"]),"content":p["content"],"image":str(image),"privfriends":STR2BOOL(p["privfriends"]),"unlisted":STR2BOOL(p["unlisted"]),"published":str(datetime.now())}
            for f in friend_ids:
                r = requests.post(f"https://{request.get_host()}/author/{f}/inbox",headers={"Authorization":"Token %s"%user_token,"Content-Type":"application/json"},json=payload)
            for f in follow_ids:
                r = requests.post(f"https://{request.get_host()}/author/{f}/inbox",headers={"Authorization":"Token %s"%user_token,"Content-Type":"application/json"},json=payload)

        elif method == 'DELETE':
            author_privacies = Author_Privacy.objects.filter(post_id=post_id)
            for ap in author_privacies: ap.delete()
            categories = Category.objects.filter(post_id=post_id)
            for ca in categories: ca.delete()
            new_post = Post.objects.get(post_id=post_id,user_id=user_id)
            new_post.delete()
            resp = "Successfully deleted post: %d\n" %post_id

        else:
            return HttpResponseBadRequest("Error: invalid method used\n")
    agent = request.META["HTTP_USER_AGENT"]
    if "Mozilla" in agent or "Chrome" in agent or "Edge" in agent or "Safari" in agent: # is the agent a browser? If yes, show html, if no, show regular post list
        if method == "GET": resp = make_post_html(data,viewer_id,isowner=trueauth)
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

    data = Author.objects.filter(consistent_id=user_id)
    viewer_id = "0"
    if type(request.user) != AnonymousUser:
        viewer_id = Author.objects.get(username=request.user).consistent_id # consistent id of the user that is viewing the posts
    if len(data)==0: return HttpResponseNotFound("The user you requested does not exist\n")
    user_token = data[0].api_token
    author_id = data[0].userid
    try: friend_ids = [Author.objects.get(userid=f.id).consistent_id for f in FriendList.objects.get(user_id=author_id).friends.all()]
    except FriendList.DoesNotExist: friend_ids = []
    try: follow_ids = [Author.objects.get(userid=f.follower.id).consistent_id for f in Follow.objects.filter(receiver=author_id)]
    except Follow.DoesNotExist: follow_ids = []
    
    print(follow_ids)
    trueauth = (request.user.is_authenticated and author_id == request.user.id) # Check if the user is authenticated AND their id is the same as the author they are viewing posts of. If all true, then they can edit
    if method == "POST":
        try: # Client is using token authentication
            token = request.META["HTTP_AUTHORIZATION"].split("Token ")[1]
            if token != user_token: return HttpResponse('{"detail":"Authentication credentials were not provided."}',status=401) # Incorrect or missing token
        except IndexError: # Client is using basic authentiation
            enc = base64.b64decode(request.META["HTTP_AUTHORIZATION"].split(" ")[1]).decode("utf-8").split(":")
            uname, pword = enc[0], enc[1]
            user = User.objects.get(id=author_id)
            if user.username != uname or not user.check_password(pword):
                return HttpResponse('{"detail":"Invalid username/password."}',status=401) # A correct uname and pword supplied, but not for this specific user
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
            new_post = Post(source=f"https://{request.get_host()}/posts",origin=f"https://{request.get_host()}/posts",id = f"https://{request.get_host()}/author/{user_id}/posts/{post_id}",post_id=post_id,user_id=user_id,title=p["title"],description=p["description"],markdown=STR2BOOL(p["markdown"]),content=p["content"],image=bytes(image,encoding="utf-8"),privfriends=STR2BOOL(p["privfriends"]),unlisted=STR2BOOL(p["unlisted"]),published=str(datetime.now()))
            resp = "Successfully created post: %d\n" % post_id
        except MultiValueDictKeyError:
            return HttpResponseBadRequest("Failed to create post:\nInvalid parameters\n")
        print("DEBUG: "+ str(p))
        # Modify the author privacy table in the database
        if "priv_author" in p.keys() or "priv_author[]" in p.keys():
            if"priv_author" in p.keys(): private_authors = p.getlist("priv_author")
            else: private_authors = p.getlist("priv_author[]")
            for pa in private_authors:
                data = Author.objects.filter(username=pa)
                if len(data) == 0: return HttpResponseNotFound("One or more user ids entered into the author privacy field are not valid user ids.")
            for pa in private_authors:
                consistent_id = Author.objects.get(username=pa).consistent_id
                new_private_author = Author_Privacy(post_id=post_id,user_id=consistent_id)
                new_private_author.save()

        # Modify the categories table in the database
        if "categories" in p.keys() or "categories[]" in p.keys():
            if "categories" in p.keys(): private_authors = p.getlist("categories")
            else: categories = p.getlist("categories[]")
            for ca in categories:
                category = Category(post_id=post_id,tag=ca)
                category.save()
        new_post.save()
        # Send the newly created posts to friend's inboxes
        author = Author.objects.get(consistent_id=user_id)
        author_dict = {
            "id": f"{author.host}/author/{author.consistent_id}",
            "host": f"{author.host}/",
            "displayName": author.username,
            "url": f"{author.host}/firstapp/{author.userid}",
            "github": author.github,
            "type": "author",
        }
        payload = {"type":"post","author":author_dict,"id" : f"https://{request.get_host()}/author/{user_id}/posts/{post_id}","post_id":post_id,"user_id":user_id,"title":p["title"],"description":p["description"],"markdown":STR2BOOL(p["markdown"]),"content":p["content"],"image":str(image),"privfriends":STR2BOOL(p["privfriends"]),"unlisted":STR2BOOL(p["unlisted"]),"published":str(datetime.now())}
        for f in friend_ids:
            r = requests.post(f"https://{request.get_host()}/author/{f}/inbox",headers={"Authorization":"Token %s"%user_token,"Content-Type":"application/json"},json=payload)
        for f in follow_ids:
            r = requests.post(f"https://{request.get_host()}/author/{f}/inbox",headers={"Authorization":"Token %s"%user_token,"Content-Type":"application/json"},json=payload)

    elif method == "GET":
        data = Post.objects.filter(user_id=user_id)
        resp = make_post_list(data,viewer_id,isowner=trueauth,uri=request.build_absolute_uri())
    else:
        return HttpResponseBadRequest("Error: invalid method used\n")
    agent = request.META["HTTP_USER_AGENT"]
    if "Mozilla" in agent or "Chrome" in agent or "Edge" in agent or "Safari" in agent: # is the agent a browser? If yes, show html, if no, show regular post list
        with open(FILEPATH+"static/allposts.js","r") as f: script = f.read() % (user_token)
        if method == "GET": resp = make_post_html(data,viewer_id,isowner=trueauth)
        # true_auth: is user logged in, and are they viewing their own posts? (determines if they can create a new post or not)
        return render(request,'allposts.html',{'post_list':resp,'true_auth':trueauth,'postscript':script})
    else: return HttpResponse(resp)

#like a post
@api_view(['POST','GET'])
def likepost(request, user_id, post_id):
    print(f"\n\n\nentered likepost {user_id} {post_id}\n\n\n")
    resp = ""
    conn = connection
    cursor = conn.cursor()
    host = request.build_absolute_uri('/')
    object = f"{host}/author/{user_id}/posts/{post_id}"
    print(f"here we go....{request} {request.user} {request.user.id}")
    cursor.execute("SELECT consistent_id FROM firstapp_author WHERE userid = %d;"% (request.user.id))
    uuid = cursor.fetchone()[0]
    print(uuid)
    cursor.execute("SELECT * FROM firstapp_like WHERE from_user = '%s' AND object = '%s'"% (uuid, object))
    data = cursor.fetchall()
    print(data)
    # if post has already been liked delete from inbox and database
    if len(data) > 0:
        Like.objects.filter(from_user = f"https://{request.get_host()}/author/{uuid}",to_user = f"https://{request.get_host()}/author/{user_id}", object = object).delete()
        print("like deleted from db, deleting from inbox now...")
        host = request.build_absolute_uri('/')
        author_id = host + "author/" + user_id
        inbox = Inbox.objects.get(author=author_id)
        for i in range(len(inbox.items)):
            item = inbox.items[i]
            print(item["author"]["id"])
            print(f"https://{request.get_host()}/author/{author_id}")
            print(item["object"])
            print(object)
            if item["author"]["id"] == author_id and item["object"] == object:
                inbox.items.pop(i)
                print("item deleted from inbox")
                break
        inbox.save()
        return HttpResponse("Unliked post")
    else:
        print("not liked. liking....")
        while True:
            like_id = rand(2**31-1)
            cursor.execute('SELECT * FROM firstapp_like WHERE like_id = %d'% (like_id))
            if len(cursor.fetchall()) == 0:
                print(f"like doesnt exist:{post_id}")
                host = request.build_absolute_uri('/')
                url = f"{host}author/{user_id}/inbox"
                object = f"{host}/author/{user_id}/posts/{post_id}"
                like_object = make_like_object(request, object, user_id, make_json=True)
                print("got past make_like_object")
                print(url)
                print(object)
                print(like_object)
                headers = headers = {'Content-type': 'application/json'}
                print(f"sending to.{url}")
                requests.post(url, data = like_object, headers=headers)
                print("like has been posted")
                break
        return HttpResponse("Like object sent to inbox", status=200)

#like a comment
@api_view(['POST'])
def like_comment(request, user_id, post_id, comment_id):
    resp = ""
    conn = connection
    cursor = conn.cursor()
    host = request.build_absolute_uri('/')
    object = f"https://{host}/author/{user_id}/posts/{post_id}"
    cursor.execute("SELECT consistent_id FROM firstapp_author WHERE userid = %d;"% (request.user.id))
    uuid = cursor.fetchall()[0]
    cursor.execute("SELECT * FROM firstapp_like WHERE from_user = '%s' AND object = '%s'"% (uuid, object))
    data = cursor.fetchall()
    # if post has already been liked
    if len(data) > 0:
        return HttpResponse("Comment already liked", status=409)
    else:
        while True:
            like_id = rand(2**31-1)
            cursor.execute('SELECT * FROM firstapp_like WHERE like_id = %d'% (like_id))
            if len(cursor.fetchall()) == 0:
                print(post_id)
                host = request.build_absolute_uri('/')
                url = f"{host}/author/{user_id}/inbox"
                object = f"{host}/author/{user_id}/posts/{post_id}/comments/{comment_id}"
                like_object = make_like_object(request, object, user_id, make_json=True)
                print(f"sending to..{url}")
                requests.post(url, data = like_object)
                like = Like(like_id=like_id, from_user = f"https://{request.get_host()}/author/{uuid}", to_user = f"https://{request.get_host()}/author/{user_id}", object = object)
                like.save()
                break
        HttpResponse("Like object sent to inbox", status=200)

def make_like_object(request, object, user_id, make_json = True):
    like_dict = {}
    like_dict["type"] = "like"
    like_dict["author"] = get_our_author_object(request.get_host(), user_id)
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
    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    host = request.build_absolute_uri('/')
    object = f"{host}author/{user_id}/posts/{post_id}"

    if is_ajax:
        print("is ajax.")
        print(object)
        postlikes = Like.objects.filter(object=object)
        like_dict_list = []
        for like in postlikes:
            try:
                print(f"consistent id is {like.from_user.split('/')[-1] if like.from_user[-1] != '/' else like.from_user.split('/')[-2]}")
                author = Author.objects.get(consistent_id=like.from_user.split('/')[-1] if like.from_user[-1] != "/" else like.from_user.split('/')[-2])
                author_dict = {
                    "id": f"{author.host}/author/{author.consistent_id}",
                    "host": f"{author.host}/",
                    "displayName": author.username,
                    "url": f"{author.host}/firstapp/{author.userid}",
                    "github": author.github,
                    "type": "author",
                }
            except:
                # It's another author
                print(f"\nfrom another author. {like.from_user}")
                print(requests.get(f"{like.from_user}"))
                author_dict = json.loads(requests.get(f"{like.from_user}"))
            like_dict = {
                "@context":"",
                "summary":f"{author_dict['displayName']} Likes your post",
                "type":"Like",
                "author":author_dict,
                "object":like.object,
            }
            like_dict_list.append(like_dict)
        return HttpResponse(json.dumps(like_dict_list), content_type="application/json")
    else:
        if "Mozilla" in agent or "Chrome" in agent or "Edge" in agent or "Safari" in agent: #if using browser
            # cursor.execute("SELECT a.username FROM firstapp_like l, firstapp_author a WHERE l.object='%s' AND l.from_user = a.consistent_id;"%object)
            # data = cursor.fetchall()
            # author_list = []
            # for d in data:
            #     author = d[0]
            #     author_list.append(author)
            # num_likes = len(author_list)
            likes = Like.objects.filter(object=object)
            return render(request, "likes.html", {"num_likes":len(likes)})
        else: 
            #return a list of like objects
            cursor.execute("SELECT a.consistent_id FROM firstapp_like l, firstapp_author a WHERE l.object='%s' AND l.from_user = a.consistent_id;"%object)
            data = cursor.fetchall()
            url = request.get_full_path()
            json_post_likes = make_post_likes_object(request, data, url)
            return HttpResponse(json.dumps(json_post_likes))

def make_post_likes_object(request, data, url):
    #Get list of likes from other authors on author_ids's post post_id
    post_likes_dict = {}
    json_like_object_list = []

    # post_likes_dict["type"] = "post likes"
    for like in data:
        like_object = make_like_object(request, url, like[0], make_json=False)
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
        cursor.execute("SELECT * FROM firstapp_like WHERE from_user = '%s';"%(user_id))
        data = cursor.fetchall()
        liked_posts_list = []
        for id in data:
            post_id = id[0]
            liked_posts_list.append(post_id)
        return render(request, "liked.html", {"liked_posts_list":liked_posts_list})

    else:
        cursor.execute("SELECT from_user, object FROM firstapp_like WHERE from_user='%s';"%(user_id))
        data = cursor.fetchall()
        liked_object_list = make_liked_object(request, request.META['HTTP_HOST'], data)

        return HttpResponse(json.dumps(liked_object_list))

def make_liked_object(request, host,data):
    liked_dict = {}
    json_like_object_list = []
    liked_dict["type"] = "liked"
    
    for like in data:
        object = like[1]
        like_object = make_like_object(request, object, like[0], make_json=False)
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
                "id": f"{author.host}/author/{author.consistent_id}",
                "host": f"{author.host}/",
                "displayName": author.username,
                "url": f"{author.host}/firstapp/{author.userid}",
                "github": author.github,
                "type": "author",
            }
            comments = Comment.objects.filter(post_id=post.id)
            print(post.id)
            print("i dont see an issue??")
            # print( Comment.objects.filter(post_id="https://127.0.0.1:8000/author/9d97fc35703a4831803aaa8bacc8a1e2/posts/201255001"))  
             
            comment_dict_list = []
            i = 0
            for comment_obj in comments:
                if i >= 5: break
                author_url = str(comment_obj.from_user)
                if request.get_host() in comment_obj.from_user:
                    print(f"https://{request.get_host()}/author/")
                    print(comment_obj.from_user[len(f"https://{request.get_host()}/author/"):])
                    author = Author.objects.get(consistent_id=comment_obj.from_user[len(f"https://{request.get_host()}/author/"):])
                    from_author_dict = {
                        "type":"author",
                        "id": f"{author.host}/author/{author.consistent_id}",
                        "host": f"{author.host}/",
                        "url": f"{author.host}/author/{author.consistent_id}",
                        "displayName": author.username,
                        "github": author.github,
                    }
                else:
                    from_author_request = requests.get(url=comment_obj.from_user)
                    from_author_dict = from_author_request.json()


                comment_dict = {
                    "type":"comment",
                    "author":from_author_dict,
                    "comment":clean_script(comment_obj.comment_text),
                    "contentType":"text/plaintext",
                    "published":comment_obj.published,
                    "id":comment_obj.comment_id,
                }
                comment_dict_list.append(comment_dict)
                i+=1
            amount_of_comments = len(comments)
            print("whats going on")
            print(comments)
            print(amount_of_comments)
            post_dict = {

                "type":"post",
                "title":clean_script(post.title),
                "id":post.id,
                "source":post.source,
                "origin":post.origin,
                "description":clean_script(post.description),
                "contentType":"text/markdown" if post.markdown else "text/plain",
                "content":clean_script(post.content),
                "author":author_dict,
                "categories":[],
                "count":amount_of_comments,
                "size":0,
                "comments_url":f"{author.host}/author/{author.consistent_id}/posts/{post.post_id}/comments",
                "comments":comment_dict_list,
                "published":post.published,
                "unlisted":False if not post.privfriends else True,
                "post_id":post.post_id,
                "user_id":post.user_id,
                "image":str(post.image,encoding="utf-8"),
                "markdown":post.markdown,
                "privfriends":post.privfriends,
                "visibility":["PUBLIC"],
                "published":post.published,
                "author":author_dict,
            }
            # retrieve all categories for post
            categories = Category.objects.filter(post_id=post.post_id)
            for ca in categories:post_dict["categories"].append(clean_script(ca.tag))
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
    cursor.execute('SELECT * FROM firstapp_comment WHERE from_user = %s AND post_id = %s;'% (request.user.id, post_id))
    data = cursor.fetchall()
    if request.method == "POST":
        while True:
            
            comment_id = f"{uuid.uuid4().hex}"
            byte_data = request.data
            comment = byte_data.get('comment')
            
            cursor.execute("SELECT comment_text FROM firstapp_comment WHERE comment_id='%s'"%(comment_id))
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
    conn = connection
    cursor = conn.cursor()
    is_ajax = request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'
    if is_ajax:
        json_comment_list = []
        comments = Comment.objects.filter(post_id=post_id)
        for comment in comments:
           # for comment in comments:
            author = Author.objects.get(consistent_id = comment.to_user[len(f"https://{request.get_host()}/author/"):])
            author_dict = {
                "type":"author",
                "id": f"{author.host}/author/{author.consistent_id}",
                "host": f"{author.host}/",
                "url": f"{author.host}/author/{author.consistent_id}",
                "displayName": author.username,
                "github": author.github,
            }
            comment_dict = {
                "type":"comment",
                "author":author_dict,
                "comment":clean_script(comment.comment_text),
                "contentType":"text/markdown",
                "published":str(datetime.now()),
                "id":f"{author.host}/author/{author.consistent_id}/posts/{comment.post_id}/viewComments/{comment.comment_id}",
            }
            json_comment_list.append(comment_dict)
        return HttpResponse(json.dumps(json_comment_list))
    agent = request.META["HTTP_USER_AGENT"]
    if "Mozilla" in agent or "Chrome" in agent or "Edge" in agent or "Safari" in agent:
        print("\n\nviewcomments in browser\n\n")
        data = Comment.objects.filter(post_id=f"https://{request.META['HTTP_HOST']}/author/{user_id}/posts/{post_id}")
        comment_list = []
        print(f"in comments https://{request.META['HTTP_HOST']}/author/{user_id}/posts/{post_id}")
        print(data)
        for d in data:
            comment_text = d.comment_text
            comment_list.append(comment_text)
        num_comments = len(comment_list)

        try:
            page_number = int(request.GET.get('page'))
            if page_number is None or page_number < 1:
                page_number = 1
        except Exception as e:
            print("exception, page number is now 1")
            print(e)
            page_number = 1
        try:
            size = request.GET.get('size')
            if size is None:
                size = len(comment_list)
        except:
            size = len(comment_list)
        paginator = Paginator(comment_list,size)
        try:
            comment_list = paginator.page(page_number).object_list
        except:
            comment_list = []
        return render(request, "comment_list.html", {"comment_list":comment_list, "num_comments":num_comments})
    else:
        print(f"\n\nviewcomments not in browser https://{request.get_host()}/author/{user_id}/posts/{post_id}\n\n")
        json_comment_list = []
        comments = Comment.objects.filter(post_id=f"https://{request.get_host()}/author/{user_id}/posts/{post_id}")
        print(comments)
        for comment in comments:
           # for comment in comments:
            author = Author.objects.get(consistent_id = comment.to_user[len(f"https://{request.get_host()}/author/"):])
            author_dict = {
                "type":"author",
                "id": f"{author.host}/author/{author.consistent_id}",
                "host": f"{author.host}/",
                "url": f"{author.host}/author/{author.consistent_id}",
                "displayName": author.username,
                "github": author.github,
            }
            comment_dict = {
                "type":"comment",
                "author":author_dict,
                "comment":comment.comment_text,
                "contentType":"text/markdown",
                "published":str(datetime.now()),
                "id":f"{author.host}/author/{author.consistent_id}/posts/{comment.post_id}/viewComments/{comment.comment_id}",
            }
            json_comment_list.append(comment_dict)
        print(json_comment_list)
        try:
            page_number = int(request.GET.get('page'))
            if page_number is None or page_number < 1:
                page_number = 1
        except:
            page_number = 1
        try:
            size = request.GET.get('size')
            if size is None:
                size = len(json_comment_list)
        except:
            size = len(json_comment_list)
        paginator = Paginator(json_comment_list,size)
        try:
            json_comment_list = paginator.page(page_number).object_list
        except:
            json_comment_list = []
        return HttpResponse(json.dumps(json_comment_list))

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
    print(f"{user_id} is Inside account function")
    # This method can GET and POST an author by their UUID
    # GET retrieves the account's information. POST updates the account's information if authenticated
    resp = ""
    method = request.META["REQUEST_METHOD"]

    try: 
        print(f"trying to get an author of {user_id}")
        for a in Author.objects.filter():
            print(a)
            print(a.consistent_id)
        author = Author.objects.get(consistent_id=user_id) # Try to retrieve the author. If not, give error HTTP response
        print("got an author")
    except:
        print("uhoh")
        return HttpResponseNotFound("The account you requested does not exist\n")
    if method == "GET": # We want to return a JSON object of the Author requested
        print("in get")
        author_dict = {
            "id": f"{author.host}/author/{author.consistent_id}",
            "host": f"{author.host}/",
            "displayName": author.username,
            "url": f"{author.host}/firstapp/{author.userid}",
            "github": author.github,
            "type": "author",
        }
        print(f"here's my thing\n\n{author_dict}\n\n")
        return HttpResponse(json.dumps(author_dict))
    else: # It's a POST request
        print("Wait, I'm in a post request")
        try: # First see if the user exists
            author = Author.objects.get(consistent_id=user_id)
        except Author.DoesNotExist:
            messages.add_message(request,messages.INFO, 'This user does not exist.')
            return HttpResponseRedirect(reverse('login'))
        authenticated = check_authentication(request)
        if not authenticated:
            return HttpResponse('{"detail":"Authentication credentials were incorrectly provided."}',status=401) # Incorrect or missing token
        # Can only POST if you're the user itself, or are the admin
        username = authenticated.get_username()

        if not username == author.username and not request.user.is_superuser:
            return HttpResponse('{"detail":"You are not the author."}',status=401)
        p = request.POST
        try: # You can only edit your github and display name.
            user = User.objects.get(username=author.username)
            user.username = p["displayName"]
            user.save()
            author = Author.objects.get(consistent_id=user_id)
            author.github = p["github"]
            author.username = p["displayName"]
            author.save()
        except MultiValueDictKeyError:
            return HttpResponseBadRequest("Failed to modify post:\nInvalid/not enough parameters. Must only change github and displayName\n")
        
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
    cursor.execute("SELECT * FROM authtoken_token t, firstapp_author a WHERE a.userid = '%s';" % user_id)

    try:
        data = cursor.fetchall()[0]
        Author = get_user_model()
        account = Author.objects.get(id = user_id)
    except IndexError: # No token exists, must create a new one!
        return HttpResponse("user doesn't exist") 


    if data != None:
        print("^^^^^^^^^data^^^^^^^^^^^")
        print(data)
        context['id'] = data[8]
        context['username1'] = data[3]
        context['email'] = data[9]
        context['host'] = data[6]
        context['me_Cid'] = data[11]
        context['githubLink']=data[4]

        try:
            friend_list = FriendList.objects.get(user=account)
        except FriendList.DoesNotExist:
            friend_list = FriendList(user=account)
            friend_list.save()

        
        friends = friend_list.friends.all()
        
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
                friend_requests = FriendRequest.objects.filter(receiver=user, is_active=True)
            except:
                pass


        is_following = False
        follow_sent = None 
        if user.is_authenticated:
            try:
                following_list = Follow.objects.filter(follower=user)
            except FollowingList.DoesNotExist:
                return HttpResponse(f"Could not find a following list for {this_user.username}")
            # Must be friends to view a friends list
            followings = [] # [(friend1, True), (friend2, False), ...]

            # get the authenticated users friend list
            auth_user_following_list = Follow.objects.filter(follower=user)
            for following in following_list:
                if following.receiver not in followings:
                    followings.append(following.receiver)

            if account not in followings:
                is_following = False
                follow_sent = 0
            else:
                is_following = True
                follow_sent = 1

            context['followings'] = followings
            
            try:
                followers_list = Follow.objects.filter(receiver=user)
            except FollowingList.DoesNotExist:
                return HttpResponse(f"Could not find a following list for {this_user.username}")
            # Must be friends to view a friends list
            followers = [] # [(friend1, True), (friend2, False), ...]

            # get the authenticated users friend list
            for follower in followers_list:
                if follower.follower not in followers:
                    followers.append(follower.follower)
            if account not in followers:
                is_follower = False
               
            else:
                is_follower = True

            context['followers'] = followers

            for follower in followers:
                for follwing in followings:
                    if follower == following.receiver:
                        print("hereeeee")
                        FL = FriendList.objects.get(user = user)
                        FL.FriendAdd(account = follower)



        user = request.user
        if not (request.user.is_authenticated and str(request.user.id) == str(user_id)):
            is_self = False
        cursor.execute("SELECT * FROM authtoken_token t, firstapp_author a WHERE a.userid = '%s';" % request.user.id)
        try:
            data2 = cursor.fetchall()[0]
        except IndexError: # No token exists, must create a new one!
            return HttpResponse("user doesn't exist") 
        # print(new_account.github)
        context['username2'] = data2[3]
        context['githubLink2'] = data2[4]
        context['receiver_Cid'] = data2[11]

        context['is_self'] =is_self
        context['friends'] = friends
        context['is_following'] = is_following
        context['is_friend'] = is_friend
        context['follow_request'] = follow_sent
        context['request_sent'] = request_sent
        context['friend_requests'] = friend_requests
        context['BASE_URL'] = settings.BASE_DIR
        context['Author'] = getAuthor(user_id)
        return render(request,"profile.html",context)

def getAuthor(userid):
    # This function gets the Author object associated with the userid. Returns None
    my_user = Author.objects.get(userid=userid) # Will change it to include the uuid rather than userid
    return my_user
        
def check_authentication(request):
    # From turtlefranklin at 2021-03-31 at https://stackoverflow.com/questions/38016684/accessing-username-and-password-in-django-request-header-returns-none
    auth_header = request.META['HTTP_AUTHORIZATION']
    encoded_credentials = auth_header.split(' ')[1]  # Removes "Basic " to isolate credentials
    decoded_credentials = base64.b64decode(encoded_credentials).decode("utf-8").split(':')
    username = decoded_credentials[0]
    password = decoded_credentials[1]
    authenticated = authenticate(username=username, password=password)
    return authenticated
    ########################

# Like a post by sending a post request to the inbox.
@api_view(['POST'])
def likeAHomePagePost(request):
    print("ok we liking a homepage post")
    post = json.loads(request.POST.get('thePost', False))
    author = Author.objects.get(username=request.POST.get('author', False))
    print(post)
    # If it's a local like:
    if post['author']['host'] == request.get_host() or f"https://{request.get_host()}/" == f"{post['author']['host']}" or f"https://{request.get_host()}/" == f"{post['author']['host']}":
        print("entering.")
        # author/<str:user_id>/posts/<int:post_id>/likepost/
        try: 
            # Try to unlike
            like = Like.objects.get(from_user=f"{author.host}/author/{author.consistent_id}",to_user=post['author']['id'],object=post["id"])
            like.delete()
        except Exception as e:
            print(e)
            # Like does not exist. Must like.
            # like = Like.objects.create(from_user=f"{author.host}/author/{author.consistent_id}",to_user=post['author']['id'],like_id=rand(2**31-1),object=post["id"])
            author_dict = {
                "type":"author",
                "id":f"{author.host}/author/{author.consistent_id}",
                "url":f"{author.host}/firstapp/{author.userid}",
                "host":author.host,
                "displayName":author.username,
                "github":author.github,
            }
            like_dict = {
                "type":"like",
                "author":author_dict,
                "object":post['id'],
                "@context":"something",
                "summary":f"{author.username} Likes your post",
            }
            like_object = json.dumps(like_dict)
            headers  = {'Content-type': 'application/json'}
            url = f"{author.host}/author/{author.consistent_id}/inbox"
            print(f"\n\nsending to...{url}\n\n")
            requests.post(url, data = like_object, headers=headers, auth=("adminB","adminB"))
        return HttpResponse("Like processed")
    # Else, it's a remote like
    print("remote post like")
    try:
        server = Node.objects.get(hostserver=f"http://{post['author']['host']}")
    except:
        try:
            server = Node.objects.get(hostserver=f"{post['author']['host']}")
        except:
            server = Node.objects.get(hostserver=f"https://{post['author']['host']}")
    auth_dict = {
        "type":"author",
        "id": f"{author.host}/author/{author.consistent_id}",
        "host": f"{author.host}/",
        "displayName": author.username,
        "url": f"{author.host}/firstapp/{author.userid}",
        "github": author.github,
    }
    like_serializer = {"type":"like","context":"","summary":f"{author.username} liked your post","author":auth_dict,"object":post["id"]}
    # Does not need headers, else it's a 400
    response = requests.post(f"{post['author']['id']}/inbox/",json=like_serializer,auth=(server.authusername,server.authpassword))
    return HttpResponse("Liked!")

# Comment a post by sending a comment request to the inbox.
@api_view(['POST'])
def commentAHomePagePost(request):
    theComment = request.POST.get("theComment",False)
    post = json.loads(request.POST.get('thePost', False))
    print(post)
    # If it's a local comment:
    author = Author.objects.get(username=request.POST.get('author', False))
    print(f"\n\n\n\nit's me: {post['author']['host']} and {request.get_host()}")
    print(f"haha{author.host}/author/{author.consistent_id}\n\n\n\n")
    if post['author']['host'] == request.get_host() or f"https://{request.get_host()}/" == f"{post['author']['host']}" or f"https://{request.get_host()}/" == f"{post['author']['host']}":
        comment = Comment.objects.create(post_id=post["id"],comment_id=f"{post['id']}/comments/{uuid.uuid4().hex}",from_user=f"{author.host}/author/{author.consistent_id}",to_user=post["author"]["id"],comment_text=theComment,published=str(datetime.now()))
        comment.save()
    else:
        print(f"this is the post's host: https://{post['author']['host']}")
        try:
            server = Node.objects.get(hostserver=f"http://{post['author']['host']}")
        except:
            try:
                server = Node.objects.get(hostserver=f"{post['author']['host']}")
            except:
                server = Node.objects.get(hostserver=f"https://{post['author']['host']}")
        author_dict = {
            "type":"author",
            "id":f"{author.host}/author/{author.consistent_id}",
            "url":f"{author.host}/firstapp/{author.userid}",
            "host":author.host,
            "displayName":author.username,
            "github":author.github,
        }
        c_id= f"{uuid.uuid4().hex}"
        comment_dict = {
            "type":"comment",
            "author":author_dict,
            "comment":theComment,
            "contentType":"text/plaintext",
            "published":str(datetime.now()),
            "id":f"{post['id']}/comments/{c_id}"
        }
        response = requests.post(f"{post['id']}/comments",json=comment_dict,auth=(server.authusername,server.authpassword))
        response = requests.post(f"{post['author']['id']}/inbox",json=comment_dict,auth=(server.authusername,server.authpassword))
    return HttpResponse("Commented!")

# Comment a post by sending a comment request to the inbox.
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
def makeComment(request,user_id,post_id):
    enc = base64.b64decode(request.META["HTTP_AUTHORIZATION"].split(" ")[1]).decode("utf-8").split(":")
    uname, pword = enc[0], enc[1]
    print(uname,pword)
    print(request.POST)
    # First see if credentials are valid. If not, return
    user = authenticate(username = uname, password = pword)
    if user is None:
        return HttpResponseBadRequest("You are not authenticated!")
    try:
        # retrieve the text and from_user
        # Create the comment object
        print("\nMaking a comment\n")
        post_id = f"https://{request.get_host()}/author/{user_id}/posts/{post_id}"
        comment_id = f"{post_id}/comments/{uuid.uuid4().hex}"
        print(f"\n\nThe data is:\n{request.data}\n\n")
        print(f"\n{request.data.get('comment')}\n")
        print(f"\n{request.data.get('author')}\n")
        print(f"\n{request.data.keys()}\n")
        try:
            author_dict = json.loads(request.data.get('author',False)) # This should be the person commenting, not the creator of the post
        except:
            # From Team 1 then
            author_dict = request.data.get('author')
        print(f"the author dict is {author_dict}")
        from_user = author_dict["id"]
        author = Author.objects.get(consistent_id=user_id)
        to_user = f"https://{request.get_host()}/author/{user_id}"
        comment_text = str(request.data.get('comment'))
        comment = Comment.objects.create(post_id=post_id,comment_id=comment_id,from_user=from_user,to_user=to_user,comment_text=comment_text,published=str(datetime.now()))
        comment.save()
    except Exception as e:
        print(e)
        return HttpResponseBadRequest(f"Something went wrong. Make sure to send an author dictionary and a comment. The error is {e}")
    return HttpResponse("Commented!")

@api_view(['GET'])
def viewComment(request,user_id,post_id,comment_id):
    try:
        comment = Comment.objects.get(comment_id=f"https://{request.META['HTTP_HOST']}/author/{user_id}/posts/{post_id}/comments/{comment_id}")
    except:
        return HttpResponseBadRequest("Comment does not exist.")
    author = Author.objects.get(consistent_id=user_id)
    author = {
        "type":"author",
        "id":f"{author.host}/author/{author.consistent_id}",
        "url":f"{author.host}/firstapp/{author.userid}",
        "host":author.host,
        "displayName":author.username,
        "github":author.github,

    }
    comment_dict = {
        "type":"comment",
        "author":author,
        "comment":comment.comment_text,
        "contentType":"text/plaintext",
        "published":comment.published,
        "id":comment.comment_id,
    }
    return HttpResponse(json.dumps(comment_dict))
@api_view(['POST'])
@authentication_classes([BasicAuthentication])
def sharePublicPost(request):
    # Takes post object and author.
    print("in sharePublicPost\n")
    post = json.loads(request.POST.get('thePost', False))
    author = Author.objects.get(username=request.POST.get('author', False))
    print(post)
    print(author)
    print(post["image"])
    author_dict = {
        "id":f"{author.host}/author/{author.consistent_id}",
        "host":f"{author.host}/",
        "displayName":author.username,
        "url":f"{author.host}/firstapp/{author.userid}",
        "github":author.github,
        "type": "author",
    }
    post_id = rand(2**28)
    print(post["image"])
    for item in [f"https://{request.get_host()}/posts",post["origin"],post["title"],sqlite3.Binary(bytes(post["image"] if post["image"] is not None else "0",encoding="utf-8")),f"https://{request.get_host()}/author/{author.consistent_id}/posts/{post_id}",post_id,author.consistent_id,post["description"],False if post["contentType"] != "text/markdown" else True,post["content"]]:
        print(item)
    print("those are them all.")

    if post['image'] == None or str(post['image']) == "0":
        print("none image")
        image = bytes("0",encoding="utf-8")
    elif ";base64," in post["image"]:
        print("base 64 image")
        image = bytes(post["image"],encoding="utf-8")
    else:
        print("else image")
        source_url = urlparse(post["source"])
        print("hm")
        image_url = "{0}://{1}{2}".format(source_url.scheme,source_url.netloc,post["image"])
        print(image_url)
        image = bytes("data:image/jpeg;base64,",encoding="utf-8")+base64.b64encode(requests.get(image_url).content)
        print(image)

    newpost = Post.objects.create(source=f"https://{request.get_host()}/posts",origin=post["origin"],title=post["title"],image=image,id=f"https://{request.get_host()}/author/{author.consistent_id}/posts/{post_id}",post_id=post_id,user_id=author.consistent_id,description=post["description"],markdown=False if post["contentType"] != "text/markdown" else True,content=post["content"],privfriends=False,unlisted=False,published=str(datetime.now()))
    newpost.save()

    # Send the newly created posts to friend's inboxes
    try: friend_ids = [Author.objects.get(userid=f.id).consistent_id for f in FriendList.objects.get(user_id=author.userid).friends.all()]
    except FriendList.DoesNotExist: friend_ids = []
    try: follow_ids = [Author.objects.get(userid=f.follower.id).consistent_id for f in Follow.objects.filter(receiver=author.userid)]
    except Follow.DoesNotExist: follow_ids = []

    payload = {"type":"post","author":author_dict,"id" : f"https://{request.get_host()}/author/{author.consistent_id}/posts/{post_id}","post_id":post_id,"user_id":author.consistent_id,"title":post["title"],"description":post["description"],"markdown":False if post["contentType"] != "text/markdown" else True,"content":post["content"],"image":image.decode("utf-8"),"privfriends":False,"unlisted":False,"published":str(datetime.now())}
    for f in friend_ids:
        r = requests.post(f"https://{request.get_host()}/author/{f}/inbox",headers={"Authorization":"Token %s"%author.api_token,"Content-Type":"application/json"},json=payload)
    for f in follow_ids:
        r = requests.post(f"https://{request.get_host()}/author/{f}/inbox",headers={"Authorization":"Token %s"%author.api_token,"Content-Type":"application/json"},json=payload)
    return HttpResponse("Shared")
    


@api_view(['GET','POST', 'DELETE'])
@authentication_classes([BasicAuthentication,SessionAuthentication,TokenAuthentication])
@permission_classes([IsAuthenticated])
def inbox(request,user_id):
    print("In Inbox function.\n")
    method = request.META["REQUEST_METHOD"]
    try:
        host = request.build_absolute_uri('/')
        print(host)
        author_id = host + "author/" + user_id
        print(author_id)
        try:
            inbox = Inbox.objects.get(author=author_id)
        except Inbox.DoesNotExist:
            inbox = Inbox.objects.get(author=author_id.replace("http","https"))
        print(inbox)
        print(method)
        if method == "GET":
            if request.user.is_authenticated:
                inbox_object = {}
                inbox_object["type"]= "inbox"
                inbox_object["author"] = author_id
                inbox_post_items = []
                print(request.user)
                try:
                    #Why does the code not work without importing this again????
                    from firstapp.models import Author
                    author = Author.objects.get(username=request.user)
                    token = author.api_token
                except Author.DoesNotExist:
                    return HttpResponseNotFound(f"In the homepage function, the user you requested does not exist!!{request.user}\n")
                token = author.api_token
                agent = request.META["HTTP_USER_AGENT"]
                if "Mozilla" in agent or "Chrome" in agent or "Edge" in agent or "Safari" in agent: # is the agent a browser? If yes, show html, if no, show regular post list
                    print("we using a browser ok")
                    json_to_display = []
                    print(inbox.items)
                    for item in inbox.items:
                        print(f"Your item is {item}")
                        if item["type"] == "post":
                            item["title"] = clean_script(item["title"])
                            item["description"] = clean_script(item["description"])
                            item["content"] = clean_script(item["content"])
                            json_to_display.append(json.dumps(item))
                        else:
                            json_to_display.append(json.dumps(item))
                        print("appended item")
                    return render(request, 'inbox.html', {'user_id':user_id,'token':token,'author_uuid':user_id,'stuff_to_display':json_to_display})
                else:
                    for item in inbox.items:
                        if item["type"] == "post":
                            inbox_post_items.append(item)
                        print("6")
                    inbox_object["items"] = inbox_post_items
                    print(inbox_object)
                    return HttpResponse(json.dumps(inbox_object))
            else:
                return HttpResponse("Please sign in before you can the inbox")
        # FIX THIS
        elif method == "POST":
            print("this")
            print(request.data["type"])
            data_json_type = request.data["type"]
            if data_json_type == "like":
                print("liking.......")
                # save to like table
                conn = connection
                cursor = conn.cursor()
                like_id = rand(2**31-1)
                print(like_id)
                cursor.execute("SELECT * FROM firstapp_like WHERE like_id = %d"% (like_id))
                #if id is not used (enforcing unique ids)
                if len(cursor.fetchall()) == 0:
                    print("id is available!!\n\n")
                    object = request.data["object"]
                    print(object)
                    #extract to_user uuid
                    to_user = object.split("author/")[1]
                    to_user = to_user.split("/")[0]
                    # extract from_user uuid
                    print(request.data["author"])
                    author_id = request.data["author"]["id"]
                    author_id = author_id.split("author/")[1]
                    print(author_id)
                    #remove backslash at end of url if it's there
                    if author_id[-1] == "/":
                        author_id = author_id[:-1]
                    try: #if already liked then remove the like from db
                        print("getting like object")
                        like = Like.objects.get(from_user = request.data["author"]["id"], to_user = f"https://{request.get_host()}/author/{to_user}", object = object)
                        print("removing like object from inbox")
                        print(like)
                        print(inbox.items)
                        print(author_id)
                        for i in range(len(inbox.items)):
                            item = inbox.items[i]
                            print(item["author"]["id"])
                            print(f"https://{request.get_host()}/author/{author_id}")
                            print(item["object"])
                            print(object)
                            if item["author"]["id"] == f"https://{request.get_host()}/author/{author_id}" and item["object"] == object:
                                inbox.items.pop(i)
                                print("item deleted from inbox")
                                break
                        inbox.save()
                        print("deleting like object from like table")
                        like.delete()

                        return HttpResponse(f"Like object has been removed from database and inbox")

                    except Exception as e: #if not liked then add like to database
                        print(e)
                        print("making like object for table")
                        like = Like(like_id=like_id, from_user = request.data["author"]["id"], to_user = f"https://{request.get_host()}/author/{to_user}", object = object)
                        print("saving like object to table")
                        like.save()
                        print("adding object to inbox")
                        inbox.items.append(request.data)
                        inbox.save()
                        return HttpResponse(f"Like object has been added to author {to_user}'s inbox")
                else:
                    return HttpResponse("already taken.")
            # MUST TEST.
            elif data_json_type == "post":
                inbox.items.append(request.data)
                inbox.save()
                return HttpResponse(f"Post object has been added to author's inbox")

            elif data_json_type == "follow":
                receive_id = request.data["id"]
                remote_sender = request.data["actor"]["id"].split('/')[-1]
                local_receiver = request.data["object"]["id"].split('/')[-1]
                print(remote_sender)
                print(local_receiver)
                get_all_remote_user_2()
                ccursor.execute("SELECT * FROM authtoken_token t, firstapp_author a WHERE a.consistent_id = '%s';" % remote_sender)
                try:
                    data1 = cursor.fetchall()[0]
                    Author = get_user_model()
                    sender = Author.objects.get(id = data1[8])
                except IndexError: # No token exists, must create a new one!
                    return HttpResponse("user doesn't exist") 

                ccursor.execute("SELECT * FROM authtoken_token t, firstapp_author a WHERE a.consistent_id = '%s';" % local_receiver)
                try:
                    data2 = cursor.fetchall()[0]
                    Author = get_user_model()
                    receiver = Author.objects.get(id = data1[8])
                except IndexError: # No token exists, must create a new one!
                    return HttpResponse("user doesn't exist")

                follow = Follow(follower = sender,receiver = receiver)
                follow.save()
                inbox.items.append(request.data["data"])
                inbox.save()
                return HttpResponse(f"Follow object has been added to author {to_user}'s inbox")


        elif method == "DELETE":
            from firstapp.models import Author
            data = Author.objects.filter(consistent_id=user_id)[0]
            user_token = data.api_token
            author_id = data.userid
            try: # Client is using token authentication
                token = request.META["HTTP_AUTHORIZATION"].split("Token ")[1]
                if token != user_token: return HttpResponse('{"detail":"Authentication credentials were not provided."}',status=401) # Incorrect or missing token
            except IndexError: # Client is using basic authentiation
                enc = base64.b64decode(request.META["HTTP_AUTHORIZATION"].split(" ")[1]).decode("utf-8").split(":")
                uname, pword = enc[0], enc[1]
                user = User.objects.get(id=author_id)
                if user.username != uname or not user.check_password(pword):
                    return HttpResponse('{"detail":"Invalid username/password."}',status=401) # A correct uname and pword supplied, but not for this specific user
            inbox.items = []
            inbox.save()



            return HttpResponse(f"{author_id}'s inbox has been cleared")

    except Exception as e:
        print("ERROR in inbox in views.py" + str(e))

@staff_member_required    
def run_post_tests(request):
    process = subprocess.Popen(['python3', 'tests/post_tests.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = process.communicate()
    return HttpResponse(err.decode("utf-8").replace("\n","</br>"))