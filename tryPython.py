import os
import re
import mpv
import threading
from time import sleep
import concurrent.futures

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
    pattern = f'.*{name}.*(?:mp[3|4]|opus|webm|wav)'
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
    
    return (path, songs) if found is True else (None, None)


class MusicTerminal:

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        return isinstance(value, TypeError)

    def __init__(self, video: bool, ytdl=True, logging=False):
        self._player = mpv.MPV() # returns a proxy object. (dont touch this)
        self.playlist0 = [] # temp.
        self._player.video = video
        self._player.ytdl = ytdl
        self.playing_msg = 'stopped'
        self.logging = logging
        self.running = False
        self._threadExecutable = False

    def addsong(self, path: str, songs: list, executor): # Make this a thread
        """ executor should be an obj of concurrent.futures.ThreadPoolExecutor """
        self.playlist0.extend(songs)
        for song in songs:
            self._player.playlist_append(os.path.join(path, song))
    
        if self._player.playlist_count > 0:
            if self._threadExecutable:
                pass
            else:
                executor.submit(self._play, executor) # Call it only once or if adding a song

    def _play(self, executor):
        """ Shouldn't be executed in main
        State : [play, pause] -> BUSY
        State : [open, close] -> IDLE
        """
        
        print('Before starting : ',  self._player.idle_active)
        if self._player.idle_active:
            print('Here : ', self._player.idle_active)
            if self._player.playlist_count > 0:
                if self.running is False:
                    self._player.playlist_pos = 0
                    self._threadExecutable = True
                    # This sleep(2) won't start another thread bcz this func. isn't a thread
                    sleep(2) # Delay problem if sleep(1) not used here.
                    executor.submit( # starts tracking a song (basically a thread)
                            self._track_song,
                            self._player.time_pos,
                            self._player.time_remaining
                    )
                    print('Here1 : ', self._player.idle_active) # The problem occured with this
                
                self.playing_msg = 'running'
                self.running = not self._player.idle_active
                print(self.running, self._player.idle_active)
                print(f'\n == {self.playing_msg} ==\n')
            else:
                self.playing_msg = 'stopped'
                self.running = self._player.idle_active


    def _track_song(self, current_time=0, remaining_time=0):
        while self._player.playlist_count > 0:
            song = filter(lambda x: 'playing' in x.keys(), self._player.playlist)

            if self._threadExecutable:
                songName = os.path.basename(list(song)[0]['filename'])
                print(songName)
                totaltime = current_time + remaining_time
                sleep(totaltime)
                self.remove(0) # Delete the song from both queues

    def remove(self, index: int):
        if index < 0:
            raise Exception('Negative Index not accepted')
        self.playlist0.pop(index)
        self._player.playlist_remove(index)

    def pause(self, val=True):
        # Not in idle state
        self._player.pause = val
        self.running = self._player.idle_active
        self.playing_msg = 'paused'
        # player won't be in idle state

    def resume(self, val=False):
        # Not in idle state
        self._player.pause = val
        self.running = not self._player.idle_active
        self.playing_msg = 'running'

    def stop(self):
        # put the player in IDLE state
        self._player.stop()
        self.running = False
        self.playing_msg = 'stopped'
        self._threadExecutable = False


if __name__ == "__main__":
    """ According to the author of python-mpv, `mpv` starts a thread
    for dealing with events, so it's already started as a thread we
    don't need to make it one
    """

    choice = 'yes'
    player = MusicTerminal(False, False)
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    path, songs = SearchSong()
    player.addsong(path, songs, executor)
    print('here, main')
    #print(future.result())
    sleep(3) #print('need sleep')
    choice = ''
    while player.running and choice != 'no': # Should accept more input
        choice = input(' More [options|no] : ')
        if choice == 'playlist':
            print(player.playlist0)

                # Once the choice = 'no', control of main goes to an end but befor that, all the threads running will complete their task.
