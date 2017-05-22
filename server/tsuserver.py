# tsuserver3, an Attorney Online server
#
# Copyright (C) 2016 argoneus <argoneuscze@gmail.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import asyncio

import yaml

from server import logger
from server.aoprotocol import AOProtocol
from server.area_manager import AreaManager
from server.ban_manager import BanManager
from server.client_manager import ClientManager
from server.districtclient import DistrictClient
from server.exceptions import ServerError
from server.masterserverclient import MasterServerClient


class TsuServer3:
    def __init__(self):
        self.client_manager = ClientManager(self)
        self.area_manager = AreaManager(self)
        self.ban_manager = BanManager()
        self.version = 'tsuserver3dev'
        self.software = 'tsuserver3'
        self.release = 3
        self.major_version = 0
        self.minor_version = 2
        self.char_list = None
        self.char_pages_ao1 = None
        self.music_list = None
        self.music_list_ao2 = None
        self.music_pages_ao1 = None
        self.backgrounds = None
        self.config = None
        self.load_config()
        self.load_characters()
        self.load_music()
        self.load_backgrounds()
        self.district_client = None
        self.ms_client = None
        logger.setup_logger(debug=self.config['debug'])

    def start(self):
        loop = asyncio.get_event_loop()

        bound_ip = '0.0.0.0'
        if self.config['local']:
            bound_ip = '127.0.0.1'

        ao_server_crt = loop.create_server(lambda: AOProtocol(self), bound_ip, self.config['port'])
        ao_server = loop.run_until_complete(ao_server_crt)

        if self.config['use_district']:
            self.district_client = DistrictClient(self)
            asyncio.ensure_future(self.district_client.connect(), loop=loop)

        if self.config['use_masterserver']:
            self.ms_client = MasterServerClient(self)
            asyncio.ensure_future(self.ms_client.connect(), loop=loop)

        logger.log_debug('Server started.')

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass

        logger.log_debug('Server shutting down.')

        ao_server.close()
        loop.run_until_complete(ao_server.wait_closed())
        loop.close()

    def get_version_string(self):
        return str(self.release) + '.' + str(self.major_version) + '.' + str(self.minor_version)

    def new_client(self, transport):
        c = self.client_manager.new_client(transport)
        c.server = self
        c.area = self.area_manager.default_area()
        c.area.new_client(c)
        return c

    def remove_client(self, client):
        client.area.remove_client(client)
        self.client_manager.remove_client(client)

    def get_player_count(self):
        return len(self.client_manager.clients)

    def load_config(self):
        with open('config/config.yaml', 'r') as cfg:
            self.config = yaml.load(cfg)

    def load_characters(self):
        with open('config/characters.yaml', 'r') as chars:
            self.char_list = yaml.load(chars)
        self.build_char_pages_ao1()

    def load_music(self):
        with open('config/music.yaml', 'r') as music:
            self.music_list = yaml.load(music)
        self.build_music_pages_ao1()
        self.build_music_list_ao2()
        

    def load_backgrounds(self):
        with open('config/backgrounds.yaml', 'r') as bgs:
            self.backgrounds = yaml.load(bgs)

    def build_char_pages_ao1(self):
        self.char_pages_ao1 = [self.char_list[x:x + 10] for x in range(0, len(self.char_list), 10)]
        for i in range(len(self.char_list)):
            self.char_pages_ao1[i // 10][i % 10] = '{}#{}&&0&&&0&'.format(i, self.char_list[i])

    def build_music_pages_ao1(self):
        self.music_pages_ao1 = []
        index = 0
        # add areas first
        for area in self.area_manager.areas:
            self.music_pages_ao1.append('{}#{}'.format(index, area.name))
            index += 1
        # then add music
        for item in self.music_list:
            self.music_pages_ao1.append('{}#{}'.format(index, item['category']))
            index += 1
            for song in item['songs']:
                self.music_pages_ao1.append('{}#{}'.format(index, song['name']))
                index += 1
        self.music_pages_ao1 = [self.music_pages_ao1[x:x + 10] for x in range(0, len(self.music_pages_ao1), 10)]

    def build_music_list_ao2(self):
        self.music_list_ao2 = []
        # add areas first
        for area in self.area_manager.areas:
            self.music_list_ao2.append(area.name)
            # then add music
        for item in self.music_list:
            self.music_list_ao2.append(item['category'])
            for song in item['songs']:
                self.music_list_ao2.append(song['name'])

    def is_valid_char_id(self, char_id):
        return len(self.char_list) > char_id >= 0

    def get_char_id_by_name(self, name):
        for i, ch in enumerate(self.char_list):
            if ch.lower() == name.lower():
                return i
        raise ServerError('Character not found.')

    def get_song_data(self, music):
        for item in self.music_list:
            if item['category'] == music:
                return item['category'], -1
            for song in item['songs']:
                if song['name'] == music:
                    try:
                        return song['name'], song['length']
                    except KeyError:
                        return song['name'], -1
        raise ServerError('Music not found.')

    def send_all_cmd_pred(self, cmd, *args, pred=lambda x: True):
        for client in self.client_manager.clients:
            if pred(client):
                client.send_command(cmd, *args)

    def broadcast_global(self, client, msg, as_mod=False):
        char_name = client.get_char_name()
        ooc_name = '{}[{}][{}]'.format('<dollar>G', client.area.id, char_name)
        if as_mod:
            ooc_name += '[M]'
        self.send_all_cmd_pred('CT', ooc_name, msg, pred=lambda x: not x.muted_global)
        if self.config['use_district']:
            self.district_client.send_raw_message(
                'GLOBAL#{}#{}#{}#{}'.format(int(as_mod), client.area.id, char_name, msg))

    def broadcast_need(self, client, msg):
        char_name = client.get_char_name()
        area_name = client.area.name
        area_id = client.area.id
        self.send_all_cmd_pred('CT', '{}'.format(self.config['hostname']),
                               '=== Advert ===\r\n{} in {} [{}] needs {}\r\n==============='
                               .format(char_name, area_name, area_id, msg), pred=lambda x: not x.muted_adverts)
        if self.config['use_district']:
            self.district_client.send_raw_message('NEED#{}#{}#{}#{}'.format(char_name, area_name, area_id, msg))
