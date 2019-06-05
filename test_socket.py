import time
from lib.messenger import SockClient, on_new_message

client = SockClient('user1@test.com', 'password')

@on_new_message
def new_message(client, data):
    print 'new message: {}'.format(data)
    if data['message'] == 'quit':
        client.disconnect()

if __name__ == '__main__':
    client.connect()
    # client.wait_before_exit()
    # time.sleep(3)
    # client.disconnect()
