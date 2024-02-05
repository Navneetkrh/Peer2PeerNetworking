# seed

import socket 
import threading



class Seed:
    def __init__(self,port=12345,ip='localhost'):
        self.ip=ip
        self.port=port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.ip,self.port))
        self.peerlist = []
        # add seed entry to config file
        self.config_entry()
        
    def config_entry(self):
        # cheack if already present
        with open('config.txt', 'r') as f:
            for line in f:
                seed_address=line.strip().split(':')
                if seed_address[0] == self.ip and seed_address[1] == str(self.port):
                    return
        with open('config.txt', 'a') as f:
            f.write('{0}:{1}\n'.format(self.ip,self.port))
        f.close()

    def listen(self):
        self.sock.listen(10)
        print("listening on  ",self.ip,self.port)
        while True:
            peer, addr = self.sock.accept()
            
            peer_thread = threading.Thread(target=self.handle_peer,args=(peer,addr))
            peer_thread.start()
            print("peer ",addr," connected")

    def close_dead_peer(self,peer,addr):
        if(addr not in self.peerlist):
            peer.close()
            print("peer should be dead with address",addr)
            return

    def handle_peer(self,peer,addr):
        
        # peer.send('peer list :{0}'.format(self.peerlist).encode())
        peer.send('welcome connected to seed with address {0}:{1}'.format(self.ip,self.port).encode())
        while True:
            # self.close_dead_peer(peer,addr)
            data = peer.recv(1024)
            decoded_data = data.decode()
            if(decoded_data == ''):
                continue
            print("received data from ",addr,": ",decoded_data)
            message = decoded_data.split(':')
            print("message is ",message)
            if message[0] == 'peer list':
                print("sending peer list")
                list_of_peers=""
                for i in self.peerlist:
                    list_of_peers = list_of_peers+":" + i[0] + "," + str(i[1]) 
                
                data_to_send = "peer list"+":"+list_of_peers
                peer.send(data_to_send.encode())
                print("peer list sent")

            if message[0] == 'register':
                print("registering peer")
                self.peerlist.append((message[1],int(message[2])))
                peer.send('registered successfully'.encode())
                

                print("peer registered successfully")
                open('outfile.txt','a').write(f'{message[1]}:{message[2]} registered to seed with address {self.ip}:{self.port}\n')


            if message[0] =='dead node':
                address_of_dead_node = (message[1],int(message[2]))
                self.peerlist.remove(address_of_dead_node)
                print("dead node ",address_of_dead_node," removed from peer list")
                open('outfile.txt','a').write(f'dead node {address_of_dead_node} removed from peer list\n')

            
            
                



    
if __name__ == '__main__':
    port=int(input('Enter port to connect to: '))
    seed = Seed(port=port)
    seed.listen()
    
    print(seed.ip)
