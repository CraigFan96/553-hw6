#!/usr/bin/env python

import os
import socket
import struct
import sys
import cPickle as pickle
from threading import Lock, Thread
import pdb, traceback
import time


QUEUE_LENGTH = 10
SEND_BUFFER = 4096
TIMEOUT = 0.01

songlist = {}

# per-client struct
class Client:
    def __init__(self):
        self.lock = Lock()
        self.conn = None
        self.addr = None

        self.status = "wait"        # wait, list, play, stop
        self.song_id = -1           # Fill with song ID >= 0
        self.last_received = False
        self.send_seq = -1
        self.rec_seq = -1
        self.wait_for_ack = False

    def create_new_socket(self, conn, addr):
        self.conn = conn
        self.addr = addr


# TODO: Thread that sends music and lists to the client.  All send() calls
# should be contained in this function.  Control signals from client_read could
# be passed to this thread through the associated Client object.  Make sure you
# use locks or similar synchronization tools to ensure that the two threads play
# nice with one another!
def client_write(client, lock):
    
    while True:

        if client.status == "list":
            
            packet = {}
            packet["type"] = "server_list"
            
            # Create string of songlist
            songlist_string = pickle.dumps(songlist)

            # Send list of infinite size
            for i in xrange(0,len(songlist_string),SEND_BUFFER):
                
                start_i = i
                end_i = i+len(songlist_string[i:i+SEND_BUFFER])
                packet["msg"] = songlist_string[start_i:end_i]
                packet["len"] = len(packet["msg"])
                if end_i == len(songlist_string):
                    packet["last"] = True
                else:
                    packet["last"] = False

                client.conn.sendall(pickle.dumps(packet))

            # Tell client to wait for next command
            lock.acquire()
            client.status = "wait"
            lock.release()

        if client.status == "play":

            packet = {}
            packet["type"] = "server_song"
            starting_to_play_id = client.song_id

            # Create string of songlist
            f = open(sys.argv[2] + "/" + songlist[client.song_id])
            song_string = f.read()
            f.close()

            # Send song of infinite size
            for i in xrange(0,len(song_string),SEND_BUFFER):

                # Check if we get the STOP command or want to play a new song
                if (client.status == "stop") or (client.song_id != starting_to_play_id):
                   
                    packet = {}
                    packet["type"] = "server_stop"
                    packet["last"] = True
                    client.conn.sendall(pickle.dumps(packet))

                    # Tell client to wait for next command
                    lock.acquire()
                    client.status = "wait"
                    lock.release()

                    # Case of new song
                    if client.song_id != starting_to_play_id:
                        client.status = "play"
                        client.send_seq = 0
                        client.rec_seq = -1

                    break;

                start_i = i
                end_i = i+len(song_string[i:i+SEND_BUFFER])

                packet["msg"] = song_string[start_i:end_i]
                packet["len"] = len(packet["msg"])
                packet["seq"] = client.send_seq

                if end_i == len(song_string):
                    packet["last"] = True
                else:
                    packet["last"] = False

                client.conn.sendall(pickle.dumps(packet))
                
                lock.acquire()
                client.wait_for_ack = True
                lock.release()

                time_start = time.time()
                time_end = time.time()
                while (client.wait_for_ack and ((time_end-time_start) < TIMEOUT)):
                    time_end=time.time()

                # If the timeout occured
                if (time_end - time_start) >= TIMEOUT:
                    continue;

                # Else we received an ACK
                if client.rec_seq == client.send_seq+1:
                    lock.acquire()
                    client.send_seq = client.rec_seq
                    lock.release()
                else:
                    continue


# TODO: Thread that receives commands from the client.  All recv() calls should
# be contained in this function.
def client_read(client, lock):
    
    while True:

        # Load data and create packet type
        data = client.conn.recv(SEND_BUFFER)
        packet = pickle.loads(data)

        if packet["type"] == "client_shutdown":
            break

        if packet["type"] == "client_request":

            request = int(packet["msg"][0]) 

            # Lock client
            lock.acquire()
            
            # Determine request type and fill song_id arg if necessary
            if request == 0:
                client.status = "list"
                client.seq = 0
            elif request == 1:
                client.status = "play"
                if int(packet["msg"][1:]) != client.song_id:
                    client.song_id = int(packet["msg"][1:])
                    client.send_seq = 0
                    client.rec_seq = -1
            elif request == 2:
                client.status = "stop"
            else:
                print("Invalid client_request sent to server!")

            # Release client
            lock.release()

        elif packet["type"] == "client_ack":
            
            # Lock client
            lock.acquire()

            client.wait_for_ack = False
            client.rec_seq = packet["seq"]

            # Release client
            lock.release()

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

        # Define lock on the client
        lock = Lock()
   
        # Create client_read thread
        t = Thread(target=client_read, args=(client, lock))
        threads.append(t)
        t.start()

        # Create client_write thread
        t = Thread(target=client_write, args=(client, lock))
        threads.append(t)
        t.start()

    s.close()

if __name__ == "__main__":
    main()
