import logging
from rest_framework import permissions

logger = logging.getLogger('filesharing')

class IsPhotographerOrRetoucher(permissions.BasePermission):
    def has_permission(self, request, view):
        is_authenticated = request.user.is_authenticated
        role = request.user.role if is_authenticated else 'none'
        email = request.user.email if is_authenticated else 'anonymous'
        logger.debug(f"Checking permission for user {email}, role: {role}, authenticated: {is_authenticated}")
        return is_authenticated and role in ['photographer', 'retoucher']