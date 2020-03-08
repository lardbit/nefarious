import os
from django.conf import settings
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.response import Response
from rest_framework.views import APIView


class ObtainAuthTokenView(ObtainAuthToken):
    """
    Overridden to not require any authentication classes (ie. csrf).
    Helpful on the auth/login url
    """
    authentication_classes = ()


class GitCommitView(APIView):
    def get(self, request):
        path = os.path.join(settings.BASE_DIR, '.commit')
        commit = None
        if os.path.exists(path):
            with open(path) as fh:
                commit = fh.read().strip()
        return Response({
            'commit': commit,
        })

