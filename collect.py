import csv
import argparse
import logging

from gevent import monkey
from gevent.pool import Pool
from valve.source.master_server import MasterServerQuerier
from valve.source.a2s import ServerQuerier, NoResponseError
from valve.source.messages import BrokenMessageError


MASTER_SERVER_ADDR = ("hl2master.steampowered.com", 27011)

# Configure gevent Pool size
pool = Pool(size=1000)
monkey.patch_all()


def get_server_info(address, csv_writer):
    server = ServerQuerier(address)

    try:
        info = server.info()

        del info['response_type']
        del info['vac_enabled']
        del info['version']
        del info['protocol']
        csv_writer.writerow(info)

        logging.info(u'Updated {0}:{1} {2}'.format(
            address[0], address[1], info['server_name'])
        )
        return True
    except ValueError as e:
        logging.exception(e)
        return None
    except (NotImplementedError, NoResponseError, BrokenMessageError):
        pass


def find_servers(region, appid=''):
    _game_addr = []
    try:
        with MasterServerQuerier(address=MASTER_SERVER_ADDR) as msq:
            for address in msq.find(region=[region], appid=appid):
                logging.info('Found server: {0}'.format(address))
                _game_addr.append(address)

    except NoResponseError as e:
        if u'Timed out' not in e.message:
            logging.warning('Error querying master server: {0}'.format(e))
    finally:
        logging.info('Found %s addresses', len(_game_addr))
        return _game_addr


if __name__ == '__main__':
    # Command line configuration
    parser = argparse.ArgumentParser()
    parser.add_argument('--appid', default='', help='Specify AppID for the game')
    parser.add_argument('--region', default='na',
                        choices=[u'na', u'sa', u'eu', u'as', u'oc', u'af', u'rest'],
                        help='Choose region of game server')
    parser.add_argument('--info', action='store_true', help='Get Game Server Info')
    _args = parser.parse_args()

    # Log configuration
    logging.basicConfig(filename='geo_filter.log', filemode='w', level=logging.INFO,
                        datefmt='[%m-%d-Y%][%H:%M]',
                        format='%(asctime)s:%(levelname)s: %(message)s')

    logging.info(_args)

    game_address = find_servers(_args.region, _args.appid)

    droplets = []
    if _args.info:
        csv_file = open('server_info.csv', 'a')
        writer = csv.DictWriter(csv_file, fieldnames=['app_id',
                                                      'bot_count',
                                                      'folder',
                                                      'game',
                                                      'map',
                                                      'max_players',
                                                      'password_protected',
                                                      'platform',
                                                      'player_count',
                                                      'server_name',
                                                      'server_type'])
        writer.writeheader()

        try:
            for addr in game_address:
                droplets.append(pool.spawn(get_server_info, addr, writer))

            droplets = [drop.get() for drop in droplets]

            success = list(filter(None, droplets))
            logging.info('Collected {%s}/{%s}', len(success), len(droplets))
        finally:
            csv_file.close()
