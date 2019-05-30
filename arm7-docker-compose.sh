#!/usr/bin/env bash

# Generates an arm version of the docker-compose.yml by replacing all images

cp docker-compose.yml docker-compose.arm.yml
sed -i "s/image:\ lardbit\/nefarious/image:\ lardbit\/nefarious:armv7/g" docker-compose.arm.yml
sed -i "s/image:\ linuxserver\/transmission/image:\ linuxserver\/transmission:arm32v7-latest/g" docker-compose.arm.yml
sed -i "s/image:\ linuxserver\/jackett/image:\ linuxserver\/jackett:arm32v7-latest/g" docker-compose.arm.yml
sed -i "s/image:\ redis/image:\ arm32v7\/redis/g" docker-compose.arm.yml
sed -i "s/image:\ v2tec\/watchtower/image:\ v2tec\/watchtower:armhf-latest/g" docker-compose.arm.yml

