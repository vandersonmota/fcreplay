from flask import request
import time

def convertLength(length):
    time_res = time.gmtime(length)
    res = time.strftime("%H:%M:%S", time_res)
    return(res)

def linkPath(url):
    if request.path != '/':
        return '../' + url
    else:
        return url