#!/bin/sh
set -e

while true; do
  python /app/checker.py
  sleep 60
done
