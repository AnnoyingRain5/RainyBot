# RainyBot

My personal Discord bot!

Rainybot is a fully modular discord bot using the Pycord (discord.py) cogs system.

Modules can be added and removed at any time (and even at runtime using owner-only commands) without disrupting the rest of the bot!

## Features:

* QuickResponse:

Respond to particular keywords in chat with a user-defined message! 

* Translator:

Translate messages across channels, allows you to have, for example, an English general, French general, Spanish general and Japanese general channel
and have up to 5 of them synced together.

The bot uses webhook profile picture and name syncing to make the experience (almost) seamless between channels!

* Admin commands:

The bot has some basic admininstration commands to load, unload and reload cogs.

## Note:

The bot is currently under **heavy** development, so some features may break, and some aspects (especially the translator) are not user friendly.

## Self-Hosting:

If you would like to self-host this bot, that's fine! You'll just need python 3.10 (other versions may work, but I am testing on 3.10) and the following pip packages:

* `py-cord`
* `googletrans==4.0.0rc1`

Note that the exact version of googletrans is *very* important, the stable release does *not* work.

You will also need to make a folder called `db` and two json files called `Translator.json` and `QuickResponses.json`. Each file should only contain `{}`.
This is just to initialize the bot's database.