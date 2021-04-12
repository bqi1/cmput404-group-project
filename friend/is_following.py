from friend.models import Follow

def Following_Or_Not(sender, receiver):
	try:
		return Follow.objects.get(follower=sender, receiver=receiver)
	except Follow.DoesNotExist:
		return False