messageTypeLen = 2
messageTypes = {
  'hello': 1,
  'connection': 2,
  'infoFile': 3,
  'ok': 4,
  'end': 5,
  'file': 6,
  'ack': 7
}

udpPortLen = 4
sequenceNumberLen = 4
chunkSizeLen = 2
fileNameLen = 15
fileSizeLen = 8
maxFilePayloadSize = 1000

def intToBytes(number, numberOfBytes):
  return number.to_bytes(numberOfBytes, byteorder="little")

def bytesToInt(byte):
  return int.from_bytes(byte, "little")