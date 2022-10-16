"""
youtube-dl mp3 music download script

This is a script that downloads youtube music videos as mp3 files.
It is designed to be used in the same directory as the script
because it will create a folder in that directory. Also, I'm too
lazy to test out the edge cases of ensuring the functionality
works in a different directory. Also, yes it downloads as mp3...
but that is ONLY because youtube-dl only allows thumbnail embedding
for mp3 and .ogg does not really support embedded images. Maybe it can
idk I am too lazy.

The purpose of creating this script as opposed to editing youtube-dl
configs is to have a much better logging system (in my opinion -- at
least its more customizable, okay?), to automatically retry failed
downloads (for some reason, youtube-dl will just fail to download the
.webm file. I think its because Google blocked quick sucessive downloads),
and to have a better way to specify important metadata to me (mostly
track numbers; youtube-dl still has not implemented this >:/).

Args:
    url: The URL of the video(s) to download
    artist (optional): The artist of the video(s)
    album (optional): The album of the video(s)
    tries (optional): The number of times to retry downloading a video
        if it fails. Defaults to 3.

Returns:
    Nothing really, it just downloads the video(s)

Raises:
    All kinds of exceptions idk read the code
"""


import os
import getopt
import sys

from mutagen.easyid3 import EasyID3  # type: ignore
import termcolor  # type: ignore
import youtube_dl  # type: ignore


class Logger(object):
    """
    Logger static class to make logging prettier and standardized
    These methods are to create manual log messages by the programmer
    """
    @staticmethod
    def info(message):
        print(termcolor.colored("[INFO]", "green"), message)

    @staticmethod
    def success(message):
        print(termcolor.colored("[SUCCESS]", "green"), message)

    @staticmethod
    def fail(message):
        print(termcolor.colored("[FAIL]", "red"), message)

    @staticmethod
    def warn(message):
        print(termcolor.colored("[WARNING]", "yellow"), message)

    @staticmethod
    def err(message):
        print(termcolor.colored("[ERROR]", "red"), message)

    """These methods here are to only be used and called by youtube_dl"""
    @staticmethod
    def hooks(hook):
        if hook["status"] == "finished":
            Logger.info(f"Finished downloading Web file: {hook['filename']}")

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
    """
    Handle arguments when the user runs the script in the terminal
    This just parases the arguments and stores them as variables to be
    used later. Also, it determines if the download is a playlist or not.
    """

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

    # Parse arguments and store them in variables
    for argument, value in arguments:
        if argument in ("-h", "--help"):
            Logger.info("Downloads youtube music videos as mp3 files")
            Logger.info("Ideally be in the same directory as this script")
            Logger.info("Usage: yt.py [--artist=<artist>] "
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
        Logger.info("Usage: yt.py [--artist=<artist>] "
                    "[--album=<album>] --url=<url>")
        sys.exit(1)

    return artist, album, url, is_playlist, max_tries


def remove_build_files(filename=None):
    """
    Removes the build files that youtube-dl creates. This can be the .webm
    files that are downloaded, but it was intended for the .jpg thumbnail
    files that youtube-dl does not clean up and does not seem to have the
    option to do so, unlike the .webm files which can be cleaned up.
    """

    # Assume that this is run in the same directory as the file
    possible_build_extensions = {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp",  # thumbnails
    }
    removed_build_files = []

    # Remove all build files if no filename is specified
    # Otherwise, remove the build file with the specified filename
    if not filename:
        for file in os.listdir():
            if os.path.splitext(file)[1] in possible_build_extensions:
                os.remove(file)
                removed_build_files.append(file)
    else:
        for extension in possible_build_extensions:
            if filename and os.path.isfile(filename + extension):
                os.remove(filename + extension)
                removed_build_files.append(filename + extension)

    return removed_build_files


def gather_video_info(artist, album, url, is_playlist):
    """
    Get every video's information for the metadata of the mp3 file and
    (less importantly), the logs. This is also to separate each video
    in a playlist (as opposed to downloading the entire playlist via
    a single command by youtube-dl). It allows us to be more
    meticulous and detailed with each video download (e.g. logs,
    metadata, any other custom commands to run inbetween downloads, etc.).
    """

    # Get info of the video(s)
    Logger.info("Starting to gather info about video(s)...")
    info = ytdl.extract_info(url, download=False)

    # Get all necessary info and metadata from all videos
    # "NA" is the default string ytdl uses if that info is unknown
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
            {
                "index": i + 1,
                "title": data.get("title", "NA"),
                "track": data.get("track", "NA"),
                "artist": artist if artist else data.get("artist", "NA"),
                "album": album if album else data.get("album", playlist_title),
                "url": data.get("webpage_url", url),

                # Ensure filename is the same name output file
                # mentioned in the youtubedl options "outtmpl"
                "filename": data.get("track", "NA")
            }
            for i, data in enumerate(info)
        ]
        Logger.info("Finished gathering info about playlist")
    else:
        Logger.info("Given URL is an individual video")
        videos = [
            {
                "index": None,
                "title": info.get("title", "NA"),
                "track": info.get("track", "NA"),
                "artist": artist if artist else info.get("artist", "NA"),
                "album": album if album else info.get("album", None),
                "url": info.get("webpage_url", url),

                # Ensure filename is the same name output file
                # mentioned in the youtubedl options "outtmpl"
                "filename": info.get("track", "NA")
            }
        ]
        Logger.info("Finished gathering info about the video")

    return videos


if __name__ == "__main__":
    """
    Main function that runs when the script is run in the terminal.
    """

    # Clear cache files because that apparently helps with less errors
    Logger.info("Removing youtube-dl cache files...")
    os.system("youtube-dl --quiet --rm-cache-dir")

    # Apply user options when downloading the videos itself
    ytdl = youtube_dl.YoutubeDL(youtubedl_options)

    # url is a mandatory argument, we assume it is not None
    artist, album, url, is_playlist, max_tries = parse_user_arguments()
    videos = gather_video_info(artist, album, url, is_playlist)

    # Create the album directory and enter it to separate downloaded files
    # without having to move files later and makes it safer to find and
    # remove any temporary build files (e.g. .jpg thumbnails)
    album = videos[0]["album"] if videos[0]["album"] else videos[0]["track"]

    if os.path.exists(album):
        Logger.info(f"Album directory {album}/ already exists")
    else:
        Logger.info(f"Creating album directory {album}/...")
        os.mkdir(album)
    Logger.info(f"Entering album directory {album}/...")
    os.chdir(os.path.join(os.getcwd(), album))

    # Download each video individually instead of together in a playlist
    # So we have more control over downloads and can have better logs
    for video in videos:
        for tries in range(1, max_tries + 1):
            try:
                # Download the video
                Logger.info(f"Starting to download {video['title']}...")
                if is_playlist:
                    Logger.info(f"Video {video['index']}/{len(videos)} | "
                                f"Try {tries}/{max_tries}")
                else:
                    Logger.info(f"Try {tries}/{max_tries}")
                ytdl.download([video["url"]])
                Logger.info(f"Finished downloading {video['title']}")

                # Remove the thumbnail file used in the build process
                thumbnail_files = remove_build_files(video["filename"])
                Logger.info(f"Removed {thumbnail_files} thumbnail")

                # Add metadata to the mp3 files
                Logger.info("Adding metadata to mp3 files...")
                audio_file = EasyID3(f"{video['filename']}.mp3")

                # Downloaded music may not be in album, hence the default Nones
                # But we assmue all music should have a title and an artist
                if video["index"]:
                    audio_file["tracknumber"] = str(video["index"])
                if video["album"]:
                    audio_file["album"] = video["album"]
                else:
                    audio_file["album"] = video["track"]
                audio_file["albumartist"] = video["artist"]
                audio_file["artist"] = video["artist"]
                audio_file["title"] = video["track"]
                audio_file.save()
                Logger.info("Finished adding metadata to mp3 files")

                Logger.success("Downloaded and processed "
                               f"{video['filename']}.mp3 successfully!")

                break
            except KeyboardInterrupt:
                # Keyboard interrupt pauses the program and allows
                # the user to control the download: skip the video, cancel etc.
                Logger.warn("\nKeyboard interrupt detected!")
                Logger.warn("Pausing and waiting for user decision...")

                while True:
                    # Ensure the user inputs a valid option
                    user_decision = input("Retry, Skip, or Exit? (r|s|x) ")
                    if user_decision in {"r", "s", "x"}:
                        break
                    else:
                        Logger.warn("Invalid input!")

                # Handle user decision
                if user_decision == "r":
                    Logger.info("Trying again...")
                    continue
                elif user_decision == "s":
                    Logger.info("Skipping this video...")
                    break
                elif user_decision == "x":
                    Logger.info("Exiting...")
                    sys.exit(0)

            except Exception as e:
                Logger.err(f"Failed to download/process {video['title']}. ")
                Logger.err(e)
                if tries <= max_tries:
                    Logger.info("Trying again...")
                else:
                    # We have tried max_tries times and failed
                    Logger.warn(f"Exceeded max tries of {max_tries}. "
                                "Skipping this video...")

                # Clear the cache files to help with less errors
                Logger.info("Removing youtube-dl cache files...")
                os.system("youtube-dl --quiet --rm-cache-dir")
                continue

    # We are finished the downloads and its post processing!
    Logger.info("Finished downloading all videos")
    Logger.info(f"Removed {remove_build_files()} remaining build files")
    Logger.info("Exiting...")
    sys.exit(0)
