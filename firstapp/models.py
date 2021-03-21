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
    consistent_id = models.TextField(primary_key=True,max_length=20,blank=True,editable=False)

    def __str__(self):
        return self.username

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

#class Post(models.Model):
 #   author = models.ForeignKey(Author, on_delete=models.CASCADE)
  #  posted_on = models.DateTimeField(auto_now=True)

class Comment(models.Model):
    #post = models.ForeignKey(Post, on_delete=models.CASCADE)
    comment_id = models.PositiveIntegerField(primary_key=True,null=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    comment_text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['created_date']
    
    def __str__(self):
        return self.comment_text

class Share(models.Model):
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="from+")
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="to+")
    is_share = models.BooleanField()
    
    def __str__(self):
        return self.from_user
