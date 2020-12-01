import mpv
import threading
import concurrent.futures
from SongPathFinder import os
from SongPathFinder import main
from connectToSql import SongDatabase


exit = threading.Event()


class MusicTerminal:
    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self._player.terminate()
        return isinstance(value, TypeError)

    def __init__(self, video: bool, ytdl=True, logging=False):
        self._player = mpv.MPV()  # returns a proxy object. (dont touch this)
        self.playlist0 = []  # temp. (provide to SQL)
        self._player.video = video
        self._player.ytdl = ytdl
        self.playing_msg = "stopped"
        self.logging = logging
        self.running = False
        self._threadExecutable = False
        self.repeat = 0

    def addsong(self, path: str, songs: list, database: bool, executor):
        """ executor should be an obj of 
        concurrent.futures.ThreadPoolExecutor """

        if database:
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
                future1 = self._play(executor)  # Call it only once or if adding a song
                return future1  # contains result of another thread

    def _play(self, executor):
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
        # bug : continues while the song is on PAUSE (Solved)

        while self._player.playlist_count > 0:

            if self._threadExecutable:
                # Get the current time stamp (not the entire time stamp of a song)
                totaltime = (
                    self._player.time_remaining + self._player.time_pos
                ) - self._player.time_pos
                print("wait until", totaltime)
                exit.wait(timeout=totaltime)  # have to make it wait
                print("loop stopped")
                if self.repeat > 0 and self.running:
                    self.repeat -= 1
                if self.repeat == 0 and self.running:
                    try:
                        self.remove(0, True)  # Delete the song from both queues
                    except Exception as err:
                        return err.args[0]
                if self._player.playlist_count > 0:
                    self._player.wait_until_playing()  # wait until new song starts

        print("here")
        self.stop(False)  # do not terminate
        return True

    def current_song(self):
        songname = filter(lambda x: "playing" in x, self._player.playlist)
        songname = os.path.basename(list(songname)[0]["filename"])
        return songname

    def remove(self, index: int, orignal=False):
        if index < 0:
            raise Exception("Negative Index not accepted")

        if self._player.playlist_count == 0:
            raise Exception("Playlist already Empty")

        if orignal:
            self.playlist0.pop(index)
        self._player.playlist_remove(index)

    def pause(self, val=True):
        # Not in idle state
        self._player.pause = val
        self.running = self._player.idle_active
        self.playing_msg = "paused"
        exit.set()

    def repeat_song(self, others):
        """ Repeat song : int(0-9) or str(0-9) """
        # Put the current song in repeat (Under-working)
        # no : normal playback
        # inf : infinite
        params = ["inf", True, False, "no", "yes"]
        if not (others in params):
            if str(others) not in "0123456789":
                raise Exception("Supplied wrong parameters")
            else:
                self.repeat += int(others) + 1

        self._player.loop_file = others
        print(" current song on repeat")

    def resume(self, val=False):
        # Not in idle state
        self._player.pause = val
        self.running = not self._player.idle_active
        self.playing_msg = "running"
        exit.clear()

    def stop(self, terminate: bool):
        # put the player in IDLE state
        # stop(): Clears the playlist
        # Not working : keep_playlist
        self._player.stop()
        self.running = False
        self.playing_msg = "stopped"
        self._threadExecutable = False
        if terminate:
            self._player.terminate()  # stop the thread. Destroys the mpv object

    def playlist_options(self, username: str, options):
        """ options : set_playlist | get_playlist """

        sd = SongDatabase(username)

        def set_playlist(playlist: list) -> None:
            sd.feed_data(playlist)
            sd.conn.close()

        def get_playlist() -> list:
            return sd.retrieve_data()
            sd.conn.close()

        if options.lower() == "set":
            return set_playlist
        elif options.lower() == "get":
            return get_playlist


def player():

    musicObj = MusicTerminal(video=False)
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)
    username = input(" User : ")
    try:
        temp = musicObj.playlist_options(username, "get")()
        if temp is not None:
            choice = input(" Wanna listen saved playlist [Y/n] ").lower()
            if choice == "y":
                future1 = musicObj.addsong(None, temp, True, executor)
        del temp
    except Exception as err:
        print(err.args[0])

    user_input = ""
    while user_input != "no":
        user_input = input(
            f" [{musicObj.playing_msg}] [Add|Repeat|Terminate|set playlist] : "
        ).lower()

        if user_input == "add":
            path, song = main()
            if song is None:
                exit()
            print("Song Added")
            temp = musicObj.addsong(path, song, False, executor)
            if temp is not None:
                future1 = temp
            del temp

        if user_input == "terminate":
            musicObj.stop(True)
            exit.set()
            # break

        if user_input == "repeat":
            repeatParam = input(" Enter repeat param : ")
            musicObj.repeat_song(repeatParam)

        if user_input == "queue":
            print("[")
            current = musicObj.current_song()
            for each_song in musicObj._player.playlist_filenames:
                each_song = os.path.basename(each_song)
                if current == each_song:
                    print("current ", each_song)
                else:
                    print("\t", each_song)
            print("]")

        if user_input == "set playlist":
            try:
                musicObj.playlist_options(username, "set")(musicObj.playlist0)
            except Exception as err:
                print(err.args[0])

    print("exit")
    return musicObj, future1
