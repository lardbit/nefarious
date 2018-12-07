import logging
from rest_framework.decorators import action
from rest_framework.response import Response

from nefarious.models import NefariousSettings, TorrentBlacklist
from nefarious.transmission import get_transmission_client


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
        nefarious_settings = NefariousSettings.singleton()

        # add to blacklist
        logging.info('Blacklisting {}'.format(watch_media.transmission_torrent_hash))
        TorrentBlacklist.objects.get_or_create(hash=watch_media.transmission_torrent_hash)

        # unset previous transmission details
        del_transmission_torrent_id = watch_media.transmission_torrent_id
        watch_media.transmission_torrent_id = None
        watch_media.transmission_torrent_hash = None
        watch_media.save()

        # re-queue search
        self._watch_media_task(watch_media_id=watch_media.id)

        # remove torrent and delete data
        logging.info('Removing blacklisted torrent id: {}'.format(del_transmission_torrent_id))
        transmission_client = get_transmission_client(nefarious_settings=nefarious_settings)
        transmission_client.remove_torrent([del_transmission_torrent_id], delete_data=True)

        return Response(self.serializer_class(watch_media).data)
