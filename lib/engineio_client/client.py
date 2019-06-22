from .emitter import Emitter
from .parser import Parser, Packet
from .transports.polling import Polling

import gevent
import gevent.event
import gevent.queue
import json

import logging
logger = logging.getLogger(__name__)

class Client(Emitter):
    TRANSPORTS = {
        'polling': Polling
    }

    def __init__(self, scheme, hostname, port, path='/engine.io', transports=[], parser=None):
        super(Client, self).__init__()
        self.scheme = scheme
        self.hostname = hostname
        self.port = port
        self.path = path
        self.transports = [t for t in self.TRANSPORTS.keys() if t in transports] or self.TRANSPORTS.keys()
        self.parser = parser or Parser()

        self.state = 'closed'
        self.sid = None
        self.ping_interval = None
        self.ping_timeout = None
        self.pong_event = gevent.event.Event()
        self.send_queue = gevent.queue.JoinableQueue()
        self.transport = None
        self.ping_pong_loop = None
        self.flush_loop = None

    def open(self):
        self.state = 'opening'
        transport_name = self.transports[0]
        transport = self.create_transport(transport_name)
        
        transport.open()
        self.set_transport(transport)

    def close(self):
        if self.state not in ['opening', 'open']:
            return

        self.state = 'closing'
        self.send_queue.join()
        self.handle_close()

    def send(self, message, binary=False):
        self.send_packet(Packet(Packet.MESSAGE, message, binary))

    def create_transport(self, name):
        return self.TRANSPORTS[name](self, self.scheme, self.hostname, self.port, self.path, self.parser)

    def set_transport(self, transport):
        if self.transport:
            logger.debug("Clearing existing transport")
            self.transport.removeAllListeners()
    
        self.transport = transport
        self.transport.on('close', self.handle_close)
        self.transport.on('packet', self.handle_packet)
        self.transport.on('error', self.handle_error)

    def send_packet(self, packet):
        if self.state in ['closing', 'closed']:
            logger.warning("Trying to send a packet while state is: %s", self.state)
            return
        self.send_queue.put(packet)

    def loop_flush(self):
        while self.state in ['open', 'closing']:
            logger.debug("Waiting packets")
            self.send_queue.peek()
            logger.debug("Flushing packets")

            packets = []
            try:
                while True:
                    packet = self.send_queue.get_nowait()
                    packets.append(packet)
            except gevent.queue.Empty:
                pass

            self.transport.send(packets)
            for packet in packets:
                self.send_queue.task_done()

    def loop_ping_pong(self):
        while self.state in ['open', 'closing']:
            self.pong_event.clear()
            self.send_packet(Packet(Packet.PING))
            pong_received = self.pong_event.wait(timeout=self.ping_timeout/1000)
            if not pong_received:
                logger.warning("Pong timeout")
                self.handle_close()
                break
            gevent.sleep(self.ping_interval/1000)
    
    def start_loop(self, func, *args, **kwargs):
        def loop_stopped(g):
            logger.debug("Stop %s", func.__name__)
        g = gevent.spawn(func, *args, **kwargs)
        g.rawlink(loop_stopped)
        logger.debug("Start %s", func.__name__)
        return g

    def stop_loop(self, loop):
        if loop:
            loop.kill(block=False)

    def handle_open(self):
        self.state = 'open'
        self.emit('open')

    def handle_close(self):
        if self.state in ['opening', 'open', 'closing']:
            logger.debug("Closing client")
            self.state = 'closed'
            not_closed_by_transport = (self.state == 'closing')
            self.transport.close(send=not_closed_by_transport)
            self.sid = None
            self.stop_loop(self.ping_pong_loop)
            self.stop_loop(self.flush_loop)
            self.emit('close')

    def handle_handshake(self, handshake):
        self.sid = handshake['sid']
        self.ping_interval = handshake['pingInterval']
        self.ping_timeout = handshake['pingTimeout']
        self.handle_open()
        self.ping_pong_loop = self.start_loop(self.loop_ping_pong)
        self.flush_loop = self.start_loop(self.loop_flush)

    def handle_packet(self, packet):
        if self.state not in ['open', 'opening']:
            logger.warning("Packet received while state is: %s", self.state)
            return
    
        if packet.type == Packet.OPEN:
            handshake = json.loads(packet.data)
            self.handle_handshake(handshake)
        elif packet.type == Packet.CLOSE:
            self.transport.close(send=False)
        elif packet.type == Packet.PONG:
            self.pong_event.set()
        elif packet.type == Packet.MESSAGE:
            self.emit('message', packet.data)
        else:
            logger.warning("Invalid message type: %s", packet.type_string)

    def handle_error(self, error):
        logger.warning("Error occured: %s", error)
        self.emit('error', error)
        self.handle_close()

