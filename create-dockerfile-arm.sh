#!/bin/bash

#
# From the main Dockerfile:
# - swap the FROM image
# - execute resin's cross build instructions to emulate an architecture
#

DOCKER_OUTPUT=Dockerfile-armv7

# https://docs.resin.io/reference/base-images/base-images/
RESIN_IMAGE=resin/armv7hf-ubuntu

sed -E "s_^FROM\s*(.*)_FROM ${RESIN_IMAGE}_" Dockerfile > ${DOCKER_OUTPUT}
sed -i -E "s_^#@@cross-build-(start|end)@@\$_RUN [ \"cross-build-\1\" ]_" ${DOCKER_OUTPUT}
