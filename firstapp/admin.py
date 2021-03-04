from django.contrib import admin

from .models import UserCreation, Setting

# Register your models here.
admin.site.register(UserCreation)
admin.site.register(Setting)
