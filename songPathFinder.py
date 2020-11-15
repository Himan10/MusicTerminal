"""
Find songs:
    1. Find in a local dir
    2. [Alt. LOOKING] Check in the local saved cache
    3. [Alt. HARD LOOKING] Scrape it from youtube
"""

import os
import re
import json
import youtube_dl


def _remove_punctuations(string: str) -> str:
    # remove path
    # regex pattern to get a filename -> ^/(?:[^/]*){4}([^/]*)
    # But i will simply use os.path.basename() to get a filename
    filename = os.path.basename(string)
    # \s = whitespace, \w = [^A-Za-z0-9]
    filename = re.sub(r'[\s\W_]', "", filename)
    return filename.lower()


class SearchSong:

    def __init__(self, path=None):
        self.dirpath = "/home/hi-man/Music/"

    def SearchLocal(self, name) -> tuple:
        """ Search a song :  Local directory [path] """

        name = _remove_punctuations(name)
        pattern = f".*{name}.*(?:mp[3|4]|opus|webm|wav)"
        songs = []
        found = False

        for path, direc, files in os.walk(self.dirpath, topdown=False):
            for i in range(0, len(files)):  # O(N)
                if re.search(
                        pattern, _remove_punctuations(files[i]), re.IGNORECASE
                ):
                    songs.append(files[i])  # O(1)
                    found = True

            if found is True:
                break  # Don't search in sub-directories

        song_path = (path, songs) if found is True else (None, None)
        return song_path


    def LoadFromFile(self, songname: str):
        """
        After not found in local dir, Check if the songname exist in
        cache file... RETURN link if exist.
        """

        def MatchSong(songname: str, target: str):
            found = True
            for i in range(0, len(songname), 4):
                if songname[i: i + 4] not in target:
                    found = ''
                    break

            return found

        found = ''
        if not os.path.exists("./cache.txt"):
            os.system("touch cache.txt")  # execute the shell command

        if os.path.getsize("./cache.txt") != 0:
            # Perform a scan
            with open("./cache.txt", "r") as file:
                songdata = json.load(file)
                songname = _remove_punctuations(songname)
                try:
                    return songdata[songname]
                except KeyError:
                    # Perform some more scan, not directly access
                    for key in songdata.keys():
                        found = MatchSong(songname, key)
                        if found is True:
                            found = songdata[key]
                            return found

        return found


    def YoutubeSearch(self, songname: str):

        ytdl_options = {
            "default_search": "auto",
            "quiet": True,
            "extractaudio": True,
            "audioformat": "mp3",
            "format": "bestaudio/best[filesize<20M]",
            "noplaylist": True,
            "outtmpl": "%(id)s",
        }

        youtube_link = "https://www.youtube.com/watch?v="
        with youtube_dl.YoutubeDL(ytdl_options) as ydl:
            try:
                info_dict = ydl.extract_info(songname, download=False)
                videoID = info_dict["entries"][0]["id"]
                youtube_link += videoID

                data = {}
                with open("./cache.txt", "r") as file:
                    if os.path.getsize("./cache.txt") != 0:
                        data = json.load(file)

                data[_remove_punctuations(songname)] = youtube_link

                with open("./cache.txt", "w") as file:
                    json.dump(data, file, indent=4)

            except Exception as err:
                print(err)

        return youtube_link

def main():
    # a basic prompt for searching songs

    searchObj = SearchSong()

    songname = ''
    while len(songname) < 1:
        songname = input(' Enter song name : ')

    found = searchObj.SearchLocal(songname)

    if None in found:
        found = searchObj.LoadFromFile(songname) # check in cache before youtube searching.
        if found == '':
            found = searchObj.YoutubeSearch(songname)

    return found if isinstance(found, tuple) else (None, found)
