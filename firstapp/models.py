from django.db import models
from django.contrib.auth.models import User




# Create your models here.
class UserCreation(models.Model):
    user = models.CharField(max_length=20)
    #password = models.CharField(max_length=20)
    github = models.URLField(blank=True)
    host = models.TextField(max_length=500, blank=True)
    authorized = models.BooleanField(default=True)
    userid = models.PositiveIntegerField(default=0)
    email = models.EmailField(default="example@gmail.com")
    name = models.CharField(max_length=20,default="testname")
    def __str__(self):
        return self.user
class Setting(models.Model):
  # Should be a singleton setting in Admin. If not set/initialized in admin, error is thrown when trying to sign up.
  UsersNeedAuthentication = models.BooleanField(default=False)
  def __str__(self):
    return "Settings"