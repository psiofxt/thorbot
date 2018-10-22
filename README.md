# Thorbot

A telegram bot that syncs with a container-ized mongo instance allowing admins to `/warn`, `/kick`, `/ban`, among other commands.

## Install
This bot is intended to work inside Docker containers and is recommended to be run one per group you wish to moderate. This
increases performance and keeps the Mongo instance nice and tidy.

Simply edit the Dockerfile to include your `GROUP_ID` and bot's `BOT_API_KEY` or include these in an external `.env` file
for your `docker-compose up -d` command.

## Commands
- `/warn [username]` -- increments the warning of the user
- `/clear_warnings [username]` -- clears all warnings for the user
- `/permit [username] [num]` -- permits the user the ability to post `num` links in chat
