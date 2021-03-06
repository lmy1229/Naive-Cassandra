import logging
import logging.config
import multiprocessing
import os
import signal
import sys
import time

from cassandra.conn.node import Node
from cassandra.util.message import GossipMessage
from cassandra.util.message_codes import MESSAGE_CODE_GOSSIP

DEFAULT_CONFIG_PATH = 'config/config.ini'

logging.config.fileConfig('config/logging_config.ini')


# noinspection PyUnusedLocal,PyUnusedLocal,PyShadowingNames
def signal_handler(signal, frame):
    logging.error('Stopping process - Pid: %s' % os.getpid())
    sys.exit(0)


def send_notification(manager):
    time.sleep(1)
    manager.send_notification(GossipMessage(bytes([1, 2, 3])))
    print('App sender: sent Gossip message notification')


def get_notification(manager):
    while True:
        msg = manager.get_msg()
        if msg:
            print('App Receiver: received message notification')
        time.sleep(1)


def main(config_path):
    logging.info('Starting main process - Pid: %s' % os.getpid())

    signal.signal(signal.SIGINT, signal_handler)

    node = Node(config_path)

    node.register('notification_receiver', MESSAGE_CODE_GOSSIP)
    node.register('notification_sender', MESSAGE_CODE_GOSSIP)

    manager1 = node.get_manager('notification_receiver')
    manager2 = node.get_manager('notification_sender')

    p1 = multiprocessing.Process(target=send_notification, args=(manager2,))
    p2 = multiprocessing.Process(target=get_notification, args=(manager1,))
    p1.start()
    p2.start()

    node.start()
