from rest_framework.permissions import BasePermission


class IsAuthorOrModerator(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return (
            request.user == obj.author
            or request.user.is_moderator
            or request.user.is_admin
        )


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin
