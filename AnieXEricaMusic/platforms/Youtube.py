import asyncio
import os
import json
import re
from typing import Union
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from youtubesearchpython.__future__ import VideosSearch

# Yaha apni YouTube API key daalein
YOUTUBE_API_KEY = "YOUR_YOUTUBE_API_KEY"


async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        return errorz.decode("utf-8")
    return out.decode("utf-8")


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.api_url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,contentDetails&id={{}}&key={YOUTUBE_API_KEY}"

    async def exists(self, link: str):
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        return (message.text or message.caption)[entity.offset : entity.offset + entity.length]
        return None

    async def details(self, video_id: str):
        url = self.api_url.format(video_id)
        response = await shell_cmd(f"curl -s {url}")
        data = json.loads(response)

        if "items" not in data or not data["items"]:
            return None

        item = data["items"][0]["snippet"]
        title = item["title"]
        thumbnail = item["thumbnails"]["high"]["url"]
        duration_min = "Unknown"
        duration_sec = 0

        return title, duration_min, duration_sec, thumbnail, video_id

    async def video(self, link: str):
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "-g",
            "-f",
            "bestaudio",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()

    async def playlist(self, playlist_id: str, limit: int):
        url = f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={playlist_id}&maxResults={limit}&key={YOUTUBE_API_KEY}"
        response = await shell_cmd(f"curl -s {url}")
        data = json.loads(response)

        if "items" not in data:
            return []

        return [item["snippet"]["resourceId"]["videoId"] for item in data["items"]]

    async def download(self, link: str, audio: bool = True):
        ydl_opts = {
            "format": "bestaudio" if audio else "best",
            "outtmpl": "downloads/%(id)s.%(ext)s",
            "geo_bypass": True,
            "nocheckcertificate": True,
            "quiet": True,
            "no_warnings": True,
        }

        loop = asyncio.get_running_loop()
        def download_media():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(link, False)
                filepath = os.path.join("downloads", f"{info['id']}.{info['ext']}")
                if os.path.exists(filepath):
                    return filepath
                ydl.download([link])
                return filepath

        return await loop.run_in_executor(None, download_media)