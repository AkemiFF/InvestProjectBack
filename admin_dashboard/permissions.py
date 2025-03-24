# admin_dashboard/permissions.py
from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Permission pour autoriser uniquement les administrateurs
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_staff