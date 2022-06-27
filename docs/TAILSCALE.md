# TAILSCALE

To share nefarious on your tailscale network you must use docker-compose.tailscale.yml and populate the `.env` with your tailscale information

All docker-compose commands must specify the `docker-compose.tailscale.yml` file explicitly.

For example, to bring up all the services, you'd run:

    docker-compose -f docker-compose.tailscale.yml up -d

The default command for tailscale up is as follows:
```
tailscale up --authkey="${TAILSCALE_AUTHKEY}" \
                    --advertise-routes ${TAILSCALE_ADVERTISE_ROUTE} \
                    --hostname ${TAILSCALE_HOSTNAME:-nefarious} \
                    --advertise-tags=${TAILSCALE_TAGS} \
                    --accept-routes \
                    --exit-node=${TAILSCALE_EXIT_NODE} \
                    --accept-dns \
                    --reset
```
The newest instructions will be available at [beardedtek-com/tailscale](https://github.com/BeardedTek-com/nefarious/TAILSCALE.md)

## IPv6

You may enable IPv6 by setting `TAILSCALE_IPV6_DISABLED=1` in your `.env` file.

## Usage

Once brought up and you bring up tailscale on your machine, you can access nefarious through the following addresses:

[Nefarious: http://192.168.254.1:8000](http://192.168.252.1:8000)
[Transmission: http://192.168.254.2:9091](http://192.168.252.2:9091)
[Jackett: http://192.168.254.3:9117](http://192.168.252.3:9117)

If these addresses conflict with your network(s) you can change them in the `.env` file