import common
import os
import socket
import select
import sys

serverAddress = sys.argv[1]
serverPort = int(sys.argv[2])
uploadFile = {
  'fileName': sys.argv[3]
}
  

f = open(uploadFile['fileName'], "r")

uploadFile['size'] = os.stat(uploadFile['fileName']).st_size
print(uploadFile['size'])
uploadFile['numberChunks'] = uploadFile['size']//common.maxFilePayloadSize if not uploadFile['size']%common.maxFilePayloadSize else (uploadFile['size']//common.maxFilePayloadSize) + 1
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

print(f)
print(f.seek(0))
for i in range(0, uploadFile['numberChunks']):
  chunk = f.read(common.maxFilePayloadSize)

  print(len(chunk))
  # uploadFile['chunks'].append({
  #   'header': common.intToBytes(common.messageTypes['file'], common.messageTypeLen),
  #   'sequence': i + 1,
  #   'sequenceBytes': common.intToBytes(i + 1, common.sequenceNumberLen),
  #   'size': common.intToBytes(len(chunk), common.chunkSizeLen),
  #   'chunk': chunk 
  # })

# for i in range(0, uploadFile['numberChunks']):
#   chunk = uploadFile['chunks'][i]
#   msg = chunk['header'] + chunk['sequenceBytes'] + chunk['size'] + chunk['chunk']
#   print(f"[hUM] chunkNumber: {chunk['sequence']}")
#   print(f"[hUM] Size: {len(chunk['chunk'])}")
#   udpSock.sendto(msg, (serverAddress, udpPort))

#   header = common.bytesToInt(tcpSock.recv(common.messageTypeLen))
#   if header == common.messageTypes['ack']:
#     sequence = common.bytesToInt(tcpSock.recv(common.sequenceNumberLen))
#     print(f"Confirmed sequence number: {sequence}")