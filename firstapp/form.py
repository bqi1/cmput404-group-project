from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import *
#from .models import User

class UserForm(UserCreationForm):

    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=20)
    last_name = forms.CharField(max_length=20)
    
    def __init__(self, *args, **kwargs):
        super(UserForm, self).__init__(*args, **kwargs)
        
        for field_number in self.fields:
            self.fields[field_number].help_text = None
            
    class Meta(UserCreationForm):
        model = User
        fields = ['email','username','first_name','last_name','password1', 'password2']
            
#https://stackoverflow.com/questions/13202845/removing-help-text-from-django-usercreateform
#for removing extra help texts
