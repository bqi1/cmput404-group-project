"""c404_proj URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from firstapp import views as a_view
from firstapp.views import(
    search_user,
    )

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('firstapp.urls')),
    path('firstapp/', a_view.index, name='index'),
    path('firstapp/login/', a_view.login, name='login'),
    path('firstapp/signup/', a_view.signup, name='signup'),
    path('firstapp/index/', a_view.index, name='index'),
    path('firstapp/homepage/', a_view.homepage, name='home'),
    path('firstapp/search/', search_user, name = "search"),
    path('firstapp/',include('firstapp.urls',namespace = 'account')),
]
