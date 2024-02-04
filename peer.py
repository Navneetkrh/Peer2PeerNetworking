import socket 
import threading
import uuid
from datetime import datetime
from time import sleep


class Peer:
    def __init__(self,port:int,ip:str='localhost'):
        self.port=port
        self.ip=ip
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((ip,port))
        
        self.available_peers = []
        self.seeds=[]
        self.find_seeds()
        self.sockets_to_seed=[]
        self.sockets_to_peers=[]
        self.MessageList={}
        self.alive_peers={}

    def find_seeds(self):
        self.seeds = []
        with open('config.txt', 'r') as f:
            for line in f:
                seed_address=line.strip().split(':')
                self.seeds.append((seed_address[0],int(seed_address[1])))
        f.close()
        print(self.seeds)
    def connect_to_seeds(self):
    
        for seed in self.seeds:
            threading.Thread(target=self.handle_seed_as_client,args=(seed,)).start()
            
                
        # print("new peers: ",new_peers)
        # # take union with available peers list
        # self.available_peers = list(set(self.available_peers) | set(new_peers))
        # print(self.available_peers)
            
    def listen(self):
        self.sock.listen(10)
        print("listening on  ",self.ip,self.port)
        while True:
            peer, addr = self.sock.accept()
            self.available_peers.append(peer)
            peer_thread = threading.Thread(target=self.handle_peer_as_server,args=(peer,addr))
            peer_thread.start()
            print("peer ",addr," connected")

    # Liveness Testing
# The liveness messages should be sent every 13 seconds, even after the gossip broadcast has stopped.
# The liveness messages won’t stop until the node goes offline.

    def liveness_sender(self):
        pass

    def liveness_receiver(self,peer):
        pass
    
    def connect_to_peers(self):
        for peer in self.available_peers:
        #  if same peer dont connect
            if(peer[0]==self.ip and peer[1]==self.port):
                continue
            # make thread for each peer
            threading.Thread(target=self.handle_peer2peer,args=(peer,)).start()      
    
    
    def handle_seed_as_client(self,seed):
        new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


        new_socket.connect((seed[0],seed[1]))
        self.sockets_to_seed.append(new_socket)#saving socket for later use

        response = new_socket.recv(1024)
        print(response)
        # register with seed
        message="register:{0}:{1}".format(self.ip,self.port)
        print(message)

        new_socket.send(message.encode())
        print("seeds connected")
        response = new_socket.recv(1024)
        print(response)
        # ask for peer list
        new_peers=[]
        new_socket.send("peer list".encode())
        print("asking for peer list")
        # receive peer list
        while True:
            data = new_socket.recv(1024)
            decoded_data = data.decode()
            message = decoded_data.split(':')
            print("message is ",message)
            if message[0] == 'peer list':
                # recive list of tuples
                adr=message[2].split(',')
                print("adr: ",adr)
                new_peers = [(adr[i],int(adr[i+1])) for i in range(0,len(adr),2)]
                break
    
    
    def handle_peer_as_server(self,peer,addr):
        peer.send('welcome connected to peer with address {0}:{1}'.format(self.ip,self.port).encode())
        while True:
            pass

        
    
    
    def handle_peer_as_client(self,peer):
        new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        new_socket.connect((peer[0],peer[1]))
        self.sockets_to_peers.append(new_socket)
        response = new_socket.recv(1024)
        print(response)
        while True:
            pass
    
    def start(self):
        # start initial threads
        threading.Thread(target=self.listen).start()
        threading.Thread(target=self.connect_to_peers).start()
        threading.Thread(target=self.connect_to_seeds).start()


if __name__ == '__main__':
    port=int(input('Enter port to connect to: '))
    peer = Peer(port=port)
    peer.connect_to_seeds()
    # port=int(input('Enter port to connect to: '))
    # ip=input('Enter ip to connect to: ')
    # peer = Peer(port,ip)
    # peer.listen()
    #