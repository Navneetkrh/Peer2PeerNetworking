import socket 
import threading

from datetime import datetime
from time import sleep
import time
import hashlib

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
        self.sockets_to_peers=[]#faaltu
        self.message_list={}
        self.alive_peers={} #faaltu ig
        self.addr_socket_map={}
        self.socket_addr_map={}
        self.peer_timestamps={}
        
    
    def start(self):
        # start initial threads
        threading.Thread(target=self.connect_to_seeds).start()
        threading.Thread(target=self.listen).start()

        


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
            new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

            new_socket.connect((seed[0],seed[1]))
            self.sockets_to_seed.append(new_socket)#saving socket for later use
            self.handle_seed(new_socket)
            # threading.Thread(target=self.handle_seed,args=(new_socket,)).start()
            
                
        # print("new peers: ",new_peers)
        # # take union with available peers list
        # self.available_peers = list(set(self.available_peers) | set(new_peers))
        # print(self.available_peers)
            
        # after getting the pl
        sleep(5)
        print("---------Available peerlist++++++ ",self.available_peers)
        threading.Thread(target=self.connect_to_peers).start() 

    def listen(self):
        self.sock.listen(10)
        print("listening on  ",self.ip,self.port)
        while True:
            peer, addr = self.sock.accept()
            self.sockets_to_peers.append(peer)
            peer_thread = threading.Thread(target=self.handle_peer,args=(peer,))
            peer_thread.start()
            print("peer ",addr," connected")

    def connect_to_peers(self):
        print("starting thread for connect_to_peers")
        print("++++++++Available peerlist++++++ ",self.available_peers)
        for peer in self.available_peers:
        #  if same peer dont connect
            if(peer[0]==self.ip and peer[1]==self.port):
                continue
            # making sockeys for each peer
            new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            new_socket.connect((peer[0],peer[1]))
            print("New Peer connected")
            self.sockets_to_peers.append(new_socket)
              # make thread for each peer
            threading.Thread(target=self.handle_peer,args=(new_socket,)).start()      
    
    
    def handle_seed(self,new_socket):

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
                for i in range(2,len(message)):
                    
                    adr=message[i].split(',')
                    print("adr: ",adr)
                    new_peers = [(adr[i],int(adr[i+1])) for i in range(0,len(adr),2)]
                    self.available_peers = list(set(self.available_peers) | set(new_peers))
                break
    
    def handle_peer(self, new_socket):
        new_socket.send("connected to peer:{0}:{1}".format(self.ip,self.port).encode())
        message="";
        while(message==""):
            data = new_socket.recv(1024)
            print(data)
            message = data.decode().split(':')
            if message[0]=="connected to peer":
                self.addr_socket_map[(message[1],int(message[2]))]=new_socket
                self.socket_addr_map[new_socket]=(message[1],int(message[2]))
                break
            new_socket.send("connected to peer:{0}:{1}".format(self.ip,self.port).encode())
        sleep(1)
        threading.Thread(target=self.handle_messages, args=(new_socket,)).start()
        threading.Thread(target=self.liveness_test, args=(new_socket,)).start()
        threading.Thread(target=self.generate_messages, args=(new_socket,)).start()

    def handle_messages(self, new_socket):
        while True:
            data = new_socket.recv(1024)
            print(data)
            message = data.decode().split(':')
            if message[0]=="connected to peer":
                self.addr_socket_map[(message[1],int(message[2]))]=new_socket
                self.socket_addr_map[new_socket]=(message[1],int(message[2]))
            elif message[0]=="Liveness Request":
                timestamp=datetime.now().timestamp()
                reply="Liveness Reply:{0}:{1}:{2}".format(timestamp,self.ip,self.port)
                new_socket.send(reply.encode())
            elif message[0]=="Liveness Reply":
                # Update timestamp of peer
                print(message)
                self.peer_timestamps[self.socket_addr_map[new_socket]] = time.time()
            elif message[0]=="gossip message":
                # Check if message is in Message List
                message_hash = hashlib.sha256(message[1].encode()).hexdigest()
                if message_hash not in self.message_list:
                    self.message_list[message_hash] = True

                    # Forward message to all peers except the one it was received from
                    for socket in self.socket_addr_map.keys():
                        if socket != new_socket:
                            socket.send(data)


    def liveness_test(self, new_socket):
        while True:
            timestamp = datetime.now().timestamp()
            request = "Liveness Request:{0}:{1}:{2}".format(timestamp, self.ip, self.port)
            new_socket.send(request.encode())
            print("Liveness Request sent to ", self.socket_addr_map[new_socket])

            # Check if peer is dead
            addr = self.socket_addr_map[new_socket]
            if addr in self.peer_timestamps and time.time() - self.peer_timestamps[addr] > 3 * 13:
                dead_node_message = "Dead Node:{0}:{1}:{2}:{3}:{4}".format(addr[0], addr[1], timestamp, self.ip, self.port)
                # Send dead_node_message to all seeds
                for seed_socket in self.sockets_to_seed:
                    seed_socket.send(dead_node_message.encode())


            sleep(13)
    
    def generate_messages(self,new_socket):
        for i in range(10):
            timestamp = datetime.now().timestamp()
            
            message = "gossip message:{0}:{1}:{2}:{3}".format(timestamp, f'message {i}',self.ip, self.port)
            message_hash = hashlib.sha256(message.encode()).hexdigest()
            self.message_list[message_hash] = True

            
            new_socket.send(message.encode())

            sleep(5)


    


if __name__ == '__main__':
    port=int(input('Enter port to connect to: '))
    peer = Peer(port=port)
    peer.start()

    # port=int(input('Enter port to connect to: '))
    # ip=input('Enter ip to connect to: ')
    # peer = Peer(port,ip)
    # peer.listen()
