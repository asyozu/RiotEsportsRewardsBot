# LoL Esports Drops Watcher

A lightweight **Python async bot** that simulates watching live matches on the official LoL Esports website in order to automatically track and claim **in-game drops** from Riot's LoL Esports events.

The script continuously checks for live matches, sends watch events to the LoL Esports rewards API, and optionally sends **Telegram notifications** when new drops are received.

---

## Features

* Automatically detects **live LoL Esports matches**
* Simulates watching the official stream
* Tracks and retrieves **earned drops**
* Optional **Telegram notifications** for new drops
* Uses **asyncio + aiohttp** for efficient networking
* Automatically refreshes Riot authentication tokens
* Displays currently watched league in the console

---

## Requirements

* Python **3.9+**
* A valid **LoL Esports refresh token**

---

## Setup

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/lolesports-drops-watcher.git
cd lolesports-drops-watcher
pip install -r requirements.txt
```

---

### 2. Configure the Script

Edit the following variables inside the `Main` class:

```python
self.refresh_token = "YOUR_REFRESH_TOKEN"
self.notify_enabled = False
self.telegram_bot_token = "YOUR_TELEGRAM_BOT_TOKEN"
self.telegram_chat_id = "YOUR_CHAT_ID"
```

#### refresh_token

Your LoL Esports refresh token from browser cookies:

```
__Secure-refresh_token
```

You can obtain it from:

```
https://lolesports.com
```

Open **Developer Tools → Application → Cookies**.

---

### 3. Run the Script

```bash
python main.py
```

Example output:

```
Logged in as: PlayerName#TAG | totalDrop: 12
19:30:04 | LCK
19:31:05 | LCK
19:32:05 | LCK
```

---

## Telegram Notifications (Optional)

To enable Telegram alerts:

1. Create a bot using **BotFather**
2. Get your **Bot Token**
3. Get your **Chat ID**
4. Set:

```python
self.notify_enabled = True
```

You will receive messages like:

```
Title: Pentakill Drop
Description: Celebrate an epic moment!
Drop: Hextech Chest
```

---

## How It Works

1. Uses Riot's **SSO refresh endpoint** to obtain an access token.
2. Queries the **LoL Esports API** for live events.
3. Retrieves stream information for the match.
4. Sends periodic **watch events** to simulate viewing.
5. Polls the rewards API to detect newly earned drops.