from django.db import models

# Create your models here.
class UserCreation(models.Model):

    user = models.CharField(max_length=20)
    #password = models.CharField(max_length=20)
    github = models.URLField(blank=True)
    host = models.TextField(max_length=500, blank=True)
    
  #  profile = models.ImageField(upload_to='profile', blank=True)
    
    def __str__(self):
        return self.user.username
