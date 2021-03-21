from django.urls import path
from . import views
from firstapp.views import(
	account_view)
app_name = 'firstapp'
urlpatterns = [
	path('<user_id>/',account_view,name = "view"),
	path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('homepage/', views.homepage, name='home'),
    path('author/<int:user_id>/posts/<int:post_id>',views.post,name='post'),
    path('author/<int:user_id>/posts/', views.allposts, name='allposts'),
    # path('author/<int:user_id>/inbox', views.inbox, name='inbox'),
    path('author/<int:user_id>/posts/<int:post_id>/likes/', views.likes, name='likes'),
    path('author/<int:user_id>/posts/<int:post_id>/likepost/', views.likepost, name='likepost'),
    path('author/<int:user_id>/liked/', views.liked, name='liked'),
    path('author/<int:user_id>/posts/<int:post_id>/commentpost/',views.commentpost,name='commentpost'),
    path('author/<int:user_id>/posts/<int:post_id>/viewComments/',views.viewComments,name='viewComments'),
    path('author/<int:user_id>/posts/<int:post_id>/share/',views.postshare,name='postshare'),
    path('author/<int:user_id>/posts/check_share/', views.check_share, name='check_share'),
    # path('author/<int:user_id>/posts/<int:post_id>/comments/<int:comment_id>/likes/', views.commlikes, name='commlikes')
]
