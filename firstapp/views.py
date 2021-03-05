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



def validate_int(p,optional=[]):
    try:
        int(p["markdown"])
        for i in optional: int(i)
        return 1
    except ValueError: return 0

def make_post_html(data,user_id,canedit=False):
    resp = ""
    start = '<div class="post" style="border:solid;" ><p class="title">%s</p><p class="desc">%s</p></br><p class="content">%s</p></br>'
    endimage = '<img src="%s"/><span class="md" style="display:none" value="%s"></span></br>'+('<input type = "button" value="Edit" onclick="viewPost(\'{}\')">' if canedit else '')+'</div>'
    endnoimage = '<span class="md" style="display:none" value="%s"></span></br>'+('<input type = "button" value="Edit" onclick="viewPost(\'{}\')">' if canedit else '')+'</div>'

    conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
    cursor = conn.cursor()
    for d in data:
        cursor.execute('SELECT * FROM author_privacy WHERE post_id=%d'%d[0])
        priv = cursor.fetchall()
        image = str(d[-2],encoding="utf-8")
        content = d[5]
        if d[4]: # use markdown!
            md = Md()
            content = md.convert(content)
        starttag = start % (d[2],d[3],content)
        if len(priv) == 0 or user_id == d[1] :
            if image == '0': resp += starttag + endnoimage.format(d[0]) % (d[4],)
            else: resp += starttag + endimage.format(d[0]) % (image,d[4])
            resp += "</br>"
        else:
            show_post = False
            for p in priv:
                if p[1] == user_id:
                    show_post = True
                    break
            if show_post and user_id != None:
                if image == '0': resp += starttag + endnoimage.format(d[0]) % (d[4],)
                else: resp += starttag + endimage.format(d[0]) % (image,d[4])
                resp += "</br>"
    conn.close()
    return resp

def make_post_list(data,user_id):
    post_list = []
    conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
    cursor = conn.cursor()
    for d in data:
        # do not append if post is private
        # Do appear if post is private and author is not author of user
    
        cursor.execute('SELECT * FROM author_privacy WHERE post_id=%d'%d[0])
        priv = cursor.fetchall()
        post_dict = {
            "post_id":d[0],
            "user_id":d[1],
            "title":d[2],
            "description":d[3],
            "markdown?":d[4],
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
    cursor.execute('SELECT * FROM posts p WHERE p.post_id=%d'%(post_id,))
    data = cursor.fetchall()
    if len(data) > 0 and method == 'PUT': return HttpResponse("The post with id %d already exists! Maybe try POST?\n"%post_id,status=409)
    cursor.execute('SELECT t.key FROM authtoken_token t, auth_user u WHERE u.id = t.user_id AND u.id = "%d";'%user_id)
    user_token = cursor.fetchall()[0][0]

    if method == 'GET':
        resp = make_post_list(data,request.user.id)
    else:
        token = request.META["HTTP_AUTHORIZATION"].split("Token ")[1]
        if token != user_token: return HttpResponseForbidden("Invalid token for the requested user!\n")

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

            if "priv_author" in p.keys() or "priv_author[]" in p.keys():
                if "priv_author" in p.keys(): private_authors = p.getlist("priv_author")
                else: private_authors = p.getlist("priv_author[]")
                for pa in private_authors:
                    cursor.execute("SELECT id from auth_user WHERE id = ?",(pa,))
                    data = cursor.fetchall()
                    if len(data) == 0: return HttpResponseNotFound("One or more user ids entered into the author privacy field are not valid user ids.")
                cursor.execute("DELETE FROM author_privacy WHERE post_id=?",(post_id,))
                conn.commit()
                for pa in private_authors:
                    cursor.execute(PRIV_ADD_QUERY, (post_id, pa))
                    conn.commit()
            else:
                cursor.execute("DELETE FROM author_privacy WHERE post_id=?",(post_id,))
                conn.commit()

 
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
    if "Mozilla" in agent or "Chrome" in agent or "Edge" in agent or "Safari" in agent:
        if method == "GET": resp = make_post_html(data,request.user.id)
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
            if not validate_int(p): return HttpResponseBadRequest("Error: you have submitted non integer values to integer fields.")
            cursor.execute(ADD_QUERY, (post_id,user_id,p["title"],p["description"],p["markdown"],p["content"],sqlite3.Binary(bytes(image,encoding="utf-8")),str(datetime.now())))
            conn.commit()
            resp = "Successfully created post: %d\n" % post_id
        except MultiValueDictKeyError:
            return HttpResponseBadRequest("Failed to create post:\nInvalid parameters\n")

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
    if "Mozilla" in agent or "Chrome" in agent or "Edge" in agent or "Safari" in agent:
        with open(FILEPATH+"static/allposts.js","r") as f: script = f.read() % user_token
        if method == "GET": resp = make_post_html(data,request.user.id,canedit=(request.user.is_authenticated and request.user.id == user_id))
        return render(request,'allposts.html',{'post_list':resp,'true_auth':(request.user.is_authenticated and request.user.id == user_id),'postscript':script})
    else: return HttpResponse(resp)


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

            if not noresult:
                if user.is_authenticated:
                    auth_user_friend_list = FriendList.objects.get(user = user )
                    for user in data:
                        if(user[3] not in duplicate):
                            accounts.append((user,auth_user_friend_list.is_mutual_friend(account)))
                            duplicate.append(user[3])
                else:
                    for user in data:
                        if(user[3] not in duplicate):
                            accounts.append((user,False))
                            duplicate.append(user[3])
            context['searchResult'] = accounts
            
    conn.close()
    return render(request,"search_user.html",context)

def account_view(request, *args, **kwargs):
    context = {}
    user_id = kwargs.get("user_id")
    conn = sqlite3.connect(FILEPATH+"../db.sqlite3")
    cursor = conn.cursor()
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
        if user.is_authenticated and user != data[7]:
            is_self = False 
        elif not user.is_authenticated:
            is_self = False

        context['is_self'] =is_self
        context['is_friend'] = is_friend
        context['request_sent'] = request_sent
        context['friend_requests'] = friend_requests
        context['BASE_URL'] = settings.BASE_DIR

        return render(request,"profile.html",context)




