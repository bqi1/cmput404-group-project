from django.contrib import admin

from .models import Author, Setting, PublicImage

# Register your models here.
admin.site.register(Author)
admin.site.register(Setting)
admin.site.register(PublicImage)