import socket
import argparse
import logging
from pathlib import Path
import requests
from packets import ClientProtocol
from utils import *
import threading

class Client:
    def __init__(self, tracker_ip, tracker_port, path, url, client_server_port, client_tracker_port, server_port):
        self.tracker_ip = tracker_ip
        self.tracker_port = int(tracker_port)
        self.path = Path(path)
        self.url = url
        self.client_server_port = int(client_server_port)
        self.client_tracker_port = int(client_tracker_port)
        self.server_port = int(server_port)

    def run(self):
        # Get peer servers
        self.get_peer_servers()

        # Get download info
        self.get_download_info()

        # Get download ranges
        self.split_download()

        # Download and merge
        self.download()
    
    def get_peer_servers(self):
        client_proto = ClientProtocol()

        # Connect to tracker
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', self.client_server_port))
        sock.connect((self.tracker_ip, self.tracker_port))

        logging.info(f"Connected to tracker at {self.tracker_ip}:{self.tracker_port}")

        # Send handshake to tracking server
        handshake = client_proto.gen_handshake()
        sock.send(handshake.encode())

        data = sock.recv(1024)
        if not client_proto.validate_handshake(data):
            logging.error("Invalid handshake! Exiting!")
            exit(1)
        else:
            logging.info("Validated handshake!")

        # Get peer servers
        fetch_peer_servers = client_proto.gen_fetcher()
        sock.send(fetch_peer_servers.encode())
        self.peer_servers = client_proto.parse_ips(sock.recv(1024))

        if self.peer_servers == []:
            logging.error("No peer servers found! Exiting!")
            exit(1)

        logging.info(f"Peer servers: {self.peer_servers}")

        sock.shutdown(socket.SHUT_RDWR)
        sock.close()

    def get_download_info(self):    
        r = requests.head(self.url)
        headers = r.headers
        self.file_size = int(headers['Content-Length'])

        if headers['Accept-Ranges'] != "bytes":
            logging.error("This URL does not accept ranges!")
            exit(1)
        
        logging.info(f"File size -> {self.file_size} bytes")
    
    def split_download(self):
        logging.info(f"Downloading with peer servers {self.peer_servers}")
        server_count = len(self.peer_servers) + 1

        parts = self.file_size // server_count 

        self.download_ranges = []

        for i in range(server_count - 1):
            self.download_ranges.append((parts * i, parts * (i + 1) - 1))
        
        self.download_ranges.append((parts * (server_count - 1), self.file_size - 1))

        logging.info(f"Download ranges -> {self.download_ranges}")
    
    def download(self):

        threads = []
        results = [None] * len(self.download_ranges)
        # Multithreaded downloader
        for i in range(len(self.download_ranges) - 1):
            thread = threading.Thread(target = self.server_downloader, args=(self.download_ranges[i], results, i))
            threads.append(thread)
            thread.start()

        thread = threading.Thread(target = self.client_downloader, args=(self.download_ranges[-1], results, len(self.download_ranges) - 1))
        threads.append(thread)
        thread.start()

        for i, thread in enumerate(threads):
            thread.join()
        
        self.merge_and_save(results)
    
    def client_downloader(self, range, results, i):
        logging.info(f"Downloading locally for range {range}")

        r = requests.get(self.url, headers = {"Range" : f"bytes={range[0]}-{range[1]}"})
        results[i] = r.content

        logging.info(f"Range {range} done! -> {len(results[i])} bytes")
    
    def server_downloader(self, range, results, i):
        logging.info(f"Downloading for range {range}")

        client_proto = ClientProtocol()
        range_sender = client_proto.gen_download_range(self.url, range)

        # Connect to peer server
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', self.client_server_port))

        sock.settimeout(10000000)

        sock.connect((self.peer_servers[i], self.server_port))

        # Send download range
        sock.send(range_sender.encode())

        data = b""

        while len(data) < (range[1] - range[0] + 2):
            data += sock.recv(1024)
        
        downloaded_data = client_proto.get_downloaded_data(data)

        if not downloaded_data:
            logging.error("Data not received!")
            exit(1)
        
        results[i] = downloaded_data

        logging.info(f"Range {range} done! -> {len(results[i])} bytes")
    
    def merge_and_save(self, results):

        logging.info(f"Received all data, merging!")
        with open(str(self.path), "wb") as f:
            for part in results:
                f.write(part)

        logging.info("Download complete!")

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description = "Peer Client")
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

                elif line.split(" ")[0] == "URL":
                    configuration['url'] = line.split(" ")[-1].strip("\n")

                elif line.split(" ")[0] == "PATH":
                    configuration['path'] = line.split(" ")[-1].strip("\n")

                elif line.split(" ")[0] == "CLIENT_SERVER_PORT":
                    configuration['client_server_port'] = line.split(" ")[-1].strip("\n")

                elif line.split(" ")[0] == "CLIENT_TRACKER_PORT":
                    configuration['client_tracker_port'] = line.split(" ")[-1].strip("\n")

                elif line.split(" ")[0] == "SERVER_CLIENT_PORT":
                    configuration['server_port'] = line.split(" ")[-1].strip("\n")

    except:
        logging.error("Invalid config file!")
        exit(1)

    try:
        c = Client(
            tracker_ip = configuration['tracker_ip'], tracker_port = configuration['tracker_port'], 
            path = configuration['path'], url = configuration['url'],
            client_server_port = configuration['client_server_port'], client_tracker_port = configuration['client_tracker_port'], 
            server_port = configuration['server_port']
        )
        c.run()

    except Exception as e:
        logging.error(e)