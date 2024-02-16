import threading
from seed import Seed 
num_seeds = int(input("Enter the number of seeds to spawn: "))
seed_list = []
# clear the config file
open('config.txt', 'w').close()
open('outfile.txt', 'w').close()
for i in range(num_seeds):
    seed_port = 5000 + i  # Assign a unique port for each seed
    seed = Seed(port=seed_port)  
    seed_list.append(seed)
    threading.Thread(target=seed.listen).start()  # Start the seed in a new thread
