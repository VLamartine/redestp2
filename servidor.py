import select
import socket
import random
import sys
import os

import common

serverPort = int(sys.argv[1])
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


s.bind(('0.0.0.0', serverPort))
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.listen(255)

tcpSockets = [s]
udpSockets = []
udpPorts = []
clients = {}

if not os.path.exists('output'):
  os.makedirs('output')

def connectNewClient(sock, address):
  clients[sock] = {
    sock: sock,
    address: address
  }
  tcpSockets.append(sock)

def addFileToClient(sock, fileName, fileSize):
  clients[sock]["file"] = {
    'name': fileName,
    'size': fileSize,
    'chunks': fileSize//common.maxFilePayloadSize if not fileSize%common.maxFilePayloadSize else (fileSize//common.maxFilePayloadSize) + 1,
    'receivedChunks': [],
    'file': open(fileName, "wb")
  }

def writeFile(client):
  print("Writing file...")

def receivedAllChunks(client):
  return client['file']['chunks'] == len(client['file']['receivedChunks'])

def createUDPChannel(sock):
  udpSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  udpSock.setblocking(False)
  port = None
  
  while True:
    port = random.randint(10000, 19999)
    if port not in udpPorts:
      break;

  udpSock.bind(('', port))
  udpSockets.append(udpSock)
  clients[sock]['udpSock'] = udpSock
  print(f"udpPort: {port}\n")
  return port

def handleUdpMessage(sock):
  message, _ = sock.recvfrom(common.messageTypeLen + common.sequenceNumberLen + common.chunkSizeLen + common.maxFilePayloadSize)
  
  header = common.bytesToInt(message[:common.messageTypeLen])
  chunkNumberBytes = message[common.messageTypeLen:common.sequenceNumberLen]
  chunkNumber = common.bytesToInt(chunkNumberBytes)
  chunkSize = common.bytesToInt(message[common.messageTypeLen+common.sequenceNumberLen:common.chunkSizeLen])
  chunk = message[common.messageTypeLen+common.sequenceNumberLen:common.chunkSizeLen:]

  print(f"[hUM] Header: {header}")
  print(f"[hUM] chunkNumber: {chunkNumber}")
  print(f"[hUM] Size: {header}")

  if header != common.messageTypes['file']:
    return

  client = [c for c in clients if c['udpSock'] == sock][0]
  client['file']['receivedChunks'].append({
    'sequence': chunkNumber,
    'chunk': chunk
  })

  if receivedAllChunks(client):
    writeFile(client)
    #sendEnd 
  else:
    header = common.intToBytes(common.messageTypes['ack'], common.messageTypeLen)
    client['sock'].send(header+chunkNumberBytes)

  return True

def handleTcpMessage(sock):
  print("[handleMessage]\n")
  message = sock.recv(common.messageTypeLen)
  
  if not len(message):
    return False

  header = common.bytesToInt(message)
  print(f"Header: {header}\n")
  if header == common.messageTypes['hello']:
    port = createUDPChannel(sock)

    responseHeader = common.intToBytes(common.messageTypes['connection'], common.messageTypeLen)
    sock.send(responseHeader + common.intToBytes(port, common.udpPortLen))

  elif header == common.messageTypes['infoFile']:
    fileName = sock.recv(common.fileNameLen).decode('ascii').strip()
    fileSize = common.bytesToInt(sock.recv(common.fileSizeLen))
    addFileToClient(sock, fileName, fileSize)
    responseHeader = common.intToBytes(common.messageTypes['ok'], common.messageTypeLen)
    sock.send(responseHeader)

  return True

while True:
  readSockets, _, _ = select.select(tcpSockets + udpSockets, [], tcpSockets + udpSockets)

  for sock in readSockets:
    if sock == s:
      clientSock, address = s.accept()
      connectNewClient(clientSock, address)
    else:
      response = None
      if sock in tcpSockets:
        response = handleTcpMessage(sock)
      elif sock in udpSockets:
        response = handleUdpMessage(sock)
      
      if response is False:
        print("Closed connection")
        tcpSockets.remove(sock)
        del clients[sock]
        continue
