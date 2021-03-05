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
import json
from django.conf import settings
from markdown import Markdown as Md

from rest_framework.decorators import api_view, permission_classes, authentication_classes
#from rest_framework.permissions import IsAuthenticated
from .permissions import EditPermission
from rest_framework.authentication import BasicAuthentication, SessionAuthentication, TokenAuthentication
from rest_framework.authtoken.models import Token
from friend.request_status import RequestStatus
from friend.models import FriendList, FriendRequest
from friend.is_friend import get_friend_request_or_false
from firstapp.models import Author
from django.contrib.auth import get_user_model
import uuid

FILEPATH = os.path.dirname(os.path.abspath(__file__)) + "/"

ADD_QUERY = "INSERT INTO posts VALUES (?, ?, ?, ?, ?, ?, ?, ?);"
EDIT_QUERY = "UPDATE posts SET post_id=?, user_id=?, title=?, description=?, markdown=?, content=?, image=?, tstamp=? WHERE post_id=? AND user_id =?;"

PRIV_ADD_QUERY = "INSERT INTO author_privacy VALUES (?,?);"

# Create your views here.
def index(request):
    #if request.user.is_authenticated:
    return render(request, 'index.html')

def homepage(request):
    print("&&&&7&&&")
    if request.user.is_authenticated:
        conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
        cursor = conn.cursor()
        cursor.execute('SELECT u.id,t.key FROM authtoken_token t, auth_user u WHERE u.id = t.user_id AND u.username = "%s";' % request.user)
        data = cursor.fetchall()[0]
        user_id,token = data[0], data[1]
        conn.close()
        print(request.user.id)
        return render(request, 'homepage.html', {'user_id':user_id,'token':token})
    
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
            conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
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
                            consistent_id=f"http://{request.get_host()}/author/{uuid.uuid4().hex}")
                # If the flag, UsersNeedAuthentication is True, redirect to Login Page with message
                messages.add_message(request,messages.INFO, 'Please wait to be authenticated by a server admin.')
                return HttpResponseRedirect(reverse('login'))
            # Else, let them in homepage.
            user = Author.objects.create(host=f"http://{request.get_host()}",username=new_username,\
                userid=request.user.id, authorized=True,email=form.cleaned_data['email'],\
                    name=f"{form.cleaned_data['first_name']} {form.cleaned_data['last_name']}",\
                        consistent_id=f"http://{request.get_host()}/author/{uuid.uuid4().hex}")
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
            cursor.execute('SELECT Authorized FROM firstapp_author WHERE userid = ? and username = ?;',(request.user.id,new_username))
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
def make_post_html(data,user_id,canedit=False):
    resp = ""
    with open(FILEPATH+"static/like.js","r") as f: script = f.read()

    #add javascript likePost function and the jquery library for ajax
    jscript = '<script>' + script + '</script>' + '<script src="http://ajax.googleapis.com/ajax/libs/jquery/1.11.1/jquery.min.js"></script>'
    start = '<div class="post" style="border:solid;" ><p class="title">%s</p><p class="desc">%s</p></br><p class="content">%s</p></br>'
    endimage = '<img src="%s"/><span class="md" style="display:none" value="%s"></span></br>'+('<input type = "button" value="Edit" onclick="viewPost(\'{0}\')">' if canedit else '')
    endnoimage = '<span class="md" style="display:none" value="%s"></span></br>'+('<input type = "button" value="Edit" onclick="viewPost(\'{0}\')">' if canedit else '')

    conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
    cursor = conn.cursor()
    for d in data:
        cursor.execute('SELECT * FROM author_privacy WHERE post_id=%d'%d[0]) # See if the current post is private to any authors
        priv = cursor.fetchall()
        image = str(d[-2],encoding="utf-8")
        content = d[5]
        if d[4]: # use markdown!
            md = Md()
            content = md.convert(content)
        starttag = jscript
        starttag += start % (d[2],d[3],content)
        if len(priv) == 0: # post is not private
            if image == '0':
                resp += starttag
                resp += endnoimage.format(d[0]) % (d[4],)
                resp += '<button onclick="likePost(\'{}\')">Like</button>'.format(d[0])
                resp += '<button onclick="viewLikes(\'{}\')">View Likes</button>'.format(d[0])
            else: 
                resp += starttag + endimage.format(d[0]) % (image,d[4])
                resp += '<form action="/{}/likes"method = get>view likes</form>'.format(d[0])
                resp += '<button onclick="viewLikes(\'{}\')">View Likes</button>'.format(d[0])
            resp += "</br>"
        else: # post is private
            show_post = False
            for p in priv:
                if p[1] == user_id:
                    show_post = True
                    break
            if show_post and user_id != None: # show post only if this variable is true, and a user is logged in!
                if image == '0': resp += starttag + endnoimage.format(d[0],d[0]) % (d[4],)
                else: resp += starttag + endimage.format(d[0],d[0]) % (image,d[4])
                resp += "</br>"
    conn.close()
    return resp

# This function will return all visible posts, and return them in a list to be displayed to non-browser user agents
# data - the list of tuples returned from sql
# user_id - used to check to see if the current user can view the post (is it private to specific authors, or public?)
def make_post_list(data,user_id):
    post_list = []
    conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
    cursor = conn.cursor()
    for d in data:
        cursor.execute('SELECT * FROM author_privacy WHERE post_id=%d'%d[0]) # See if the current post is private to any authors
        priv = cursor.fetchall()
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
        # post is public or post belongs to user
        if len(priv) == 0 or user_id == d[1]: post_list.append(post_dict)
        else:
            show_post = False
            # Determine if requesting author is among privacy list
            for p in priv:
                if p[1] == user_id:
                    show_post = True
                    break
            if show_post and user_id != None: post_list.append(post_dict)
    conn.close()
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
    conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM auth_user WHERE id=%d'%user_id) # Check to see if user in url exists
    data = cursor.fetchall()
    if len(data)==0: return HttpResponseNotFound("The user you requested does not exist\n")
    cursor.execute('SELECT * FROM posts p WHERE p.post_id=%d AND p.user_id=%d'%(post_id,user_id))
    data = cursor.fetchall()
    if len(data)==0 and method != 'PUT': return HttpResponseNotFound("The post you requested does not exist\n") # Check to see if post in url exists (not for PUT)
    cursor.execute('SELECT * FROM posts p WHERE p.post_id=%d'%(post_id,))
    data = cursor.fetchall()
    if len(data) > 0 and method == 'PUT': return HttpResponse("The post with id %d already exists! Maybe try POST?\n"%post_id,status=409) # check to see if post already exists (for PUT)
    cursor.execute('SELECT t.key FROM authtoken_token t, auth_user u WHERE u.id = t.user_id AND u.id = "%d";'%user_id)
    user_token = cursor.fetchall()[0][0]

    if method == 'GET':
        resp = make_post_list(data,request.user.id)
    else:
        token = request.META["HTTP_AUTHORIZATION"].split("Token ")[1]
        if token != user_token: return HttpResponse('{"detail":"Authentication credentials were not provided."}',status=401) # Incorrect or missing token

        if method == 'POST':
            p = request.POST
            try: image = p["image"] # image is an optional param!
            except MultiValueDictKeyError: image = '0'
            try: # if all mandatory fields are passed
                if not validate_int(p,[post_id,user_id]): return HttpResponseBadRequest("Error: you have submitted non integer values to integer fields.") # non integer markdown field (0-1)
                cursor.execute(EDIT_QUERY, (post_id,user_id,p["title"],p["description"],p["markdown"],p["content"],sqlite3.Binary(bytes(image,encoding="utf-8")),str(datetime.now()),post_id,user_id))
                conn.commit()
                resp = "Successfully modified post: %d\n" % post_id
            except MultiValueDictKeyError:
                return HttpResponseBadRequest("Failed to modify post:\nInvalid parameters\n")

            # Modify the author privacy table in the database
            if "priv_author" in p.keys() or "priv_author[]" in p.keys():
                if "priv_author" in p.keys(): private_authors = p.getlist("priv_author")
                else: private_authors = p.getlist("priv_author[]")
                for pa in private_authors:
                    cursor.execute("SELECT id from auth_user WHERE id = ?",(pa,))
                    data = cursor.fetchall()
                    if len(data) == 0: return HttpResponseNotFound("One or more user ids entered into the author privacy field are not valid user ids.") # check if author ids are valid
                cursor.execute("DELETE FROM author_privacy WHERE post_id=?",(post_id,)) # delete all before updating with new values
                conn.commit()
                for pa in private_authors:
                    cursor.execute(PRIV_ADD_QUERY, (post_id, pa))
                    conn.commit()
            else:
                cursor.execute("DELETE FROM author_privacy WHERE post_id=?",(post_id,)) # if nothing is supplied, user wants to make post public
                conn.commit()

 
        elif method == 'PUT':
            p = request.POST
            try: image = p["image"] # image is an optional param!
            except MultiValueDictKeyError: image = '0'
            try: # if all mandatory fields are passed
                if not validate_int(p,[post_id,user_id]): return HttpResponseBadRequest("Error: you have submitted non integer values to integer fields.") # non integer markdown field (0-1)
                cursor.execute(ADD_QUERY, (post_id,user_id,p["title"],p["description"],p["markdown"],p["content"],sqlite3.Binary(bytes(image,encoding="utf-8")),str(datetime.now())))
                conn.commit()
                resp = "Successfully created post: %d\n" % post_id
            except MultiValueDictKeyError:
                return HttpResponseBadRequest("Failed to modify post:\nInvalid parameters\n")

            # Modify the author privacy table in the database
            if "priv_author" in p.keys() or "priv_author[]" in p.keys():
                if "priv_author" in p.keys(): private_authors = p.getlist("priv_author")
                else: private_authors = p.getlist("priv_author[]")
                for pa in private_authors:
                    cursor.execute("SELECT id from auth_user WHERE id = ?",(pa,))
                    data = cursor.fetchall()
                    if len(data) == 0: return HttpResponseNotFound("One or more user ids entered into the author privacy field are not valid user ids.")
                for pa in private_authors:
                    cursor.execute(PRIV_ADD_QUERY, (post_id, pa))
                    conn.commit()

        elif method == 'DELETE':
            cursor.execute("DELETE FROM author_privacy WHERE post_id=?",(post_id,))
            conn.commit()
            cursor.execute("DELETE FROM posts WHERE post_id=%d AND user_id=%d"%(post_id,user_id))
            conn.commit()
            resp = "Successfully deleted post: %d\n" %post_id
        else:
            conn.close()
            return HttpResponseBadRequest("Error: invalid method used\n")
    conn.close()
    agent = request.META["HTTP_USER_AGENT"]
    if "Mozilla" in agent or "Chrome" in agent or "Edge" in agent or "Safari" in agent: # is the agent a browser? If yes, show html, if no, show regular post list
        if method == "GET": resp = make_post_html(data,request.user.id)
        with open(FILEPATH+"static/post.js","r") as f: script = f.read() % (user_token, user_token)
        # true_auth: is user logged in, and are they viewing their own post? (determines if they can edit /delete the post or not)
        return render(request,'post.html',{'post_list':resp,'true_auth':(request.user.is_authenticated and request.user.id == user_id),'postscript':script})
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
    conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
    cursor = conn.cursor()
    cursor.execute('SELECT id FROM auth_user WHERE id=%d'%user_id) # Check to see if user in url exists
    data = cursor.fetchall()
    if len(data)==0: return HttpResponseNotFound("The user you requested does not exist\n")
    cursor.execute('SELECT t.key FROM authtoken_token t, auth_user u WHERE u.id = t.user_id AND u.id = "%d";'%user_id)
    user_token = cursor.fetchall()[0][0]
    if method == "POST":
        token = request.META["HTTP_AUTHORIZATION"].split("Token ")[1]
        if token != user_token: return HttpResponse('{"detail":"Authentication credentials were not provided."}',status=401) # Incorrect or missing token
        p = request.POST
        while True:
            post_id = rand(2**63)
            cursor.execute("SELECT post_id FROM posts WHERE post_id=%d;" % post_id)
            data = cursor.fetchall()
            if len(data) == 0 : break
        
        try: image = p["image"] # image is an optional param!
        except MultiValueDictKeyError: image = '0'

        try: # if all mandatory fields are passed
            if not validate_int(p): return HttpResponseBadRequest("Error: you have submitted non integer values to integer fields.")
            cursor.execute(ADD_QUERY, (post_id,user_id,p["title"],p["description"],p["markdown"],p["content"],sqlite3.Binary(bytes(image,encoding="utf-8")),str(datetime.now())))
            conn.commit()
            resp = "Successfully created post: %d\n" % post_id
        except MultiValueDictKeyError:
            return HttpResponseBadRequest("Failed to create post:\nInvalid parameters\n")

        # Modify the author privacy table in the database
        if "priv_author" in p.keys() or "priv_author[]" in p.keys():
            if"priv_author" in p.keys(): private_authors = p.getlist("priv_author")
            else: private_authors = p.getlist("priv_author[]")
            for pa in private_authors:
                cursor.execute("SELECT id from auth_user WHERE id = ?",(pa,))
                data = cursor.fetchall()
                if len(data) == 0: return HttpResponseNotFound("One or more user ids entered into the author privacy field are not valid user ids.")
            for pa in private_authors:
                cursor.execute(PRIV_ADD_QUERY, (post_id, pa))
                conn.commit()
        
    elif method == "GET":
        cursor.execute("SELECT * FROM posts WHERE user_id=%d;" % user_id)
        data = cursor.fetchall()
        resp = make_post_list(data,request.user.id)
    else:
        conn.close()
        return HttpResponseBadRequest("Error: invalid method used\n")
    conn.close()
    agent = request.META["HTTP_USER_AGENT"]
    if "Mozilla" in agent or "Chrome" in agent or "Edge" in agent or "Safari" in agent: # is the agent a browser? If yes, show html, if no, show regular post list
        with open(FILEPATH+"static/allposts.js","r") as f: script = f.read() % (user_token)
        if method == "GET": resp = make_post_html(data,user_id,canedit=True)
        # true_auth: is user logged in, and are they viewing their own posts? (determines if they can create a new post or not)
        return render(request,'allposts.html',{'post_list':resp,'true_auth':(request.user.is_authenticated and request.user.id == user_id),'postscript':script})
    else: return HttpResponse(resp)

#like a post
@api_view(['POST'])
def likepost(request, user_id, post_id):
    resp = ""
    conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM postlikes WHERE from_user = %d AND post_id = %d'% (user_id,post_id))
    data = cursor.fetchall()
    # if post has already been liked
    if len(data) > 0:
        return HttpResponse("Post already liked")
    else:
        like_id = rand(2**31)
        cursor.execute('INSERT INTO postlikes VALUES(%d, %d, %d, %d);'% (like_id, request.user.id, user_id, post_id))
        conn.commit()
        return HttpResponse("Post liked successfully")

#get a list of likes from other authors on the post id
@api_view(['GET'])
def likes(request, user_id, post_id):
    conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM postlikes l, auth_user u WHERE l.post_id=%d AND l.from_user = u.id;'%post_id)
    data = cursor.fetchall()
    author_list = []
    for d in data:
        author = d[0]
        author_list.append(author)
    num_likes = len(author_list)
    return render(request, "likes.html", {"author_list":author_list,"num_likes":num_likes})

#get a list of posts and comments that the author has liked
@api_view(['GET'])
def liked(request,user_id):
    conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
    cursor = conn.cursor()
    cursor.execute('SELECT post_id FROM postlikes WHERE from_user=%d;'%(user_id))
    data = cursor.fetchall()
    liked_posts_list = []
    for id in data:
        post_id = id[0]
        liked_posts_list.append(post_id)
    # cursor.execute('SELECT * FROM commentlikes WHERE from_id=%d;'%user_id)
    # data = cursor.fetchall()

    return render(request, "liked.html", {"liked_posts_list":liked_posts_list})

# def comment(request, user_id, post_id):
#     if request.method == "POST":

# #get a list of likes from other authors on the post id's comment id
# @api_view(['GET'])
# def commlikes(request):
#     method = request.META["REQUEST_METHOD"]
#     conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
#     cursor = conn.cursor()
#     cursor.execute('SELECT from_id FROM likes WHERE id=%d AND comm;'%post_id)
#     data = cursor.fetchall()

#     return HttpResponse("why")

# @api_view(['GET','POST','DELETE'])
# def inbox(request):
#     ADD_LIKE_QUERY = "INSERT INTO likes VALUES (?,?,?,?);"

#     method = request.META["REQUEST_METHOD"]
#     conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
#     cursor = conn.cursor()

#     if method  == "GET":
#         #Get a list of posts sent to author id
#     elif method == "POST":
#         if request.type == "post":
#             #TODO add post to author's inbox
#         elif request.type == "follow":
#             #TODO add follow to author's inbox
#         elif request.type == "like":
#             #TODO add like to author's inbox
#             cursor.execute('SELECT id FROM auth_user WHERE id=%d'%user_id)
#             data = cursor.fetchall()
#             if len(data) == 0:
#                 return HttpResponseNotFound("The user you requested does not exist\n")
#             cursor.execute(ADD_LIKE_QUERY, (from_user, user_id, post_id, comment_id)
            
#         else:
#             return HttpResponseNotFound("This type of object does not exist\n")
#     else:
#         #TODO clear the inbox

def search_user(request, *args, **kwargs):
    context = {}
    noresult = False
    if request.method == "GET":
        search_query = request.GET.get("q")
        if len(search_query) > 0:
            accounts = []
            conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM authtoken_token t, auth_user u WHERE u.username LIKE ?', ('{}%'.format(search_query),))
            duplicate = []
            try:
                data = cursor.fetchall()
                Author = get_user_model()
                account = Author.objects.filter(username = search_query)
                
            except IndexError: # No token exists, must create a new one!
                noresult = True 
            user = request.user

            # if not noresult:
            #     if user.is_authenticated:
            #         auth_user_friend_list = FriendList.objects.get( user = user )
            #         for user in data:
            #             if(user[3] not in duplicate):
            #                 accounts.append((user,auth_user_friend_list.is_mutual_friend(account)))
            #                 duplicate.append(user[3])
            #     else:
            #         for user in data:
            #             if(user[3] not in duplicate):
            #                 accounts.append((user,False))
            #                 duplicate.append(user[3])
            if not noresult:
                for user in data:
                    if(user[3] not in duplicate):
                        accounts.append((user,False))
                        duplicate.append(user[3])


            context['searchResult'] = accounts
            
    conn.close()
    return render(request,"search_user.html",context)
@api_view(['GET','POST'])
def account_view(request, *args, **kwargs):


    context = {}
    user_id = kwargs.get("user_id")
    conn = sqlite3.connect(FILEPATH+"../db.sqlite3")

    # Receive request method from profile page. One possibility is having to change git username and user
    method = request.META["REQUEST_METHOD"]
    if method == "POST":
        data = request.POST
        # print(data["git_url"])
        from firstapp.models import Author
        author = Author.objects.get(userid = user_id)
        author.github = data["git_url"]
        author.github_username = data["git_username"]
        author.save()


    cursor = conn.cursor()
    print("*****************")
    print(user_id)
    cursor.execute('SELECT * FROM authtoken_token t, auth_user u WHERE u.id = "%s";' % user_id)

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

