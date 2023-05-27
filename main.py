import os
import json
import argparse
import logging
import discord
import httpx
from typing import Dict, List, Optional
from httpx import AsyncClient
from pathlib import Path

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Discord message scraper')
    parser.add_argument('--settings', default='settings.json', help='Path to the settings file')
    parser.add_argument('--output_json', default='data.json', help='Path to the output JSON file')
    parser.add_argument('--output_folder', default='./attachments', help='Path to the output attachments folder')
    parser.add_argument('--user_id', type=str, help='Filter messages by user ID')
    parser.add_argument('--skip_message', choices=['none', 'bot', 'user'], default='bot', help='Skip messages sent by bots or users')
    parser.add_argument('--image_only', action='store_true', help='Only scrape messages with attachments')
    parser.add_argument('--limit', type=int, help='Maximum number of messages to scrape')
    parser.add_argument('--token', type=str, help='Discord bot token')
    parser.add_argument('--channel_id', type=int, help='ID of the Discord channel')
    parser.add_argument('--download_attachments', action='store_true', help='Download all attachments')
    return parser.parse_args()

def load_settings(settings_path: str) -> Dict[str, str]:
    with open(settings_path, 'r') as f:
        return json.load(f)

def is_message_valid(message: discord.Message, args: argparse.Namespace) -> bool:
    if args.skip_message == 'bot' and message.author.bot:
        return False
    if args.skip_message == 'user' and not message.author.bot:
        return False
    if args.user_id and str(message.author.id) != args.user_id:
        return False
    if args.image_only and not message.attachments:
        return False
    return True

def construct_message_data(message: discord.Message) -> Dict[str, List[Dict[str, str]]]:
    attachments = [{
        'filename': attachment.filename,
        'url': attachment.url,
        'size': attachment.size
    } for attachment in message.attachments]
    return {'content': message.content, 'attachments': attachments}

def save_to_json(data: List[Dict[str, str]], file_path: str) -> None:
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

async def download_file(url: str, path: str) -> None:
    async with AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        with open(path, 'wb') as f:
            f.write(resp.content)

def main():
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
    
    args = parse_arguments()

    token = args.token
    channel_id = args.channel_id

    if not (token and channel_id):
        try:
            settings = load_settings(args.settings)
            token = settings.get('token')
            channel_id = settings.get('channel_id')
        except Exception as e:
            logging.error(f"Failed to load settings: {e}")

    if not token:
        token = input("Enter your Discord bot token: ")

    if not channel_id:
        channel_id = int(input("Enter the ID of the channel you want to scrape: ")) # convert input to int

    client = discord.Client()

    @client.event
    async def on_connect():
        channel = client.get_channel(channel_id)

        logging.info(f'Scraping in "{channel.name}" as {client.user}')
        data = []

        async for message in channel.history(limit=args.limit):
            if not is_message_valid(message, args):
                continue

            message_data = construct_message_data(message)

            if args.download_attachments:
                for attachment in message_data['attachments']:
                    output_folder = Path(args.output_folder)
                    output_folder.mkdir(parents=True, exist_ok=True)
                    path = output_folder / attachment['filename']
                    await download_file(attachment['url'], path)

            data.append(message_data)

            if args.limit and len(data) >= args.limit:
                break

        save_to_json(data, args.output_json)
        logging.info(f'Found {len(data)} messages in "{channel.name}"')
        await client.close()  # disconnect the client

    client.run(token)

if __name__ == "__main__":
    main()