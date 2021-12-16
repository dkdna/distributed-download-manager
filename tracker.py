import socket
import argparse
import logging
from packets import TrackerProtocol
from utils import *

class Tracker:
    def __init__(self, tracker_port):
        self.tracker_port = int(tracker_port)
        self.peer_servers = []

    def run(self):
        self.listener()
    
    def listener(self):
        self.tracker_proto = TrackerProtocol()

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', self.tracker_port))
        sock.listen(1)

        while True:
            io, addr = sock.accept()
            logging.info(f"Received connection from {addr}")

            data = io.recv(1024)
            out = self.tracker_proto.validate_handshake(data)

            if not out:
                logging.error("Invalid handshake!")
                exit(1)
            
            if out == "client":
                self.client_handler(io)
            
            else:
                self.server_handler(io, addr)
            
            io.shutdown(socket.SHUT_RDWR)
            io.close()
    
    def client_handler(self, sock):
        # Send handshake
        handshake = self.tracker_proto.gen_handshake()
        sock.send(handshake.encode())
        
        # Validate peer request
        data = sock.recv(1024)
        out = self.tracker_proto.validate_peer_req(data)

        if not out:
            logging.error("Invalid request!")
            exit(1)
        
        # Send available peers
        servers = self.tracker_proto.gen_peers(self.peer_servers)
        sock.send(servers.encode())
    
    def server_handler(self, sock, addr):
        # Send handshake
        handshake = self.tracker_proto.gen_handshake()
        sock.send(handshake.encode())

        data = sock.recv(1024)
        out = self.tracker_proto.handle_server_req(data)

        if not out:
            logging.error("Invalid request!")
            exit(1)
        
        if out == "add":
            if addr[0] not in self.peer_servers:
                # Add peer server
                self.peer_servers.append(addr[0])
                logging.info(f"Added peer server {addr[0]}")
        
        else:
            try:
                # Remove peer server
                self.peer_servers.remove(addr[0])
            except:
                pass


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "Tracker Server")
    parser.add_argument("-c", "--config", help = "Path to config file", required = False, default = ".config")
    parser.add_argument("-d", "--debug", help = "Debug Mode", required = False, default = False)

    args = parser.parse_args()

    logging.basicConfig(format='[*] %(message)s', level = logging.INFO if args.debug else logging.ERROR)

    configuration = dict()

    try:
        with open(args.config, "r") as f:
            for line in f.readlines():

                if line.split(" ")[0] == "TRACKER_PORT":
                    configuration['tracker_port'] = line.split(" ")[-1].strip("\n")

    except:
        logging.error("Invalid config file!")
        exit(1)

    try:
        t = Tracker(
            tracker_port = configuration['tracker_port']
        )
        t.run()

    except Exception as e:
        logging.error(e)