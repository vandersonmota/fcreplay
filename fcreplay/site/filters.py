from flask import request
import time


def convertLength(length) -> str:
    time_res = time.gmtime(length)
    res = time.strftime("%H:%M:%S", time_res)
    return(res)
