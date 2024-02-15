#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

flask db init

flask db migrate

flask db upgrade