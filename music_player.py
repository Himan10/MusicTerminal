import mpv
from threading import Event
from threading import Thread
from threading import enumerate
from threading import current_thread
from SongPathFinder import os
from SongPathFinder import findone, findmany
from connectToSql import SongDatabase
from command_handler import Command
from command_handler import InputParser
from concurrent.futures import Executor # for executor type checking
from concurrent.futures import ThreadPoolExecutor


class MusicTerminal(InputParser):
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.stop(True)
        return isinstance(value, TypeError)

    def __init__(self, video: bool, prefix: str, ytdl=True, logging=False, event_thread=True):
        super().__init__(prefix)
        self._player = mpv.MPV()  # returns a proxy object. (dont touch this)
        self.playlist0 = []  # temp. (provide to SQL)
        self.playlistpos = 0 # orignal playlist position 
        self._player.video = video
        self._player.ytdl = ytdl
        self.playing_msg = "stopped"
        self.logging = logging
        self.running = False
        self._threadStopper = Event()
        self._threadExecutor = None
        self._threadExecutable = False
        self.repeat = 0

        if event_thread:
            self._threadExecutor = ThreadPoolExecutor(max_workers=1)

    def addViaDB(self, song_playlist):
        """ shortcut decorator that invokes
        1. _addsong()
        Called only at the startup
        """        
        futureObj = self._addsong(None, song_playlist, True)
        return futureObj

    @InputParser.command
    def add(self, *arg):
        """ shortcut decorator that invokes
        1. findSong()
        2. _addsong()

        args: possible a thread executor
        """
        if len(arg) >= 1 and arg[0] != 'many':
            raise Exception('Usage : /add or /add many')
        
        if arg:
            # find multiple songs
            result = ''
            getdict = findmany(',')
            for path, songs in getdict.items():
                if path is not None and songs.__sizeof__() != 40:
                    temp = self._addsong(path, songs, False)
                    if temp is not None:
                        result = temp
                    del temp
            
            print('Songs Added')
            return result

        else:
            path, songs = findone()
            print('Song Added')
            return self._addsong(path, songs, False)

    def _addsong(self, path: str, songs: list, database: bool):
        """ executor should be an obj of 
        concurrent.futures.ThreadPoolExecutor """

        if database:
            self.playlistpos = len(songs)
            for song in songs:
                self._player.playlist_append(song[0])
                self.playlist0.append([song[0]])

        else:
            # provide values to SQLite DB. [[], []]
            for song in songs:
                
                if path is None and song not in self._player.playlist_filenames:
                    self._player.playlist_append(song)
                    self.playlist0.append([song])

                elif path is not None:
                    songpath = os.path.join(path, song)
                    if songpath not in self._player.playlist_filenames:
                        self._player.playlist_append(songpath)
                        self.playlist0.append([songpath])

        if self._player.playlist_count > 0:
            if self._threadExecutable:
                return None
            else:
                future1 = self._play() # Call it only once or if adding a song
                return future1  # contains result of another thread

    def _play(self):
        """ Shouldn't be executed in main
        State : [play, pause] -> BUSY
        State : [open, close] -> IDLE
        """
        if self._player.idle_active:
            if self._player.playlist_count > 0:
                if self.running is False:
                    self._player.playlist_pos = 0
                    self._player.wait_until_playing()  # PAUSE everything until song doesn't get started.
                    self._threadExecutable = True
                    Future = self._threadExecutor.submit(self._track_song)

                self.playing_msg = "running"
                self.running = not self._player.idle_active
                #print(self.running, self._player.idle_active) 
                #print(f"\n == {self.playing_msg} ==\n")
            else:
                self.playing_msg = "stopped"
                self.running = self._player.idle_active

        return Future

    def _track_song(self):  # Because we want real timestamp updates, not only once.
        # bug : continues while the song is on PAUSE (Solved)

        while self._player.playlist_count > 0:

            if self._threadExecutable:
                # Get the current time stamp (not the entire time stamp of a song)
                totaltime = (
                    self._player.time_remaining + self._player.time_pos
                ) - self._player.time_pos
                self._threadStopper.wait(timeout=totaltime)  # have to make it wait
                if self.repeat > 0 and self.running:
                    self.repeat -= 1
                if self.repeat == 0 and self.running:
                    try:
                        self.remove(0, True)  # Delete the song from both queues
                    except Exception as err:
                        return err.args[0]
                if self._player.playlist_count > 0:
                    self._player.wait_until_playing()  # wait until new song starts
            else:
                break

        self.stop(False)  # do not terminate
        return True

    @InputParser.command
    def current(self, show=True):
        if not self._player.playlist:
            return print('Playlist Empty')
        songname = filter(lambda x: "playing" in x, self._player.playlist)
        songname = os.path.basename(list(songname)[0]["filename"])
        return songname if not show else print(songname)

    @InputParser.command
    def remove(self, index: int, orignal=False):
        if index < 0:
            raise Exception("Negative Index not accepted")

        if self._player.playlist_count == 0:
            raise Exception("Playlist already Empty")

        if orignal:
            self.playlist0.pop(index)
        self._player.playlist_remove(index)

    @InputParser.command
    def pause(self):
        # Not in idle state
        if not self.running:
            raise Exception('Player is Already Stopped/Paused')
        self._player.pause = True
        self.running = self._player.idle_active
        self.playing_msg = "paused"
        if not self._threadStopper.is_set():
            self._threadStopper.set()

    @InputParser.command
    def repeat(self, others):
        """ Repeat song : int(0-9) or str(0-9) """
        # Put the current song in repeat (Under-working)
        # no : normal playback
        # inf : infinite

        if not self._threadExecutable:
            raise Exception('Nothing to Repeat')

        params = ["inf", True, False, "no", "yes"]
        if not (others in params):
            if str(others) not in "0123456789":
                raise Exception("Supplied wrong parameters")
            else:
                self.repeat += int(others) + 1

        self._player.loop_file = others
        print(" current song on repeat")

    @InputParser.command
    def resume(self):
        # Not in idle state
        # while playing a song 
        if self.running and self._threadExecutable:
            raise Exception('Nothing on paused rn')
        # while player is terminated
        elif not self.running and not self._threadExecutable:
            raise Exception('Player is already stopped')
        # while player is paused (running = False, threadExecutable = True)
        else:
            self._player.pause = False
            self.running = not self._player.idle_active
            self.playing_msg = "running"
            self._threadStopper.clear()

    ##### FIX THIS [TERMINATE THE OBJECT AND DON'T RESUE IT #####
    @InputParser.command
    def stop(self, terminate=False):
        # Not working : keep_playlist
        
        terminate = bool(terminate)
        self._player.stop()
        if self.running and not self._threadStopper.is_set():
            self._threadStopper.set() # set the flag and ends the func. has event.wait()
        self._player.pause = False
        self.running = False
        self.playing_msg = "stopped"
        self._threadExecutable = False
        if isinstance(terminate, bool) and terminate is True:
            if self._threadStopper.is_set():
                self._threadStopper.clear()
            # stop the thread and destroys the mpv object
            self._player.quit()
            self._player.wait_for_shutdown()
            self._player.terminate()

            # free all the resources (thread function) executor has executed..
            self._threadExecutor.shutdown(wait=True) # prevents executor to accepts new threads
 
        if self._threadStopper.is_set():
            self._threadStopper.clear() # remove the flag [for re-use]

    @InputParser.command
    def queue(self):
        if not self.running and not self._threadExecutable:
            return print("Playlist empty")
        print('\n [')
        current = self.current(show=False)
        for songname in self._player.playlist_filenames:
            songname = os.path.basename(songname)
            if songname == current:
                print('   [Current]    ', current)
            else:
                print('\t\t', songname)
        print(' ]\n')

    @InputParser.command
    def playlist(self, username: str, options):
        """ options = set | get 
        USE : /playlist raven set
        """

        sd = SongDatabase(username)

        def set_playlist(playlist: list) -> None:
            sd.feed_data(playlist)
            sd.conn.close()

        def get_playlist() -> list:
            return sd.retrieve_data()
            sd.conn.close()

        if options.lower() == "set":
            set_playlist(self.playlist0)
        elif options.lower() == "get":
            return get_playlist
