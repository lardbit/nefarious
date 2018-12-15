from rest_framework.authtoken.views import ObtainAuthToken


class ObtainAuthToken(ObtainAuthToken):
    """
    Overridden to not require any authentication classes (ie. csrf).
    Helpful on the auth/login url
    """
    authentication_classes = ()
