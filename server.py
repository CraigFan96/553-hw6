#!/usr/bin/env python

import os
import socket
import struct
import sys
from threading import Lock, Thread


QUEUE_LENGTH = 10
SEND_BUFFER = 4096

# per-client struct
class Client:
    def __init__(self):
        self.lock = Lock()
        self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.addr = ()

    def create_new_socket(self, conn, addr):
        self.conn = conn
        self.addr = addr


# TODO: Thread that sends music and lists to the client.  All send() calls
# should be contained in this function.  Control signals from client_read could
# be passed to this thread through the associated Client object.  Make sure you
# use locks or similar synchronization tools to ensure that the two threads play
# nice with one another!
def client_write(client):
    pass

# TODO: Thread that receives commands from the client.  All recv() calls should
# be contained in this function.
def client_read(client):
    
    
    


def get_mp3s(musicdir):
    print("Reading music files...")
    songs = []
    songlist = []

    for filename in os.listdir(musicdir):
        if not filename.endswith(".mp3"):
            continue

        # TODO: Store song metadata for future use.  You may also want to build
        # the song list once and send to any clients that need it.


        songlist.append(filename)

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

        
        t = Thread(target=client_read, args=(client))
        threads.append(t)
        t.start()

        t = Thread(target=client_write, args=(client))
        threads.append(t)
        t.start()
    s.close()

if __name__ == "__main__":
    main()
