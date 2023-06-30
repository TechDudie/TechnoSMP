from nextcord import *
from python_aternos import *
import pytz

from datetime import datetime
import threading
import time
import json

# Dataset

dataset = open(".env").read().strip().split("\n")
data = {}
for set in dataset:
    split = set.split("=")
    data[split[0]] = split[1]

# General utilities

def log(message="", level="INFO"):
    '''Logs a message. `level` specifies the message importance (defaults to `"INFO"`), and `message` specifies the message to log (defaults to nothing).'''
    print(f"[TechnoBot] [{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[11:-3]}] [{level}] {message}")

def user_log(interaction: Interaction, message="", level="INFO"):
    '''Logs a user-specific message. `interaction` specifies the interaction, `level` specifies the message importance (defaults to `"USER"`), and `message` specifies the message to log (defaults to nothing).'''
    log(f"[{interaction.user.id}] [{level}] {message}", "USER")

async def embed(interaction: Interaction, message="", level="INFO", header=""):
    '''Sends a `nextcord.Embed` and logs a user-specific message. `interaction` specifies the interaction, `level` specifies the message importance (defaults to `"INFO"`), and `message` specifies the message to log (defaults to nothing).'''
    color = Color.default()
    title = level.title()
    if level == "OK":
        color = Color.green()
        title = "Success"
    elif level == "WARN":
        color = Color.yellow()
        title = "Warning"
    elif level == "ERROR":
        color = Color.red()
        title = "Error"
    if header != "":
        title = header

    log(f"[{interaction.user.id}] [{level}] {message}", "USER")
    await interaction.send(embed=Embed(title=title, description=message, color=color))

def load() -> dict:
    '''Loads the JSON file `data.json` and returns the Python dictionary representation.`'''
    return json.loads(open(f"data.json").read())

def save(jsonData: dict):
    '''Saves `jsonData` as a JSON string to `data.json`.'''
    with open(f"data.json", "w") as file:
        json.dump(jsonData, file, indent=4)

def player_info(data: dict, id: int) -> dict:
    teamName = ""
    isLeader = False
    teamID = -1
    strikes = 0
    isOp = False

    for i in range(0, len(data["teams"])):
        if id in data["teams"][i]["members"]:
            teamName = data["teams"][i]["name"]
            isLeader = data["teams"][i]["leader"] == id
            teamID = i
            break
    
    for i in range(0, len(data["strikes"])):
        if id in data["strikes"].keys():
            strikes = data["strikes"][i][id]
            break
    
    if id in data["ops"]:
        isOp = True

    return {
        "team": teamName,
        "isLeader": isLeader,
        "teamID": teamID,
        "strikes": strikes,
        "isOp": isOp
    }

def team_id(data: dict, name: str) -> str:
    teamID = 0
    for team in data["teams"]:
        if team["name"] == name:
            break
        teamID += 1

    return teamID

# Nextcord utilities

class Confirm(ui.View):
    def __init__(self):
        super().__init__()
        self.value = None
        self.caller = None
        self.clicked = []

    @ui.button(label="Confirm", style=ButtonStyle.green)
    async def confirm(self, button: ui.Button, interaction: Interaction):
        if self.caller == interaction.user.id:
            await interaction.response.send_message("Confirmed!")
            self.value = True
            self.stop()
        elif interaction.user.id in self.clicked:
            pass
        else:
            await interaction.response.send_message(f"{interaction.user.mention}, you're not the command sender!")
            self.clicked.append(interaction.user.id)
    
    @ui.button(label="Cancel", style=ButtonStyle.red)
    async def cancel(self, button: ui.Button, interaction: Interaction):
        if self.caller == interaction.user.id:
            await interaction.response.send_message("Cancelled!")
            self.value = False
            self.stop()
        elif interaction.user.id in self.clicked:
            pass
        else:
            await interaction.response.send_message(f"{interaction.user.mention}, you're not the command sender!")
            self.clicked.append(interaction.user.id)

# Minecraft utilities

global target_server
target_server = None
config = load()["config"]

async def start_server(interaction: Interaction):
    if curfew_check():
        target_server.start()
        await embed(interaction, "Server started!", "OK")
    else:
        await embed(interaction, "Server curfew active! Please try again later.", "ERROR")

def curfew_check() -> bool:
    timezone = pytz.timezone("America/Detroit")
    hour = datetime.now(timezone).hour

    return False if hour < int(config["whenDisabled"].split("-")[0]) or hour > int(config["whenDisabled"].split("-")[1]) else True

def curfew_thread():
    timezone = pytz.timezone("America/Detroit")
    hour = datetime.now(timezone).hour

    if hour < int(config["whenDisabled"].split("-")[0]) or hour > int(config["whenDisabled"].split("-")[1]):
        if target_server.status != "offline":
            log("Server curfew reached, server shutting down")
            target_server.stop()

    time.sleep(300)

def setup_mc():
    if data["server.ip"].find(".aternos.me") != -1:
        global target_server
        log("Aternos server detected")
        aternos = Client()
        aternos.login(data["aternos.username"], data["aternos.password"])
        servers = aternos.account.list_servers()
        for server in servers:
            if server.address == data["server.ip"]:
                target_server = server
                log("Server successfully found with associated Aternos account", "INFO")
        if target_server is None:
            log("Server not found with associated Aternos account", "ERROR")
            exit()
        if config["serverCurfew"]:
            global curfew_thread
            log("Server curfew enabled, launching daemon thread")
            curfew_thread = threading.Thread(target=curfew_thread)
            curfew_thread.setDaemon(True)
            curfew_thread.start()
        else:
            log("Server curfew disabled, time limit inexistent for sad tryhards who don't know what grass is")