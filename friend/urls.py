from django.urls import path

from friend.views import(
	send_friend_request,
	request_view,
	accept_friend_request,
	friends_list_view,
)

app_name = 'friend'

urlpatterns = [
	path('list/<user_id>', friends_list_view, name='list'),
    path('friend_request/', send_friend_request, name='friend-request'),
    path('friend_requests/<user_id>/', request_view, name='friend-requests'),
    path('friend_request_accept/<friend_request_id>/', accept_friend_request, name='friend-request-accept'),

    ]
