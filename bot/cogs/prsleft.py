from discord.ext import commands
import logging
import aiohttp
import discord

bot = commands.Bot(command_prefix='.', description='pr bot')

@bot.command()
async def prsleft(github_username: str):
    base_url = "https://api.github.com/search/issues?q="
    not_label = "invalid"
    action_type = "pr"
    is_query = f"public+author:{github_username}"
    date_range = "2018-10-01..2018-11-01"
    per_page = "300"
    query_url = (
        f"{base_url}"
        f"-label:{not_label}"
        f"+type:{action_type}"
        f"+is:{is_query}"
        f"+created:{date_range}"
        f"&per_page={per_page}"
    )

    headers = {"user-agent": "Discord Python Hactoberbot"}
    async with aiohttp.ClientSession() as session:
        async with session.get(query_url, headers=headers) as resp:
            jsonresp = await resp.json()

    if "message" in jsonresp.keys():
        # One of the parameters is invalid, short circuit for now
        api_message = jsonresp["errors"][0]["message"]
        logging.error(f"GitHub API request for '{github_username}' failed with message: {api_message}")
        return
    else:
        if jsonresp["total_count"] == 0:
            # Short circuit if there aren't any PRs
            logging.info(f"No Hacktoberfest PRs found for GitHub user: '{github_username}'")
            return
        else:
            tmp = {jsonresp['total_count']}
            tmp = tmp.pop()
            rem = 5 - tmp
            if rem<0:
                rem=0
            message = (
                f"The user: {github_username} has {rem} pull requests remaining for Hacktoberfest!\n" +
                f"The {tmp} completed pull requests were:\n\n"
            )
            for item in jsonresp["items"]:
                repo = item["repository_url"]
                title = item["title"]
                state = item["state"]
                prinfo = (
                    f"Repository URL: {repo}\n"+
                    f"Pull request title: {title}\n"+
                    f"State: {state}\n\n"
                )
                message+=(prinfo)

            await bot.say(message)



bot.run('token')
