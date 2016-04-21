#!/bin/bash
set -e

rm -rf payload
mkdir -p payload
bundle exec ruby generate.rb

rm -rf dist
mkdir -p dist
tar --create --file=dist/primary.tar   payload/primary
tar --create --file=dist/secondary.tar payload/secondary
tar -tvf dist/primary.tar
tar -tvf dist/secondary.tar

scp dist/primary.tar vagrant@192.168.33.10:payload.tar
scp dist/secondary.tar vagrant@192.168.33.11:payload.tar
scp dist/secondary.tar vagrant@192.168.33.12:payload.tar

sup vagrant deploy
