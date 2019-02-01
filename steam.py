import six
import select
import socket
import itertools
import functools


import message


REGION_US_EAST_COAST = 0x00
REGION_US_WEST_COAST = 0x01
REGION_SOUTH_AMERICA = 0x02
REGION_EUROPE = 0x03
REGION_ASIA = 0x04
REGION_AUSTRALIA = 0x05
REGION_MIDDLE_EAST = 0x06
REGION_AFRICA = 0x07
REGION_REST = 0xFF

MASTER_SERVER_ADDR = ("hl2master.steampowered.com", 27011)


def format_(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        regions = {
            "na-east": [REGION_US_EAST_COAST],
            "na-west": [REGION_US_WEST_COAST],
            "na": [REGION_US_EAST_COAST, REGION_US_WEST_COAST],
            "sa": [REGION_SOUTH_AMERICA],
            "eu": [REGION_EUROPE],
            "as": [REGION_ASIA, REGION_MIDDLE_EAST],
            "oc": [REGION_AUSTRALIA],
            "af": [REGION_AFRICA],
            "rest": [REGION_REST],
            "all": [REGION_US_EAST_COAST,
                    REGION_US_WEST_COAST,
                    REGION_SOUTH_AMERICA,
                    REGION_EUROPE,
                    REGION_ASIA,
                    REGION_AUSTRALIA,
                    REGION_MIDDLE_EAST,
                    REGION_AFRICA,
                    REGION_REST],
        }

        # Map Regions
        regions_ = []
        if isinstance(kwargs['region'], six.text_type):
            regions_.extend(regions[kwargs['region'].lower()])
        elif isinstance(kwargs['region'], list):
            for _j in kwargs['region']:
                regions_.extend(regions[_j.lower()])
        else:
            raise TypeError('Regions is not of type \'str\' or \'list\'')
        del kwargs['region']

        # format filters
        filters_ = {}
        for key, value in six.iteritems(kwargs):
            if key not in ('secure', 'gamedir', 'map', 'linux', 'empty', 'full',
                           'proxy', 'napp', 'appid', 'noplayers', 'white', 'gametype',
                           'gamedata', 'gamedataor'):
                continue

            if key in ('secure', 'linux', 'empty', 'full', 'proxy', 'noplayers', 'white'):
                value = int(bool(value))
            elif key in {"gametype", "gamedata", "gamedataor"}:
                value = [six.text_type(elt) for elt in value if six.text_type(elt)]
                if not value:
                    continue
                value = ",".join(value)
            elif key == "napp":
                value = int(value)

            filters_[key] = six.text_type(value)

        temp_ = sorted(filters_.items(), key=lambda pair: pair[0])
        fs = "\\".join([part for pair in temp_ for part in pair])
        if fs:
            fs = "\\" + fs

        return func(args[0], regions_, fs)

    return wrapper


class BaseQueryService(object):

    def __init__(self, address, timeout=5.0):
        self.host = address[0]
        self.port = address[1]
        self.timeout = timeout
        self._contextual = False
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def __enter__(self):
        self._contextual = True
        return self

    def __exit__(self, type_, exception, traceback):
        self._contextual = False
        self.close()

    def close(self):
        if self._contextual:
            print("{0.__class__.__name__} used as context manager but close called "
                  "before exit".format(self))
        if self._socket is not None:
            self._socket.close()
            self._socket = None

    def request(self, *request):
        if self._socket is None:
            raise ValueError('Socket is None')
        request_final = b"".join(segment.encode() for segment in request)
        self._socket.sendto(request_final, (self.host, self.port))

    def get_response(self):
        if self._socket is None:
            raise ValueError('Socket is None')
        ready = select.select([self._socket], [], [], self.timeout)
        if not ready[0]:
            raise ValueError("Timed out waiting for response")

        data = ready[0][0].recv(1400)

        return data


class SteamQueryService(BaseQueryService):

    def __init__(self, address=MASTER_SERVER_ADDR, timeout=10.0):
        super(SteamQueryService, self).__init__(address, timeout)

    def query(self, region, filter_string):
        last_addr = "0.0.0.0:0"
        first_request = True
        while first_request or last_addr != "0.0.0.0:0":
            first_request = False
            self.request(message.MasterServerRequest(
                region=region, address=last_addr, filter=filter_string))
            try:
                raw_response = self.get_response()
            except (socket.error, ValueError):
                return
            else:
                response = message.MasterServerResponse.decode(raw_response)
                for address in response["addresses"]:
                    last_addr = "{}:{}".format(
                        address["host"], address["port"])
                    if not address.is_null:
                        yield address["host"], address["port"]

    @format_
    def find(self, region, filter_string):
        print(filter_string)
        queries = []
        for region in region:
            queries.append(self.query(region, filter_string))

        seen = set()
        for address in itertools.chain.from_iterable(queries):
            if address in seen:
                continue
            seen.add(address)

        print('Found %d addresses' % len(seen))
        for address in seen:
            yield address


if __name__ == '__main__':

    with SteamQueryService() as msq:
        servers = msq.find(
            region=["na"],
            appid='440'
        )
        for host, port in servers:
            print("{0}:{1}".format(host, port))
