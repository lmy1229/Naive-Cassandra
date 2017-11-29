import logging
import multiprocessing
import socket

from gossip.util.queue_item_types import *
from gossip.conn.receiver import Receiver
from gossip.util.exceptions import IdentifierNotFoundException

class Sender(multiprocessing.Process):
    """ Sender: send message from a queue or establish a new connection """
    def __init__(self, label, reciever_label, from_queue, to_queue, connection_pool):
        super(Sender, self).__init__()
        self.label = label
        self.reciever_label = reciever_label
        self.from_queue = from_queue
        self.to_queue = to_queue
        self.connection_pool = connection_pool
        self.reciever_counter = 0

    def run(self):
        
        logging.info('%s started - Pid: %ds' % (self.label, self.pid))
        while True:
            item = self.from_queue.get()
            item_type = item['type']
            item_identifier = item['identifier']

            if item_type == QUEUE_ITEM_TYPE_SEND_MESSAGE:
                message = item['message']

                try:
                    connection = self.connection_pool.get_connection(item_identifier)
                except IdentifierNotFoundException:
                    logging.error('%s | connection %s not found' % (self.label, item_identifier))
                    continue

                if connection and message:
                    data = message.encode()
                    try:
                        connection.send(data)
                        logging.debug('%s | sent message (type %d) to client %s - %s' % (self.label, message.code, item_identifier, message.data))
                    except Exception as e:
                        self.connection_pool.remove_connection(item_identifier)
                        logging.error('%s | connection %s lost' % (self.label, item_identifier))

            elif item_type == QUEUE_ITEM_TYPE_NEW_CONNECTION:
                logging.info('%s | establishing new connection to %s' % (self.label, item_identifier))

                socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                addr, port = item_identifier.split(':')
                port = int(port)
                try:
                    socket.connect((addr, port))
                    self.connection_pool.add_connection(item_identifier, socket, server_name=item_identifier)
                except Exception as e:
                    logging.error('%s | Connection error %s' % (self.label, e))
                    continue

                logging.info('%s | adding connection %s to connection pool' % (self.label, item_identifier))

                # create receiver for new connection
                receiver = Receiver(self.reciever_label, socket, addr, port, self.to_queue, self.connection_pool)
                receiver.start()
                self.reciever_counter = self.reciever_counter + 1

            else:
                # unrecognized message type
                logging.error('%s | Unrecognized message type' % self.label)
                raise Exception('Unrecognized message type')
        