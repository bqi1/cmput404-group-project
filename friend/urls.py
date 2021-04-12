from django.urls import path

from friend.views import(
	send_friend_request,
	request_view,
	accept_friend_request,
	friends_list_view,
	following_list_view,
	follower_list_view,
	send_following_request
)

app_name = 'friend'

urlpatterns = [
	path('list/<user_id>', friends_list_view, name='list'),
	path('followinglist/<user_id>', following_list_view, name='followinglist'),
	path('followerlist/<user_id>', follower_list_view, name='followerlist'),
    path('friend_request/', send_friend_request, name='friend-request'),
    path('friend_requests/<user_id>/', request_view, name='friend-requests'),
    path('friend_request_accept/<friend_request_id>/', accept_friend_request, name='friend-request-accept'),
    path('follow_request/<following_request_id>/', send_following_request, name='send_following_request'),

    ]
