import select
import socket
import random
import sys
import os

import common

serverPort = int(sys.argv[1])
serverSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)


serverSock.bind(('0.0.0.0', serverPort))
serverSock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serverSock.listen(255)

tcpSockets = [serverSock]
udpSockets = []
udpPorts = []
clients = []

if not os.path.exists('output'):
  os.makedirs('output')

def getClientByTCPSock(sock):
  for client in clients:
    if client['sock'] == sock:
      return client

def connectNewClient(sock, address):
  clients.append({
    'sock': sock,
    'address': address
  })
  tcpSockets.append(sock)

def addFileToClient(sock, fileName, fileSize):
  client = getClientByTCPSock(sock)
  client["file"] = {
    'name': fileName,
    'size': fileSize,
    'chunks': fileSize//common.maxFilePayloadSize if not fileSize%common.maxFilePayloadSize else (fileSize//common.maxFilePayloadSize) + 1,
    'receivedChunks': [],
    'file': open(f"output/{fileName}", "wb")
  }

def writeFile(client):
  chunks = client['file']['receivedChunks']
  chunks = sorted(chunks, key=lambda k:k['sequence'])
  file = client['file']['file']
  for chunk in chunks:
    file.write(chunk['chunk'])
  
  file.close()

def receivedAllChunks(client):
  return client['file']['chunks'] == len(client['file']['receivedChunks'])

def isNewChunk(chunks, number):
  for chunk in chunks:
    if chunk['sequence'] == number:
      return False
  return True

def createUDPChannel(sock):
  client = getClientByTCPSock(sock)

  udpSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  udpSock.setblocking(False)
  port = None
  
  while True:
    port = random.randint(10000, 19999)
    if port not in udpPorts:
      break;

  udpSock.bind(('', port))
  udpSockets.append(udpSock)
  client['updPort'] = port
  client['udpSock'] = udpSock

  print(f"udpPort: {port}\n")
  return port

def handleUdpMessage(sock):
  print('[handleUdpMessage]')
  message, _ = sock.recvfrom(common.messageTypeLen + common.sequenceNumberLen + common.chunkSizeLen + common.maxFilePayloadSize)
  
  port = sock.getsockname()[1]
  header = common.bytesToInt(message[:common.messageTypeLen])
  chunkNumberBytes = message[common.messageTypeLen:common.messageTypeLen+common.sequenceNumberLen]
  chunkNumber = common.bytesToInt(chunkNumberBytes)
  chunkSize = common.bytesToInt(message[common.messageTypeLen+common.sequenceNumberLen:common.messageTypeLen+common.sequenceNumberLen+common.chunkSizeLen])
  chunk = message[common.messageTypeLen+common.sequenceNumberLen+common.chunkSizeLen:]
  
  if header != common.messageTypes['file']:
    return

  client = None
  for c in clients:
    if c['updPort'] == port:
      client = c
      break

  print(f"Received chunk: {chunkNumber}")
  if(isNewChunk(client['file']['receivedChunks'], chunkNumber)):
    client['file']['receivedChunks'].append({
      'sequence': chunkNumber,
      'chunk': chunk
    })

  header = common.intToBytes(common.messageTypes['ack'], common.messageTypeLen)
  client['sock'].send(header+chunkNumberBytes)

  if receivedAllChunks(client):
    writeFile(client)
    client['sock'].send(common.intToBytes(common.messageTypes['end'], common.messageTypeLen))

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
    if sock == serverSock:
      clientSock, address = serverSock.accept()
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
        client = getClientByTCPSock(sock)
        clients.remove(client)
        continue
