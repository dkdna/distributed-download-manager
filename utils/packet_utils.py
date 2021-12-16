from utils.byte_utils import *

class ClientProtocol:
    def gen_handshake(self):
        data = ""
        data += "\x00" # Client ID
        data += "\x00" # Type (Handshake)
        return data
    
    def gen_fetcher(self):
        data = ""
        data += "\x00" # Client ID
        data += "\x01" # Type (Fetch Servers)
        return data
    
    def validate_handshake(self, data):
        try:
            id = data[0]
            type = data[1]

            if (
                id == 2 and \
                type == 0
            ):
                return True

            return False

        except:
            return False
    
    def parse_ips(self, data):
        ips = []
        ip_count = data[0]
        idx = 0
        i = 1
        while idx < ip_count:
            ip_len = data[i]
            i += 1
            ip = data[i:(i+ip_len)]
            i += ip_len
            ips.append(b2s(ip))
            idx += 1
        return ips
    
    def gen_download_range(self, url, range):
        data = ""
        data += "\x00" # Client ID
        data += "\x02" # Type (Range)
        data += b2s(int2byte((len(url))))
        data += str(url)
        data += b2s(int2byte((len(str(range[0])))))
        data += str(range[0])
        data += b2s(int2byte((len(str(range[1])))))
        data += str(range[1])
        return data
    
    def get_downloaded_data(self, data):
        try:
            id = data[0]
            type = data[1]
            out = data[2:]

            if (
                id == 1 and \
                type == 3
            ):
                return out

            return False

        except:
            return False
    
class ServerProtocol:
    def gen_handshake(self):
        data = ""
        data += "\x01" # Server ID
        data += "\x00" # Type (Handshake)
        return data
    
    def add_peer(self):
        data = ""
        data += "\x01" # Server ID
        data += "\x01" # Type (Add peer)
        return data
    
    def remove_peer(self):
        data = ""
        data += "\x01" # Server ID
        data += "\x02" # Type (Remove peer)
        return data
    
    def validate_handshake(self, data):
        try:
            id = data[0]
            type = data[1]

            if (
                id == 2 and \
                type == 0
            ):
                return True

            return False

        except:
            return False
    
    def get_ranges(self, data):
        try:
            id = data[0]
            type = data[1]
            idx = 2
            url_len = data[idx]
            idx += 1
            url = data[idx:(idx+url_len)]
            idx += url_len

            len1 = data[idx]
            idx += 1
            range1 = int(data[idx:(idx+len1)])
            idx += len1

            len2 = data[idx]
            idx += 1
            range2 = int(data[idx:(idx+len2)])
            range = (range1, range2)

            if (
                id == 0 and \
                type == 2
            ):
                return [url, range]

            return False

        except:
            return False
    
    def gen_data_packet(self, content):
        data = b""
        data += b"\x01" # Server ID
        data += b"\x03" # Type (Download)
        data += content
        return data

class TrackerProtocol:
    def gen_handshake(self):
        data = ""
        data += "\x02" # Tracker ID
        data += "\x00" # Type (Handshake)
        return data   
    
    def validate_handshake(self, data):
        try:
            id = data[0]
            type = data[1]

            if (
                (id == 0 or id == 1) and \
                type == 0
            ):
                return "client" if id == 0 else "server"

            return False

        except:
            return False
    
    def validate_peer_req(self, data):
        try:
            id = data[0]
            type = data[1]

            if (
                id == 0 and \
                type == 1
            ):
                return True

            return False

        except:
            return False

    def gen_peers(self, peer_servers):
        data = ""
        data += b2s(int2byte((len(peer_servers))))
        for ip in peer_servers:
            data += b2s(int2byte((len(ip))))
            data += ip
        return data
    
    def handle_server_req(self, data):
        try:
            id = data[0]
            type = data[1]

            if (
                id == 1 and \
                (type == 1 or type == 2)
            ):
                return "add" if type == 1 else "remove"

            return False

        except:
            return False