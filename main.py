from nextcord import *
import json
import requests

import utils
from utils import log, user_log, embed

log("Imported libraries")

token = utils.data["discord.token"]

serverIP = utils.data["server.ip"]

log("Gathered secrets")

intents = Intents.default()
intents.members = True
bot: Client = Client(intents=intents)

log("Defined bot")

json_data = utils.load()

log("Loaded data")

def reload_data():
    global json_data
    utils.save(json_data)
    json_data = utils.load()

def reset_data():
    global json_data
    json_data = utils.load()

log("Defined helper functions")

@bot.event
async def on_ready():
    log("Successfully authenicated")

@bot.slash_command(name="status", description="Queries server status")
async def status(interaction: Interaction):
    user_log(interaction, "User ran /status")

    embed = Embed(title="Querying Server", description="Hold tight... we're checking!", color=Color.blurple())
    message = await interaction.send(embed=embed)

    payload = json.loads(requests.get(f"https://api.minetools.eu/ping/{serverIP.split(':')[0]}/{serverIP.split(':')[1]}").content)

    try:
        if payload["description"]:
            players_online, player_limit = payload.get("players").get("online"), payload.get("players").get("max")
            if player_limit == 0:
                embed = Embed(title="Server Offline", description="Start the server!", color=Color.green())
                await message.edit(embed=embed)
                return
            embed = Embed(title="Server Online", description="Start the server!", color=Color.green())
            embed.add_field(name="Capacity", value=f"`{players_online}/{player_limit}`")
            await message.edit(embed=embed)
    except KeyError:
        embed = Embed(title="Server Offline", description="Start the server!", color=Color.red())
        await message.edit(embed=embed)

@bot.slash_command(name="teams", description="TechnoSMP teams")
async def teams(
    interaction: Interaction,
    action: str = SlashOption(
        name="action",
        description="Action to perform",
        choices={
            "Join a team": "join",
            "Invite someone to your team": "invite",
            "Leave current team": "leave",
            "Create a team": "create",
            "Disband a team": "delete",
            "Rename your team": "rename",
            "Transfer ownership": "transfer",
            "View stats": "stats"
        }
    ),
    data: str = SlashOption(
        name="data",
        description="Action options",
        required=False
    )
):
    user_log(interaction, "User ran /teams")
    user_log(interaction, f"Action: {action}")
    user_log(interaction, f"Data: {data}")

    if action == "join":
        reload_data()

        match = False
        for team in json_data["teams"]:
            if team["name"] == data:
                match = True
                break
        if not match:
            embed = Embed(title="Team not found", description=f"The team `{data}` does not exist!", color=Color.red())
            await interaction.send(embed=embed)
            return

        player_info = utils.player_info(json_data, interaction.user.id)

        if len(json_data["teams"][utils.team_id(json_data, data)]["members"]) < 3:
            if utils.player_info(json_data, interaction.user.id)["team"] == "":
                json_data["teams"][utils.team_id(json_data, data)]["members"].append(interaction.user.id)
            else:
                confirm = utils.Confirm()
                confirm.caller = interaction.user.id
                await interaction.send(embed=Embed(title="Confirm", description=f"Are you sure you want to leave your current team {player_info['team']}?", color=Color.yellow()), view=confirm)
                await confirm.wait()
                if confirm.value:
                    json_data["teams"][utils.team_id(json_data, data)]["members"].append(interaction.user.id)

                    for id in json_data["teams"][player_info["teamID"]]["members"]:
                        member = bot.get_user(id)
                        await member.send(embed=Embed(title="Notice", description=f"{interaction.user.display_name} has joined your team {data}!", color=Color.blurple()))
                    pass
                else:
                    await utils.embed(interaction, "Cancelled!", "ERROR")
        else:
            await embed(interaction, "That team is full!", "ERROR")
        
        reload_data()
    elif action == "invite":
        await utils.embed(interaction, "This feature hasn't been implemented yet!", "ERROR") # TODO
    elif action == "leave":
        await utils.embed(interaction, "This feature hasn't been implemented yet!", "ERROR") # TODO
    elif action == "create":
        reload_data()

        if data == None:
            await utils.embed(interaction, "Huh?", "ERROR")
            return

        if utils.player_info(json_data, interaction.user.id)["team"] == "":
            names = [json_data["teams"][i]["name"] for i in range(0, len(json_data["teams"]))]
            if data in names:
                await utils.embed(interaction, "A team with that name already exists!", "ERROR")
                return

            json_data["teams"].append({
                "name": data,
                "leader": interaction.user.id,
                "members": [interaction.user.id]
            })
            await utils.embed(interaction, "Team created!", "OK")
        else:
            await utils.embed(interaction, "You're already on a team!", "ERROR")

        reload_data()
    elif action == "delete":
        reload_data()

        if utils.player_info(json_data, interaction.user.id)["isLeader"]:
            team = utils.player_info(json_data, interaction.user.id)["team"]
            confirm = utils.Confirm()
            confirm.caller = interaction.user.id
            await interaction.send(embed=Embed(title="Confirm", description=f"Are you sure you want to disband your team {team}?", color=Color.yellow()), view=confirm)
            await confirm.wait()
            if confirm.value:
                log(f"Disbanding team {team}")

                for i in range(0, len(json_data["teams"])):
                    if json_data["teams"][i]["name"] == team:
                        for id in json_data["teams"][i]["members"]:
                            member = bot.get_user(id)
                            await member.send(embed=Embed(title="Notice", description=f"Your team {team} has been disbanded!", color=Color.red()))
                        del json_data["teams"][i]
                        await utils.embed(interaction, "Team disbanded!", "OK")
                        break

            elif not confirm.value:
                log("Disband cancelled")
            else:
                log("Interaction timed out")
        else:
            user_log(interaction, "User isn't team leader", "ERROR")
            await interaction.send(embed=Embed(title="Error", description="You don't have permission to use this command!", color=Color.red()), ephemeral=True)

        reload_data()
    elif action == "rename":
        reload_data()

        if data == None:
            await utils.embed(interaction, "Huh?", "ERROR")
            return

        player_data = utils.player_info(json_data, interaction.user.id)
        if player_data["isLeader"]:
            team = player_data["team"]
            json_data["teams"][player_data["teamID"]]["name"] = data
            await utils.embed(interaction, "Team renamed!", "OK")

            for id in json_data["teams"][player_data["teamID"]]["members"]:
                member = bot.get_user(id)
                await member.send(embed=Embed(title="Notice", description=f"Your team {team} has been renamed to {data}!", color=Color.blurple()))
        else:
            user_log(interaction, "User isn't team leader", "ERROR")
            await interaction.send(embed=Embed(title="Error", description="You don't have permission to use this command!", color=Color.red()), ephemeral=True)

        reload_data()
    elif action == "transfer":
        reload_data()

        if data == None:
            await utils.embed(interaction, "Huh?", "ERROR")
            return

        player_data = utils.player_info(json_data, interaction.user.id)
        new_leader = utils.player_info(json_data, int(data[2:-1]))
        if player_data["isLeader"] and player_data["team"] == new_leader["team"]:
            confirm = utils.Confirm()
            confirm.caller = interaction.user.id
            await interaction.send(embed=Embed(title="Confirm", description="Are you sure you want to resign?", color=Color.yellow()), view=confirm)
            await confirm.wait()
            if confirm.value:
                log(f"Changing team leader of {player_data['team']} to {interaction.user.mention}")

                json_data["teams"][player_data["teamID"]]["leader"] = int(data[2:-1])
                await utils.embed(interaction, "Team leader changed!", "OK")

                for id in json_data["teams"][player_data["teamID"]]["members"]:
                    member = bot.get_user(id)
                    await member.send(embed=Embed(title="Notice", description=f"Your team {player_data['team']} has changed team leaders!", color=Color.blurple()))
        elif player_data["team"] != new_leader["team"]:
            user_log(interaction, "New leader isn't on team", "ERROR")
            await interaction.send(embed=Embed(title="Error", description=f"{bot.get_user(int(data[2:-1])).mention} isn't on your team {player_data['team']}!", color=Color.red()))
        else:
            user_log(interaction, "User isn't team leader", "ERROR")
            await interaction.send(embed=Embed(title="Error", description="You don't have permission to use this command!", color=Color.red()), ephemeral=True)

        reload_data()
    elif action == "stats":
        await utils.embed(interaction, "This feature hasn't been implemented yet!", "ERROR")
    else:
        log("Invalid action argument", "ERROR")

@bot.slash_command(name="purge", description="Purges all messages from channel")
async def purge(
    interaction: Interaction,
    amount: int = SlashOption(
        name="amount",
        description="Amount of messages to purge",
        required=False,
        default=1000,
        min_value=1,
        max_value=1000
    ),
    include: str = SlashOption(
        name="include",
        description="Only purge messages from this user",
        required=False
    ),
    exclude: str = SlashOption(
        name="exclude",
        description="Exclude messages from this user",
        required=False
    )
):
    user_log(interaction, "User ran /purge")

    if utils.player_info(json_data, interaction.user.id)["isOp"]:
        channel = interaction.channel
        if include is None and exclude is None:
            await utils.embed(interaction, "Messages purged!", "OK")
            async for message in channel.history(limit=amount):
                await message.delete()
        elif include is not None and exclude is None:
            await utils.embed(interaction, "Messages purged!", "OK")
            async for message in channel.history(limit=amount):
                if f"<@{message.author.id}>" == include:
                    await message.delete()
        elif include is None and exclude is not None:
            await utils.embed(interaction, "Messages purged!", "OK")
            async for message in channel.history(limit=amount):
                if f"<@{message.author.id}>"!= exclude:
                    await message.delete()
        else:
            await utils.embed(interaction, "Huh?", "ERROR")

    else:
        user_log(interaction, "User doesn't have op perms", "ERROR")
        await interaction.send(embed=Embed(title="Error", description="You don't have permission to use this command!", color=Color.red()), ephemeral=True)
        return

@bot.slash_command(name="op", description="Gives someone op perms")
async def op(
    interaction: Interaction,
    user: str = SlashOption(
        name="user",
        description="Give this user op perms",
    )
):
    user_log(interaction, "User ran /op")
    user_log(interaction, f"User: {user}")

    if utils.player_info(json_data, interaction.user.id)["isOp"]:
        team = utils.player_info(json_data, interaction.user.id)["team"]
        confirm = utils.Confirm()
        confirm.caller = interaction.user.id
        
        await interaction.send(embed=Embed(title="Confirm", description=f"Are you sure you want to give {bot.get_user(int(user[2:-1])).mention} TechnoBot op permissions?", color=Color.yellow()), view=confirm)
        await confirm.wait()
        if confirm.value:
            log(f"Giving {user} op perms")
            json_data["ops"].append(int(user[2:-1]))
        else:
            log("Interaction timed out")

    else:
        user_log(interaction, "User doesn't have op perms", "ERROR")
        await interaction.send(embed=Embed(title="Error", description="You don't have permission to use this command!", color=Color.red()), ephemeral=True)
        return

@bot.slash_command(name="strike", description="Modifies a player's strikes")
async def strike(
    interaction: Interaction,
    player: str = SlashOption(
        name="player",
        description="Player to modify",
        required=True
    ),
    action: str = SlashOption(
        name="action",
        description="Action to perform",
        choices={
            "Add strikes": "add",
            "Remove strikes": "remove",
            "Set strikes": "set",
            "Reset strikes": "reset"
        },
        required=False,
        default="add"
    ),
    amount: int = SlashOption(
        name="amount",
        description="Amount of strikes",
        required=False,
        default=1,
        min_value=1,
    )
):
    user_log(interaction, "User ran /strike")
    user_log(interaction, f"Action: {action}")
    user_log(interaction, f"Amount: {amount}")

    if interaction.user.id in json_data["ops"]:
        target = int(player[2:-1])
        message = "not changed"
        if action == "add":
            json_data["strikes"][target] += amount
            message = "added"
        elif action == "remove":
            json_data["strikes"][target] -= amount
            message = "removed"
        elif action == "set":
            json_data["strikes"][target] = amount
            message = "set"
        elif action == "reset":
            json_data["strikes"][target] = 0
            message = "reset"
        await utils.embed(interaction, f"Strikes {message}", "OK")
    else:
        user_log(interaction, "User doesn't have op perms", "ERROR")
        await interaction.send(embed=Embed(title="Error", description="You don't have permission to use this command!", color=Color.red()), ephemeral=True)

@bot.slash_command(name="start", description="Starts the server")
async def start(interaction: Interaction):
    user_log(interaction, "User ran /start")

    if interaction.user.id in json_data["strikes"].keys() and json_data["strikes"][interaction.user.id] > 1:
        user_log(interaction, "User has too many strikes", "ERROR")
        await interaction.send(embed=Embed(title="Error", description="You have too many strikes!", color=Color.red()), ephemeral=True)
        return
    
    try:
        await utils.start_server(interaction)
    except:
        await utils.embed("An error occured :(")

@bot.slash_command(name="save", description="Saves all manually modified data")
async def save(interaction: Interaction):
    user_log(interaction, "User ran /save")

    if utils.player_info(json_data, interaction.user.id)["isOp"]:
        reset_data()
        await embed(interaction, "Data saved!", "OK")
    else:
        user_log(interaction, "User doesn't have op perms", "ERROR")
        await interaction.send(embed=Embed(title="Error", description="You don't have permission to use this command!", color=Color.red()), ephemeral=True)

log("Commands defined")

utils.setup_mc()

try:
    bot.run(token)
except HTTPException as exception:
    if exception.status == 429:
        log("Connection denied by Discord servers", "ERROR")
    else:
        log("Unknown error", "ERROR")
    log("Terminating program", "ERROR")
    exit()
