#!/bin/bash

python3 -m venv venv
source venv/bin/activate
./main.py --username $1
