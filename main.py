import asyncio
import json
import aiohttp
from datetime import datetime, timezone

RIOT_ACCESS_TOKEN = ''

LIVE_DATA_URL = 'https://esports-api.lolesports.com/persisted/gw/getLive?hl=en-GB'
EVENT_DETAILS_URL = 'https://esports-api.lolesports.com/persisted/gw/getEventDetails?hl=en-GB&id={event_id}'
REWARDS_URL = 'https://rex.rewards.lolesports.com/v1/events/watch'
HEADERS = {'x-api-key': '0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z'}

async def fetch_json(session, url, headers=None):
    async with session.get(url, headers=headers) as response:
        response.raise_for_status()
        return await response.json()
async def send_rewards(session, token, body):
    headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
    async with session.post(REWARDS_URL, headers=headers, json=body) as response:
        response_data = await response.json()
        print(f"Received: {response_data}")
async def process_event(event, session, current_time):
    if event['type'] == 'match':
        teams = event.get('match', {}).get('teams', [])
        print(f"Currently broadcasting {event['league']['name']} Match: {event['blockName']} - {teams[0]['name']} ({teams[0]['code']}) vs. {teams[1]['name']} ({teams[1]['code']})")
    elif event['type'] == 'show':
        print(f"Currently broadcasting {event['league']['name']} Show")
    else:
        print(f"Currently broadcasting {event['league']['name']} {event['type']}")
    event_details_data = await fetch_json(session, EVENT_DETAILS_URL.format(event_id=event['id']), HEADERS)
    streams = event_details_data.get('data', {}).get('event', {}).get('streams', [])
    stream = next((s for s in streams if s.get('locale', '').startswith('en')), streams[0] if streams else None)
    tournament_id = event_details_data.get('data', {}).get('event', {}).get('tournament', {}).get('id')
    body = {
        'stream_id': stream['parameter'],
        'source': stream['provider'],
        'stream_position_time': current_time,
        'geolocation': {'code': 'VN', 'area': 'AS'},
        'tournament_id': tournament_id,
    }
    print(f"Sending: {json.dumps(body)}")
    tokens = RIOT_ACCESS_TOKEN.split(';')
    await asyncio.gather(*(send_rewards(session, token, body) for token in tokens))
async def main():
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                live_data = await fetch_json(session, LIVE_DATA_URL, HEADERS)
                events = live_data.get('data', {}).get('schedule', {}).get('events', [])
                if not events:
                    print('No live events found.')
                    await asyncio.sleep(60)
                    continue
                current_time = datetime.now(timezone.utc).isoformat()
                await asyncio.gather(*(process_event(event, session, current_time) for event in events))
            except Exception as e:
                print(f'Error: {e}')
            await asyncio.sleep(60)
if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
