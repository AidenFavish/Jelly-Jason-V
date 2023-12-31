from time import sleep
import random
import discord
import json
import channels
from secrets import tokenD
import datetime
import time
import asyncio
import os
import backgroundTasks
import customCommands
import psutil
from langdetect import detect
import sys

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
MANUAL_ADD = ["733148326337314936"]

FLAG = 13


class aclient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.synced = False  # added to make sure that the command tree will be synced only once
        self.added = False


client = aclient()
tree = discord.app_commands.CommandTree(client)
# get datetime of last restarted
time_logged = str(datetime.datetime.now())
other_languages = ['nl', 'fr', 'de', 'he', 'hi', 'ja', 'ko', 'pl', 'pt', 'ru', 'es', 'vi', 'yi', 'zh', 'zh-cn', 'af']


async def daily_check(force: bool = False):
    with open("storage.json", "r") as j:
        data = json.load(j)
    # print(time.time() / 86400 + 0.5, flush=True)  # +0.75 is to offset utc time
    days_since_epoch = (datetime.datetime.now() - datetime.datetime(day=28, month=7, year=2022, hour=2, minute=32,
                                                                    second=30)).days
    if data["Date"] != int(days_since_epoch) or force:
        print("Daily check triggered")
        data["Date"] = int(days_since_epoch)
        with open("storage.json", "w") as j:
            json.dump(data, j)

        # Update member info
        for i in client.get_guild(SERVER_ID).members:
            if str(i.id) in data["Whitelist"]:
                member_info = {"NAME": i.name, "PFP": i.avatar.url,
                               "COLOR": [i.top_role.color.r, i.top_role.color.g, i.top_role.color.b],
                               "MANUAL": data["Whitelist"][str(i.id)]["MANUAL"]}
                data["Whitelist"][str(i.id)] = member_info

        # one a day code here
        temp_events = []
        for key, value in data["EventApplications"].items():
            days_until = (datetime.datetime(day=value[1], month=value[2], year=value[3], hour=23, minute=59,
                                            second=59) - datetime.datetime.now()).days
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
        testingCh = client.get_channel(channels.TESTING)
        await testingCh.send("Daily check\nRebooting...")
        os.system('git pull')
        await asyncio.sleep(5)
        os.system('reboot')

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

    await daily_check()

    await client.get_channel(channels.TESTING).send("Ready")


@client.event
async def on_member_join(member):
    with open("storage.json", "r") as j:
        data = json.load(j)

    if str(member.id) in data["Whitelist"] and not data["Whitelist"][str(member.id)]["MANUAL"]:
        rock_role = client.get_guild(SERVER_ID).get_role(947983184409272340)
        await member.add_roles(rock_role)

        with open("storage.json", "r") as j:
            data = json.load(j)

        choose_msg = await member.send(
            "Welcome to The Unkillable Server!\nYou are on the whitelist so you can jump right in!\nWould you like\nPG and up channels 🔵\nOr\nPG and under channels 🟢")
        data["ChoosePG"].append(choose_msg.id)
        await choose_msg.add_reaction("🔵")
        await choose_msg.add_reaction("🟢")

        with open("storage.json", "w") as j:
            json.dump(data, j)

    elif str(member.id) in data["Whitelist"] and data["Whitelist"][str(member.id)]["MANUAL"]:
        rock_role = client.get_guild(SERVER_ID).get_role(947983184409272340)
        await member.add_roles(rock_role)
        await member.send(
            "Welcome to The Unkillable Server\nYou are on the whitelisted and listed as manual role entry\nYou can enjoy some of our Rock channels while we update your roles!")


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


@tree.command(name='leave_event', description='When done in a designated event channel, you will leave the event')
async def leave_event(interaction: discord.Interaction):
    with open("storage.json", "r") as j:
        data = json.load(j)

    event_key = "None"
    for key, value in data["EventApplications"].items():
        if len(value) >= 10 and value[9] == interaction.channel_id:
            event_key = str(key)
            break

    if event_key == "None":
        try:
            await interaction.response.send_message(
                "Something went wrong, make sure your in a designated event channel")
        except Exception as e:
            await client.get_user(ADMIN_ID).send(str(e) + "\nSomething went wrong when leaving an event")
        return

    try:
        event_role = data["EventApplications"][event_key][8]
        role = client.get_guild(SERVER_ID).get_role(event_role)
        member = client.get_guild(SERVER_ID).get_member(interaction.user.id)
        await member.remove_roles(role)
        await interaction.channel.send(member.name + " has left the event")
    except Exception as e:
        await client.get_channel(interaction.channel.id).send(str(e.__cause__))
        await client.get_channel(interaction.channel.id).send("Error thrown when trying to leave event")


@tree.command(description='When done in a designated event channel invites member personally')
async def event_invite(interaction: discord.Interaction, member: discord.Member):
    with open("storage.json", "r") as j:
        data = json.load(j)

    success = False

    for key, value in data["EventApplications"].items():
        if len(value) >= 10 and value[9] == interaction.channel_id:
            invite_msg = await member.send(
                "# Your invited to: " + value[0] + "\nIt will take place: " + str(
                    datetime.date(day=value[1], month=value[2], year=value[3]).strftime(
                        '%A, %B %d, %Y')) + "\nLocation: " + value[4] + "\nDescription: " + value[
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


@tree.command(name='change_date', description='When done in a designated event channel, changes the date of the event')
async def change_date(interaction: discord.Interaction, day: int, month: int, year: int):
    with open("storage.json", "r") as j:
        data = json.load(j)

    success = False

    for key, value in data["EventApplications"].items():
        if len(value) >= 10 and value[9] == interaction.channel_id:
            data["EventApplications"][key][1] = day
            data["EventApplications"][key][2] = month
            data["EventApplications"][key][3] = year
            with open("storage.json", "w") as j:
                json.dump(data, j)

            await client.get_channel(channels.GENERAL).send(
                "# Notice\nThe event ``" + value[0] + "`` has had its date change to ``"
                + str(datetime.date(day=day, month=month, year=year).strftime('%A, %B %d, %Y')) + "``")

            success = True

    try:
        if success:
            await interaction.response.send_message("date changed")

        else:
            await interaction.response.send_message(
                "Something went wrong. Make sure you are using this command in a designated event channel.")
    except Exception as e:
        print(str(e) + "\nerror thrown while doing change date")


@tree.command(name='restart', description='Owner only')
async def restart(interaction: discord.Interaction):
    try:
        if interaction.user.id == ADMIN_ID:
            await interaction.response.send_message('Restarting...')
            os.system('git pull')
            await asyncio.sleep(5)
            os.system('reboot')
        else:
            await interaction.response.send_message('You need to be the admin to use this command')
    except Exception as e:
        await client.get_user(ADMIN_ID).send(str(e) + "\nError thrown when trying to restart")


@tree.command(name='translate', description='translate text to english')
async def translate(interaction: discord.Interaction, text_in_other_language: str):
    translated = await customCommands.translate(text_in_other_language)
    embed = discord.Embed(
        title=interaction.user.name + " translated message (" + str(detect(text_in_other_language)) + ")",
        description=str(translated), color=interaction.user.top_role.color)
    await interaction.response.send_message(embed=embed)
    print(translated)


@tree.command(name='system_summary', description='For debug purposes')
async def system_summary(interaction: discord.Interaction):
    file = discord.File("storage.json")
    file2 = discord.File("/home/aiden/Programs/my.log")

    # Get the current CPU usage
    cpu_usage = psutil.cpu_percent()

    # Get the current memory usage
    memory_usage = psutil.virtual_memory().used / psutil.virtual_memory().total

    # Get the current CPU temperature
    try:
        cpu_temp = psutil.sensors_temperatures()['cpu_thermal'][0].current
    except Exception as e:
        print(e)
        cpu_temp = -9999.0

    summary = "Last restarted: " + time_logged + "\n"
    summary += "Flag: " + str(FLAG) + "\n"
    summary += 'CPU usage: {}%'.format(cpu_usage) + "\n"
    summary += 'Memory usage: {}%'.format(memory_usage) + "\n"
    summary += 'CPU temperature: {}°C'.format(cpu_temp)
    await interaction.response.send_message(file=file, content=summary)
    await interaction.channel.send(file=file2)


@tree.command(name='request_command', description='Owner only!')
async def request_command(interaction: discord.Interaction, command: str):
    if interaction.user.id == ADMIN_ID:
        try:
            os.system(command)
        except Exception as e:
            await interaction.response.send_message("Error thrown: " + str(e))
    else:
        await interaction.response.send_message("You must be the owner to use this command")


@tree.command(name='add_whitelist', description='Owner only!')
async def add_whitelist(interaction: discord.Interaction, user_id: str, manual: bool = False):
    try:
        if interaction.user.id == ADMIN_ID:
            i = client.get_user(int(user_id))
            print(int(user_id))
            with open("storage.json", "r") as j:
                data = json.load(j)

            member_info = {"NAME": "Loading", "PFP": "none",
                           "COLOR": [100, 100, 100], "MANUAL": manual}
            data["Whitelist"][str(user_id)] = member_info

            with open("storage.json", "w") as j:
                json.dump(data, j)
            await interaction.response.send_message("Added")
        else:
            await interaction.response.send_message("Owner only!")
    except Exception as e:
        await client.get_channel(channels.TESTING).send("Error thrown when adding whitelist: " + str(e))


@tree.command(name='remove_whitelist', description='Owner only!')
async def remove_whitelist(interaction: discord.Interaction, user_id: str):
    try:
        if interaction.user.id == ADMIN_ID:
            with open("storage.json", "r") as j:
                data = json.load(j)

            data["Whitelist"].pop(str(user_id))

            with open("storage.json", "w") as j:
                json.dump(data, j)
            await interaction.response.send_message("Removed")
        else:
            await interaction.response.send_message("Owner only!")
    except Exception as e:
        await client.get_channel(channels.TESTING).send("Error thrown when removing whitelist: " + str(e))


@tree.command(name='quit', description='Owner only')
async def quit(interaction: discord.Interaction):
    try:
        if interaction.user.id == ADMIN_ID:
            await interaction.response.send_message('Quitting...')
        else:
            await interaction.response.send_message('You need to be the admin to use this command')
    except Exception as e:
        await client.get_user(ADMIN_ID).send(str(e) + "\nError thrown when trying to quit")
    await asyncio.sleep(2)
    if interaction.user.id == ADMIN_ID:
        sys.exit()


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
            await admin.send("Approved event")

            # TODO Approved
            guild = client.get_guild(SERVER_ID)
            admin_dms = client.get_channel(ADMIN_DMS)
            output = "# Event Invite\n" + (await admin_dms.fetch_message(payload.message_id)).content[
                                          len("Application waiting for approval:\n\n"):]
            output += "\nplease react 👍 to gain access to the event channel!"
            generalCh = client.get_channel(channels.GENERAL)
            #generalPgCh = client.get_channel(channels.GENERAL_PG)
            invite1 = await generalCh.send("🟢\n" + output)
            #invite2 = await generalPgCh.send("🔵\n" + output)

            await invite1.add_reaction("👍")
            #await invite2.add_reaction("👍")

            event_data = data["EventApplications"][str(payload.message_id)]

            # create role
            role_id = await guild.create_role(name=event_data[0], color=0xF1C40F)

            # create channel
            try:
                event_channel = await client.get_channel(channels.EVENTS_CAT).create_text_channel(name=event_data[0])
                await event_channel.edit(sync_permissions=False)
                await event_channel.set_permissions(role_id, view_channel=True)
                await event_channel.set_permissions(guild.get_role(ROCK), view_channel=False)
                event_author = guild.get_member(event_data[7])
                await event_author.add_roles(role_id)
            except Exception as e:
                await client.get_user(ADMIN_ID).send(str(e) + "\nError with creating channel")

            data["EventInvites"][str(invite1.id)] = str(payload.message_id)
            #data["EventInvites"][str(invite2.id)] = str(payload.message_id)
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
                    await client.get_channel(channels.CENSORED_LOG).send(
                        bad_msg.author.name + ' said "' + bad_msg.content + '"')
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
            if role not in member.roles:
                await member.add_roles(role)
                await client.get_channel(event_channel).send(member.name + " has joined the event")
        except Exception as e:
            await client.get_channel(payload.channel_id).send(str(e))
            await client.get_channel(payload.channel_id).send("Error thrown with invalid event invite")

    elif payload.emoji.name == "❔":
        try:
            message = await client.get_channel(payload.channel_id).fetch_message(payload.message_id)
            lang: str = detect(str(message.content))
            translated = await customCommands.translate(message.content)
            embed = discord.Embed(title=message.author.name + " translated message (" + lang + ")",
                                  url=message.jump_url,
                                  description=str(translated), color=message.author.top_role.color)
            await client.get_channel(channels.TRANSLATOR).send(embed=embed)
            print(translated)
        except Exception as e:
            await client.get_channel(channels.TESTING).send("Error thrown with translator: " + str(e))
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
    return


client.run(tokenD)
