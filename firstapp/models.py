from django.db import models
from django.contrib.auth.models import User




# Create your models here.
class Author(models.Model):
    username = models.CharField(max_length=20)
    #password = models.CharField(max_length=20)
    github = models.URLField(blank=True) # Github link
    host = models.TextField(max_length=500, blank=True)
    authorized = models.BooleanField(default=True) # Whether they are allowed to log in
    userid = models.PositiveIntegerField(default=0) # Good for finding their URL in posts
    email = models.EmailField(default="example@gmail.com")
    name = models.CharField(max_length=20,default="testname") # First and last name
    def __str__(self):
        return self.user
class Setting(models.Model):
  # Contains variables for global settings
  # Should be a singleton setting in Admin. If not set/initialized in admin, error is thrown when trying to sign up.
  UsersNeedAuthentication = models.BooleanField(default=False)
  def __str__(self):
    return "Settings"
class PublicImages(models.Model):
  name = models.CharField(max_length=50)
  img = models.ImageField(upload_to='image/')