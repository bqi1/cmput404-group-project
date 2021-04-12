from django.urls import path
from . import views
from firstapp.views import(
	account_view)
app_name = 'firstapp'
urlpatterns = [
	path('<int:user_id>/',account_view,name = "view"),
	path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),
    path('login/', views.login, name='login'),
    path('homepage/', views.homepage, name='home'),
    path('author/<str:user_id>/posts/<int:post_id>',views.post,name='post'),
    path('author/<str:user_id>/posts/', views.allposts, name='allposts'),
    # path('author/<int:user_id>/inbox', views.inbox, name='inbox'),
    path('author/<str:user_id>/posts/<int:post_id>/likes/', views.postlikes, name='postlikes'),
    path('author/<str:user_id>/posts/<int:post_id>/likepost/', views.likepost, name='likepost'),
    path('author/<str:user_id>/posts/<int:post_id>/likecomment/', views.like_comment, name='likecomment'),
    path('author/<str:user_id>/liked/', views.liked, name='liked'),
    path('author/<str:user_id>', views.account, name='account'),

    path('author/<str:user_id>/posts/<int:post_id>/commentpost/',views.commentpost,name='commentpost'),
    path('author/<str:user_id>/posts/<int:post_id>/comments/',views.viewComments,name='viewComments'),

    path('posts/', views.publicposts,name='publicposts'),
    path('author/<str:user_id>/inbox', views.inbox,name='inbox'),
    path('like',views.likeAHomePagePost,name="likeAPost"),
    path('comment',views.commentAHomePagePost,name="commentAPost"),
    path('author/<str:user_id>/posts/<int:post_id>/comments/<str:comment_id>',views.viewComment,name='viewComment'),
    path('author/<str:user_id>/posts/<int:post_id>/comment',views.makeComment,name='makeComment'),
    path('publicshare',views.sharePublicPost),
]
