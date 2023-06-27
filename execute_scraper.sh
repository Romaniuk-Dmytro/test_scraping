#!/bin/bash
echo 11 >> /home/droman/checkin.txt
cd /home/droman/workdir/test_scraping/
source venv/bin/activate
python3 sendMessage.py
echo 1 >> /home/droman/checkin.txt
