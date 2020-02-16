# synarere -- a highly modular and stable IRC bot.
# Copyright (C) 2010 Michael Rodriguez.
# Rights to this code are documented in docs/LICENSE.

'''Initialization code.'''

__all__ = ['command', 'confparse', 'event', 'io', 'irc', 'logger', 'module', 'timer', 'var']

def shutdown(code=0, reason="No reason specified."):
    '''Exit gracefully.'''

    pid_file = None

    # Import required Python functions.
    from sys import exit
    from os import remove

    # Import required source modules.
    import logger, var, irc, module

    logger.info('shutdown(): exiting with code %d: %s' % (code, reason))
    irc.quit_all('shutdown(): exiting with code %d: %s' % (code, reason))
    module.unload_all()

    # Remove the PID file.
    try:
        pid_file = open(var.conf.get('options', 'pidfile')[0], 'r')
        remove(pid_file)
    except IOError:
        pass

    exit(code)
