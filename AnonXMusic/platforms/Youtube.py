import asyncio
import glob
import json
import os
import random
import re
from concurrent.futures import ThreadPoolExecutor
from typing import Union
import string
import requests
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from youtubesearchpython.__future__ import VideosSearch, CustomSearch
import base64
from AnonXMusic import LOGGER
from AnonXMusic.utils.database import is_on_off
from AnonXMusic.utils.formatters import time_to_seconds
from config import YT_API_KEY, YTPROXY_URL as YTPROXY

logger = LOGGER(__name__)

def cookie_txt_file():
    try:
        folder_path = f"{os.getcwd()}/cookies"
        filename = f"{os.getcwd()}/cookies/logs.csv"
        txt_files = glob.glob(os.path.join(folder_path, '*.txt'))
        if not txt_files:
            raise FileNotFoundError("No .txt files found in the specified folder.")
        cookie_txt_file = random.choice(txt_files)
        with open(filename, 'a') as file:
            file.write(f'Choosen File : {cookie_txt_file}\n')
        return f"""cookies/{str(cookie_txt_file).split("/")[-1]}"""
    except:
        return None


async def check_file_size(link):
    async def get_format_info(link):
        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--cookies", cookie_txt_file(),
            "-J",
            link,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            print(f'Error:\n{stderr.decode()}')
            return None
        return json.loads(stdout.decode())

    def parse_size(formats):
        total_size = 0
        for format in formats:
            if 'filesize' in format:
                total_size += format['filesize']
        return total_size

    info = await get_format_info(link)
    if info is None:
        return None
    
    formats = info.get('formats', [])
    if not formats:
        print("No formats found.")
        return None
    
    total_size = parse_size(formats)
    return total_size

async def shell_cmd(cmd):
    proc = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out, errorz = await proc.communicate()
    if errorz:
        if "unavailable videos are hidden" in (errorz.decode("utf-8")).lower():
            return out.decode("utf-8")
        else:
            return errorz.decode("utf-8")
    return out.decode("utf-8")


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
        self.dl_stats = {
            "total_requests": 0,
            "okflix_downloads": 0,
            "cookie_downloads": 0,
            "existing_files": 0
        }

    async def _get_video_details(self, link: str, limit: int = 20) -> Union[dict, None]:
        """Helper function to get video details with duration limit and error handling"""
        try:
            results = VideosSearch(link, limit=limit)
            search_results = (await results.next()).get("result", [])

            for result in search_results:
                duration_str = result.get("duration", "0:00")

                # Convert duration to seconds
                try:
                    parts = duration_str.split(":")
                    duration_secs = 0
                    if len(parts) == 3:  # HH:MM:SS
                        duration_secs = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    elif len(parts) == 2:  # MM:SS
                        duration_secs = int(parts[0]) * 60 + int(parts[1])

                    # Skip videos longer than 1 hour
                    if duration_secs > 3600:
                        continue

                    return result

                except (ValueError, IndexError):
                    continue
            
            search = CustomSearch(query=link, searchPreferences="EgIYAw==" ,limit=1)
            for res in (await search.next()).get("result", []):
                return res

            return None

        except Exception as e:
            LOGGER(__name__).error(f"Error in _get_video_details: {str(e)}")
            return None

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if re.search(self.regex, link):
            return True
        else:
            return False

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        text = ""
        offset = None
        length = None
        for message in messages:
            if offset:
                break
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        offset, length = entity.offset, entity.length
                        break
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        if offset in (None,):
            return None
        return text[offset : offset + length]

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]


        result = await self._get_video_details(link)
        if not result:
            raise ValueError("No suitable video found (duration > 1 hour or video unavailable)")

        title = result["title"]
        duration_min = result["duration"]
        thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        vidid = result["id"]

        if str(duration_min) == "None":
            duration_sec = 0
        else:
            duration_sec = int(time_to_seconds(duration_min))

        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]
            
        result = await self._get_video_details(link)
        if not result:
            raise ValueError("No suitable video found (duration > 1 hour or video unavailable)")
        return result["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]

        result = await self._get_video_details(link)
        if not result:
            raise ValueError("No suitable video found (duration > 1 hour or video unavailable)")
        return result["duration"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]

        result = await self._get_video_details(link)
        if not result:
            raise ValueError("No suitable video found (duration > 1 hour or video unavailable)")
        return result["thumbnails"][0]["url"].split("?")[0]

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]

        proc = await asyncio.create_subprocess_exec(
            "yt-dlp",
            "--cookies",cookie_txt_file(),
            "-g",
            "-f",
            "best[height<=?720][width<=?1280]",
            f"{link}",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if stdout:
            return 1, stdout.decode().split("\n")[0]
        else:
            return 0, stderr.decode()

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]
        playlist = await shell_cmd(
            f"yt-dlp -i --get-id --flat-playlist --cookies {cookie_txt_file()} --playlist-end {limit} --skip-download {link}"
        )
        try:
            result = playlist.split("\n")
            for key in result:
                if key == "":
                    result.remove(key)
        except:
            result = []
        return result

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]

        result = await self._get_video_details(link)
        if not result:
            raise ValueError("No suitable video found (duration > 1 hour or video unavailable)")

        track_details = {
            "title": result["title"],
            "link": result["link"],
            "vidid": result["id"],
            "duration_min": result["duration"],
            "thumb": result["thumbnails"][0]["url"].split("?")[0],
        }
        return track_details, result["id"]

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]
        ytdl_opts = {"quiet": True, "cookiefile" : cookie_txt_file()}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    str(format["format"])
                except:
                    continue
                if not "dash" in str(format["format"]).lower():
                    try:
                        format["format"]
                        format["filesize"]
                        format["format_id"]
                        format["ext"]
                        format["format_note"]
                    except:
                        continue
                    formats_available.append(
                        {
                            "format": format["format"],
                            "filesize": format["filesize"],
                            "format_id": format["format_id"],
                            "ext": format["ext"],
                            "format_note": format["format_note"],
                            "yturl": link,
                        }
                    )
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        if "?si=" in link:
            link = link.split("?si=")[0]
        elif "&si=" in link:
            link = link.split("&si=")[0]

        try:
            results = []
            search = VideosSearch(link, limit=10)
            search_results = (await search.next()).get("result", [])

            # Filter videos longer than 1 hour
            for result in search_results:
                duration_str = result.get("duration", "0:00")
                try:
                    parts = duration_str.split(":")
                    duration_secs = 0
                    if len(parts) == 3:
                        duration_secs = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                    elif len(parts) == 2:
                        duration_secs = int(parts[0]) * 60 + int(parts[1])

                    if duration_secs <= 3600:
                        results.append(result)
                except (ValueError, IndexError):
                    continue

            if not results or query_type >= len(results):
                raise ValueError("No suitable videos found within duration limit")

            selected = results[query_type]
            return (
                selected["title"],
                selected["duration"],
                selected["thumbnails"][0]["url"].split("?")[0],
                selected["id"]
            )

        except Exception as e:
            LOGGER(__name__).error(f"Error in slider: {str(e)}")
            raise ValueError("Failed to fetch video details")

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            vid_id = link
            link = self.base + link
        loop = asyncio.get_running_loop()

        def create_session():
            session = requests.Session()
            retries = Retry(total=3, backoff_factor=0.1)
            session.mount('http://', HTTPAdapter(max_retries=retries))
            session.mount('https://', HTTPAdapter(max_retries=retries))
            return session

        async def download_with_curl(url, filepath, headers=None, max_retries=3):
            
            cmd = [
                "curl",
                "-L",  # Follow redirects
                "-C", "-",  # Resume partial downloads
                "--retry", str(max_retries),
                "--retry-delay", "1", 
                "--retry-max-time", "600",
                "--connect-timeout", "30",
                "--max-time", "60",  # 1 minute max
                "--silent",  # Silent mode
                "--show-error",  # Show errors
                "--fail",  # Fail silently on server errors
                "-o", filepath,
                url
            ]
            
            # Add headers  x-api-key for authentication required now in 3.5.0
            if headers:
                for key, value in headers.items():
                    cmd.extend(["-H", f"{key}: {value}"])
            
            try:
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await process.communicate()
                
                if process.returncode == 0 and os.path.exists(filepath):
                    file_size = os.path.getsize(filepath)
                    return filepath
                else:
                    error_msg = stderr.decode() if stderr else "Unknown curl error"
                    logger.error(f"Curl download failed: {error_msg}")

                    if os.path.exists(filepath):
                        os.remove(filepath)
                    return None
                    
            except Exception as e:

                if os.path.exists(filepath):
                    os.remove(filepath)
                return None

        async def download_with_requests_fallback(url, filepath, headers=None):
            try:
                session = create_session()
                
                # Use headers for authentication (including x-api-key)
                response = session.get(url, headers=headers, stream=True, timeout=60)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 1024 * 1024 
                
                with open(filepath, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            file.write(chunk)
                            downloaded += len(chunk)
                
                return filepath
                
            except Exception as e:
                logger.error(f"Requests download failed: {str(e)}")
                if os.path.exists(filepath):
                    os.remove(filepath)
                return None
            finally:
                session.close()

        async def audio_dl(vid_id):
            try:
                if not YT_API_KEY:
                    logger.error("API KEY not set in config, Set API Key you got from @tgmusic_apibot")
                    return None
                if not YTPROXY:
                    logger.error("API Endpoint not set in config\nPlease set a valid endpoint for YTPROXY_URL in config.")
                    return None
                
                headers = {
                    "x-api-key": f"{YT_API_KEY}",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                filepath = os.path.join("downloads", f"{vid_id}.mp3")
                
                if os.path.exists(filepath):
                    return filepath
                
                session = create_session()
                getAudio = session.get(f"{YTPROXY}/info/{vid_id}", headers=headers, timeout=60)
                
                try:
                    songData = getAudio.json()
                except Exception as e:
                    logger.error(f"Invalid response from API: {str(e)}")
                    return None
                finally:
                    session.close()
                
                status = songData.get('status')
                if status == 'success':
                    audio_url = songData['audio_url']
                    #audio_url = base64.b64decode(songlink).decode() remove in 3.5.0
                    
                    result = await download_with_curl(audio_url, filepath, headers)
                    if result:
                        return result
                    
                    result = await download_with_requests_fallback(audio_url, filepath, headers)
                    if result:
                        return result
                    
                    return None
                    
                elif status == 'error':
                    logger.error(f"API Error: {songData.get('message', 'Unknown error from API.')}")
                    return None
                else:
                    logger.error("Could not fetch Backend \nPlease contact API provider.")
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error while fetching audio info: {str(e)}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid response from proxy: {str(e)}")
            except Exception as e:
                logger.error(f"Error in audio download: {str(e)}")
            
            return None
        
        
        async def video_dl(vid_id):
            try:
                if not YT_API_KEY:
                    logger.error("API KEY not set in config, Set API Key you got from @tgmusic_apibot")
                    return None
                if not YTPROXY:
                    logger.error("API Endpoint not set in config\nPlease set a valid endpoint for YTPROXY_URL in config.")
                    return None
                
                headers = {
                    "x-api-key": f"{YT_API_KEY}",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
                
                filepath = os.path.join("downloads", f"{vid_id}.mp4")
                
                if os.path.exists(filepath):
                    return filepath
                
                session = create_session()
                getVideo = session.get(f"{YTPROXY}/info/{vid_id}", headers=headers, timeout=60)
                
                try:
                    videoData = getVideo.json()
                except Exception as e:
                    logger.error(f"Invalid response from API: {str(e)}")
                    return None
                finally:
                    session.close()
                
                status = videoData.get('status')
                if status == 'success':
                    video_url = videoData['video_url']
                    #video_url = base64.b64decode(videolink).decode() removed in 3.5.0
                    
                    result = await download_with_curl(video_url, filepath, headers)
                    if result:
                        return result
                    
                    result = await download_with_requests_fallback(video_url, filepath, headers)
                    if result:
                        return result
                    
                    return None
                    
                elif status == 'error':
                    logger.error(f"API Error: {videoData.get('message', 'Unknown error from API.')}")
                    return None
                else:
                    logger.error("Could not fetch Backend \nPlease contact API provider.")
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Network error while fetching video info: {str(e)}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid response from proxy: {str(e)}")
            except Exception as e:
                logger.error(f"Error in video download: {str(e)}")
            
            return None
        
        def song_video_dl():
            formats = f"{format_id}+140"
            fpath = f"downloads/{title}"
            ydl_optssx = {
                "format": formats,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile" : cookie_txt_file(),
                "prefer_ffmpeg": True,
                "merge_output_format": "mp4",
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        def song_audio_dl():
            fpath = f"downloads/{title}.%(ext)s"
            ydl_optssx = {
                "format": format_id,
                "outtmpl": fpath,
                "geo_bypass": True,
                "nocheckcertificate": True,
                "quiet": True,
                "no_warnings": True,
                "cookiefile" : cookie_txt_file(),
                "prefer_ffmpeg": True,
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
            x = yt_dlp.YoutubeDL(ydl_optssx)
            x.download([link])

        if songvideo:
            await loop.run_in_executor(None, song_video_dl)
            fpath = f"downloads/{title}.mp4"
            return fpath
        elif songaudio:
            await loop.run_in_executor(None, song_audio_dl)
            fpath = f"downloads/{title}.mp3"
            return fpath
        elif video:
            direct = True
            downloaded_file = await video_dl(vid_id)
        else:
            direct = True
            downloaded_file = await audio_dl(vid_id)
        
        return downloaded_file, direct
