# Peer-to-Peer Network

This project is a simple implementation of a peer-to-peer network with a seed node. The seed node maintains a list of active peers and provides this list to any peer that requests it. The peers can then communicate directly with each other.

## Files

- `peer.py`: This file contains the `Peer` class which is responsible for handling the peer nodes in the network. It includes methods for connecting to seeds and peers, handling messages, and performing liveness tests.

- `seed.py`: This file contains the `Seed` class which is responsible for handling the seed node in the network. It includes methods for listening to incoming connections and handling peers.

- `config.txt`: This file contains the IP addresses and ports of the seed nodes in the network.

- `outfile.txt`: This file is used for logging.

## Usage

To start a seed node, run the `seed.py` file and enter the port to connect to when prompted:

```sh
python seed.py
```
To start a peer node, run the `peer.py` file and enter the port to connect to when prompted:

```sh
python peer.py
```
## Features

- **Seed Node**: The seed node maintains a list of active peers and provides this list to any peer that requests it.

- **Peer Node**: The peer nodes can connect to the seed node to get a list of active peers. They can then communicate directly with these peers.

- **Liveness Test**: The peer nodes periodically send liveness requests to check if the other nodes are still active.

- **Message Generation and Handling**: The peer nodes can generate and send messages to other peers. They can also handle incoming messages.

Please note that this is a simple implementation and may not include all the features of a full-fledged peer-to-peer network.