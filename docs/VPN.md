# VPN 

To secure Transmission and Jackett traffic with a VPN you must use the separate `docker-compose.transmission-vpn.yml` file and populate the `.env` with your
VPN provider's details.

The documentation for supported providers and additional configuration can be found at: [docker-transmission-openvpn](https://haugene.github.io/docker-transmission-openvpn/).

All docker-compose commands must specify the `docker-compose.transmission-vpn.yml` file explicitly.

For example, to bring up all the services, you'd run:

    docker-compose -f docker-compose.transmission-vpn.yml up -d

**NOTE**: You must also define the *jackett* host described in [Part 2](../README.md#part-2) as `transmission` vs `jackett` since the transmission service is also the VPN.
