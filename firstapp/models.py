from django.db import models
#from django.contrib.auth.models import AbstractUser




# Create your models here.
class UserCreation(models.Model):

    user = models.CharField(max_length=20)
    #password = models.CharField(max_length=20)
    github = models.URLField(blank=True)
    host = models.TextField(max_length=500, blank=True)
    authorized = models.BooleanField(default=True)
    userid = models.PositiveIntegerField()
    email = models.EmailField()
    name = models.CharField(max_length=20)
    
  #  profile = models.ImageField(upload_to='profile', blank=True)
    
    def __str__(self):
        return self.user
class Setting(models.Model):
  UsersNeedAuthentication = models.BooleanField(default=False)
  def __str__(self):
    return "Settings"