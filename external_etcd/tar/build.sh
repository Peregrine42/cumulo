#!/bin/bash
set -e

rm -rf payload
mkdir -p payload
bundle exec ruby generate.rb

rm -rf dist
mkdir -p dist
tar --create --file=dist/192.168.33.10.tar payload/192.168.33.10
tar --create --file=dist/192.168.33.11.tar payload/192.168.33.11
tar --create --file=dist/192.168.33.12.tar payload/192.168.33.12
tar -tvf dist/192.168.33.10.tar
tar -tvf dist/192.168.33.11.tar
tar -tvf dist/192.168.33.12.tar

scp dist/192.168.33.10.tar vagrant@192.168.33.10:payload.tar
scp dist/192.168.33.11.tar vagrant@192.168.33.11:payload.tar
scp dist/192.168.33.12.tar vagrant@192.168.33.12:payload.tar

sup vagrant deploy_stage_1 deploy_stage_2 deploy_stage_3
