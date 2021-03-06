import socketio
import base64


class SockClient():
    _got_message_target = None

    LOG_NAME = 'teamwatch-messenger'

    DEBUG = 2 # 0 = HIGH, 1 = MEDIUM, 2 = LOW lasciare a uno! (solo _log <= DEBUG vengono visualizzati)

    SERVER_NAME = '51.15.43.20' # teamwatch.it
    SERVER_URL = 'http://{}:3000'.format(SERVER_NAME)

    SocketIO = None

    def __init__(self, email, password, **kwargs):

        self.login_email = email
        self.login_password = password
        self.feed_channel = kwargs.get('feed_channel', ['teamwatch'])
        self.reconnect_on_disconnect = kwargs.get('reconnect_on_disconnect', True)
        self.reconnect_on_error = kwargs.get('reconnect_on_error', True)
        self.current_reconnection_times = kwargs.get('current_reconnection_times', 0)

        self.SocketIO = socketio.Client({
            'reconnection': self.reconnect_on_disconnect,
            'reconnection_attempts': self.current_reconnection_times,
            'reconnection_delay': 1,
            'reconnection_delay_max': 5,
            'randomization_factor': 0.5
        })

        self.SocketIO.on('connect', self._on_connect)
        self.SocketIO.on('disconnect', self._on_disconnect)
        # self.SocketIO.on('message', self._got_message)
        self.SocketIO.on('new_message', self._got_message)



    def _log(self, text, debug_level=2):
        # if self.DEBUG >= debug_level:
        try:
            # import xbmc
            print ('{} [{}] {}'.format(self.LOG_NAME, self.DEBUG, text))
        except:
            print '{}: exception in _log {}'.format(self.LOG_NAME, sys.exc_info() )




    def _convertToBase64(self, text):
        return base64.b64encode( text )


    def connect(self):
        self._log('try to connect to {}'.format(self.SERVER_NAME), 1)

        headers = {
            'Authorization': self._convertToBase64('{}:{}'.format(self.login_email, self.login_password))
        }

        url = self.SERVER_URL
        # in alpha version just use the teamwatch feed
        url = url + '?feed={}'.format(self.feed_channel[0])

        self.SocketIO.connect( url, headers=headers )

    def disconnect(self):
        self._log('try to disconnect to {}'.format(self.SERVER_NAME), 1)
        self.SocketIO.disconnect()

    def wait_before_exit(self):
        self.SocketIO.wait()


    def _on_connect(self):
        self._log('socket connected: sid {}'.format(self.SocketIO.sid), 1)

    def _on_disconnect(self):
        self._log('socket diconnected', 1)

    def _got_message(self, data):
        # parse message
        if self._got_message_target == None:
            self._log( 'Got message: {}'.format(data), 0 )
            return

        self._got_message_target(data)

    def sendMessage(feed, message):
        self.SocketIO.emit('try_send_message', {'feed': feed, 'message': message})

class on_new_message(SockClient):
    def __init__(self, func):
        parent = self.__class__.__bases__[0]
        parent._got_message_target = func

