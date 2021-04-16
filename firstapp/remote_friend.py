import json 
import requests
import base64
from firstapp.models import Author
from django.contrib.auth import get_user_model
from random import randrange




def get_all_remote_user():
	base_id = randrange(30000,60000)
	#for group seven url only 
	print(base_id)
	request_url = 'https://iconicity-part2.herokuapp.com/author/'
	PARAMS = {'Authorization:':f"Basic {base64.b64encode('auth_user:authpass'.encode('ascii'))}"}
	r = requests.get(url=request_url, auth=("auth_user", "authpass"))
	remote_author_list = []
	if r.status_code == 200:
		response = r.content.decode("utf-8")
		author_data = json.loads(response)	
		try:
			print(author_data)
			for author in author_data:
				print(author)
				author_id = author["id"].split("/")[-1]
				author_name = author["displayName"]
				author_github = author["github"]
				# print(author_name)
				# print(author_github)
				Author2 = get_user_model()
				try:
					Author.objects.get(consistent_id = author_id)
				except:	
					Author2.objects.create(password = "********",username = author_name, id = base_id, is_staff = 0 )
					remote_author = Author.objects.create(host = f"https://iconicity-test-a.herokuapp.com/",authorized=False, username = author_name, github = author_github ,consistent_id = author_id, userid = base_id)
					print(remote_author)

					remote_author.save()
					remote_author_list.append(remote_author)
					base_id = 1 + base_id
					 
		except Exception as e :
			print("An error occcur, error message: " +str(e) )



def get_all_remote_user_2():
	base_id = randrange(30000,60000)
	#for group seven url only 
	request_url = 'https://social-distribution-t1.herokuapp.com/all-authors/'
	PARAMS = {'Authorization:':f"Basic {base64.b64encode('auth_user:authpass'.encode('ascii'))}"}
	r = requests.get(url=request_url, auth=("auth_user", "authpass"))
	remote_author_list = []
	if r.status_code == 200:
		response = r.content.decode("utf-8")
		author_data = json.loads(response)	
		print(author_data)
		try:
			for author in author_data:
				print(author)
				author_id = author["id"].split("/")
				author_name = author["displayName"]
				author_github = author["github"]
				# print(author_id)
				# print(author_name)
				# print(author_github)
				print("test1")
				Author2 = get_user_model()
				try:
					Author.objects.get(consistent_id = author_id)
				except:	
					print("test2")
					Author2.objects.create(password = "********",username = author_name, id = base_id, is_staff = 0 )
					print("test3")
					remote_author = Author.objects.create(host = f"https://iconicity-test-a.herokuapp.com/",authorized=False, username = author_name, github = author_github ,consistent_id = author_id, userid = base_id)
					print(remote_author)

					remote_author.save()
					remote_author_list.append(remote_author)
					base_id = 1 + base_id
					 
		except Exception as e :
			print("An error occcur, error message: " +str(e) )








