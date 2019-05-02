import socket
from pathlib import Path
import matplotlib.pyplot as plt
from threading import Thread, Condition
import os
import ServerHelper as SH

#file extentions for file types
DPX_DATA_FILE_EXTENSION = ".dsi"
SPEC_DATA_FILE_EXTENSION = ".ssi"
IQ_DATA_FILE_EXTENSION = ".isi"

#root path of saved data
DATA_PATH = "C:/Users/thema/OneDrive/Documents/Malcolm's_Things/Fall 2018/temp"

#ip of server, needs update on change of network
SERVER_IP = "10.17.186.55"


class Server():
    """A server is a object that translates user commands, sends them to the client, and saves data"""


    def __init__(self):
        self.s = socket.socket() #initial socket

        #bind socket to IP and port
        port = 12345
        self.s.bind((SERVER_IP,port))

        #listen for client request, save socket
        self.s.listen(5)
        self.sc = [] #client sockts
        self.cur = -1 #current client in communication
        self.listenThreads = [] #threads used to listen for data
        self.threadActive = [] #boolean on if each thread is active
        self.dataModes = [] #the type of data being received by each thread

        #special thread for displaying spectrum
        self.setupThread = None
        self.setupActive = False

    #Connect server to client
    def connect(self):
        self.sc.append(self.s.accept()[0])
        self.cur = len(self.sc)-1
        self.listenThreads.append(Thread(None))
        self.threadActive.append(False)
        self.dataModes.append("spec")
        print("Connected to Client " + str(self.cur))

    #send translated command to client, changes server variables when aplicable, starts listen threads
    def sendCommand(self, command):
        sending = True
        if(command == "setup"):
            with G.scond:
                G.setupActive = True
                G.scond.notify()
            if (self.setupThread == None):
                self.setupThread = Thread(target=self.listen,args=(self.cur, True, ))
                self.setupThread.start()
        elif(command == "exit"):
            G.setupActive = False
            sending = False
        elif(command.split(" ")[0] == "data"):
            self.dataModes[self.cur] = command.split(" ")[1]
        elif(command == "start"):
            self.listenThreads[self.cur] = Thread(target=self.listen,args=(self.cur, False, ))
            self.threadActive[self.cur] = True
            self.listenThreads[self.cur].start()
        elif(command == "stop"):
            self.threadActive[self.cur] = False
            sending = False
        elif(command == "connect"):
            self.connect()
            sending = False
        elif(command.split(" ")[0] == "changersa"):
            self.cur = int(command.split(" ")[1])
            sending = False

        #some commands are not sent
        if (sending):
            tosend = bytes(command,"utf-8") + b'|'
            self.sc[self.cur].send(tosend)

    #***SHOULD ONLY BE CREATED IN SEPERATE THREAD***
    #listens for data from client
    def listen(self, conn_i, setup):
        if(setup): #listening for server frames to display, displaying them
            while(True):
                with G.scond:
                    if(G.setupActive == False):
                        self.sc[conn_i].send(b'stop|')
                        plt.close(1)
                    while(G.setupActive == False):
                        G.scond.wait()
                    self.sc[conn_i].send(b'f_r|')
                    self.sc[conn_i].send(b'c_r|')
                    inc = self.sc[self.cur].recv(1024)
                    dispSpec = open(DATA_PATH + "/display_spectrum" + SPEC_DATA_FILE_EXTENSION, "wb+")
                    while(inc != b"done"):
                        dispSpec.write(inc)
                        self.sc[conn_i].send(b'c_r|')
                        inc = self.sc[conn_i].recv(1024)
                    dispSpec.close()
                    dispSpec = open(DATA_PATH + "/display_spectrum" + SPEC_DATA_FILE_EXTENSION, "rb")
                    spec = SH.readSpec(dispSpec)

                    SH.specGraph(spec.ref_level-100.0,spec.ref_level,spec.center_frequency-spec.span/2.0,
                                   spec.center_frequency+spec.span/2.0,spec.span/(spec.width-1),spec.trace)
        else: #listening for any type of data to store
            datapath = "/data_" + str(conn_i) + "_"
            datanum = 0
            while(os.path.exists(Path(DATA_PATH + datapath + str(datanum))) == True):
                datanum += 1
            datapath = datapath + str(datanum)
            os.mkdir(Path(DATA_PATH + datapath))
            datatype = self.dataModes[conn_i]

            os.path.exists
            i = 0
            while(True):
                if(self.threadActive[conn_i] == False):
                    self.sc[conn_i].send(b'stop')
                    break
                self.sc[conn_i].send(b'f_r|')
                self.sc[conn_i].send(b'c_r|')
                inc = self.sc[self.cur].recv(1024)
                saveData = None
                if( datatype == "spec" ):
                    saveData = open(DATA_PATH+datapath+"/data_" + str(i) + SPEC_DATA_FILE_EXTENSION, "wb+")
                elif( datatype == "dpx" ):
                    saveData = open(DATA_PATH+datapath+"/data_" + str(i) + DPX_DATA_FILE_EXTENSION, "wb+")
                elif( datatype == "iq" ):
                    saveData = open(DATA_PATH+datapath+"/data_" + str(i) + IQ_DATA_FILE_EXTENSION, "wb+")

                while (inc != b"done"):
                    saveData.write(inc)
                    self.sc[conn_i].send(b'c_r|')
                    inc = self.sc[conn_i].recv(1024)
                saveData.close()
                i += 1

    def setCur(self, cur):
        self.cur = cur

#helper class to pause and restart threads
class G:
    setupActive = False
    scond = Condition()

#MAIN

conn = Server() #create server

while True: #wait for commands
    command = input('Enter Command: ')
    parsedCommand = SH.parseCommand(str(command))
    if(parsedCommand[0]):
        conn.sendCommand(parsedCommand[1])
    else:
        print(parsedCommand[1])

