import time
from lib.messenger import SockClient

client = SockClient('user1@test.com', 'password')

@client._got_message
def new_message(data):
    print 'on message event fired!'

if __name__ == '__main__':
    client.connect()
    time.sleep(3)
    client.disconnect()
