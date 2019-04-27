#!/usr/bin/env python

import os
import socket
import struct
import sys
import cPickle as pickle
from threading import Lock, Thread


QUEUE_LENGTH = 10
SEND_BUFFER = 4096

songlist = {}

# per-client struct
class Client:
    def __init__(self):
        self.lock = Lock()
        self.conn = None
        self.addr = None

        self.test_string = ""


    def create_new_socket(self, conn, addr):
        self.conn = conn
        self.addr = addr


# TODO: Thread that sends music and lists to the client.  All send() calls
# should be contained in this function.  Control signals from client_read could
# be passed to this thread through the associated Client object.  Make sure you
# use locks or similar synchronization tools to ensure that the two threads play
# nice with one another!
def client_write(client):
    
    client.conn.sendall(pickle.dumps(songlist, pickle.HIGHEST_PROTOCOL))
    client.conn.sendall("")


# TODO: Thread that receives commands from the client.  All recv() calls should
# be contained in this function.
def client_read(client):
    
    while True:
        data = client.conn.recv(SEND_BUFFER)
        client.test_string = data
        print(client.test_string)
   
    return 0


def get_mp3s(musicdir):
    print("Reading music files...")
    songs = []
    song_i = 0

    for filename in os.listdir(musicdir):
        if not filename.endswith(".mp3"):
            continue

        # TODO: Store song metadata for future use.  You may also want to build
        # the song list once and send to any clients that need it.

        songlist[song_i] = filename
        song_i += 1

    print("Found {0} song(s)!".format(len(songlist)))

    return songs, songlist

def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python server.py [port] [musicdir]")
    if not os.path.isdir(sys.argv[2]):
        sys.exit("Directory '{0}' does not exist".format(sys.argv[2]))

    port = int(sys.argv[1])
    songs, songlist = get_mp3s(sys.argv[2])

    threads = []

    # TODO: create a socket and accept incoming connections
    
    # Set up necessary parts
    HOST = ''           # Symbolic name meaning all available interfaces
    master_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    master_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    master_socket.bind((HOST, port))
    master_socket.listen(QUEUE_LENGTH) 

    while True:
       
        # Accept new connection and declare it as client
        client_socket, addr = master_socket.accept()
        client = Client()
        client.create_new_socket(client_socket, addr)

        t = Thread(target=client_read, args=(client,))
        threads.append(t)
        t.start()

        t = Thread(target=client_write, args=(client,))
        threads.append(t)
        t.start()
    s.close()

if __name__ == "__main__":
    main()
