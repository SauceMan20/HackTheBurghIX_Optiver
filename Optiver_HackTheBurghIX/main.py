import subprocess
import os
import time
import logging

logging.getLogger('client').setLevel('ERROR')
logger = logging.getLogger(__name__)

while True:
    
    absolute_path = os.path.realpath(__file__).replace("main_model.py", "")
    logging.info(f"running {absolute_path}/legacy.py")
    subprocess.run(["python3", absolute_path + "/legacy.py"])
    
    time.sleep(1)