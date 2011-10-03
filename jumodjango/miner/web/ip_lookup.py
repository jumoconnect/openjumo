'''
Created on Jul 21, 2011

@author: al
'''

from miner.web import dstk

def ip_to_lat_lon(ip):
    if ip is None:
        return {}

    try:
        resp = dstk.ip2coordinates(ip)
    except Exception:
        return None

    if not resp.get(ip):
        return {}

    return resp[ip]
