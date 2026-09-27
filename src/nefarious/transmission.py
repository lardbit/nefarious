import transmission_rpc
from nefarious.models import NefariousSettings


def get_transmission_client(nefarious_settings: NefariousSettings):
    return transmission_rpc.Client(
        host=nefarious_settings.transmission_host,
        port=nefarious_settings.transmission_port,
        username=nefarious_settings.transmission_user,
        password=nefarious_settings.transmission_pass,
        timeout=20,
    )
