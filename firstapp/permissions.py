# this code is based off of an answer from https://stackoverflow.com/questions/37642175/how-to-add-django-rest-framework-permissions-on-specific-method-only
from rest_framework import permissions


class EditPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == 'GET':
            return True
        else:
            return request.user and request.user.is_authenticated