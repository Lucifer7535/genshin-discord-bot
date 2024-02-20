# GENSHIN DISCORD BOT
Invite the Bot to your own server

[![Badge](https://dcbadge.vercel.app/api/shield/1199307310980419605?bot=true&style=flat&theme=discord-inverted)](https://discord.com/api/oauth2/authorize?client_id=1199307310980419605&permissions=2147765313&scope=bot%20applications.commands)

Join Support Server

[![](https://dcbadge.vercel.app/api/server/Gh9TRfnVEk?style=flat)](https://discord.gg/Gh9TRfnVEk)

## What does this bot do?
This bot can be used to check various information from Genshin Impact, Honkai Impact 3rd & Honkai Star Rail directly in Discord channels, including:

- Query realtime in-game data
    - <u>**Genshin Impact:**</u> <br> Includes Resin, Realm Currency, Parametric Transformer, Expedition completion time, etc.

    - <u>**Star Rail:**</u> <br> Includes Exploration Power, Commission Execution.

- Daily automatic check-in for Hoyolab (includes check-ins for Genshin Impact, Honkai Impact 3rd, Star Rail & Tears of Themis).

- Automatic checks for real-time expeditions (Genshin Impact, Star Rail), Resins, Realm Currency, Parametric Transformer, and Expedition completion. Sends reminders when they are close to being full/complete.

- Check Spiral Abyss records, Forgotten hall records & Pure fiction records.

- Check Traveler's Notes 

- Personal record card (days active, achievements, Anemoculi/Geoculi, world exploration progress, etc.)

- Display the character showcase for any player in Genshin Impact/Star Rail, showing the builds of the showcased characters.

- View in-game announcements for Genshin Impact, including events and gacha information.

- Use the new slash commands with auto-suggest features. No need to memorize command usage.

## Project Folder Structure

```
genshin-discord-bot
├── assets           = Folder for storing assets
|   ├── font         = Fonts used for drawing
|   └── image        = Images and background images used for drawing
├── cogs             = Discord.py cog folder, containing all bot commands
├── cogs_external    = Custom Discord.py cog folder,add your commands.
├── configs          = Bot's Configuration file folder
├── database         = SQLAlchemy ORM, database operation-related code
|   ├── dataclass    = Custom data classes
|   └── legacy       = Old database code used for data migration
├── enka_network     = Code related to Enka Network API
|   └── enka_card    = Submodule, code related to drawing Enka images
├── genshin_db       = Code related to genshin-db API
|   └── models       =  Pydantic models for genshin-db data
├── genshin_py       = Code related to genshin.py
|   ├── auto_task    = Code for automatic scheduled tasks(daily check-in)
|   ├── client       = Code for making requests to APIs
|   └── parser       = Code for converting API data into Discord embeds.
├── star_rail        = Code for Star Rail showcase
└── utility          = Code for utility functions used in this project.
```

## How to Setup the Bot?

### Web Browser
You need to obtain the following in this step:

1. Bot Application ID
2. Bot Token
3. Your Discord server ID

<details><summary>>>> Click to see the complete content <<<</summary>

1. Go to [Discord Developer Portal](https://discord.com/developers/applications "Discord Developer Portal") and log in with your Discord account.

2. Click "New Application" to create an application. Enter the desired name and click "Create."<br>
![](https://i.imgur.com/dbDHEM3.png)
![](https://i.imgur.com/BcJcSnU.png)

3. On the Bot page, click "Add Bot" to add a bot.<br>
![](https://i.imgur.com/lsIgGCi.png)

4. In OAuth2/URL Generator, check "bot," "applications.commands," and "Send Messages." The URL generated at the bottom is the invitation link for the bot. Open the link to invite the bot to your server.<br>
![](https://i.imgur.com/y1Ml43u.png)


### Getting values of bot_token, application_id & test_server_id for config file.

1. On the General Information page, get the Application ID of the bot.<br>
![](https://i.imgur.com/h07q5zT.png)

2. On the Bot page, click "Reset Token" to get the Bot Token.<br>
![](https://i.imgur.com/BfzjewI.png)

3. Right-click on your Discord server name or icon, copy the server ID (enable Developer Mode in Settings -> Advanced -> Developer Mode).<br>
![](https://i.imgur.com/tCMhEhv.png)

</details>

### Locally

- <details><summary>For Windows/Linux :</summary>

    1. Install [Git](https://git-scm.com/download/win) & [Python Version == 3.10](https://www.python.org/downloads/release/python-3100/).<br>

    2. clone this repository using:
    ```
    git clone https://github.com/Lucifer7535/genshin-discord-bot.git
    ```
    3. Install pipenv to install required packages.
    ```
    pip install pipenv
    ```
    4. Open command prompt inside the cloned genshin-discord-bot folder. It should look like ```D:\Genshin-Discord-Bot>```, install the packages using
    ```
    pipenv install
    ```
    5. Use ```pipenv shell``` in the project folder path to run the virtual environment, after the packages are succesfully installed.

    6. It would look like this ```(Genshin-Discord-Bot-4wfjLgXf) D:\Node\genshin-discord-bot>``` where ```(Genshin-Discord-Bot-4wfjLgXf)``` will be your environment name.

    7. Open the <u>**Utility\config.py**</u> file in a text editor. Fill in the Application ID, Server ID, and Bot Token obtained from the web browser. Save the file. Example:
        - application_id: int = 1234567
        - test_server_id: int = 1234567
        - bot_token: str = "abcd12345"

    8. Run the bot using
    ```
    python main.py
    ```
    
</details>

- <details><summary>Using Docker (Windows/Linux): [Recommended]</summary>

    1. Install Docker
        - For Windows install [Docker Desktop](https://www.docker.com/products/docker-desktop/).
        - For Linux install [Docker](https://docs.docker.com/desktop/install/linux-install/).

    2. Create a new folder where you want to setup the bot. for e.g. create a new folder named ```Genshin-Discord-Bot```.

    3. Download the [docker-compose.yml](https://github.com/Lucifer7535/genshin-discord-bot/blob/a948d1f79e0f9024448c562f4f31ba0d25ca4a04/docker-compose.yml) file and place it in that folder you just created.
    
    4. Open the ```docker-compose.yml``` file in a text editor. Fill in the Application ID, Server ID, and Bot Token obtained from the [Web Browser](#web-browser). Save the file. Example:
        - application_id: int = 1234567
        - test_server_id: int = 1234567
        - bot_token: str = "abcd12345"

    5. Open **Command Prompt/Powershell/Terminal** in this folder and enter the following command to run it. Make sure your Docker Desktop is running.
    ```
    docker-compose up
    ```
    
</details>

- <details><summary>For Android (termux):</summary>

    1. Install [Termux Monet](https://github.com/KitsunedFox/termux-monet/releases/tag/v0.118.0-33) based on your device's architecture.

    2. Open the app and run these commands one by one after successfull execution of one after another.
    ```
    pkg update & pkg upgrade
    ```
    ```
    pkg install git
    ```
    ```
    pkg install tur-repo
    ```
    ```
    pkg install python-is-python3.10/tur-packages
    ```
    ```
    pkg install libjpeg-turbo libpng libzmq freetype
    ```
    ```
    pip install greenlet
    ```
    3. clone this repository using:
    ```
    git clone https://github.com/Lucifer7535/genshin-discord-bot.git
    ```
    4. Install pipenv to install required packages.
    ```
    pip install pipenv
    ```
    5. Open the folder using ```cd genshin-discord-bot``` and run
    ```
    pipenv install
    ```
    6. Use ```pipenv shell``` in the project folder path to run the virtual environment, after the packages are succesfully installed.

    7. It would look like this ```(Genshin-Discord-Bot-4wfjLgXf)~genshin-discord-bot>``` where ```(Genshin-Discord-Bot-4wfjLgXf)``` will be your environment name.

    8. Open the <u>**Utility\config.py**</u> file using nano. Use command ```nano utility/config.py
    
    9. Fill in the Application ID, Server ID, and Bot Token obtained from the web browser. Save the file. Example:
        - application_id: int = 1234567
        - test_server_id: int = 1234567
        - bot_token: str = "abcd12345"

    10. Upgrade the pillow package from version 9.5.0 due to some errors in android linux based OS.
    ```
    pip install --upgrade pillow
    ```
    11. Run the bot using
    ```
    python main.py
</details>

### Notes to be Considered:

**Note 1:**<br>
When the bot is running, and you see【System】on_ready: You have logged in as XXXXX, it means the parameters are set correctly, and the bot has started successfully. The bot will automatically sync all commands to your test server, known as "local sync."

**Note 2:**<br>
If you can't see commands after typing /, try refreshing with CTRL + R or completely close and restart Discord.

**Note 3:**<br>
To use the bot in multiple servers, type $jsk sync in the bot's DM and wait a few minutes for Discord to push the commands. This is known as "global sync."

Additionally, the bot includes the jsk command to load/reload modules, sync commands, execute code, etc. Refer to the [jishaku documentation](https://github.com/Gorialis/jishaku) for more information.<br>

To use jsk commands:

Use them in the bot's DM, for example: $jsk ping.<br>
Tag the bot in a regular channel, for example: @bot_username jsk ping.


## SCREENSHOTS:
<details><summary>>>> Click to view screenshots <<<</summary>
<br>

1. Bot's Slash Commands<br>
![](https://i.imgur.com/zwgJdqO.png)<br>
<br>

2. /showcase-characters<br>
![](https://i.imgur.com/G3IrQcr.png)<br>
<br>

3. /abyss-record<br>
![](https://i.imgur.com/46795lR.png)<br>
<br>

4. /characters-list<br>
![](https://i.imgur.com/LdyWcUL.png)<br>
<br>

5. /diary_notes<br>
![](https://i.imgur.com/LSOmvoX.png)<br>
<br>

6. /game-notices<br>
![](https://i.imgur.com/UEqzuWO.png)<br>
<br>

7. /instant-notes<br>
![](https://i.imgur.com/V0FASxg.png)<br>
<br>

8. /record-card(data overview)<br>
![](https://i.imgur.com/dcelsvr.png)<br>
<br>

9. /record-card(world exploration)<br>
![](https://i.imgur.com/CfTmFrR.png)<br>
<br>

10. /schedule command<br>
![](https://i.imgur.com/rZ7Vu94.png)<br>
<br>

11. daily check-in<br>
![](https://i.imgur.com/8a63R7n.png)<br>
<br>

12. scheduled reminders<br>
![](https://i.imgur.com/z61kUh1.png)
</details>

## Acknowledgments
SOURCE CODE:
- [KT-Yeh/Genshin-Discord-Bot](https://github.com/KT-Yeh/Genshin-Discord-Bot)

API：
- Hoyolab: https://github.com/thesadru/genshin.py
- Discord: https://github.com/Rapptz/discord.py
- Enka Network: https://github.com/EnkaNetwork/API-docs
- Mihomo: https://march7th.xiaohei.moe/en/resource/mihomo_api.html
- Genshin-DB: https://github.com/theBowja/genshin-db

Card：
- [hattvr/enka-card](https://github.com/hattvr/enka-card)
- [DEViantUA/HSRCard](https://github.com/DEViantUA/HSRCard)
- [DEViantUA/GenshinPyRail](https://github.com/DEViantUA/GenshinPyRail)

Misc：
- [Apollo-Roboto/discord.py-ext-prometheus](https://github.com/Apollo-Roboto/discord.py-ext-prometheus)
