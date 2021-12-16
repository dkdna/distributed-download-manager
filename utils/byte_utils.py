import struct

def b2s(a):
    return "".join(list(map(chr, a)))

def int2byte(a):
    return struct.pack('>B', a)

def short2byte(a):
    return struct.pack('>H', a)

def byte2int(a):
    return struct.unpack('>B', a)[0]

def bytes2short(a):
    return struct.unpack('>H', a)[0]
