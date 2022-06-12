import os
import getopt
import sys

import mutagen  # type: ignore
import termcolor  # type: ignore
import youtube_dl  # type: ignore


class Logger(object):
    """Use these methods to create manual log messages"""
    @staticmethod
    def info(message):
        print(termcolor.colored("[INFO]", "green"), message)

    @staticmethod
    def warn(message):
        print(termcolor.colored("[WARNING]", "yellow"), message)

    @staticmethod
    def err(message):
        print(termcolor.colored("[ERROR]", "red"), message)

    """These methods are to only be used and called by youtube_dl"""
    @staticmethod
    def hooks(h):
        if h["status"] == "finished":
            Logger.info(f"Finished downloading Web file: {h['filename']}")

    def debug(self, message):
        pass

    def warning(self, message):
        pass

    def error(self, message):
        print(termcolor.colored("[ERROR]", "red"), message)


youtubedl_options = {
    # Logs
    "logger": Logger(),
    "progress_hooks": [Logger.hooks],

    # Download configs
    "sleep_interval": 10,
    "outtmpl": "%(track)s.%(ext)s",

    # Only applies to the downloaded webm file
    "format": "bestaudio/best",
    "writethumbnail": True,

    # Post-processing the audio from the webm file
    "keepvideo": False,
    "prefer_ffmpeg": True,
    "postprocessors": [{
        "key": "FFmpegExtractAudio",
        "preferredcodec": "mp3",
        "preferredquality": "192",
    }, {
        "key": "FFmpegMetadata",
    }, {
        # Must be after metadata because that wipes the thumbnail
        "key": "EmbedThumbnail",
        "already_have_thumbnail": True,
    }],
    # To actually embed thumbnail into the mp3 file
    "postprocessor_args": ["-id3v2_version", "3"],
}


def parse_user_arguments():
    artist = None
    album = None
    url = None
    is_playlist = False
    max_tries = 3

    # User arguments
    try:
        arguments, values = getopt.getopt(
            sys.argv[1:],
            "hA:a:u:t",
            ["help", "artist=", "album=", "url=", "tries="]
        )
    except getopt.error as err:
        Logger.err("Invalid arguments:", err)
        sys.exit(1)

    # Parse arguments
    for argument, value in arguments:
        if argument in ("-h", "--help"):
            Logger.info("Downloads youtube music videos as mp3 files")
            Logger.info("Ideally be in the same directory as this script")
            Logger.info("Usage: yt.py [--artist=<artist>] " +
                        "[--album=<album>] --url=<url>")
            sys.exit(0)
        elif argument in ("-A", "--artist"):
            artist = value
        elif argument in ("-a", "--album"):
            album = value
        elif argument in ("-u", "--url"):
            if "youtube.com/playlist?list=" in value:
                is_playlist = True
            url = value
        elif argument in ("-t", "--tries"):
            max_tries = int(value)

    if not url:
        Logger.err("No URL specified")
        Logger.info("Usage: yt.py [--artist=<artist>] " +
                    "[--album=<album>] --url=<url>")
        sys.exit(1)

    return artist, album, url, is_playlist, max_tries


def remove_build_files(filename=None):
    # Assume that this is run in the same directory as the file
    possible_build_extensions = {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",  # thumbnails
    }
    removed_build_files = []

    # Remove all build files if no filename is specified
    # Otherwise, remove the build file with the specified filename
    if filename:
        for file in os.listdir():
            if os.path.splitext(file)[1] in possible_build_extensions:
                os.remove(file)
                removed_build_files.append(file)
    else:
        for extension in possible_build_extensions:
            if os.path.isfile(filename + extension):
                os.remove(filename + extension)
                removed_build_files.append(filename + extension)

    return removed_build_files


def gather_video_info(artist, album, url, is_playlist):
    # Get info of the video(s)
    Logger.info("Starting to gather info about video(s)...")
    info = ytdl.extract_info(url, download=False)

    # Get all necessary info and metadata from all videos
    # Use list of tuples to ensure order of video index in playlists
    # index: Used in logs and metadata, int | None (may not need index)
    # title: Used in logs, str (this is not necessarily the title of the music)
    # track: Used in filename and metadata, str (all music has a title)
    # artist: Used in metadata, str (all music has an artist)
    # album: Used in metadata and folder name, str | None (may not have album)
    # url: Used to download the video
    # filename: Identical to track
    if is_playlist:
        Logger.info("Given URL is a playlist")

        info = info["entries"]  # Makes it easier to reference each video
        playlist_title = info[0]["playlist_title"]  # Default album name

        videos = [
            {"index": i + 1,
             "title": info[i].get("title", "Unknown"),
             "track": info[i].get("track", "Unknown"),
             "artist": artist if artist else info[i].get("artist", "Unknown"),
             "album": album if album else info[i].get("album", playlist_title),
             "url": info[i].get("webpage_url", url),

             # Ensure filename is the same name output file
             # mentioned in the youtubedl options "outtmpl"
             "filename": info[i].get("track", "Unknown")}
            for i in range(len(info))
        ]
        Logger.info("Finished gathering info about playlist")
    else:
        Logger.info("Given URL is an individual video")
        videos = [
            {"index": None,
             "title": info.get("title", "Unknown"),
             "track": info.get("track", "Unknown"),
             "artist": artist if artist else info.get("artist", "Unknown"),
             "album": album if album else info.get("album", None),
             "url": info.get("webpage_url", url),

             # Ensure filename is the same name output file
             # mentioned in the youtubedl options "outtmpl"
             "filename": info.get("track", "Unknown")}
        ]
        Logger.info("Finished gathering info about the video")

    return videos


if __name__ == "__main__":
    Logger.info("Removing youtube-dl cache files...")
    os.system("youtube-dl --quiet --rm-cache-dir")

    ytdl = youtube_dl.YoutubeDL(youtubedl_options)

    # url is a mandatory argument, we assume it is not None
    artist, album, url, is_playlist, max_tries = parse_user_arguments()
    videos = gather_video_info(artist, album, url, is_playlist)

    # Create the album directory and enter it to separate downloaded files
    # without having to move files later and makes it safer to find and
    # remove any temporary build files (e.g. .jpg thumbnails)
    album = videos[0]["album"]
    if not os.path.exists(album):
        Logger.info(f"Creating album directory {album}/...")
        os.mkdir(album)
    else:
        Logger.info(f"Album directory {album}/ already exists")
    Logger.info(f"Entering album directory {album}/...")
    os.chdir(os.path.join(os.getcwd(), album))

    # Download each video individually instead of together in a playlist
    # So we have more control over downloads and can have better logs
    for video in videos:
        for tries in range(1, max_tries + 1):
            try:
                # Download the video
                Logger.info(f"Starting to download {video['title']}...")
                Logger.info(f"Video {video['index']}/{len(videos)} | " +
                            f"Try {tries}/{max_tries}")
                ytdl.download([video['url']])
                Logger.info(f"Finished downloading {video['title']}")

                # Remove the thumbnail file used in the build process
                thumbnail_files = remove_build_files(video["filename"])
                Logger.info(f"Removed {thumbnail_files} thumbnail")

                # Add metadata to the mp3 files
                audio_file = mutagen.easyid3.EasyID3(
                    video["filename"] + ".mp3"
                )

                # Downloaded music may not be in album, hence the default Nones
                # But all music should have a title and an artist
                if video["index"]:
                    audio_file["tracknumber"] = video["index"]
                if video["album"]:
                    audio_file["album"] = video["album"]
                    audio_file["albumartist"] = video["artist"]
                audio_file["title"] = video["track"]
                audio_file["artist"] = video["artist"]
                audio_file.save()

                break
            except KeyboardInterrupt:
                Logger.warn("Keyboard interrupt. Skipping to next video...")
                break
            except:
                Logger.err(f"Failed to download {video['title']}. " +
                           "Trying again...")
                Logger.info("Removing youtube-dl cache files...")
                os.system("youtube-dl --quiet --rm-cache-dir")
                continue

    Logger.info("Finished downloading all videos")
    Logger.info(f"Removed {remove_build_files()}")
    Logger.info("Exiting...")
    sys.exit(0)
