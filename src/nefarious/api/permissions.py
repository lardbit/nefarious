from rest_framework.permissions import SAFE_METHODS, IsAuthenticated


class IsAuthenticatedDjangoObjectUser(IsAuthenticated):
    """
    User must be authenticated and updating object they "own"
    """

    def has_object_permission(self, request, view, obj):

        # update operation, not staff, and the requesting user differs from the object's user
        if request.method not in SAFE_METHODS:
            if not request.user.is_staff and getattr(obj, 'user', None) and request.user != obj.user:
                return False

        return super().has_object_permission(request, view, obj)
