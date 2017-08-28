#!/bin/bash

cd "$(dirname "$0")"

./docker-monitor.py --metric=docker_memory_used