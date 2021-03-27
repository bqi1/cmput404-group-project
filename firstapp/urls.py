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
    path('author/<str:user_id>/posts/<int:post_id>',views.post,name='post'),
    path('author/<str:user_id>/posts/', views.allposts, name='allposts'),
    # path('author/<int:user_id>/inbox', views.inbox, name='inbox'),
    path('author/<str:user_id>/posts/<int:post_id>/likes/', views.likes, name='likes'),
    path('author/<str:user_id>/posts/<int:post_id>/likepost/', views.likepost, name='likepost'),
    path('author/<str:user_id>/liked/', views.liked, name='liked'),
    path('author/<str:user_id>', views.account, name='account'),
    # path('author/<int:user_id>/posts/<int:post_id>/comments/<int:comment_id>/likes/', views.commlikes, name='commlikes')
]
