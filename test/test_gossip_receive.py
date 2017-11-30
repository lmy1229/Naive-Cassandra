import signal
import sys 
import logging
import logging.config
import os
from argparse import ArgumentParser
import time
import multiprocessing

from gossip.conn.node import Node
from gossip.util.message_codes import MESSAGE_CODE_GOSSIP

DEFAULT_CONFIG_PATH = 'config/config.ini'

logging.config.fileConfig('config/logging_config.ini')

def signal_handler(signal, frame):
    logging.error('Stopping process - Pid: %s' % os.getpid())
    sys.exit(0)

def receive(manager):
    while True:
        msg = manager.get_msg()
        if msg:
            print('APP: get msg %s' % msg['message'].data)
        time.sleep(0.5)

def main():
    cli_parser = ArgumentParser()
    cli_parser.add_argument('-c', '--config', help='Configuration file path', default=DEFAULT_CONFIG_PATH)
    cli_args = cli_parser.parse_args()
    config_path = cli_args.config

    logging.info('Starting main process - Pid: %s' % os.getpid())

    signal.signal(signal.SIGINT, signal_handler)

    node = Node(config_path)

    node.register('test_sender', MESSAGE_CODE_GOSSIP)

    manager = node.get_manager('test_sender')

    p = multiprocessing.Process(target=receive, args = (manager, ))
    p.start()

    node.start()
