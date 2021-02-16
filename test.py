import cliente
import requests
import os

url = 'https://upload.wikimedia.org/wikipedia/en/thumb/3/3b/SpongeBob_SquarePants_character.svg/800px-SpongeBob_SquarePants_character.svg.png'
# url = 'https://external-content.duckduckgo.com/iu/?u=https%3A%2F%2Fupload.wikimedia.org%2Fwikipedia%2Fen%2Fthumb%2F3%2F3b%2FSpongeBob_SquarePants_character.svg%2F1200px-SpongeBob_SquarePants_character.svg.png&f=1&nofb=1'

response = requests.get(url)

os.system('clear')
print('Got the image')
with open('bob.png', 'wb') as f:
  f.write(response.content)

print('Gonna run')
cliente.run('127.0.0.1', 51511, 'bob.png')