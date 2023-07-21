from time import sleep
import random
import discord
import json
from secrets import tokenD

intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True
intents.invites = True
intents.guilds = True
servers_synced = {}
SERVER_ID = 895359434539302953

class aclient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.synced = False  # added to make sure that the command tree will be synced only once
        self.added = False


client = aclient()
tree = discord.app_commands.CommandTree(client)

@client.event
async def on_ready():
    print("I'm in")
    print(client.user)

    with open("storage.json", "r") as j:
        data = json.load(j)

    activity = discord.Activity(type=discord.ActivityType.watching, name=" " + data["Status"])
    await client.change_presence(status=discord.Status.online, activity=activity)

    await client.wait_until_ready()

    async for i in client.fetch_guilds():
        servers_synced[i.id] = False

    # Todo update last bot refresh time to control pannel

@tree.command(description='Apply to host an event')
async def event(interaction: discord.Interaction, title: str):
    await interaction.response.send_message(
        'https://discord.com/api/oauth2/authorize?client_id=1089259451002916935&permissions=2148076608&scope=bot')

@client.event
async def on_message(message):
    # Syncs to server
    if message.guild and not servers_synced[message.guild.id]:
        await tree.sync()
        servers_synced[message.guild.id] = True
        print(f"synced to server: {message.guild.name}")

client.run(tokenD)