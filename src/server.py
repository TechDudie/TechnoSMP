from python_aternos import Client as AternosClient
import PloudosAPI
from mcstatus import JavaServer
import pytz

import datetime
import time

from .config import *

config = get_config("config")
timezone = pytz.timezone(config["playerTimezone"])

class ProviderServer():
    def __init__(self):
        self.client = None
        self.server = None
        self.ip = None
    
    def login(self, username: str, password: str):
        self.client.login(username, password)

    def set_target(self, ip: str):
        self.ip = ip
    
    def _query_server(self) -> JavaServer:
        return JavaServer.lookup(self.ip.split(":")[0])

    def get_status(self) -> str:
        server = self._query_server()
        status = server.status()
        if status.players.max == 0:
            return "offline"
        return "online"

    def get_players(self) -> str | None:
        playerlist = self.get_playerlist()
        return len(playerlist) if playerlist is not None else None
    
    def get_playerlist(self) -> list | None:
        try:
            data = [user['name'] for user in self._query_server().status().raw['players']['sample']]
        except TimeoutError:
            return None
        for i in data:
            if "§" in i:
                data.remove(i)
        return data
    
    def start(self):
        try:
            self.server.start()
        except AttributeError:
            print("Server not found")
    
    def stop(self):
        try:
            self.server.stop()
        except AttributeError:
            print("Server not found")
    
    def get_console(self) -> str:
        return "This feature is not supported by all wrappers yet!"
    
    def run_command(self, command: str):
        return "This feature is not supported by all wrappers yet!"

class AternosServer(ProviderServer):
    def __init__(self):
        self.client = AternosClient()
        self.server = None
        self.ip = ""

    def set_target(self, ip: str):
        self.ip = ip
        servers = self.client.account.list_servers()
        for server in servers:
            if server.address == self.ip:
                self.server = server

class PloudosServer(ProviderServer):
    def __init__(self):
        self.client = None
        self.server = None
        self.ip = ""
    
    def login(self, username: str, password: str):
        self.client = PloudosAPI.login(username, password)
    
    def set_target(self, ip: str):
        self.ip = ip
        servers = self.client.servers()["owned"] + self.client.servers()["shared"]
        for server in servers:
            if server.serverIP == self.ip.split(":")[0]:
                self.server = server
    
    def get_console(self) -> str:
        return self.server.get_console()

    def run_command(self, command):
        self.server.post_to_console(command)

def check_curfew() -> bool:
    hour = datetime.now(timezone).hour
    return False if hour < int(config["whenDisabled"].split("-")[0]) or hour > int(config["whenDisabled"].split("-")[1]) else True

def curfew_thread(server):
    hour = datetime.now(timezone).hour
    if hour < int(config["whenDisabled"].split("-")[0]) or hour > int(config["whenDisabled"].split("-")[1]):
        if server.get_status() != "offline":
            server.stop()

    time.sleep(300)

my_client = PloudosServer()
my_client.login("username", "password")
my_client.set_target("example.server.lol:25565")
print(my_client._query_server())
print(my_client.get_status())
print(my_client.get_players())
print(my_client.get_playerlist())
print(my_client.get_console())
print(my_client.run_command("/say TechnoDot is awesome"))