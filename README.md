# Distributed Download Manager

A small distributed download manager to help bypass device-specific bandwidth limitations.

## Architecture

The download manager consists of 3 parts:

+ Tracker server: An always-on server, stores a list of available peer servers which can be fetched by the peer client
+ Peer client: Initiates the download, receives a list of available peer servers from the tracker and splits the download among them, and finally merges all the downloaded chunks together
+ Peer server: Informs tracker of its availability, receives chunks to download from peer server, downloads and sends back chunks

## Usage

+ Setup a config file ([Sample config](.config)). The config should contain:
    + `TRACKER_IP <ip>` -> IP address of the tracker (Should always be running)
    + `TRACKER_PORT <port>` -> Port of the tracker
    + `URL <url>` -> URL of file to be downloaded
    + `PATH <path>` -> Path to save output file (on peer client)
    + `CLIENT_SERVER_PORT <port>` -> Port for communication b/w client and server (can be hardcoded)
    + `CLIENT_TRACKER_PORT <port>` -> Port for communication b/w client and tracker (can be hardcoded)
    + `SERVER_CLIENT_PORT <port>` -> Port for communication b/w server and client (can be hardcoded)
    + `SERVER_TRACKER_PORT <port>` -> Port for communication b/w server and tracker (can be hardcoded)

+ Run the tracker, all the peer servers (other machines) and then the peer client:

```
python3 tracker.py
python3 peer_server.py
python3 peer_client.py
```
