from music_player import MusicTerminal
from concurrent.futures import Executor

def music_player():
    player = MusicTerminal(video=False, prefix='/')
    
    username = input(" User : ")
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
    future = None
    print(f' Use Prefix before command : /command args')
    try:
        while user_input != "no":
            user_input = input(f"[{player.playing_msg}] [Add|Repeat|Terminate|playlist set/get] : ").lower()
            # only one function will return smth, and it's `add_song`
            # so, we only need to create a var. `future`
            temp = player.process_command(user_input)
            if isinstance(temp, Executor):
                future = temp
            del temp
    except KeyboardInterrupt:
        return future
    finally:
        return future
