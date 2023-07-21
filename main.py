from time import sleep
import random
import discord
import json
import channels
from secrets import tokenD

intents = discord.Intents.default()
intents.members = True
intents.presences = True
intents.message_content = True
intents.invites = True
intents.guilds = True
servers_synced = {}
SERVER_ID = 895359434539302953
ADMIN_ID = 779481064636809246
ADMIN_DMS = 948329194050445372


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


@client.event
async def on_member_join(member):
    rock_role = client.get_guild(SERVER_ID).get_role(947983184409272340)
    await member.add_roles(rock_role)

    with open("storage.json", "r") as j:
        data = json.load(j)

    choose_msg = await member.send("Would you like\nPG and up channels 🔵\nOr\nPG and under channels 🟢")
    data["ChoosePG"].append(choose_msg.id)
    await choose_msg.add_reaction("🔵")
    await choose_msg.add_reaction("🟢")

    with open("storage.json", "w") as j:
        json.dump(data, j)



@tree.command(description='Apply to host an event')
async def event(interaction: discord.Interaction, event_name: str, day: int, month: int, year: int, location: str,
                description: str, link: str):
    output = "```SUMMARY:\nEvent name: " + event_name
    output += "\nDate: " + str(month) + "/" + str(day) + "/" + str(year)
    output += "\nLocation: " + location
    output += "\nDescription: " + description
    output += "\nLink: " + link + "```"
    await interaction.response.send_message("Your application has been submitted\n\n" + output)
    admin = client.get_user(ADMIN_ID)
    admin_msg = await admin.send("Application waiting for approval:\n\n" + output)
    await admin_msg.add_reaction("🟢")
    await admin_msg.add_reaction("🔴")

    with open("storage.json", "r") as j:
        data = json.load(j)
    data["EventApplications"].append(admin_msg.id)
    with open("storage.json", "w") as j:
        json.dump(data, j)


@tree.command(description='When done in a designated event channel invites member personally')
async def event_invite(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.send_message(member.name)


@tree.command(name='sync', description='Owner only')
async def sync(interaction: discord.Interaction):
    if interaction.user.id == ADMIN_ID:
        if interaction.guild and not servers_synced[interaction.guild.id]:
            await tree.sync()
            servers_synced[interaction.guild.id] = True
            print(f"synced to server: {interaction.guild.name}")
            await interaction.response.send_message('Command tree synced.')
        else:
            await interaction.response.send_message('Command tree synced already.')
    else:
        await interaction.response.send_message('You must be the owner to use this command!')


@client.event
async def on_raw_reaction_add(payload):
    with open("storage.json", "r") as j:
        data = json.load(j)

    if payload.channel_id == ADMIN_DMS:
        for i in range(0, len(data["EventApplications"])):
            if payload.message_id == data["EventApplications"][i]:
                admin = client.get_user(ADMIN_ID)
                if payload.emoji.name == "🟢":
                    await admin.send("Approved event")
                    del data["EventApplications"][i]
                    with open("storage.json", "w") as j:
                        json.dump(data, j)
                    # TODO Approved
                elif payload.emoji.name == "🔴":
                    await admin.send("Denied event")
                    del data["EventApplications"][i]
                    with open("storage.json", "w") as j:
                        json.dump(data, j)
                else:
                    await admin.send("Reaction not found")
                break
    elif channels.GENERAL_PG == payload.channel_id and payload.emoji.name == "❌":
        for i in range(0, len(data["PG"])):
            if data["PG"][i][0] == payload.message_id:
                if data["PG"][i][1] < 2:
                    data["PG"][i][1] += 1
                else:
                    del data["PG"][i]
                    bad_msg = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
                    await bad_msg.delete()

                with open("storage.json", "w") as j:
                    json.dump(data, j)

                return

        data["PG"].append([payload.message_id, 1])

        with open("storage.json", "w") as j:
            json.dump(data, j)
    elif payload.message_id in data["ChoosePG"]:
        for i in range(0, len(data["ChoosePG"])):
            if payload.message_id == data["ChoosePG"][i]:
                if payload.emoji.name == "🔵":
                    pg_plus_role = client.get_guild(SERVER_ID).get_role(1128726932561854585)
                    member = client.get_guild(SERVER_ID).get_member(payload.user_id)
                    await member.add_roles(pg_plus_role)
                    del data["ChoosePG"][i]
                    with open("storage.json", "w") as j:
                        json.dump(data, j)
                elif payload.emoji.name == "🟢":
                    pg_role = client.get_guild(SERVER_ID).get_role(1128725136820932608)
                    member = client.get_guild(SERVER_ID).get_member(payload.user_id)
                    await member.add_roles(pg_role)
                    del data["ChoosePG"][i]
                    with open("storage.json", "w") as j:
                        json.dump(data, j)
                else:
                    print("Reaction not found for ChangePG")


    print(payload)

@client.event
async def on_raw_reaction_remove(payload):
    if channels.GENERAL_PG == payload.channel_id and payload.emoji.name == "❌":
        with open("storage.json", "r") as j:
            data = json.load(j)

        for i in range(0, len(data["PG"])):
            if data["PG"][i][0] == payload.message_id:
                data["PG"][i][1] -= 1

                if data["PG"][i][1] <= 0:
                    del data["PG"][i]

                break

        with open("storage.json", "w") as j:
            json.dump(data, j)
    print("reaction remove detected")


@client.event
async def on_message(message):
    # Syncs to server
    print()


client.run(tokenD)
