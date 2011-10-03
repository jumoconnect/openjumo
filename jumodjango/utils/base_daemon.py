'''
Created on Apr 13, 2011

@author: al
'''

from datetime import datetime

import sys
import os
import logging
import signal
import time
from contextlib import contextmanager
from optparse import OptionParser
from logging import StreamHandler
from logging.handlers import RotatingFileHandler

def get_logger(name, settings, console=False, log_file_name=None):
    """
    Defaults to set up logging to a file.
    If console==True also add a StreamHandler to log to console
    """
    if log_file_name is None:
        log_file_name = settings.LOG_DIR + name + '.log'
    os.path.isdir(settings.LOG_DIR) or os.makedirs(settings.LOG_DIR)

    log = logging.getLogger(name)
    log.setLevel(settings.LOG_LEVEL)
    handler = RotatingFileHandler(log_file_name)
    formatter = logging.Formatter(settings.LOG_FORMAT)
    handler.setFormatter(formatter)
    log.addHandler(handler)

    if console:
        foreground_handler = StreamHandler(sys.stdout)
        log.addHandler(foreground_handler)

    return log

class DaemonAlreadyRunningException(Exception):
    pass

class DaemonInterruptException(Exception):
    pass

@contextmanager
def pid_lock(lock_file_path):
    """ Usage:
    with pid_lock(some_file):
        # Do stuff
    """
    lock_dir = os.path.dirname(lock_file_path)
    if not os.path.exists(lock_dir):
        os.makedirs(lock_dir)

    has_lock = False
    try:
        if os.path.isfile(lock_file_path):
            lockfile = open(lock_file_path)
            pid = int(lockfile.readline())
            if pid == os.getpid():
                has_lock = True
            else:
                raise DaemonAlreadyRunningException('Daemon is already running with process id %d' % pid)
        else:
            with open(lock_file_path, 'w') as lock_file:
                pid = os.getpid()
                lock_file.write(str(pid)+'\n')
            has_lock = True
        yield pid
    finally:
        if has_lock:
            os.remove(lock_file_path)

class JumoDaemon(object):
    # Override this in subclass!
    process_name='jumo_daemon'
    sleep_interval=60
    max_sleep_interval = 60

    def __init__(self, settings, log_to_console=None, log_level='debug', sleep_interval=None):
        self.startup_time = datetime.now()
        # Allows for debugging when you want to run with a sleep of 1, etc.
        if sleep_interval is not None:
            self.sleep_interval = int(sleep_interval)
        else:
            self.sleep_interval = self.__class__.sleep_interval
        self.logger = get_logger(self.process_name, settings, console=log_to_console)
        self.logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        self.logger.info('%s started' % self.process_name)

    @classmethod
    def get_options_parser(cls):
        parser = OptionParser('usage: %prog [options]')
        parser.add_option('-l', '--log-level', dest='log_level', action='store', choices=('DEBUG','INFO','WARN','CRITICAL','ERROR'), help='log level [DEBUG,INFO,WARN,CRITICAL,ERROR]')
        parser.add_option('-v', '--verbose', dest='log_to_console', action='store_true', help='redirect log output to console')
        parser.add_option('-t', '--time_to_sleep', dest='sleep_interval', action='store', help='sleep interval in seconds')
        return parser

    def reset_sleep(self):
        self.sleep_interval = self.__class__.sleep_interval

    def increase_sleep(self):
        if self.sleep_interval <= self.max_sleep_interval:
            self.sleep_interval += 1

    def die(self):
        raise DaemonInterruptException()

    def run(self):
        signal.signal(signal.SIGINT, lambda sig,frm: self.die())
        signal.signal(signal.SIGTERM, lambda sig,frm: self.die())

        try:
            self.run_loop()
        except DaemonInterruptException:
            self.logger.warn('%s killed by outside process' % self.process_name)


    def run_loop(self):
        while True:
            sleep_interval = self.run_iteration()
            if sleep_interval:
                self.logger.info('Sleeping for %d seconds' % sleep_interval)
                time.sleep(sleep_interval)

    # Override this!!!!
    def run_iteration(self):
        sleep_interval = 1
        self.logger.warn("You didn't override run_iteraion!!!!")
        return sleep_interval

    @classmethod
    def start(cls, settings):
        parser = cls.get_options_parser()
        (options, args) = parser.parse_args()
        with pid_lock(os.path.join('/var/lock/jumo', cls.process_name + '.lock')):
            cls(settings, options.log_to_console, options.log_level, options.sleep_interval).run()
