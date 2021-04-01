from django.contrib import admin

from .models import Author, Setting, PublicImage, Comment, Node

# Register your models here.
admin.site.register(Author)
admin.site.register(Setting)
admin.site.register(PublicImage)
admin.site.register(Comment)
admin.site.register(Node)
