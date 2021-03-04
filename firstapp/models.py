from django.db import models
#from django.contrib.auth.models import AbstractUser

# Create your models here.
class UserCreation(models.Model):

    user = models.CharField(max_length=20)
    #password = models.CharField(max_length=20)
    github = models.URLField(blank=True)
    host = models.TextField(max_length=500, blank=True)
    
  #  profile = models.ImageField(upload_to='profile', blank=True)
    
    def __str__(self):
        return self.user.username

# class PostLikes(models.Model):
#   post = models.ForeignKey(Post, on_delete=models.CASCADE)
#   from_user = models.IntegerField()

# class Comment(models.Model):
#   post = models.ForeignKey(Post, on_delete=models.CASCADE)

# class CommentLikes(models.Model):
#   comment = models.ForeignKey(comment, on_delete=models.CASCADE)
#   from_user = models.IntegerField()
