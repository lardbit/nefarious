import os
from django.conf import settings
from django.http import HttpResponse, HttpResponseNotFound


def view_logs(request, log_type: str):
    file_path = settings.NEFARIOUS_LOG_FILE_BACKGROUND if log_type == 'background' else settings.NEFARIOUS_LOG_FILE_FOREGROUND
    if os.path.exists(file_path):
        with open(file_path, 'r') as fh:
            return HttpResponse(fh.read(), content_type='text/plain')
    return HttpResponseNotFound('Log file not found: {}'.format(file_path))
