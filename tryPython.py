import os
import re
import mpv
import threading


def SearchSong(path='/home/hi-man/Music/') -> list:
    """ Search a song : 
    1. Local directory
    2. Fetch a youtube link (if it isn't found in local dir.)
    """
    def remove_punctuations(string: str) -> str:
        # remove path
        # regex pattern to get a filename -> ^/(?:[^/]*){4}([^/]*)
        # But i will simply use os.path.basename() to get a filename
        filename = os.path.basename(string)
        filename = re.sub('[\s\W_]', '', filename) # \s = whitespace, \W = [^A-Za-z0-9]
        return filename

    name = remove_punctuations(input(' Enter song name : '))
    pattern = f'.*{name}.*(?:mp[3|4]|opus|webm|wav)?'
    songs = []
    found = False

    for path, direc, files in os.walk(path, topdown=False):
        # no sorted files. 
        for i in range(0, len(files)): # O(N)
            if re.search(pattern, remove_punctuations(files[i]), re.IGNORECASE):
                songs.append(files[i]) # O(1)
                found = True
        
        if found is True:
            break # Don't search in sub-directories
    
    return (path, songs) if found is True else None


class MusicTerminal(mpv.MPV):
    pass

