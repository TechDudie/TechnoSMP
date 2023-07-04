from python_aternos import Client as AternosClient
import python_aternos
import PloudosAPI
from mcstatus import JavaServer
import pytz
from requests.exceptions import ConnectionError

import datetime
import time

from config import get_config
from log import log as L, error as E

config = get_config("config")
timezone = pytz.timezone(config["playerTimezone"])
curfew_interval = config["curfewCheckInterval"]

L("S/Configuration loaded")

class ProviderServer():
    def __init__(self):
        self.client = None
        self.server = None
        self.ip = None
    
    def login(self, username: str, password: str):
        try:
            self.client.login(username, password)
            L("S/Successfully connected to provider")
        except ConnectionError:
            E("S/Failed to connect to provider")
        except python_aternos.atclient.CredentialsError:
            E("S/Failed to authenicate with Aternos, check your credentials")

    def set_target(self, ip: str):
        self.ip = ip
        L("S/Target server successfully found")
    
    def _query_server(self) -> JavaServer:
        return JavaServer.lookup(self.ip.split(":")[0])

    def get_status(self) -> str:
        server = self._query_server()
        status = server.status()
        if status.players.max == 0:
            E("S/Failed to connect to server", False)
            return "offline"
        return "online"
    
    def get_latency(self) -> float:
        try:
            return self._query_server().ping()
        except TimeoutError:
            E("S/Failed to connect to server", False)
            return 2147483647

    def get_players(self) -> str | None:
        playerlist = self.get_playerlist()
        return len(playerlist) if playerlist is not None else None
    
    def get_playerlist(self) -> list | None:
        try:
            data = [user['name'] for user in self._query_server().status().raw['players']['sample']]
        except TimeoutError:
            E("S/Failed to connect to server", False)
            return None
        for i in data:
            if "§" in i:
                data.remove(i)
        return data
    
    def start(self):
        try:
            self.server.start()
        except AttributeError:
            E("S/Server not found", False)
    
    def stop(self):
        try:
            self.server.stop()
        except AttributeError:
            E("S/Server not found", False)
    
    def get_console(self) -> str:
        E("S/This feature is not supported by all wrappers yet!", False)
    
    def run_command(self, command: str):
        E("S/This feature is not supported by all wrappers yet!", False)

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
                server.fetch()
                self.server = server
                L("S/Target server successfully found")
                return
        L("S/Target server not found, check the IP in the configuration")

class PloudosServer(ProviderServer):
    def __init__(self):
        self.client = None
        self.server = None
        self.ip = ""
    
    def login(self, username: str, password: str):
        try:
            self.client = PloudosAPI.login(username, password)
            L("S/Successfully connected to Ploudos")
        except ConnectionError:
            E("S/Failed to connect to Ploudos")
    
    def set_target(self, ip: str):
        self.ip = ip
        servers = self.client.servers()["owned"] + self.client.servers()["shared"]
        for server in servers:
            if server.serverIP == self.ip.split(":")[0]:
                self.server = server
                L("S/Target server successfully found")
                return
        E("S/Target server not found, check the IP in the configuration")

    def get_console(self) -> str:
        return self.server.get_console()

    def run_command(self, command):
        self.server.post_to_console(command)

def check_curfew() -> bool:
    hour = datetime.now(timezone).hour
    return False if hour < int(config["serverOpen"].split("-")[0]) or hour > int(config["serverOpen"].split("-")[1]) else True

def curfew_thread(server):
    hour = datetime.now(timezone).hour
    if hour < int(config["serverOpen"].split("-")[0]) or hour > int(config["serverOpen"].split("-")[1]):
        if server.get_status() != "offline":
            L("S/Violation of curfew detected, shutting server down")
            server.stop()

    time.sleep(curfew_interval)

my_client = PloudosServer()
my_client.login("username", "password")
my_client.set_target("example.server.lol:25565")
print(my_client._query_server())
print(my_client.get_status())
print(my_client.get_players())
print(my_client.get_playerlist())
print(my_client.get_console())
print(my_client.run_command("/say TechnoDot is awesome"))