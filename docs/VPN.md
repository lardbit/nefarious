# VPN 

To secure Transmission and Jackett traffic with a VPN you must use the separate `docker-compose.transmission-vpn.yml` file and populate the `.env` with your
VPN provider's details.

The documentation for supported providers and additional configuration can be found at: [docker-transmission-openvpn](https://haugene.github.io/docker-transmission-openvpn/).

All docker-compose commands must specify the `docker-compose.transmission-vpn.yml` file explicitly.

For example, to bring up all the services, you'd run:

    docker-compose -f docker-compose.transmission-vpn.yml up -d

**NOTE**: You must also define the *jackett* host described in [Part 2](../README.md#part-2) as `transmission` vs `jackett` since the transmission service is also the VPN.

## IPv6

For [some VPNs](https://haugene.github.io/docker-transmission-openvpn/provider-specific) IPv6 must be **enabled**. To enable it, set `VPN_IPV6_DISABLED=0` in your `.env` file.

## Port Forwarding

If you want to use Transmission in Active Mode your VPN provider must support [Port Forwarding](https://haugene.github.io/docker-transmission-openvpn/building-blocks/#starting_transmission). For some VPN providers it will be enabled automatically. For others you manually need to configure the Peer Port using the transmission user interface. 
