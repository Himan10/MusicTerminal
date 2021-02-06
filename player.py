from concurrent.futures import Future
from music_player import MusicTerminal

def prompt():

    player = MusicTerminal(video=False, prefix='/')
    username = input(" User : ")
    future = None
    
    try:
        saved_playlist = player.playlist(username, "get")()
        if saved_playlist is not None:
            choice = input(" Wanna listen saved playlist [Y/n] ").lower()
            if choice == "y":
                future = player.addViaDB(saved_playlist)

        del saved_playlist
    except Exception as err:
        print(err.args[0])

    user_input = ''
    print(f' Use Prefix before command : /command args')
    try:
        while user_input != "no" and not player.core_shutdown():
            user_input = input(f"[{player.playing_msg}] [Add|Repeat|Terminate|playlist set/get] : ").lower()
            # only one function will return smth, and it's `add_song`
            # so, we only need to create a var. `future`
            temp = player.process_command(user_input)
            if isinstance(temp, Future):
                future = temp
            del temp
    except KeyboardInterrupt:
        return player, future
    finally:
        return player, future
