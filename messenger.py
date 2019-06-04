import socketio
import base64


class SockClient():

    LOG_NAME = 'teamwatch-messenger'

    DEBUG = 2 # 0 = HIGH, 1 = MEDIUM, 2 = LOW lasciare a uno! (solo _log <= DEBUG vengono visualizzati)

    SERVER_NAME = '51.43.15.20' # teamwatch.it
    SERVER_URL = 'http://{}:3000'.format(self.SERVER_NAME)

    SocketIO = None

    def __init__(self, email, password, **kwargs):

        self.login_email = email
        self.login_password = password
        self.feed_channel = kwargs.get('feed_channel', ['teamwatch'])
        self.reconnect_on_disconnect = kwargs.get('reconnect_on_disconnect', True)
        self.reconnect_on_error = kwargs.get('reconnect_on_error', True)
        self.current_reconnection_times = kwargs.get('current_reconnection_times', 0)

        self.SocketIO = socketio.Client({
            reconnection: self.reconnect_on_disconnect,
            reconnection_attempts: self.current_reconnection_times,
            reconnection_delay: 1,
            reconnection_delay_max: 5,
            randomization_factor: 0.5
        })


    def _log(self, text, debug_level=2):
        if self.DEBUG >= debug_level:
            try:
                xbmc.log ('{} [{}] {}'.format(LOG_NAME, self.DEBUG, text))
            except:
                xbmc.log ('{}: exception in _log {}'.format(LOG_NAME, sys.exc_info() )  )
                
                
                
                


    def _convertToBase64(self, text):
        return base64.b64encode( bytes(text, 'utf-8') )


    def connect(self):
        self._log('try to connect to {}'.format(self.SERVER_NAME), 1)

        headers = {
            'Authorization': self.convertToBase64('{}:{}'.format(self.login_email, self.login_password))
        }

        url = self.SERVER_URL
        # in alpha version just use the teamwatch feed
        url = url + '?feed={}'.format(self.feed_channel[0])

        self.SocketIO.connect( url, headers )


    def wait_before_exit(self):
        self.SocketIO.wait()


    @SocketIO.on('connect')
    def on_connect(self, data):
        self._log('socket connected: sid {}'.format(self.SocketIO.sid), 1)

    @SocketIO.on('disconnect')
    def on_disconnect(self, data):
        self._log('socket diconnected', 1)

        '''
        # DO not handle reconnection: it will be handled by socket-io internally
        if self.current_reconnection_times < self.attempt_reconnection_limit:
            self.current_reconnection_times = self.current_reconnection_times + 1
            self.connect()
        else:
            self._log('reconnection limit reached. Socket won\'t be reconnecting', 1)
        '''

    @SocketIO.on('new_message')
    def got_message(self, data):
        # parse message
        self._log( 'Got message: {}'.format(self, data), 0 )
