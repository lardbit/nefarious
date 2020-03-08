import logging
from rest_framework.decorators import action
from rest_framework.response import Response

from nefarious.models import NefariousSettings, TorrentBlacklist, WatchMediaBase
from nefarious.tasks import send_websocket_message_task
from nefarious.transmission import get_transmission_client
from nefarious.utils import destroy_transmission_result
from nefarious import websocket


class UserReferenceViewSetMixin:
    """
    ViewSet Mixin which includes the "request" object in the serializer context
    """

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context


class BlacklistAndRetryMixin:
    """
    ViewSet Mixin which adds a torrent result to a "black list" and retries the media (i.e movie/tv) instance
    """

    def _watch_media_task(self, watch_media_id: int):
        """
        Child classes need to define how to queue the new task
        """
        raise NotImplementedError

    @action(['post'], detail=True, url_path='blacklist-auto-retry')
    def blacklist_auto_retry(self, request, pk):
        watch_media = self.get_object()
        nefarious_settings = NefariousSettings.get()

        # add to blacklist
        logging.info('Blacklisting {}'.format(watch_media.transmission_torrent_hash))
        TorrentBlacklist.objects.get_or_create(hash=watch_media.transmission_torrent_hash)

        # unset previous details
        del_transmission_torrent_hash = watch_media.transmission_torrent_hash
        watch_media.transmission_torrent_hash = None
        watch_media.collected = False
        watch_media.collected_date = None
        watch_media.save()

        # re-queue search
        self._watch_media_task(watch_media_id=watch_media.id)

        # remove torrent and delete data
        logging.info('Removing blacklisted torrent hash: {}'.format(del_transmission_torrent_hash))
        transmission_client = get_transmission_client(nefarious_settings=nefarious_settings)
        transmission_client.remove_torrent([del_transmission_torrent_hash], delete_data=True)

        return Response(self.serializer_class(watch_media).data)


class DestroyTransmissionResultMixin:
    """
    Deletes transmission result, including data, for any media that's been requested to be deleted
    """

    def perform_destroy(self, instance: WatchMediaBase):
        # delete transmission result, including data, if it still exists
        destroy_transmission_result(instance)
        super().perform_destroy(instance)


class WebSocketMediaMessageUpdatedMixin:

    def perform_create(self, serializer):
        # create instance first then send websocket message
        super().perform_create(serializer)
        # send websocket message media was updated
        media_type, data = websocket.get_media_type_and_serialized_watch_media(serializer.instance)
        send_websocket_message_task.delay(websocket.ACTION_UPDATED, media_type, data)

    def perform_destroy(self, instance):
        # send websocket message first then remove
        media_type, data = websocket.get_media_type_and_serialized_watch_media(instance)
        send_websocket_message_task.delay(websocket.ACTION_REMOVED, media_type, data)
        super().perform_destroy(instance)
