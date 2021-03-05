from django.urls import path
from . import views

app_name = 'firstapp'

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('homepage/', views.homepage, name='home'),
    path('author/<int:user_id>/posts/<int:post_id>',views.post,name='post'),
    path('author/<int:user_id>/posts/',views.allposts,name='allposts')
]
