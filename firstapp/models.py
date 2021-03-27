from django.db import models
from django.contrib.auth.models import User
import uuid




# Create your models here.
class Author(models.Model):
    type = "author"
    username = models.CharField(max_length=20)
    github = models.URLField(blank=True) # Github link
    github_username = models.TextField(max_length=20,blank=True)
    host = models.TextField(max_length=500, blank=True)
    authorized = models.BooleanField(default=True) # Whether they are allowed to log in
    userid = models.PositiveIntegerField(default=0) # Good for finding their URL in posts
    email = models.EmailField(default="example@gmail.com")
    name = models.CharField(max_length=20,default="testname") # First and last name
    consistent_id = models.TextField(primary_key=True,max_length=20,blank=True)

    def __str__(self):
        return self.username

class Post(models.Model):
  type = "post"
  post_id = models.PositiveIntegerField(primary_key=True, default=0)
  user_id = models.TextField(max_length=20,blank=True)
  title = models.CharField(max_length=20,default="")
  description = models.CharField(max_length=30,default="")
  markdown = models.BooleanField(default=False)
  content = models.TextField(max_length=500,blank=True)
  image = models.BinaryField(default=b"")
  privfriends = models.BooleanField(default = False)
  tstamp = models.CharField(max_length=50,default="")

class Author_Privacy(models.Model):
  type = "author_privacy"
  post_id = models.PositiveIntegerField(default=0)
  models.TextField(max_length=20,blank=True)

# class PostLikes(models.Model):
#   post = models.ForeignKey(Post, on_delete=models.CASCADE)
#   from_user = models.IntegerField()

# class Comments(models.Model):
#   post = models.ForeignKey(Post, on_delete=models.CASCADE)

# class CommentLikes(models.Model):
#   comment = models.ForeignKey(comment, on_delete=models.CASCADE)
#   from_user = models.IntegerField()

class Setting(models.Model):
  # Contains variables for global settings
  # Should be a singleton setting in Admin. If not set/initialized in admin, error is thrown when trying to sign up.
  UsersNeedAuthentication = models.BooleanField(default=False)
  def __str__(self):
    return "Settings"
class PublicImage(models.Model): # Host images to a folder in server. Accessible in server admin
  # Followed tutorial by Will Vincent at 2021-03-05 at https://learndjango.com/tutorials/django-file-and-image-uploads-tutorial
  title = models.TextField()
  image = models.ImageField(upload_to='images/')
  def __str__(self):
    return self.title