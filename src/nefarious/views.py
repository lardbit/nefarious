import os
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound


def view_logs(request):
    file_path = settings.NEFARIOUS_LOG_FILE
    if os.path.exists(file_path):
        with open(file_path, 'r') as fh:
            response = HttpResponse(fh.read(), content_type="text/plain")
            response['Content-Disposition'] = 'inline'
            return response
    return HttpResponseNotFound('Log file not found: {}'.format(file_path))
