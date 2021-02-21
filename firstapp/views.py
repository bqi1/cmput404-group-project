from django.shortcuts import render, HttpResponse, HttpResponseRedirect
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

# Create your views here.
def index(request):
    #if request.user.is_authenticated:
    return render(request, 'index.html')

def homepage(request):
    if request.user.is_authenticated:
        return render(request, 'homepage.html')
    
def signup(request):
    success = False
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save()
         #   new_username = form.cleaned_data.get('username')
          #  new_password = form.cleaned_data.get('password1')
           # user = authenticate(username = new_username, password=new_password)
        #    login(request, new_user)
        #    user.save()
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
            form = auth_login(request, user)
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

FILEPATH = os.path.dirname(os.path.abspath(__file__)) + "/"

POST_QUERY = "INSERT INTO posts VALUES (%d, %d, '%s', '%s', '%s', ?, '%s');"


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
