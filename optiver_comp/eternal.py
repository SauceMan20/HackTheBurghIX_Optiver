import subprocess
import os
import time
from optibook.synchronous_client import Exchange

while True:
    absolute_path = os.getcwd()
    subprocess.run(["python3", absolute_path + "/esg_trading/main_model.py"])
    