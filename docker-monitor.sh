#!/bin/bash

cd "$(dirname "$0")"

container_name=$1
./docker-monitor.py --metric=memory_used --name=$container_name