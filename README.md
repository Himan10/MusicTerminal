# Music Terminal (Enhanced MPV)

## What is it about?
  Basically, the idea of this project is to enhance the usage of `mpv` media player using python.

  What makes this project different from using the linux command-line tool called `mpv` is that you can implement and connect your ideas with the working of `mpv module` methods. It's better to have one package which does all the thing instead of having different tools and scripts, and figuring out some ways to connect or communicate with each other and with the tool. 

  Python `mpv module` provides methods which are also available in the command line tool as well, so here we can use those methods with our ideas and create something entirely different.

## Initial Tasks :
- ### **Find songs in the given directory** : 
    This task makes use of several techniques to find songs and extract songs from the given directory. This task finds the absolute path of the song and returns it to the caller. If the song isn't found in the given directory, then it tries to get a youtube link of that particular song. 

    It's possible to iterate over multiple directories but for that you've to pass directory path to the attribute called `self.dirname` of class `SearchSong`. Right now I've only used one single directory so that it only searches the song in the given directory and its sub-dir.  Iterating over N number of sub-directories is done by using the technique called `recursion`, and in case if the song is found in sub-directory "A", then it won't go to the other sub-directories. Here, suppose if you've two songs with the same name in two diff. sub-directories, then it returns only the matched song path present in first iterated sub-directory.

    In case if the song isn't found in any of the given directories, then it fetches the song youtube link using `youtube-dl` and saves the link in a cache file along with the song name, so that next time if script tries to get the path of the same song which previously wasn't found in the given directories, then script gets it from the cache file which stores a json object in it, in this format -> `{song_name : song_link}`. This reduces some couple of seconds of going through youtube everytime. 
    
    Following are techniques used in this task :
    - os.walk()
    - regex
    - recursion
    - youtube_dl.YoutubeDL
    - json

- ### **Command Handler** :
    Think of it as like a discord bot, you give it a command and it performs the action related with that command.
    All the commands are stored in a dictionary `commands_dict` of class `Commands`. The reason why I chose to store the commands in a dictionary because it would seem odd to write such a large file only dedicated to `if command == 'play'` and many others if statements, and it doesn't make much sense having a separate file. 

    Used techniques :
    - decorators
    - single level inheritance

- ### **Pretty Queue** :
    I got the idea to create this by a command line tool called `tree`.  In the method `_addsong()` it appends the songs in two different list i.e., `self.playlist0` and `self._player.playlist` (this one is provided by the MPV class). So when the items are successfully appended to both the lists and the user runs a command `queue` it makes a call to `prettyprint` which prints the list items in a tree style. 

    For example:
 
          /Music/LinkinPark
              ├── Crawling (Official Video) Linkin Park.mp4
              ├── AudioSlave Like a Stone.mp4
              └── Snuff Slipknot.mp4
    
    Used techniques : 
    - Merge sort 
          
        *Reason* : Used a merge sort based on the directory level. For example : `/home/user/Music/` has level = 3. So, all the songs get sorted according to their directory level. 
    (Note : This isn't much efficient neither well written, it isn't working correctly but its looks fashionable still, will make changes in future :) )

- ### **Connect To SQL** :
    This task is used to store listened songs in the database (using SQLite3). Why used SQL? Because here, a user can store all the songs he has listened to or listening to in a database with his `name.db`, so when he comes back and uses the player, it'll check if the database of the given name exists or not, if it exists then retrieve songs from there and appends them to both the list (`self.playlist0` and `self._player.playlist`).

- ### **Music Player** :
    Finally, the boss script which connects everything and does all the job.
  
    Commands list : 
    - **addViaDB** - Add songs stored in the database to the list
    - **add** - Add songs found using `SongPathFinder.py`
      - **_play** - Play songs
        - **_tracksong** - (The important one for pause/resume/stop) Wait until the song ends, once it is end then remove it from the list. 
    - **current** - Returns the current playing song
    - **pause** - Pause the song
    - **resume** - resume the song
    - **repeat** - repeat N times.
    - **stop** - if `terminate=True` stops the music player, shutdown the core and exit. You can't use it again. If `terminate=False` (or not set) stops the music player only
    - **queue** - prints the queue (in tree structure)
    - **playlist**
      - **set_playlist** - store the songs onto database
      - **get_playlist** - Retrives the songs from database


**Long short story - This is just a fun project to learn new things and challenge me in new ways. There's a lot to add to this project.**

***Stay tuned!!!***
