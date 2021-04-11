from django.contrib import admin

from .models import Author, Setting, PublicImage, Post, Comment, Node, Like, Inbox

# Register your models here.
admin.site.register(Author)
admin.site.register(Setting)
admin.site.register(PublicImage)
admin.site.register(Post)
admin.site.register(Comment)
admin.site.register(Node)
admin.site.register(Like)
admin.site.register(Inbox)


