from django.db import models
from django.contrib.auth.models import User
import uuid
from django.utils import timezone
from django.conf import settings


# Create your models here.
class Author(models.Model):
    type = "author"
    username = models.CharField(max_length=20, null=False)
    github = models.URLField(blank=True) # Github link
    github_username = models.TextField(max_length=20,blank=True)
    host = models.TextField(max_length=500, blank=True)
    authorized = models.BooleanField(default=True) # Whether they are allowed to log in
    userid = models.PositiveIntegerField(default=0,null=True) # Good for finding their URL in posts
    email = models.EmailField(default="example@gmail.com")
    name = models.CharField(max_length=20,default="testname") # First and last name
    consistent_id = models.TextField(primary_key=True,blank=True)
    api_token = models.TextField(max_length=50,blank=True)

    def __str__(self):
        return self.username

class Setting(models.Model):
  # Contains variables for global settings
  # Should be a singleton setting in Admin. If not set/initialized in admin, error is thrown when trying to sign up.
  usersneedauthentication = models.BooleanField(default=False)
  def __str__(self):
    return "Settings"
class PublicImage(models.Model): # Host images to a folder in server. Accessible in server admin
  # Followed tutorial by Will Vincent at 2021-03-05 at https://learndjango.com/tutorials/django-file-and-image-uploads-tutorial
  title = models.TextField()
  image = models.ImageField(upload_to='images/')
  def __str__(self):
    return self.title

class Post(models.Model):
  type = "post"
  id = models.TextField(blank=True)
  post_id = models.PositiveIntegerField(primary_key=True, default=0)
  user_id = models.TextField(blank=True)
  title = models.CharField(max_length=40,default="")
  description = models.CharField(max_length=40,default="")
  markdown = models.BooleanField(default=False)
  content = models.TextField(max_length=500,blank=True)
  image = models.BinaryField(default=b"")
  privfriends = models.BooleanField(default = False)
  unlisted = models.BooleanField(default = False)
  published = models.CharField(max_length=50,default="")
  source = models.TextField(blank=True)
  origin = models.TextField(blank=True)

class Author_Privacy(models.Model):
  type = "author_privacy"
  post_id = models.PositiveIntegerField(default=0)
  user_id = models.TextField(max_length=20,blank=True)

class Category(models.Model):
  type = "category"
  post_id = models.PositiveIntegerField(default=0)
  tag = models.TextField(max_length=20,blank=True) # The actual content of the category

class Comment(models.Model):
    # post = models.ForeignKey(Post, on_delete=models.CASCADE)
    post_id = models.TextField(blank=True, null=False)
    comment_id = models.TextField(primary_key=True,null=False)
    from_user = models.TextField(blank=True, null=True)
    to_user = models.TextField(blank=True, null=True)
    comment_text = models.TextField(null=False)
    published = models.CharField(max_length=50,default="")
    
    def __str__(self):
        return self.comment_text

class Like(models.Model):
  like_id = models.PositiveIntegerField(primary_key=True, blank=True, null=False)
  from_user = models.TextField()
  to_user = models.TextField(max_length=500,blank=True)
  object = models.TextField()

class Node(models.Model):
  hostserver = models.URLField(null=False)
  authusername = models.TextField(null=False)
  authpassword = models.TextField(null=False)
  def __str__(self):
    return self.hostserver
  
class Inbox(models.Model):
  type = models.TextField()
  author = models.TextField()
  items = models.JSONField(default=list)