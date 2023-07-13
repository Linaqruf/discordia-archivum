import os
import argparse
import logging
import discord
import httpx
import json
import toml
import datetime
from typing import Dict, List, Optional, Any
from httpx import AsyncClient
from pathlib import Path
from PIL import Image

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Discord message scraper')
    parser.add_argument('--token', type=str, help='Discord bot token')
    parser.add_argument('--channel_id', type=int, help='ID of the Discord channel')
    parser.add_argument('--config_file', default='./config.toml', help='Path to the configuration file in TOML format')
    parser.add_argument('--output_json', default='./output.json', help='Path to the output JSON file')
    parser.add_argument('--output_folder', default='./attachments', help='Path to the output attachments folder')
    parser.add_argument('--nijijourney', action='store_true', help='Set user_id to 1022952195194359889')
    parser.add_argument('--midjourney', action='store_true', help='Set user_id to 936929561302675456')
    parser.add_argument('--limit', type=int, default=100, help='Maximum number of messages to scrape')
    parser.add_argument('--download_attachments', action='store_true', help='Download all attachments')
    parser.add_argument('--single', action='store_true', help='Only download non-grid images')
    parser.add_argument('--prompt', type=str, help='Only include messages that contain this word')
    parser.add_argument('--undesired_words', type=str, help='Exclude messages that contain this word')
    parser.add_argument('--style', choices=["default", "expressive", "cute", "scenic", "original", "raw"], help='Only proceed messages with "--style {value}" string')
    parser.add_argument('--niji', choices=["4", "5"], help='Only proceed messages with "--niji {value}" string')
    parser.add_argument('--version', choices=["1", "2", "3", "4", "5", "5.1", "5.2"], help='Only proceed messages with "--v {value}" string')
    parser.add_argument('--before_date', type=str, help='Only include messages before this date (YYYY-MM-DD format)')
    parser.add_argument('--after_date', type=str, help='Only include messages after this date (YYYY-MM-DD format)')
    return parser.parse_args()

def load_settings(config_file: str) -> Dict[str, str]:
    return toml.load(config_file)

def is_message_valid(message: discord.Message, args: argparse.Namespace, user_id: str) -> bool:
    if args.before_date or args.after_date:
        message_date = message.created_at.date()
        if args.before_date:
            before_date = datetime.datetime.strptime(args.before_date, '%Y-%m-%d').date()
            if message_date >= before_date:
                return False
        if args.after_date:
            after_date = datetime.datetime.strptime(args.after_date, '%Y-%m-%d').date()
            if message_date <= after_date:
                return False    
    if str(message.author.id) != user_id:
        return False
    if args.undesired_words:
        undesired_words = [word.strip() for word in args.undesired_words.split(',')]
        if any(word in message.content for word in undesired_words):
            return False
    if args.prompt:
        prompt = [word.strip() for word in args.prompt.split(',')]
        if not any(word in message.content for word in prompt):
            return False
    if args.style and f'--style {args.style}' not in message.content:
        return False
    if args.niji and f'--niji {args.niji}' not in message.content:
        return False
    if args.version and f'--v {args.version}' not in message.content:
        return False
    return True

def parse_message_content(content: str) -> dict:
    parts = content.split("--")

    prompt = parts[0].split('** - ')[0].replace('**', '').strip()
    category = content.split('** - ')[1] if '** - ' in content else ''

    extra_keys = {"prompt": prompt, "category": category}

    for part in parts[1:]:
        key_value = part.strip().split(maxsplit=1)
        key = key_value[0]
        value = True
        if len(key_value) > 1:
            value = key_value[1]
            if '** - ' in value:
                value = value.split('** - ')[0].rstrip()
        extra_keys[key] = value

    return extra_keys

def print_unique_metadata_keys(data: List[Dict[str, Any]]) -> None:
    keys = set()
    for message in data:
        keys.update(message.get('metadata', {}).keys())
    print(f'Unique keys in metadata: {keys}')

def construct_message_data(message: discord.Message) -> Dict[str, List[Dict[str, str]]]:
    attachments = [{
        'filename': attachment.filename,
        'url': attachment.url,
        'size': attachment.size
    } for attachment in message.attachments]
    timestamp = message.created_at
    data = {'content': message.content, 'attachments': attachments, 
            'metadata': parse_message_content(message.content), 
            'timestamp': {
                'date': str(timestamp.date()),
                'time': str(timestamp.time())
                }
            }
    return data

def save_to_json(data: List[Dict[str, str]], file_path: str) -> None:
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def save_category(data: List[Dict[str, Any]], file_path: str) -> None:
    category = [message.get('metadata', {}).get('category', '') for message in data]
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(category, f, ensure_ascii=False, indent=4)

async def download_file(url: str, dir_path: str, filename: str) -> None:
    async with AsyncClient() as client:
        resp = await client.get(url)
        resp.raise_for_status()
        os.makedirs(dir_path, exist_ok=True)
        path = os.path.join(dir_path, filename)
        with open(path, 'wb') as f:
            f.write(resp.content)

def convert_webp_to_jpg(webp_path: str) -> None:
    image = Image.open(webp_path).convert("RGB")
    jpg_path = os.path.splitext(webp_path)[0] + '.jpg'
    image.save(jpg_path, "JPEG")

def main():
    logging.basicConfig(format='%(asctime)s %(message)s', level=logging.INFO)
    
    args = parse_arguments()

    token = args.token
    channel_id = args.channel_id

    user_id = None
    if args.nijijourney:
        user_id = "1022952195194359889"
    elif args.midjourney:
        user_id = "936929561302675456"
        
    if not (token and channel_id):
        try:
            settings = load_settings(args.config_file)
            token = settings.get('token', token)
            channel_id = settings.get('channel_id', channel_id)
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
            if not is_message_valid(message, args, user_id):
                continue

            message_data = construct_message_data(message)

            if args.download_attachments:
                for attachment in message_data['attachments']:
                    category = message_data['metadata']['category'].lower()
                    if args.single:
                        dir_path = os.path.join(args.output_folder, channel.name)
                        if not category.startswith(("image", "upscaled")):
                            continue
                        
                        await download_file(attachment['url'], dir_path, attachment['filename'])
                    else:
                        if "variations" in category:
                            dir_path = os.path.join(args.output_folder, channel.name, 'variations')
                        elif "zoom out" in category:
                            dir_path = os.path.join(args.output_folder, channel.name, 'zoom_out')
                        elif "pan" in category:
                            dir_path = os.path.join(args.output_folder, channel.name, 'pan')
                        elif "image" in category or "upscaled" in category:
                            dir_path = os.path.join(args.output_folder, channel.name, 'single')
                        else:
                            dir_path = os.path.join(args.output_folder, channel.name, 'grid')
                        
                        await download_file(attachment['url'], dir_path, attachment['filename'])
                    
            data.append(message_data)

            if args.limit and len(data) >= args.limit:
                break

        save_to_json(data, args.output_json)
        # save_category(data, './experiment.json') 
        print_unique_metadata_keys(data)
        logging.info(f'Found {len(data)} messages in "{channel.name}"')
        await client.close()  # disconnect the client

    client.run(token)

if __name__ == "__main__":
    main()