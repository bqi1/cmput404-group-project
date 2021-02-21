from django.urls import path
from . import views

app_name = 'firstapp'

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('homepage/', views.homepage, name='home'),
    path('author/12345/posts/<int:post_id>',views.post,name='post'), # Only one user for now: user id 12345
    path('author/12345/posts',views.allposts,name='allposts')
]
