import common
import os
import socket
from select import select
import sys
import time

def sendFile(chunks, udpSock, tcpSock, serverAddress, udpPort):
  print("[sendFile]")
  confirmedChunks = []
  sentChunks = []

  packetChunks = [chunks[i:i+10] for i in range(0, len(chunks), 10)]

  for packet in packetChunks:
    print("inside packet chunks")
    for chunk in packet:
      print("inside inner loop")
      msg = chunk['header'] + chunk['sequenceBytes'] + chunk['size'] + chunk['chunk']
      udpSock.sendto(msg, (serverAddress, udpPort))
      sentChunks.append(chunk['sequence'])

  # t_end = time.time() + 10
  # while time.time() < t_end:
  #   readSocks, _, _ = select([tcpSock], [], [])
  #   for sock in readSocks:
  #     header = common.bytesToInt(sock.recv(common.messageTypeLen))
  #     if header == common.messageTypes['ack']:
  #       sequence = common.bytesToInt(sock.recv(common.sequenceNumberLen))
  #       confirmedChunks.append(sequence)
  #       print(f"Received confirmation for packet: {sequence}")
  #     elif header == common.messageTypes['end']:
  #       return []

  return []
  # return [chunk for chunk in sentChunks if chunk not in confirmedChunks]
def run(serverAddress, serverPort, fileName):
  uploadFile = {
    'fileName': fileName
  }
  f = open(uploadFile['fileName'], "rb")

  uploadFile['size'] = os.stat(uploadFile['fileName']).st_size
  print(f"File size: {uploadFile['size']}")
  uploadFile['numberChunks'] = uploadFile['size']//common.maxFilePayloadSize if not uploadFile['size']%common.maxFilePayloadSize else (uploadFile['size']//common.maxFilePayloadSize) + 1
  print(f"Number of chunks: {uploadFile['numberChunks']}")
  uploadFile['chunks'] = []
  uploadFile['confirmedChunks'] = []

  tcpSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  udpSock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  tcpSock.connect((serverAddress, serverPort))

  tcpSock.send(common.intToBytes(common.messageTypes['hello'], common.messageTypeLen))

  msgType = common.bytesToInt(tcpSock.recv(common.messageTypeLen))

  if msgType != common.messageTypes['connection']:
    print('Error comunicating with the server')
    tcpSock.close()
    udpSock.close()


  udpPort = tcpSock.recv(common.udpPortLen)
  udpPort = common.bytesToInt(udpPort)
  print(f"udpPort: {udpPort}")

  fileInfoMsgHeader = common.intToBytes(common.messageTypes['infoFile'], common.messageTypeLen)
  fileInfoMsgFileName = f"{uploadFile['fileName']:>{common.fileNameLen}}"

  fileSize = common.intToBytes(uploadFile['size'], common.fileSizeLen)

  tcpSock.send(fileInfoMsgHeader + bytes(fileInfoMsgFileName, 'ascii') + fileSize)

  message = common.bytesToInt(tcpSock.recv(common.messageTypeLen))
  if message != common.messageTypes['ok']:
    print('Error comunicating with the server')
    tcpSock.close()
    udpSock.close()

  for i in range(0, uploadFile['numberChunks']):
    chunk = f.read(1000)

    uploadFile['chunks'].append({
      'header': common.intToBytes(common.messageTypes['file'], common.messageTypeLen),
      'sequence': i,
      'sequenceBytes': common.intToBytes(i, common.sequenceNumberLen),
      'size': common.intToBytes(len(chunk), common.chunkSizeLen),
      'chunk': chunk 
    })

  chunksToSend = uploadFile['chunks']
  while chunksToSend != []:
    print("[sendFile]")
    confirmedChunks = []
    sentChunks = []

    packetChunks = [chunksToSend[i:i+10] for i in range(0, len(chunksToSend), 10)]

    for packet in packetChunks:
      for chunk in packet:
        msg = chunk['header'] + chunk['sequenceBytes'] + chunk['size'] + chunk['chunk']
        udpSock.sendto(msg, (serverAddress, udpPort))
        sentChunks.append(chunk['sequence'])

      t_end = time.time() + 10
      while time.time() < t_end:
        readSocks, _, _ = select([tcpSock], [], [], t_end - time.time())
        for sock in readSocks:
          header = common.bytesToInt(sock.recv(common.messageTypeLen))
          if header == common.messageTypes['ack']:
            sequence = common.bytesToInt(sock.recv(common.sequenceNumberLen))
            confirmedChunks.append(sequence)
            print(f"Received confirmation for packet: {sequence}")
          elif header == common.messageTypes['end']:
            return []

    chunksToSend = [chunk for chunk in sentChunks if chunk not in confirmedChunks]
    print(chunksToSend)

  tcpSock.close()
  udpSock.close()
  f.close()
if __name__ == '__main__':
  run(sys.argv[1], sys.argv[2], sys.argv[3])