# Discordia Archivum

Discordia Archivum is an efficient Discord Message and Attachments Archiver. It's a powerful tool for seamlessly scraping and organizing Discord messages and attachments, simplifying the process of archiving important conversations and media files.

## Features
- Filter messages by user ID
- Skip messages sent by bots or users
- Scrape only messages with attachments
- Limit the maximum number of messages to scrape
- Download all attachments from messages
- Save scraped data to a JSON file

## Prerequisites
- Python 3.7 or higher
- Packages: discord.py-self, httpx

## Installation

We recommend using a virtual environment to avoid conflicts with other Python projects. You can set it up as follows:

```shell
git clone https://github.com/Linaqruf/discordia-archivum discordia-archivum
cd discordia-archivum
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Usage
Set your `settings.json` first:
```json
{
    "token": "YOUR_DISCORD_BOT_TOKEN",
    "channel": "CHANNEL_ID_TO_SCRAPE"
}
```
Then, run the scraper with command line arguments:
```shell
python main.py --settings ./settings.json
```
Alternatively, you can directly pass `token` and `channel_id` with arguments:
```shell
python main.py --token YOUR_DISCORD_BOT_TOKEN --channel_id CHANNEL_ID_TO_SCRAPE
```

Please replace `"YOUR_DISCORD_BOT_TOKEN"` and `"CHANNEL_ID_TO_SCRAPE"` with your actual Discord bot token and the ID of the channel you want to scrape, respectively.

## Command Line Arguments
- `--settings`: Path to the settings file (default: `./settings.json`)
- `--output_json`: Path to the output JSON file (default: `./output.json`)
- `--output_folder`: Path to the output attachments folder (default: `./attachments`)
- `--user_id`: Filter messages by user ID
- `--skip_message`: Skip messages sent by bots or users (choices: `none`, `bot`, `user`, default: `bot`)
- `--image_only`: Only scrape messages with attachments
- `--limit`: Maximum number of messages to scrape (default: `100`)
- `--token`: Discord bot token
- `--channel_id`: ID of the Discord channel to scrape
- `--download_attachments`: Download all attachments

## Warning
[Self-bots](https://medium.com/@scarlettokun/selfbots-explanation-and-perspectives-51d437ce0849) are against Discord's Terms of Service. Using a self-bot can lead to account termination. Use this script at your own risk. This script should be used for personal archival purposes only.

## Disclaimer
Please use this tool responsibly and in accordance with Discord's Terms of Service and relevant laws. The creator of this tool does not take any responsibility for its misuse.
