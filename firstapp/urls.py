from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('author/12345/posts/<int:post_id>',views.post,name='post'), # Only one user for now: user id 12345
    path('author/12345/posts',views.allposts,name='allposts')
]
