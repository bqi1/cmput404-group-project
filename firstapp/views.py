from django.shortcuts import render

# Create your views here.
def index(reqeuest):
    return HttpResponse("Hello, this is our first web app")
