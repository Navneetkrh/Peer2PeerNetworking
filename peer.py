import socket 
import threading
import logging
from datetime import datetime
from time import sleep
import time
import hashlib
import random

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
        # Calculate the number of seeds to connect to
        num_seeds_to_connect = (len(self.seeds) // 2) + 1

        # Randomly select seeds
        selected_seeds = random.sample(self.seeds, num_seeds_to_connect)

    
        for seed in selected_seeds:
            try:
                new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

                new_socket.connect((seed[0],seed[1]))
                self.sockets_to_seed.append(new_socket)#saving socket for later use
                self.handle_seed(new_socket)
                # threading.Thread(target=self.handle_seed,args=(new_socket,)).start()
            except Exception as e:
                print("seed not connected")
                print(e)
                continue
                
        # print("new peers: ",new_peers)
        # # take union with available peers list
        # self.available_peers = list(set(self.available_peers) | set(new_peers))
        # print(self.available_peers)
            
        # after getting the pl
        sleep(2)
        print("Available peerlist ",self.available_peers)
        logging.info(f'({self.ip}:{self.port}) received peer list: {self.available_peers} ')
        threading.Thread(target=self.connect_to_peers).start() 

    def listen(self):
        self.sock.listen(10)
        print("listening on  ",self.ip,self.port)
        while True:
            try:
                peer, addr = self.sock.accept()
                self.sockets_to_peers.append(peer)
                peer_thread = threading.Thread(target=self.handle_peer,args=(peer,))
                peer_thread.start()
                print("peer ",addr," connected")
            except Exception as e:
                print("An error occurred while listening/handling a peer: ", e)

    def connect_to_peers(self):
        # print("starting thread for connect_to_peers")
        # print("++++++++Available peerlist++++++ ",self.available_peers)
        # randomly select 4 peers
        peers_to_connect = random.sample(self.available_peers, min(len(self.available_peers),4))
        for peer in peers_to_connect:
            #  if same peer dont connect
            if(peer[0]==self.ip and peer[1]==self.port):
                continue
            try:
                # making sockets for each peer
                new_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                new_socket.connect((peer[0],peer[1]))
                # print("New Peer connected")
                self.sockets_to_peers.append(new_socket)
                # make thread for each peer
                threading.Thread(target=self.handle_peer,args=(new_socket,)).start()
            except Exception as e:
                print(f"An error occurred while connecting to peer {peer}: ", e)
    def handle_seed(self,new_socket):
        try:
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
            # print("asking for peer list")
            # receive peer list
            while True:
                data = new_socket.recv(1024)
                decoded_data = data.decode()
                message = decoded_data.split(':')
                print("message is ",message)
                if message[0] == 'peer list':
                    # receive list of tuples
                    for i in range(2,len(message)):
                        adr=message[i].split(',')
                        print("adr: ",adr)
                        new_peers = [(adr[i],int(adr[i+1])) for i in range(0,len(adr),2)]
                        self.available_peers = list(set(self.available_peers) | set(new_peers))
                    break
        except Exception as e:
            print(f"An error occurred while handling the seed: ", e)
    
    def handle_peer(self, new_socket):

        try:
            # print("SOCKET ADDR MAP: ", self.socket_addr_map)
            # if already connections atmost 4 then dont connect
            if len(self.addr_socket_map) >= 4:
                # send message to peer that already connected to 4 peers
                new_socket.send("PEER BUSY,already,connected to 4 peers".encode())
                # print("I AM BUSY")
                new_socket.close()
                return
            new_socket.send("connected to peer:{0}:{1}".format(self.ip,self.port).encode())
            message="";
            while(message==""):
                data = new_socket.recv(1024)
                # print(data)
                message = data.decode().split(':')
                if message[0]=="connected to peer":
                    self.addr_socket_map[(message[1],int(message[2]))]=new_socket
                    self.socket_addr_map[new_socket]=(message[1],int(message[2]))
                    break
                elif message[0]=="PEER BUSY,already,connected to 4 peers":
                    # print("Peer is busy")
                    print("recieved:PEER BUSY,already,connected to 4 peers")
                    new_socket.close()
                    return
                new_socket.send("connected to peer:{0}:{1}".format(self.ip,self.port).encode())
            sleep(1)
            threading.Thread(target=self.handle_messages, args=(new_socket,)).start()
            threading.Thread(target=self.liveness_test, args=(new_socket,)).start()
            threading.Thread(target=self.generate_messages, args=(new_socket,)).start()
        except Exception as e:
            print(f"An error occurred while handling the peer (handle_peer)")
    def handle_messages(self, new_socket):
        
        while True:
            try:
                data = new_socket.recv(1024)
                # print(data)
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
                    # print(message)
                    self.peer_timestamps[self.socket_addr_map[new_socket]] = time.time()
                elif message[0]=="gossip message":
                    # Check if message is in Message List
                    # print("HERE HAVE THIS+",message)
                    message_hash = hashlib.sha256(message[4].encode()).hexdigest()
                    # print('gossip message recieved',message[4])
                    new_socket.send(f'gm recieved'.encode())
                    if message_hash not in self.message_list:
                        self.message_list[message_hash] = True
                        logging.info(f'gossip message recieved on ({self.ip}:{self.port}) from peer with address {self.socket_addr_map[new_socket]}: {message[4]}')
                        print(f'gossip message recieved from peer with address {self.socket_addr_map[new_socket]}: {message[4]}')
                        # Forward message to all peers except the one it was received from
                        for socket in self.socket_addr_map.keys():
                            if socket != new_socket:
                                socket.send(data)
                elif message[0]=="gm recieved":
                    # print(message)
                    pass
                else:
                    print("Invalid message+",message)
                    continue
            except Exception as e:
                print(f"An error occurred while handling messages: ", e)
                break

    def liveness_test(self, new_socket):
        fail_count = 0
        while True:
            timestamp = datetime.now().timestamp()
            try:
                request = "Liveness Request:{0}:{1}:{2}".format(timestamp, self.ip, self.port)
                new_socket.send(request.encode())
                print("Liveness Request sent to ", self.socket_addr_map[new_socket])
            except Exception as e:
                fail_count += 1
                print(f"An error occurred while sending liveness request {fail_count}",)
               
            # Check if peer is dead
            addr = self.socket_addr_map[new_socket]
            if addr in self.peer_timestamps and time.time() - self.peer_timestamps[addr] > 3 * 13:
                dead_node_message = "Dead Node:{0}:{1}:{2}:{3}:{4}".format(addr[0], addr[1], timestamp, self.ip, self.port)
                print(f"Peer {addr} is dead")
                # Send dead_node_message to all seeds
                for seed_socket in self.sockets_to_seed:
                    seed_socket.send(dead_node_message.encode())
                break
            sleep(13)

    
    def generate_messages(self, new_socket):
        sleep(0.5)
        for i in range(10):
            try:
                timestamp = datetime.now().timestamp()
                generated_message=f'message {i}'
                message = "gossip message:{0}:{1}:{2}:{3}".format(timestamp, self.ip, self.port,generated_message)
                message_hash = hashlib.sha256(generated_message.encode()).hexdigest()
                self.message_list[message_hash] = True
                
                new_socket.send(message.encode())
            except Exception as e:
                print(f"error in sending gossips request")
                break
            sleep(5)

    


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO,filename='outputfile.log',format='%(asctime)s:%(message)s')

    port=int(input('Enter port to connect to: '))
    peer = Peer(port=port)
    peer.start()

    # port=int(input('Enter port to connect to: '))
    # ip=input('Enter ip to connect to: ')
    # peer = Peer(port,ip)
    # peer.listen()
