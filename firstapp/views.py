from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def index(reqeuest):
    return HttpResponse("Hello, this is our first web app")
