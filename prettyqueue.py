# Pretty printing of dir items

import os
import re
import json
from colorama import Fore, Style

getlevel = lambda path: (sum(i and 1 or 0 for i in re.finditer(r".*?\/", path)) - 1)

def sortqueue(songs):
    # implementation of merge sort
    # Time : O(N LogN)

    def merge(left, right, songs):
        i = 0  # index of left
        j = 0  # index of right
        k = 0  # index of orignal list
        while i < len(left) and j < len(right):
            leftlevel = getlevel(left[i])
            rightlevel = getlevel(right[j])
            if leftlevel <= rightlevel:
                songs[k] = left[i]
                i += 1
            elif leftlevel > rightlevel:
                songs[k] = right[j]
                j += 1
            k += 1

        while i < len(left):
            songs[k] = left[i]
            i += 1
            k += 1

        while j < len(right):
            songs[k] = right[j]
            j += 1
            k += 1

    def handler(songs):
        if len(songs) <= 1:
            return songs
        mid = len(songs) // 2
        left = songs[0:mid]
        right = songs[mid::]
        handler(left)
        handler(right)
        merge(left, right, songs)
        return songs

    handler(songs)


def prettyprint(songs: list, playing: str, repeatno: int):
    # print contents of songs in tree format
    # chr(9492) = '└' , chr(9472) = '─'

    sortqueue(songs)  # sort songs list
    level = -4  # for 4 whitespaces
    current = ""
    islink = lambda x: not x.startswith("/") and 1 or 0

    for i in songs:
        if islink(i):
            print("[Link] ", i)
        else:
            path, file_ = re.search(f"{os.getenv('HOME')}(.*)/(.*)$", i).group(1, 2)
            if path != current:
                if not current and level == -4:
                    print(f"{Fore.BLUE}{Style.BRIGHT}{path}{Style.RESET_ALL}")
                current = path
                if level > -4:
                    path = f"{Fore.BLUE}{Style.BRIGHT}{path}{Style.RESET_ALL}"
                    print(" " * level + chr(9492) + chr(9472) * 2 + " " + path)
                level += 8
            i = os.path.basename(i)
            if file_ == playing:
                print(" " * level + chr(9492) + chr(9472) * 2 + " " + file_ + f" [current][{repeatno}]")
            else:
                print(" " * level + chr(9492) + chr(9472) * 2 + " " + file_)

    print("\n")
