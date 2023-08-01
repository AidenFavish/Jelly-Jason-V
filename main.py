from time import sleep
import random
import discord
import json
import channels
from secrets import tokenD
import datetime
import time
import asyncio

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
ROCK = 947983184409272340


class aclient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.synced = False  # added to make sure that the command tree will be synced only once
        self.added = False


client = aclient()
tree = discord.app_commands.CommandTree(client)


async def daily_check(force: bool = False):
    with open("storage.json", "r") as j:
        data = json.load(j)
    print(time.time() / 86400 + 0.5, flush=True)  # +0.75 is to offset utc time
    print((datetime.date(day=30, month=7, year=2023) - datetime.date.today()).days)
    if data["Date"] != int(time.time() / 86400 + 0.75) or force:
        print("Daily check triggered")
        data["Date"] = int(time.time() / 86400 + 0.75)
        with open("storage.json", "w") as j:
            json.dump(data, j)

        # one a day code here
        temp_events = []
        for key, value in data["EventApplications"].items():
            days_until = (datetime.date(day=value[1], month=value[2], year=value[3]) - datetime.date.today()).days
            if days_until < 0:
                try:
                    archives = client.get_channel(channels.ARCHIVES_CAT)
                    event_channel = client.get_channel(value[9])
                    await event_channel.send("---------- THIS CHANNEL HAS BEEN ARCHIVED ----------")
                    await event_channel.move(category=archives, beginning=True)
                    guild = client.get_guild(SERVER_ID)
                    await event_channel.set_permissions(guild.get_role(ROCK), view_channel=True)
                    event_role = guild.get_role(value[8])
                    await event_role.delete()
                except Exception as e:
                    print(str(e) + "\nwas thrown when trying to archive an event")

                temp_events.append(key)
                temp = []
                for key2, value2 in data["EventInvites"].items():
                    if value2 == key:
                        temp.append(key2)

                for i in temp:
                    data["EventInvites"].pop(i)

        for i in temp_events:
            data["EventApplications"].pop(i)
        with open("storage.json", "w") as j:
            json.dump(data, j)

    # repeater
    await asyncio.sleep(30)
    await daily_check()


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

    await daily_check(force=True)

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


@tree.command(description='Create an event with its own channel and its own members. *Will auto-archive after date')
async def event(interaction: discord.Interaction, event_name: str, day: int, month: int, year: int, location: str,
                description: str, link: str = "None"):
    output = "```SUMMARY:\nEvent name: " + event_name
    output += "\nDate: " + str(month) + "/" + str(day) + "/" + str(year)
    output += "\nLocation: " + location
    output += "\nDescription: " + description
    output += "\nLink: " + link + "```"
    admin = client.get_user(ADMIN_ID)
    try:
        await interaction.response.send_message("Your application has been submitted")
    except Exception as e:
        print(e)
        await admin.send(str(e) + "\ngenerated with event creation")

    admin_msg = await admin.send("Application waiting for approval:\n\n" + output)
    await admin_msg.add_reaction("🟢")
    await admin_msg.add_reaction("🔴")

    with open("storage.json", "r") as j:
        data = json.load(j)
    data["EventApplications"][str(admin_msg.id)] = [event_name, day, month, year, location, description, link,
                                                    interaction.user.id]
    with open("storage.json", "w") as j:
        json.dump(data, j)


@tree.command(description='When done in a designated event channel invites member personally')
async def event_invite(interaction: discord.Interaction, member: discord.Member):
    with open("storage.json", "r") as j:
        data = json.load(j)

    success = False

    for key, value in data["EventApplications"].items():
        if len(value) >= 10 and value[9] == interaction.channel_id:
            invite_msg = await member.send(
                "# Your invited to: " + value[0] + "\nIt will take place: " + str(value[2]) + ", " + str(
                    value[1]) + ", " + str(value[3]) + "\nLocation: " + value[4] + "\nDescription: " + value[
                    5] + "\nLink: " + value[6] + "\n\nReact with a 👍 to join!")
            await invite_msg.add_reaction("👍")
            data["EventInvites"][str(invite_msg.id)] = key
            with open("storage.json", "w") as j:
                json.dump(data, j)
            success = True

    try:
        if success:
            await interaction.response.send_message("member invited")
        else:
            await interaction.response.send_message(
                "Something went wrong. Make sure you are using this command in a designated event channel.")
    except Exception as e:
        print(str(e) + "\nerror thrown while doing specific invite")


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

    if payload.channel_id == ADMIN_DMS and (payload.emoji.name == "🟢" or payload.emoji.name == "🔴") and str(
            payload.message_id) in data["EventApplications"] and payload.user_id == ADMIN_ID:
        admin = client.get_user(ADMIN_ID)
        if payload.emoji.name == "🟢":
            await admin.send("Approved event1")

            # TODO Approved
            guild = client.get_guild(SERVER_ID)
            admin_dms = client.get_channel(ADMIN_DMS)
            output = "# Event Invite\n" + (await admin_dms.fetch_message(payload.message_id)).content[
                                          len("Application waiting for approval:\n\n"):]
            output += "\nplease react 👍 to gain access to the event channel!"
            generalCh = client.get_channel(channels.GENERAL)
            generalPgCh = client.get_channel(channels.GENERAL_PG)
            invite1 = await generalCh.send("🟢\n" + output)
            invite2 = await generalPgCh.send("🔵\n" + output)

            await invite1.add_reaction("👍")
            await invite2.add_reaction("👍")

            event_data = data["EventApplications"][str(payload.message_id)]

            # create role
            role_id = await guild.create_role(name=event_data[0], color=0xF1C40F)

            # create channel
            event_channel = await client.get_channel(channels.EVENTS_CAT).create_text_channel(name=event_data[0])
            await event_channel.set_permissions(role_id, view_channel=True)
            await event_channel.set_permissions(guild.get_role(ROCK), view_channel=False)
            event_author = guild.get_member(event_data[7])
            await event_author.add_roles(role_id)

            data["EventInvites"][str(invite1.id)] = str(payload.message_id)
            data["EventInvites"][str(invite2.id)] = str(payload.message_id)
            data["EventApplications"][str(payload.message_id)].append(role_id.id)
            data["EventApplications"][str(payload.message_id)].append(event_channel.id)
            with open("storage.json", "w") as j:
                json.dump(data, j)

        elif payload.emoji.name == "🔴":
            await admin.send("Denied event")
            data["EventApplications"].pop(str(payload.message_id))
            with open("storage.json", "w") as j:
                json.dump(data, j)
        else:
            await admin.send("Reaction not found")

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
    elif str(payload.message_id) in data["EventInvites"] and payload.emoji.name == "👍":

        try:
            event_role = data["EventApplications"][data["EventInvites"][str(payload.message_id)]][8]
            event_channel = data["EventApplications"][data["EventInvites"][str(payload.message_id)]][9]
            role = client.get_guild(SERVER_ID).get_role(event_role)
            member = client.get_guild(SERVER_ID).get_member(payload.user_id)
            await member.add_roles(role)
            await client.get_channel(event_channel).send(member.name + " has joined the event")
        except Exception as e:
            await client.get_channel(payload.channel_id).send(str(e))
            await client.get_channel(payload.channel_id).send("Error thrown with invalid event invite")

    else:
        print("just reaction")

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
