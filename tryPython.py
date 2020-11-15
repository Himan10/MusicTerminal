import mpv
import threading
import concurrent.futures
from songPathFinder import os
from songPathFinder import main

exit = threading.Event()


class MusicTerminal:
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        return isinstance(value, TypeError)

    def __init__(self, video: bool, ytdl=True, logging=False):
        self._player = mpv.MPV()  # returns a proxy object. (dont touch this)
        self.playlist0 = []  # temp. (saving)
        self._player.video = video
        self._player.ytdl = ytdl
        self.playing_msg = "stopped"
        self.logging = logging
        self.running = False
        self._threadExecutable = False
        self.repeat = 0

    def addsong(self, path: str, songs: list, executor):
        """ executor should be an obj of 
        concurrent.futures.ThreadPoolExecutor """

        songs = songs if isinstance(songs, list) else [songs]
        self.playlist0.extend(songs)
        for song in songs:
            if path is None:
                self._player.playlist_append(song)
            else:
                self._player.playlist_append(os.path.join(path, song))

        if self._player.playlist_count > 0:
            if self._threadExecutable:
                pass
            else:
                future1 = self._play()  # Call it only once or if adding a song
                return future1 # contains result of another thread

    def _play(self):
        """ Shouldn't be executed in main
        State : [play, pause] -> BUSY
        State : [open, close] -> IDLE
        """
        if self._player.idle_active:
            if self._player.playlist_count > 0:
                if self.running is False:
                    self._player.playlist_pos = 0
                    self._player.wait_until_playing() # PAUSE everything until song doesn't get started.
                    self._threadExecutable = True
                    Future = executor.submit(self._track_song)

                self.playing_msg = "running"
                self.running = not self._player.idle_active
                print(self.running, self._player.idle_active)
                print(f"\n == {self.playing_msg} ==\n")
            else:
                self.playing_msg = "stopped"
                self.running = self._player.idle_active

        return Future

    def _track_song(self):  # Because we want real timestamp updates, not only once.

        while self._player.playlist_count > 0:
            song = filter(lambda x: "playing" in x.keys(), self._player.playlist)
            # check if the song is url or path

            if self._threadExecutable:
                songName = os.path.basename(list(song)[0]["filename"])
                totaltime = self._player.time_pos + self._player.time_remaining
                exit.wait(timeout=totaltime) 
                if self.repeat > 0:
                    self.repeat -= 1
                if self.repeat == 0:
                    self.remove(0, True)  # Delete the song from both queues
                if len(self.playlist0) > 0:
                    self._player.wait_until_playing() # wait until new song starts

        print("here")
        self.stop(False)  # do not terminate
        return True

    def remove(self, index: int, orignal=False):
        if index < 0:
            raise Exception("Negative Index not accepted")
        
        self.playlist0.pop(index)
        self._player.playlist_remove(index)

    def pause(self, val=True):
        # Not in idle state
        self._player.pause = val
        self.running = self._player.idle_active
        self.playing_msg = "paused"

    def repeat_song(self, others):
        """ Repeat song : int(0-9) or str(0-9) """
        # Put the current song in repeat (Under-working)
        # no : normal playback
        # inf : infinite
        params = ['inf', True, False, 'no', 'yes']
        if not (others in params):
            if str(others) not in '0123456789':
                raise Exception('Supplied wrong parameters')
            else:
                self.repeat += int(others)+1

        self._player.loop_file = others
        print(" current song on repeat")

    def resume(self, val=False):
        # Not in idle state
        self._player.pause = val
        self.running = not self._player.idle_active
        self.playing_msg = "running"

    def stop(self, terminate: bool):
        # put the player in IDLE state
        self._player.stop() 
        self.running = False
        self.playing_msg = "stopped"
        self._threadExecutable = False
        if terminate:
            self._player.terminate()  # stop the thread. Destroys the mpv object


if __name__ == "__main__":

    musicObj = MusicTerminal(video=False)
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    user_input = ''
    while user_input != 'no':
        user_input = input(f' [{musicObj.running}] [Add|Repeat|Terminate|Playlist] : ').lower()
        if user_input == 'add':
            path, song = main()
            if song is None:
                exit()
            print('Song Added')
            future1 = musicObj.addsong(path, song, executor)

        if user_input == 'terminate':
            musicObj.stop(True)
            break

        if user_input == 'repeat':
            repeatParam = input(' Enter repeat param : ')
            musicObj.repeat_song(repeatParam)

        if user_input == 'playlist':
            print(musicObj.playlist0)

    print('exit')
