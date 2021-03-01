# Pretty printing of dir items

import os
import re
import json
from colorama import Fore, Style

def getdirandfile(string):
    j = 0
    file_ = ""
    dirtuple = ("", "")
    for i in string:
        if i == "/":
            j += 1
        if j == 1:
            file_ += i
            continue
        if j > 1:
            j = 1
            dirtuple = (dirtuple[1], file_)
            file_ = "/"

    return dirtuple, file_[1:]


def getlevel(path: str):
    if not path.startswith("/"):
        return -1
    return sum(1 for i in re.finditer(r".*?/", path)) - 1

getvalue2 = lambda x: isinstance(x, list) and x[0] or x
getvalue = lambda y: isinstance(y, list) and y or [y]

def makelist(data, new=[]):
    if not data:
        return new
    if isinstance(data[0], list):
        return makelist(data[1:], new+data[0]) 
    else:
        return makelist(data[1:], new+[data[0]])

def sortqueue(songs):
    # implementation of merge sort
    # Time : O(N LogN)

    def merge(left, right, songs):
        i = 0  # index of left
        j = 0  # index of right
        k = -1  # index of orignal list
        while i < len(left) and j < len(right):
            leftlevel = getlevel(getvalue2(left[i]))
            rightlevel = getlevel(getvalue2(right[j]))
            if leftlevel < rightlevel:
                if k < 0:
                    k += 1
                    songs[k] = getvalue(left[i])
                else:
                    if isinstance(songs[k], list) and songs[k][0] == left[i]:
                        songs[k].append(left[i])
                    else:
                        k += 1
                        songs[k] = getvalue(left[i])
                i += 1

            elif leftlevel > rightlevel:
                if k < 0:
                    k += 1
                    songs[k] = getvalue(right[j])
                else:
                    if isinstance(songs[k], list) and songs[k][0] == right[j]:
                        songs[k].append(right[j])
                    else:
                        k += 1
                        songs[k] = getvalue(right[j])
                j += 1

            elif leftlevel == rightlevel:
                k += 1
                if os.path.dirname(getvalue2(left[i])) != os.path.dirname(
                    getvalue2(right[j])
                ):
                    songs[k] = getvalue(right[j])
                    k += 1
                    songs[k] = getvalue(left[i])
                else:
                    songs[k] = makelist([left[i], right[j]])
                i += 1
                j += 1
                # k += 1

        # uncompared elements
        while i < len(left):
            if isinstance(songs[k], list) and os.path.dirname(
                getvalue2(songs[k][0])
            ) == os.path.dirname(getvalue2(left[i])):
                songs[k].extend(getvalue(left[i]))
            else:
                k += 1
                songs[k] = getvalue(left[i])
            i += 1

        while j < len(right):
            if isinstance(songs[k], list) and os.path.dirname(
                getvalue2(songs[k][0])
            ) == os.path.dirname(getvalue2(right[j])):
                songs[k].extend(getvalue(right[j]))
            else:
                k += 1
                songs[k] = getvalue(right[j])
            j += 1

        # remove unnecessary elements
        if k < len(songs) - 1:
            temp = songs[0 : k + 1]
            songs.clear()
            songs.extend(temp)

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

    if not isinstance(songs[0], list):
        if len(songs) == 1:
            songs[0] = [songs[0]]
        handler(songs)
    else: # if list is already sorted (nested containers)
        return


def prettyprint(songs: list, playing="", repeat=0):
    # chr(9500) = '├', chr(9492) = '└', chr(9472) = '─', chr(9474) = '│'

    sortqueue(songs)
    level = 0
    parent = ""
    belong = 0
    islink = lambda x: not x.startswith("/") and 1 or 0
    dirclr = "\x1b[94m\x1b[1m {0}\x1b[0m"

    for i in range(len(songs)):
        for j in range(len(songs[i])):
            if islink(songs[i][j]):
                print(songs[i][j], " [Link]")
            else:
                dir_, file_ = getdirandfile(songs[i][j])
                if j == 0:  # first element of sublist (print it's dir name)
                    if level == 0 and not parent:
                        print(dirclr.format(dir_[1]))
                        parent = dir_[1]
                    elif level > 0 and parent:
                        if parent == dir_[0]:
                            belong += 1
                            if belong > 1:
                                level -= 4
                            if i != len(songs) - 1:
                                nextdir = getdirandfile(songs[i + 1][0])[0]
                                if parent == nextdir[0]:
                                    print(" " * level + chr(9500) + chr(9472) + dirclr.format(dir_[1]))
                                else:
                                    parent = nextdir[0]
                                    belong = 0
                                    print(" " * level + chr(9492) + chr(9472) + dirclr.format(dir_[1]))
                            else:
                                print(" " * level + chr(9492) + chr(9472) + dirclr.format(dir_[1]))
                                belong = 0
                        else:
                            parent = dir_[0]
                            belong = 0
                            print(" " * level + chr(9492) + chr(9472) + dirclr.format(dir_[1]))
                    level += 4
                if belong >= 1:
                    print(
                        " " * (level - 4)
                        + chr(9474)
                        + " " * 3
                        + chr(9500)
                        + chr(9472)
                        + ' '
                        + file_
                    )
                elif not (i == len(songs) - 1 and j == len(songs[-1]) - 1):
                    print(" " * level + chr(9500) + chr(9472) + ' ' + file_)
                else:
                    print(" " * level + chr(9492) + chr(9472) + ' ' + file_)
