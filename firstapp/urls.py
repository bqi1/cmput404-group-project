from django.urls import path
from . import views
from firstapp.views import(
	account_view)
app_name = 'firstapp'
urlpatterns = [
	path('<user_id>/',account_view,name = "view"),
]
