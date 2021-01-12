import requests, configparser, asyncio, aiohttp, tqdm, itertools

limit = 100  # Number of messages to scan in the channel. MAX: 100
baseurl = "https://discord.com/api/v8"


async def get_server_ids(session, auth_token):
    async with session.get(
        f"{baseurl}/users/@me/guilds",
        headers={"Authorization": auth_token},
    ) as response:
        response = await response.json()
    server_ids = []
    for server in response:
        server_ids.append(server["id"])
    return server_ids


async def get_channel_ids(session, auth_token, server_id):
    async with session.get(
        f"{baseurl}/guilds/{server_id}/channels",
        headers={"Authorization": auth_token},
    ) as response:
        response = await response.json()

    channel_ids = []
    for channel in response:
        if channel["type"] == 0 or channel["type"] == 4 or channel["type"] == 5:
            channel_ids.append(channel["id"])
    return channel_ids


async def get_messages(session, auth_token, channel_id):
    while True:
        async with session.get(
            f"{baseurl}/channels/{channel_id}/messages?limit={limit}",
            headers={"Authorization": auth_token},
        ) as response:
            response = response
            headers = response.headers
            messages = await response.json()
        if "Retry-After" in headers:
            await asyncio.sleep(5)
            continue
        else:
            break
    return {"messages": messages, "channel_id": channel_id}


def evaluate_message(message):
    if message == []:
        print("No message")
        return

    if "bot" in message["author"] and "reactions" in message:
        for reaction in message["reactions"]:
            if reaction["emoji"]["name"] == "🎉" and reaction["me"] == False:
                return True

    return False


async def react_messages(session, auth_token, channel_id, message_id):
    while True:
        async with session.put(
            f"{baseurl}/channels/{channel_id}/messages/{message_id}/reactions/🎉/@me",
            headers={"Authorization": auth_token},
        ) as response:
            headers = response.headers

        if "Retry-After" in headers:
            await asyncio.sleep(10)
            continue
        else:
            break
    return


async def main(auth_token):
    async with aiohttp.ClientSession() as session:  # create aiohttp session

        ### GET server IDs
        print("Fetching servers...")
        tasks = [get_server_ids(session, auth_token)]
        for t in tqdm.tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            server_ids = await t

        ### GET channel IDs
        print("Fetching channels...")
        tasks = [
            get_channel_ids(session, auth_token, server_id) for server_id in server_ids
        ]
        channel_ids = []
        for t in tqdm.tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            channel_ids.append(await t)
        channel_ids = list(itertools.chain.from_iterable(channel_ids))

        ### GET messages
        print("Fetching messages...")
        tasks = [
            get_messages(session, auth_token, channel_id) for channel_id in channel_ids
        ]
        channels = []
        for t in tqdm.tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            channels.append(await t)

        giveaways = []
        for channel in channels:
            for message in channel["messages"]:
                if type(message) == dict and evaluate_message(message) == True:
                    giveaways.append(
                        {"messages": message, "channel_id": channel["channel_id"]}
                    )
        print("--------------------------")
        print(f"{len(giveaways)} giveaways found!")
        print("--------------------------")

        ### React to giveaways
        print("Joining...")
        giveaway_ids = []
        for item in giveaways:
            giveaway_ids.append(
                {
                    "message_id": item["messages"]["id"],
                    "channel_id": item["channel_id"],
                }
            )
        tasks = [
            react_messages(
                session,
                auth_token,
                giveaway_id["channel_id"],
                giveaway_id["message_id"],
            )
            for giveaway_id in giveaway_ids
        ]

        responses = []
        for t in tqdm.tqdm(asyncio.as_completed(tasks), total=len(tasks)):
            responses.append(await t)


def init():
    config = configparser.ConfigParser()
    config.read("config.ini")
    try:
        token = config["DEFAULT"]["token"]
    except KeyError:
        config["DEFAULT"]["token"] = input(
            "Input authentification token here: "
        ).strip()
        with open("config.ini", "w") as configfile:
            config.write(configfile)
    auth_token = config["DEFAULT"]["token"]

    print()
    print("Read token from file: " + auth_token)
    print()

    with requests.get(
        baseurl + "/users/@me", headers={"Authorization": token}
    ) as response:
        response = response

    if response.status_code == 200:
        user = response.json()["username"]
        print("----------------------")
        print("Logged in with user " + user)
        print("----------------------")
        asyncio.get_event_loop().run_until_complete(main(auth_token))
        print("All servers completed!")

    elif response.status_code == 401:
        open("config.ini", "w").close()  # clear config file
        print("Wrong token!")
        print()
        init()
    elif response.status_code == 429:
        retry_after = response.headers["Retry-After"]
        exit(
            f"Too many requests! \nPlease retry again in {retry_after} seconds ({round(int(retry_after) / 60)} minute(s)).\nAlternatively, change your IP."
        )
    else:
        exit(f"Unknown error! The server returned {response}.")


import warnings

if __name__ == "__main__":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        init()