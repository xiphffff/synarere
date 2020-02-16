# synarere -- a highly modular and stable IRC bot.
# Copyright (C) 2010 Michael Rodriguez.
# Rights to this code are documented in docs/LICENSE.

'''Logger facility.'''

# Import required Python module.
import logging

# Import required Python function.
from logging import handlers

# Import required core modules.
import var

# Make these references to the real methods.
debug, info, warning, error, critical = None, None, None, None, None

def get_level():
    '''Get the logging level.'''

    if var.conf.get('logger', 'level')[0] == 'info':
        return logging.INFO
    elif var.conf.get('logger', 'level')[0] == 'warning':
        return logging.WARNING
    elif var.conf.get('logger', 'level')[0] == 'debug':
        return logging.DEBUG
    elif var.conf.get('logger', 'level')[0] == 'error':
        return logging.ERROR
    elif var.conf.get('logger', 'level')[0] == 'critical':
        return logging.CRITICAL

    return logging.INFO

def init():
    '''Initialise the logging subsystem.'''

    global debug, info, warning, error, critical

    var.log = logging.getLogger('synarere')

    # Set up logging to stderr if we're in foreground mode.
    if not var.fork:
        stream = logging.StreamHandler()
    else:
        stream = None

    handler = handlers.RotatingFileHandler(filename=var.conf.get('logger', 'path')[0], maxBytes=var.conf.get('logger', 'max_size')[0], backupCount=var.conf.get('logger', 'max_logs')[0])
    formatter = logging.Formatter(var.conf.get('logger', 'format')[0])

    handler.setFormatter(formatter)

    if stream:
        stream_format = logging.Formatter(var.conf.get('logger', 'stream_format')[0])
        stream.setFormatter(stream_format)
        var.log.addHandler(stream)

    var.log.addHandler(handler)
    var.log.setLevel(get_level())

    debug, info, warning = var.log.debug, var.log.info, var.log.warning
    error, critical = var.log.error, var.log.critical
