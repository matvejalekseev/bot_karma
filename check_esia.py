from conf import ESIA_URL
import schedule
import time
import requests
from functions import esia_current_status, esia_status_add


def check_esia():
    try:
        r = requests.get(ESIA_URL)
        status = esia_current_status()
        if r.status_code == 200 and status == 0:
            esia_status_add(1)
        elif r.status_code != 200 and status == 1:
            esia_status_add(0)
    except:
        esia_status_add(0)


schedule.every(5).seconds.do(check_esia)


while True:
    schedule.run_pending()
    time.sleep(1)