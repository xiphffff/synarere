# synarere -- a highly modular and stable IRC bot.
# Copyright (C) 2010 Michael Rodriguez.
# Rights to this code are documented in docs/LICENSE.

'''Command handlers.'''

# Import required Python function.
from thread import start_new_thread

# Import required core modules.
import logger, event

# This is the IRC command hash table.
# This determines which functions are called
# when certain IRC events happen.
# This is initialised in irc.py.
irc = {}

# This is the IRC channel command hash table.
# This determines which functions are called
# when someone says certain things on IRC.
chan = {}

# This is the IRC channel addressed hash table.
# This determines which functions are called
# when someone addresses us on IRC.
chanme = {}

# This is the private message command hash table.
# This determines which functions are called
# when someone sends a certian PRIVMSG to the bot.
priv = {}

# This is the CTCP command hash table.
# This determines which functions are called
# when someone sends a certain CTCP.
ctcp = {}

def dispatch(on_thread, cmd_type, command, *args):
    '''Dispatch commands.'''

    logger.debug('Dispatching %s of type %s (threaded = %s)' % (command, cmd_type, on_thread))

    try:
        if cmd_type[command]['first']:
            if on_thread:
                start_new_thread(cmd_type[command]['first'], args)
            else:
                cmd_type[command]['first'](*args)

        for func in cmd_type[command]['funcs']:
            if on_thread:
                start_new_thread(func, args)
            else:
                func(*args)

        if cmd_type[command]['last']:
            if on_thread:
                start_new_thread(cmd_type[command]['last'], args)
            else:
                cmd_type[command]['last'](*args)
    except:
        pass

def add(eventname, func, cmd_type):
    '''Add a function to an event's list of functions.'''

    eventname = eventname.upper()

    try:
        test = cmd_type[eventname]
    except KeyError:
        cmd_type[eventname] = { 'first' : None,
                            'funcs' : [],
                            'last'  : None }

    if func in cmd_type[eventname]['funcs']:
        return True

    cmd_type[eventname]['funcs'].append(func)
    return True

    logger.debug('Created new command %s assigned to function %s (low-priority)' % (eventname, func))
    event.dispatch('OnCommandAdd', eventname, func, cmd_type)

def add_first(eventname, func, cmd_type):
    '''Add a function as an event's first function.'''

    eventname = eventname.upper()

    try:
        test = cmd_type[eventname]
    except KeyError:
        cmd_type[eventname] = { 'first' : None,
                            'funcs' : [],
                            'last'  : None }

    if cmd_type[eventname]['first']:
        return False

    cmd_type[eventname]['first'] = func
    return True

    logger.debug('Created new command %s assigned to %s (high-priority)' % (eventname, func))
    event.dispatch('OnCommandAddFirst', eventname, func, cmd_type)

def delete(eventname, func, cmd_type):
    '''Remove a function from an event's list of functions.'''

    eventname = eventname.upper()

    if func not in cmd_type[eventname]['funcs']:
        return False

    cmd_type[eventname]['funcs'].remove(func)
    return True

    logger.debug('Deleted command %s assigned to %s (low-priority)' % (eventname, func))
    event.dispatch('OnCommandDelete', eventname, func, cmd_type)

def delete_first(eventname, func, cmd_type):
    '''Remove a function as an event's first function.'''

    eventname = eventname.upper()

    cmd_type[eventname]['first'] = None
    logger.debug('Deleted command %s assigned to %s (high-priority)' % (eventname, func))
    event.dispatch('OnCommandDeleteFirst', eventname, func, cmd_type)
