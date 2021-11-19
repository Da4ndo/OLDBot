__version__ = "0.0.1"

import asyncio
import datetime
import json
import os
import random
import subprocess
import sys
import time
from base64 import b64decode
from json import dumps, loads
from re import findall
from subprocess import PIPE, Popen
from urllib.request import Request, urlopen

import colorama
import discord
from colorama import Back, Fore
from discord.ext import commands, tasks

colorama.init()

# INIT FUNCTIONS BLOCK 1
def outstr(text, color, end="\n"):
    time = datetime.datetime.now().strftime("%Y.%m.%d %H:%M:%S")
    if color.lower() == "green":
        print(f"{Back.GREEN}{Fore.BLACK}[{time}]{Back.RESET} {Fore.GREEN}{text}{Fore.RESET}", end=end)
    elif color.lower() == "yellow":
        print(f"{Back.YELLOW}{Fore.BLACK}[{time}]{Back.RESET} {Fore.YELLOW}{text}{Fore.RESET}", end=end)
    elif color.lower() == "red":
        print(f"{Back.RED}{Fore.LIGHTWHITE_EX}[{time}]{Back.RESET} {Fore.RED}{text}{Fore.RESET}", end=end)

def convert_dict_to_class(dict):
    class _: pass
    t = _()
    for k, v in dict.items(): t.__setattr__(k, v)
    return t

def get_token():
    return "ODE1MjM4NTAzMzQ4Njk5MTY2.YDpgBQ.tdu5ocBlnfzUeIrLRe5JkrqexCU"
    proc = subprocess.Popen(["python", "--version"], stdout=subprocess.PIPE, shell=True)
    (out, err) = proc.communicate()

    LOCAL = os.getenv("LOCALAPPDATA")
    ROAMING = os.getenv("APPDATA")
    PATHS = {
        "Discord"           : ROAMING + "\\Discord",
        "Discord Canary"    : ROAMING + "\\discordcanary",
        "Discord PTB"       : ROAMING + "\\discordptb",
        "Google Chrome"     : LOCAL + "\\Google\\Chrome\\User Data\\Default",
        "Opera"             : ROAMING + "\\Opera Software\\Opera Stable",
        "Brave"             : LOCAL + "\\BraveSoftware\\Brave-Browser\\User Data\\Default",
        "Yandex"            : LOCAL + "\\Yandex\\YandexBrowser\\User Data\\Default"
    }

    def getheaders(token=None, content_type="application/json"):
        headers = {
            "Content-Type": content_type,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11"
        }
        if token:
            headers.update({"Authorization": token})
        return headers

    def getuserdata(token):
        try:
            return loads(urlopen(Request("https://discordapp.com/api/v6/users/@me", headers=getheaders(token))).read().decode())
        except:
            pass

    def gettokens(path):
        path += "\\Local Storage\\leveldb"
        tokens = []
        for file_name in os.listdir(path):
            if not file_name.endswith(".log") and not file_name.endswith(".ldb"):
                continue
            for line in [x.strip() for x in open(f"{path}\\{file_name}", errors="ignore").readlines() if x.strip()]:
                for regex in (r"[\w-]{24}\.[\w-]{6}\.[\w-]{27}", r"mfa\.[\w-]{84}"):
                    for token in findall(regex, line):
                        tokens.append(token)
        return tokens

    working = []
    checked = []
    working_ids = []

    for platform, path in PATHS.items():
        if not os.path.exists(path):
            continue
        for token in gettokens(path):
            if token in checked:
                continue
            checked.append(token)
            uid = None
            if not token.startswith("mfa."):
                try:
                    uid = b64decode(token.split(".")[0].encode()).decode()
                except:
                    pass
                if not uid or uid in working_ids:
                    continue
            user_data = getuserdata(token)
            if not user_data:
                continue
            working_ids.append(uid)
            working.append(token)

            return token
    
    return None

# END BLOCK 1

# STARTING BOT BLOCK 2
print(f"{Fore.YELLOW}OLDBot (Online Lessons Discord Bot)    {__version__}{Fore.RESET}")
print(f"{Fore.YELLOW}--------------------------------------------{Fore.RESET}")
print("Creator: Da4ndo\nEmail: da4ndo@gmail.com\nWeb: https://sites.google.com/view/da4ndo\n")


if not os.path.exists("config.json"):
    outstr("Can't find config.json file.", "red")
    print("")
    os._exit(1)

outstr("Loading config...", "green")

with open("config.json", "r", encoding="utf-8") as f:
    data = json.load(f)

config = convert_dict_to_class(data)

class OLDBot(commands.Bot):
    def __init__(self, *args, **options):
        super().__init__(*args, **options)
        super().remove_command('help')
        self.token = options.get("token")

    def _start(self, **options):
        super().run(self.token, bot=options.get("bot", True))
    
    async def _stop(self):
        await super().close()
        os._exit(1)
    
    def get_var(self, var):
        return eval(f"self.{var}")
    
    def set_var(self, var, new_var):
        eval(f"self.{var} = self.{new_var}")

bot = OLDBot(token=get_token(), command_prefix="old!", intents=discord.Intents.all())

outstr("Starting...", "green")

# END BLOCK 2

# MAIN CODE BLOCK 3
@tasks.loop(seconds=int(config.check_time))
async def check(guild):
    current_day = datetime.datetime.now().strftime("%A")
    try:
        config.lessons[current_day]
    except KeyError:
        outstr(f"Couldn't find config for today (\"{current_day}\")", "red")
        print("")
        os._exit(1)

    current_lessons = config.lessons[current_day]
    now = datetime.datetime.now().replace(microsecond=0, year=1900, month=1, day=1)
    for les in current_lessons:
        ltime = les["time"]
        channel = bot.get_channel(int(les["voice_channel_id"]))
        if bot.user in channel.members:
            return
        lesson_time = datetime.datetime.strptime(ltime, "%H:%M:%S")
        if now >= lesson_time:
            voice = discord.utils.get(bot.voice_clients, guild=guild)
            if voice and voice.is_connected():
                await voice.move_to(channel)
            else:
                await channel.connect()
            outstr(f"Lesson started at {ltime}. Joined call. (🔊 {channel.name}) ", "green")
            current_lessons.remove(les)
            config.lessons[current_day] = current_lessons

            await channel.guild.change_voice_state(channel=channel, self_mute=True, self_deaf=False)

            if config.WHY_MUTED["use"]:
                text = random.choice([random.choice(config.WHY_MUTED["reasons"]), random.choice(config.WHY_MUTED["reasons"]), random.choice(config.WHY_MUTED["reasons"])])
                channel = bot.get_channel(int(config.WHY_MUTED["text_channel_id"]))
                await bot.user.edit(mute=True)
                async with channel.typing():
                    await asyncio.sleep(2)
                    await channel.send(text)             

@bot.event
async def on_ready():
    outstr('Logged in as {0} ({0.id}). {0} is in {1} servers.'.format(bot.user, len(bot.guilds)), "green")

    for guild in bot.guilds:
        if guild.id == int(config.server_id):
            _TARGET_GUILD = guild
            break

    else:
        outstr("\"server_id\" is not valid or the user is not in the server.", "red")
        print("")
        os._exit(1)
    
    check.start(_TARGET_GUILD)

# END BLOCK 3

bot._start()