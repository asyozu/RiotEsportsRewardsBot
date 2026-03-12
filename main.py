#!/usr/bin/env python3
import aiohttp, asyncio, json, urllib.parse
from datetime import datetime, timezone, timedelta
from contextlib import suppress

API_URL = 'https://esports-api.lolesports.com/persisted/gw/get'
WATCH_URL = 'https://rex.rewards.lolesports.com/v1/events/watch'
EARNED_DROPS_URL = "https://account.service.lolesports.com/fandom-account/v1/earnedDrops?locale=en_GB&site=LOLESPORTS"

class Main:
    def __init__(self):
        self.refresh_token = ""
        self.access_token = None
        self.cache = {}
        self.notify_enabled = False
        self.telegram_bot_token = ""
        self.telegram_chat_id = ""

    async def refresh(self, session: aiohttp.ClientSession) -> bool:
        session.cookie_jar.update_cookies({"__Secure-refresh_token": self.refresh_token},response_url=aiohttp.client_reqrep.URL("https://.lolesports.com/"))
        try:
            await session.get("https://xsso.lolesports.com/refresh")
        except Exception:
            return False
        self.access_token = session.cookie_jar._cookies[("lolesports.com", "")]["__Secure-access_token"].value
        return True

    async def notify(self, session: aiohttp.ClientSession, i: dict):
        drop = ", ".join(j['localizedInventory']['title']['en_US'] for j in i['inventory'])
        text = f"Title: {i['dropsetTitle']}\nDescription: {i['dropsetDescription']}\nDrop: {drop}"
        url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
        payload = {"chat_id": self.telegram_chat_id, "text": text}
        await session.post(url, data=payload)

    async def get_riot_id(self, session: aiohttp.ClientSession) -> str:
        a = json.loads(urllib.parse.unquote(session.cookie_jar._cookies[("lolesports.com", "")]["__Secure-id_hint"].value))["acct"]
        return f"{a['game_name']}#{a['tag_line']}"

    async def get_total_drops(self, session: aiohttp.ClientSession) -> list:
        async with session.get(EARNED_DROPS_URL, headers={"Authorization": f"Bearer {self.access_token}"}) as r:
            r.raise_for_status()
            return await r.json(content_type=None)

    async def fetch_json(self, session, url):
        async with session.get(url, headers={'x-api-key': '0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z'}) as r:
            r.raise_for_status()
            return await r.json(content_type=None)

    async def watch(self, session, body):
        async def post():
            async with session.post(WATCH_URL, headers={'Authorization': f'Bearer {self.access_token}'}, json=body) as r:
                try:
                    return await r.json()
                except aiohttp.ContentTypeError:
                    return None
        if (data := await post()) is None and await self.refresh(session):
            return await post()
        return data

    async def process_event(self, event, session):
        if event['id'] not in self.cache:
            details = (await self.fetch_json(session, f"{API_URL}EventDetails?hl=en-US&id={event['id']}"))["data"]["event"]
            stream = next((i for i in details["streams"] if "provider" in i and "parameter" in i), None)
            if not stream:
                return
            self.cache[event['id']] = {"tournament_id": details["tournament"]["id"],"stream": {"parameter": stream["parameter"], "provider": stream["provider"]}}
        now_utc = datetime.now(timezone.utc)
        payload = {"stream_id": self.cache[event['id']]["stream"]["parameter"],"source": self.cache[event['id']]["stream"]["provider"],"stream_position_time": now_utc.isoformat().replace("+00:00", "Z"),"geolocation": {"code": "VN", "area": "AS", "locale": "vi-VN"},"tournament_id": self.cache[event['id']]["tournament_id"]}
        await self.watch(session, payload)
        print(f"{now_utc.astimezone(timezone(timedelta(hours=7))):%H:%M:%S} | {event['league']['name']}")

    async def next_live(self, session) -> int:
        now = datetime.now(timezone.utc)
        events = (await self.fetch_json(session, f"{API_URL}Schedule?hl=en-US"))['data']['schedule']['events']
        future_events = (datetime.fromisoformat(i['startTime'].replace('Z', '+00:00')) - now for i in events if i['state'] == 'unstarted' and 'startTime' in i)
        return max(0, int(min(future_events, default=timedelta()).total_seconds()))

    async def run(self):
        async with aiohttp.ClientSession(headers={"Referer": "https://lolesports.com/"}) as session:
            if not await self.refresh(session):
                print("Cannot get initial access_token.")
                return
            seen_ids = {i["dropID"] for i in await self.get_total_drops(session)}
            print(f"Logged in as: {await self.get_riot_id(session)} | totalDrop: {len(seen_ids)}")
            while True:
                try:
                    events = (await self.fetch_json(session, f"{API_URL}Live?hl=en-US"))['data']['schedule']['events']
                    self.cache = {j: v for j, v in self.cache.items() if j in {i["id"] for i in events}}
                    if events:
                        await asyncio.gather(*(self.process_event(i, session) for i in events))
                        new_drops = [i for i in await self.get_total_drops(session) if i['dropID'] not in seen_ids]
                        if self.notify_enabled:
                            await asyncio.gather(*(self.notify(session, i) for i in new_drops))
                        seen_ids |= {i['dropID'] for i in new_drops}
                        await asyncio.sleep(60)
                        continue
                    await asyncio.sleep(await self.next_live(session))
                except Exception as e:
                    print(f"Error: {e}")
                    await asyncio.sleep(10)

if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        asyncio.run(Main().run())