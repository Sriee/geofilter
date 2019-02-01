import re
import requests
import functools

from math import radians, sin, cos, sqrt, atan2
from geopy import distance

ACCESS_KEY = ''


def validate(func):

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if kwargs:
            print("Received unexpected arguments dropping them.")

        if type(args[0]) is not tuple and type(args[1]) is not tuple:
            raise TypeError('Co-ordinates not in  format')

        for i_ in range(2):
            if not isinstance(tuple, args[i_]):
                raise TypeError('args[{}] is not of type \'(latitude, longitude)\''
                                .format(i_))

        return func((radians(args[0][0]), radians(args[0][1])),
                    (radians(args[1][0]), radians(args[1][1])))
    return wrapper


@validate
def geo_distance2(origin, destination):

    lat1, long1 = origin
    lat2, long2 = destination

    diff_lat, diff_long = (lat2 - lat1), (long2 - long1)

    _a = (sin(diff_lat / 2) * sin(diff_lat / 2) +
          cos(lat1) * cos(lat2) * sin(diff_long / 2) * sin(diff_long / 2))
    _c = 2 * atan2(sqrt(_a), sqrt(1 - _a))
    return 6371 * _c


def geo_distance(origin, destination, units='km'):
    dist_ = distance.distance(origin, destination)
    return dist_.miles if units == 'miles' else dist_.km


def get_current_ip():
    _res = requests.get('http://checkip.dyndns.com/')
    if _res.status_code == 200:
        return re.compile(r'Address: (\d+\.\d+\.\d+\.\d+)').search(_res.text).group(
            1)
    print('Failed to get Current IP')


def bulk_ip_lookup(ip_address, fields='main'):
    bulk_res = []
    for _ip in ip_address:
        _res = standard_ip_lookup(_ip, fields)
        bulk_res.append(_res if _res else {})
    return bulk_res


def standard_ip_lookup(ip_address, fields='main'):
    if isinstance(ip_address, list):
        ip_address = ','.join(ip_address)

    if isinstance(fields, list):
        fields = ','.join(fields)

    url = "http://api.ipstack.com/" + ip_address

    payload = {
        'access_key': ACCESS_KEY,
        'fields': fields,
        'language': 'en',
        'output': 'json'
    }

    response = requests.get(url, params=payload)
    if response.status_code == 200:

        _res = response.json()
        if 'success' in _res and _res['success'] is False:
            print('IP Stack Error:', _res['error']['code'], _res['error']['info'])
            return None

        print('Standard IP lookup success!')
        return response.json()

    print('Standard IP Lookup failed:', response.status_code, response.text)


if __name__ == '__main__':
    print(get_current_ip())
    r = standard_ip_lookup('134.201.250.155')
    print('{}: {}, {}'.format(r['latitude'], r['longitude'], r['ip']))
