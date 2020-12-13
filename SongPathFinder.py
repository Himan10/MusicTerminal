"""
Find songs:
    1. Find in a local dir
    2. [Alt. LOOKING] Check in the local saved cache
    3. [Alt. HARD LOOKING] Scrape it from youtube
"""

import os
import re
import json
import doctest
import youtube_dl


def _remove_punctuations(string: str) -> str:
    # remove path
    # regex pattern to get a filename -> ^/(?:[^/]*){4}([^/]*)
    # But i will simply use os.path.basename() to get a filename
    #filename = os.path.basename(string)
    # \s = whitespace, \w = [^A-Za-z0-9]
    filename = re.sub(r"(?<!\d)[^A-Za-z0-9,-]", "", string)
    return filename.lower()


class SearchSong:

    def __init__(self, songname: str, path=None):
        self.dirpath = "/home/hi-man/Music/"
        self.songname  = songname
        self.songname2 = lambda: re.sub(r'[\s\W_]', '', self.songname)

    def _yieldOrignalNames(self, path: str):
        """ call me again to get files stored in path """

        for dir_, subdir, files in os.walk(path, topdown=True):
            yield dir_, files

    def SearchLocal(self):

        def Helper(user_input: str, path: str, AlreadySearched: dict):
            """ Search songs in local directories [Recursive] """

            if path in AlreadySearched:
                return AlreadySearched[path]

            nonlocal orignalSongNames
            genObj = self._yieldOrignalNames(path)
            path, orignalSongNames = next(genObj)
            # Pause the generator at yield statement
            # until we send something to it or run next()

            temp = _remove_punctuations(', '.join(str(i)+'-'+orignalSongNames[i] for i in range(0, len(orignalSongNames))))

            # Find the songs
            user_input = re.sub(r'[^\s\w]', ' ', user_input).split()
            match = 0
            n = len(user_input)
            i = 0

            while i < n and match < n:
                pattern = r"[^,]*{0}[^,]*(?:mp[3|4]|opus|mkv|webm)".format(user_input[i])
                found = re.findall(pattern, temp, re.I)  # returns a list
                if found.__sizeof__() > 40:  # not an empty list
                    i += 1
                    match += 1
                    temp = ", ".join(found)

                    if match >= n:
                        genObj.close()
                        break
                else:
                    try:
                        path, orignalSongNames = next(genObj) # Call for path of another dir.
                        success, found, path = Helper(' '.join(user_input), path, AlreadySearched)
                        AlreadySearched[path] = success, found, path
                        if success:
                            genObj.close()
                            break
                    except Exception as err:
                        # Possible condition : We've iterated over all the paths but couldn't find any
                        return False, None, path

            AlreadySearched[path] = True, found, path
            return True, found, path

        # Main
        orignalSongNames = []
        AlreadySearched = {}
        songs = []
        path = self.dirpath
        result = Helper(self.songname, path, AlreadySearched)
        del AlreadySearched
        if result[0]:
            for i in result[1]:
                songs.append(orignalSongNames[int(i.lstrip().split('-')[0])])
            return result[2], songs # Path, songs

        return None, None


    def LoadFromFile(self):
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
            os.system("touch cache.txt")  # execute the shell commandi [vulnerable]

        if os.path.getsize("./cache.txt") != 0:
            # Perform a scan
            with open("./cache.txt", "r") as file:
                songdata = json.load(file)
                try:
                    return songdata[self.songname2()]
                except KeyError:
                    # Perform some more scan, not directly access
                    for key in songdata.keys():
                        found = MatchSong(self.songname2(), key)
                        if found is True:
                            found = songdata[key]
                            return found

        return found


    def YoutubeSearch(self):

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
                info_dict = ydl.extract_info(self.songname, download=False)
                videoID = info_dict["entries"][0]["id"] # song video ID
                title = info_dict['entries'][0]['title'] # song video Title
                youtube_link += videoID

                data = {}
                with open("./cache.txt", "r") as file:
                    if os.path.getsize("./cache.txt") != 0:
                        data = json.load(file)

                data[self.songname2()] = youtube_link

                with open("./cache.txt", "w") as file:
                    json.dump(data, file, indent=4)

            except Exception as err:
                print(err)

        return youtube_link


def findone():
    # a basic prompt for searching songs

    songname = ''
    while len(songname) < 1:
        songname = input(' Enter song name : ')

    searchObj = SearchSong(songname)
    found = searchObj.SearchLocal()

    if None in found:
        found = searchObj.LoadFromFile() # check in cache before youtube searching.
        if found == '':
            found = searchObj.YoutubeSearch()

    return found if isinstance(found, tuple) else (None, found.split())


def findmany(delim=','):
    # a basic prompt for searching all songs at once

    songlist = ''
    while len(songlist) < 1:
        songlist = input(' [Names separated by delimeter \',\']\n Enter Names : ').split(delim)
    
    data = {None: []}
    searchObj = SearchSong(songname=None)
    while songlist:
        searchObj.songname = songlist.pop().strip()
        found = searchObj.SearchLocal()

        if None in found:
            found = searchObj.LoadFromFile()
            if found == '':
                found = searchObj.YoutubeSearch()
            
            data[None].append(found)

        else:
            if found[0] in data:
                data[found[0]].extend(found[1])
            else:
                data[found[0]] = found[1]

    return data
