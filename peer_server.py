import socket
import argparse
import logging
import requests
from utils.packet_utils import ServerProtocol
from utils.byte_utils import *

class Server:
    def __init__(self, tracker_ip, tracker_port, client_port, server_client_port, server_tracker_port):
        self.tracker_ip = tracker_ip
        self.tracker_port = int(tracker_port)
        self.client_port = int(client_port)
        self.server_client_port = int(server_client_port)
        self.server_tracker_port = int(server_tracker_port)
    
    def run(self):
        # Connect to tracker
        self.connect_to_tracker()

        # Listen for connections from client
        self.listener()
    
    def connect_to_tracker(self):
        self.server_proto = ServerProtocol()

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', self.server_tracker_port))
        sock.connect((self.tracker_ip, self.tracker_port))

        # Send handshake to tracking server
        handshake = self.server_proto.gen_handshake()
        sock.send(handshake.encode())

        # Validate received handshake
        data = sock.recv(1024)
        if not self.server_proto.validate_handshake(data):
            logging.error("Invalid handshake! Exiting!")
            exit(1)
        else:
            logging.info("Validated handshake!")
        
        # Send request to add peer
        add_req = self.server_proto.add_peer()
        sock.send(add_req.encode())

        sock.shutdown(socket.SHUT_RDWR)
        sock.close()
    
    def listener(self):

        # Listen for requests from peer servers
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', self.server_client_port))
        sock.listen(1)

        while True:
            io, client_addr = sock.accept()
            io.settimeout(10000000)
            logging.info(f"Connected to client {client_addr}")

            # Get download range
            data = io.recv(1024)
            out = self.server_proto.get_ranges(data)

            if not out:
                logging.error("Invalid download range!")
                exit(1)

            url = b2s(out[0])
            ranges = out[1]
            
            logging.info(f"Received download URL {url}")
            logging.info(f"Received download range {ranges}")

            # Download with URL and range
            data = self.download(url, ranges)

            # Send data back to peer client
            packet = self.server_proto.gen_data_packet(data)
            for i in range(0, len(packet), 1024):
                if (i + 1024 > len(packet)):
                    io.send(packet[i:len(packet)])
                else:
                    io.send(packet[i:i+1024])

            io.shutdown(socket.SHUT_RDWR)
            io.close()

    
    def download(self, url, ranges):

        # Download with given range
        logging.info("Downloading!")
        r = requests.get(url, headers = {"Range" : f"bytes={ranges[0]}-{ranges[1]}"})

        logging.info("Download complete!")
        return r.content
    
    def kill(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', self.server_tracker_port))
        sock.connect((self.tracker_ip, self.tracker_port))

        # Send handshake to tracking server
        handshake = self.server_proto.gen_handshake()
        sock.send(handshake.encode())

        # Validate received handshake
        data = sock.recv(1024)
        if not self.server_proto.validate(data):
            logging.error("Something went wrong!")
            exit(1)
        
        # Send request to remove peer server
        rm_req = self.server_proto.remove_peer()
        sock.send(rm_req.encode())
        sock.shutdown(socket.SHUT_RDWR)
        sock.close()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "Peer Server")
    parser.add_argument("-c", "--config", help = "Path to config file", required = False, default = ".config")
    parser.add_argument("-d", "--debug", help = "Debug Mode", required = False, default = False)

    args = parser.parse_args()

    logging.basicConfig(format='[*] %(message)s', level = logging.INFO if args.debug else logging.ERROR)

    configuration = dict()

    try:
        with open(args.config, "r") as f:
            for line in f.readlines():

                if line.split(" ")[0] == "TRACKER_IP":
                    configuration['tracker_ip'] = line.split(" ")[-1].strip("\n")

                elif line.split(" ")[0] == "TRACKER_PORT":
                    configuration['tracker_port'] = line.split(" ")[-1].strip("\n")

                elif line.split(" ")[0] == "CLIENT_SERVER_PORT":
                    configuration['client_port'] = line.split(" ")[-1].strip("\n")

                elif line.split(" ")[0] == "SERVER_CLIENT_PORT":
                    configuration['server_client_port'] = line.split(" ")[-1].strip("\n")
                
                elif line.split(" ")[0] == "SERVER_TRACKER_PORT":
                    configuration['server_tracker_port'] = line.split(" ")[-1].strip("\n")
    
    except:
        logging.error("Invalid config file!")
        exit(1)

    # try:
    s = Server(
        tracker_ip = configuration['tracker_ip'], tracker_port = configuration['tracker_port'],
        client_port = configuration['client_port'], server_client_port = configuration['server_client_port'],
        server_tracker_port = configuration['server_tracker_port']
    )
    s.run()

    # except Exception as e:
        # logging.error(e)