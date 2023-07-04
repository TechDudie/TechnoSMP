from nextcord import Interaction, Embed, Color
from datetime import datetime

source_aliases = {
    "M": "MasterThread",
    "J": "JSONManager",
    "S": "ServerHandler",
    "D": "DiscordWorker",
    "W": "WebsiteThread"
}

def log(message="", level="INFO"):
    try:
        source = source_aliases[message.split("/")[0]]
    except KeyError:
        source = "UnknownSource"
    print(f"[{source}] [{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[11:-3]}] [{level}] {message[2:]}")

def error(message="", fatal=True):
    log(message, level="ERROR")
    if fatal:
        exit()

def user_log(interaction: Interaction, message="", level="INFO"):
    log(f"D/[{interaction.user.id}] [{level}] {message}", "USER")

async def embed(interaction: Interaction, message="", level="INFO", header=""):
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

    user_log(interaction, message, level)
    await interaction.send(embed=Embed(title=title, description=message, color=color))