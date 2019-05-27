import transmissionrpc
from nefarious.models import NefariousSettings


def get_transmission_client(nefarious_settings: NefariousSettings):
    return transmissionrpc.Client(
        address=nefarious_settings.transmission_host,
        port=nefarious_settings.transmission_port,
        user=nefarious_settings.transmission_user,
        password=nefarious_settings.transmission_pass,
        timeout=20,
    )
