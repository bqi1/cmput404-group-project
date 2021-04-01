from django.contrib import admin

from .models import Author, Setting, PublicImage, Post

# Register your models here.
admin.site.register(Author)
admin.site.register(Setting)
admin.site.register(PublicImage)
admin.site.register(Post)