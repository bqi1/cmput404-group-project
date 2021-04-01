import json 
import requests
import base64
from firstapp.models import Author



def get_all_remote_user():
	#for group seven url only 
	request_url = 'https://iconicity-test-a.herokuapp.com/author/'
	PARAMS = {'Authorization:':f"Basic {base64.b64encode('auth_user:authpass'.encode('ascii'))}"}
	r = requests.get(url=request_url, auth=("auth_user", "authpass"))
	remote_author_list = []
	print(r.status_code)
	if r.status_code == 200:
		response = r.content.decode("utf-8")
		author_data = json.loads(response)
		try:
			for author in author_data:
				#print(author)
				author_id = author["uid"].split("/")[-1]
				author_name = author["display_name"]
				author_github = author["github"]
				# print(author_id)
				# print(author_name)
				# print(author_github)
				if Author.objects.get(consistent_id=author_id):
					return
				else:	
					remote_author = Author.objects.create(host = f"https://iconicity-test-a.herokuapp.com/",authorized=False, username = author_name, github = author_github ,consistent_id = author_id, userid = 1000)
					print(remote_author)
					remote_author.save()
					remote_author_list.append(remote_author)
				return 
		except Exception as e :
			print("An error occcur, error message: " + e)

def send_remote_friend_request(remote_user,local_user):
	pass




