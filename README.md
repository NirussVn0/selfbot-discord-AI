# 🤖 Self-Bot Discord AI (Astraa)

<div align="center">

![Discord Self-Bot](https://img.shields.io/badge/Discord-SelfBot-5865F2?style=for-the-badge&logo=discord&logoColor=white)
[![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Google Gemini](https://img.shields.io/badge/AI-Gemini_Pro-8E75B2?style=for-the-badge&logo=google&logoColor=white)](https://deepmind.google/technologies/gemini/)
[![Rich CLI](https://img.shields.io/badge/CLI-Rich-009688?style=for-the-badge&logo=python&logoColor=white)](https://rich.readthedocs.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](./LICENSE)

**Your Advanced AI-Powered Discord Assistant** 🚀

Elevate your Discord experience with automation, AI responses, and powerful utilities.

[Features](#features) • [Installation](#installation) • [Usage](#usage) • [Tech Stack](#tech-stack) • [Disclaimer](#disclaimer)

</div>

---

## ✨ Features

| Module | Description |
|--------|-------------|
| 🧠 **AI Core** | Powered by **Google Gemini Pro** for intelligent, context-aware responses |
| 🛠️ **Utilities** | `h!geoip`, `h!tts`, `h!qr`, `h!tokeninfo` and more tools at your fingertips |
| 🛡️ **Moderation** | `h!purge`, `h!whremove` and automated cleanup tools |
| 🎭 **Status Ops** | `h!afk`, `h!playing`, `h!hypesquad` - Manage your presence in style |
| ⚡ **Actions** | `h!spam`, `h!dmall`, `h!copycat` - High-impact commands (Use responsibly!) |
| 🔍 **Insight** | `h!pingweb`, `h!uptime`, `h!fetchmembers` - Deep server analysis |

---

## 🚀 Installation

### Prerequisites

- Python 3.11 or higher
- A valid Discord Token

### Setup

```bash
# Clone the repository
git clone https://github.com/NirussVn0/self_discord_bot.git

# Navigate to project directory
cd self_discord_bot

# Install dependencies
pip install -r requirements.txt
# OR if using uv/poetry
uv sync 
```

### Configuration

1. Copy `.env.example` to `.env`.
2. Fill in your **Discord Token** and **Gemini API Key**.

```env
DISCORD_USER_TOKEN=your_token_here
GOOGLE_GEMINI_API_KEY=your_gemini_key_here
```

---

## 🎮 Usage

Start the bot with:

```bash
python main.py
# OR
./run.sh
```

### Common Commands

> **Note**: The default prefix is `h!`, but you can change it using `h!changeprefix <new_prefix>`.

| Command | Action |
|---------|--------|
| `h!astraa` | Show owner's social networks |
| `h!geoip <ip>` | Locate an IP address |
| `h!afk ON` | Enable AFK mode with auto-response |
| `h!copycat ON <@user>` | Mimic a target user's messages |
| `h!minesweeper 10 10` | Play a game of Minesweeper |

---

## 🛠️ Tech Stack

<table>
<tr>
<td align="center" width="120">

**Core**

![Python](https://img.shields.io/badge/-Python-3776AB?style=flat&logo=python&logoColor=white)

</td>
<td align="center" width="120">

**AI Engine**

![Gemini](https://img.shields.io/badge/-Gemini-8E75B2?style=flat&logo=google&logoColor=white)

</td>
<td align="center" width="120">

**Library**

![Discord.py](https://img.shields.io/badge/-Discord.py_Self-5865F2?style=flat&logo=discord&logoColor=white)

</td>
<td align="center" width="120">

**UI**

![Rich](https://img.shields.io/badge/-Rich-009688?style=flat)

</td>
</tr>
</table>

### Architecture

- see in [Architecture](./ARCHITECTURE.md)
### License
- see in [LICENSE](./LICENSE)

## ⚠️ Disclaimer

<div align="center">

> [!WARNING]
> **Use at your own risk.**
> Self-bots operate in a grey area of Discord's Terms of Service. 
> Abusing API limits or spamming can lead to account termination.

**Made with 💜 by [NirussVn0](https://github.com/NirussVn0)**

</div>
