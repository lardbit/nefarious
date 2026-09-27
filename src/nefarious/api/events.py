import redis.asyncio as aioredis
from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
from rest_framework.authtoken.models import Token

from nefarious.events import EVENTS_CHANNEL

# heartbeat interval (seconds) to keep the connection alive through proxies
HEARTBEAT_SECONDS = 15.0


async def media_events(request):
    # EventSource cannot send the Authorization header, so the token is passed as a query parameter
    token_key = request.GET.get('token')
    if not token_key:
        return HttpResponse(status=401)

    try:
        await Token.objects.aget(key=token_key)
    except Token.DoesNotExist:
        return HttpResponse(status=401)

    redis_client = aioredis.from_url(
        'redis://{}:{}/0'.format(settings.REDIS_HOST, settings.REDIS_PORT))
    pubsub = redis_client.pubsub()
    await pubsub.subscribe(EVENTS_CHANNEL)

    async def event_stream():
        try:
            yield ': connected\n\n'
            while True:
                message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=HEARTBEAT_SECONDS)
                if message and message['type'] == 'message':
                    payload = message['data']
                    if isinstance(payload, bytes):
                        payload = payload.decode()
                    yield 'data: {}\n\n'.format(payload)
                else:
                    # keep-alive heartbeat
                    yield ': ping\n\n'
        finally:
            await pubsub.unsubscribe(EVENTS_CHANNEL)
            await pubsub.aclose()

    response = StreamingHttpResponse(event_stream(), content_type='text/event-stream')
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response
