import requests


ACCESS_KEY = ''


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
    r = standard_ip_lookup('134.201.250.155')
    print('{}: {}, {}'.format(r['latitude'], r['longitude'], r['ip']))
