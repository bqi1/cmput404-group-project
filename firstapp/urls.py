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
    path('author/<int:user_id>/posts/',views.allposts,name='allposts')
]
