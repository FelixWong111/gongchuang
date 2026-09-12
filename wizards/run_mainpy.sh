#!/bin/bash

export PYTHONPATH="/home/wusie/Logistic_Robot2025"
echo ${PYTHONPATH}

cd /home/wusie/Logistic_Robot2025

sudo /home/wusie/miniforge3/envs/computer_vision/bin/python proj/main.py

cd -