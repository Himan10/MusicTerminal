import mpv
import threading
from time import sleep
import concurrent.futures
from SongPathFinder import os
from SongPathFinder import re
from SongPathFinder import SearchSong

exit = threading.Event()

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
        songs = songs if isinstance(songs, list) else [songs]
        self.playlist0.extend(songs)
        for song in songs:
            if path is None:
                self._player.playlist_append(song)
            else:
                self._player.playlist_append(os.path.join(path , song))
    
        if self._player.playlist_count > 0:
            if self._threadExecutable:
                pass
            else:
                future1 = executor.submit(self._play) # Call it only once or if adding a song
                return future1 # this future1.result() contains future of another thread

    def _play(self):
        """ Shouldn't be executed in main
        State : [play, pause] -> BUSY
        State : [open, close] -> IDLE
        """
        
        if self._player.idle_active:
            if self._player.playlist_count > 0:
                if self.running is False:
                    self._player.playlist_pos = 0
                    self._threadExecutable = True
                    sleep(5) # Delay problem if sleep(1) not used here.
                    Future = executor.submit(self._track_song)

                self.playing_msg = 'running'
                self.running = not self._player.idle_active
                print(self.running, self._player.idle_active)
                print(f'\n == {self.playing_msg} ==\n')
            else:
                self.playing_msg = 'stopped'
                self.running = self._player.idle_active

        return Future

    def _track_song(self): # Because we want real timestamp updates, not only once.

        while a:=self._player.playlist_count > 0:
            song = filter(lambda x: 'playing' in x.keys(), self._player.playlist)
            # check if the song is url or path

            if self._threadExecutable:
                songName = os.path.basename(list(song)[0]['filename'])
                #url = True if songName.startswith('https://www.youtube.com') else False
                #delay = 4 if url else 0
                print(songName)
                totaltime = self._player.time_pos + self._player.time_remaining
                exit.wait(timeout=totaltime) #sleep(totaltime)
                self.remove(0) # Delete the song from both queues
                if len(self.playlist0) > 0:
                    self._player.wait_until_playing()

        print('here')
        self.stop(False) # do not terminate
        return True

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

    def resume(self, val=False):
        # Not in idle state
        self._player.pause = val
        self.running = not self._player.idle_active
        self.playing_msg = 'running'

    def stop(self, terminate: bool):
        # put the player in IDLE state
        self._player.stop()
        self.running = False
        self.playing_msg = 'stopped'
        self._threadExecutable = False
        if terminate:
            self._player.terminate() # stop the thread. Destroys the mpv object


if __name__ == "__main__":

    choice = 'yes'
    player = MusicTerminal(video=False)
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    path, songs = SearchSong()
    future1 = player.addsong(path, songs, executor) # Might use partial function for this
    sleep(6) #print('need sleep')
    choice = ''
    while player.running and choice != 'no': # Should accept more input
        choice = input(' More [options|no|terminate|add] : ')
        if choice == 'playlist':
            print(player.playlist0)
        if choice == 'terminate':
            player.stop(True)
        if choice == 'add':
            p, s = SearchSong()
            future2 = player.addsong(p, s, executor)

    # Once the choice = 'no', control of main goes to an end but befor that, all the threads running will complete their task.
