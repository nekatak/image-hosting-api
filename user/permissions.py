from rest_framework import permissions


class HasPlan(permissions.BasePermission):
    message = 'You must have a Plan to perform this action'

    def has_permission(self, request, view):
        if request.user.plan:
            return True

        return False
