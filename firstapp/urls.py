from django.urls import path
from . import views

app_name = 'firstapp'

urlpatterns = [
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('homepage/', views.homepage, name='home'),
    path('author/<int:user_id>/posts/<int:post_id>',views.post,name='post'), # Only one user for now: user id 12345
    path('author/<int:user_id>/posts/', views.allposts, name='allposts'),
    # path('author/<int:user_id>/inbox', views.inbox, name='inbox'),
    path('author/<int:user_id>/posts/<int:post_id>/likes/', views.likes, name='likes'),
    path('author/<int:user_id>/posts/<int:post_id>/likepost/', views.likepost, name='likepost'),
    path('author/<int:user_id>/liked/', views.liked, name='liked'),
    # path('author/<int:user_id>/posts/<int:post_id>/comments/<int:comment_id>/likes/', views.commlikes, name='commlikes')
]
