import requests
import re

from geopy import distance


def geo_distance(orgin, destination, units='km'):
    dist_ = distance.distance(origin, destination)
    return dist_.miles if units == 'miles' else dist_.km


def get_current_ip():
    _res = requests.get('http://checkip.dyndns.com/')
    if _res.status_code == 200:
        return re.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(_res.text).group(
            1)
    print('Failed to get Current IP')


if __name__ == '__main__':
    print(get_current_ip())
