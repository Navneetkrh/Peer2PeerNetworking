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
        self.addr_socket_map={}
        self.socket_addr_map={}
    
    def start(self):
        # start initial threads
        threading.Thread(target=self.listen).start()
        threading.Thread(target=self.connect_to_peers).start()
        threading.Thread(target=self.connect_to_seeds).start()


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

            threading.Thread(target=self.handle_seed,args=(new_socket,)).start()
            
                
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
            peer_thread = threading.Thread(target=self.handle_peer,args=(peer,addr))
            peer_thread.start()
            print("peer ",addr," connected")

    def connect_to_peers(self):
        for peer in self.available_peers:
        #  if same peer dont connect
            if(peer[0]==self.ip and peer[1]==self.port):
                continue
            # making sockeys for each peer
            new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            new_socket.connect((peer[0],peer[1]))
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
                adr=message[2].split(',')
                print("adr: ",adr)
                new_peers = [(adr[i],int(adr[i+1])) for i in range(0,len(adr),2)]
                break
    
    

    
    def handle_peer(self,new_socket):
        new_socket.send("connected to peer:{0}:{1}".format(self.ip,self.port).encode())
        
        while True:
            data = new_socket.recv(1024)
            print(data)
            message = data.decode().split(':')
            if message[0]=="connected to peer":
                self.addr_socket_map[(message[1],int(message[2]))]=new_socket
                self.socket_addr_map[new_socket]=(message[1],int(message[2]))
                # Liveness Request:<self.timestamp>:<self.IP >:<self.port>
            elif message[0]=="liveness Request":
                # Liveness Reply:<sender.timestamp >:<sender.IP >:<self.IP >
                timestamp=datetime.now().timestamp()
                reply="Liveness Reply:{0}:{1}:{2}".format(timestamp,self.ip,self.port)
                new_socket.send(reply.encode())
            elif message[0]=="Liveness Reply":
                pass

    


if __name__ == '__main__':
    port=int(input('Enter port to connect to: '))
    peer = Peer(port=port)
    peer.start()

    # port=int(input('Enter port to connect to: '))
    # ip=input('Enter ip to connect to: ')
    # peer = Peer(port,ip)
    # peer.listen()
