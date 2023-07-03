from nextcord import Interaction, Embed, Color
from datetime import datetime

def log(message="", source="Main", level="INFO"):
    print(f"[{source}] [{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S.%f')[11:-3]}] [{level}] {message}")

def user_log(interaction: Interaction, message="", level="INFO"):
    log(f"[{interaction.user.id}] [{level}] {message}", "Discord", "USER")

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