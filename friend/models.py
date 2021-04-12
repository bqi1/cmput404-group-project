from django.db import models
from django.conf import settings 
from django.utils import timezone 

# Create your models here.


class FriendShip(models.Model):
	friend_a = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="friend_a_set", on_delete=models.CASCADE,blank=True, null=True)
	friend_b = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="friend_b_set", on_delete=models.CASCADE, blank=True, null=True)
	def __str__(self):
		return '%s %s' % (self.friend_a, self.friend_b)



class Follow(models.Model):
	follower = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="follower_set", on_delete=models.CASCADE, blank=True, null=True)
	receiver = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="receiver_set", on_delete=models.CASCADE, blank=True, null=True)
	ignored = models.BooleanField(default=False)
	def __str__(self):
		return '%s %s' % (self.follower, self.receiver)
	def get_following(self):
		return receiver


class FollowingList(models.Model):
	follower = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete= models.CASCADE,related_name="follower")
	following = models.ManyToManyField(settings.AUTH_USER_MODEL, blank = True, related_name="following")
	
	def __str__ (self):
		return self.follower.username
	def FollowAdd(self, account):
		if not account in self.following.all():
			self.following.add(account)
			self.save()
	def FollowDelete(self,account):
		if account in self.following.all():
			self.following.remove(account)
			self.save()

	def unFollow(self,removee):
		remover_friends_list = self # people start to unfriend 

		remover_friends_list.FollowDelete(removee)
		following_list = FollowingList.objects.get(user = removee)
		following_list.FollowDelete(self.user)
	def is_mutual_following(self, follow):
		"""
		Is this a friend?
		"""
		if follow in self.following.all():
			return True
		return False




class FriendList(models.Model):
	user = models.OneToOneField(settings.AUTH_USER_MODEL,on_delete= models.CASCADE,related_name="user")
	friends = models.ManyToManyField(settings.AUTH_USER_MODEL, blank = True, related_name="friends")
	
	def __str__ (self):
		return self.user.username
	def FriendAdd(self, account):
		if not account in self.friends.all():
			self.friends.add(account)
			self.save()
	def FriendDelete(self,account):
		if account in self.friends.all():
			self.friends.remove(account)
			self.save()

	def unfriend(self,removee):
		remover_friends_list = self # people start to unfriend 

		remover_friends_list.FriendDelete(removee)
		friends_list = FriendList.objects.get(user = removee)
		friends_list.FriendDelete(self.user)
	def is_mutual_friend(self, friend):
		"""
		Is this a friend?
		"""
		if friend in self.friends.all():
			return True
		return False
class FriendRequest(models.Model):
	sender = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete = models.CASCADE, related_name = "sender")
	receiver = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete = models.CASCADE, related_name = "receiver")
	is_active = models.BooleanField(blank = True, null = False, default = True)
	timestamp = models.DateTimeField(auto_now_add = True)
	def __str__(self):
		return self.sender.username
	def accept( self):
		receiver_friend_list = FriendList.objects.get(user=self.receiver)
		if receiver_friend_list:
			receiver_friend_list.FriendAdd(self.sender)
			sender_friend_list = FriendList.objects.get(user = self.sender)
			if sender_friend_list:
				sender_friend_list.FriendAdd(self.receiver)
				self.is_active = False
				self.save()
	def decline(self):
		self.is_active = False
		self.save()
	def cancel(self):
		self.is_active = False
		self.save()




