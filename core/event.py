# synarere -- a highly modular and stable IRC bot.
# Copyright (C) 2010 Michael Rodriguez.
# Rights to this code are documented in docs/LICENSE.

'''Event system for non-IRC events.'''

# Import required core module.
import logger

# Event data.
events = {}

def dispatch(name, *args):
    '''Dispatch the event.'''

    global events

    # Call every function attached to 'name'.
    try:
        for func in events[name]['funcs']:
            func(*args)
    except KeyError:
        pass

def attach(event, func):
    '''Add a function to an event.'''

    global events

    try:
        test = events[event]
    except KeyError:
        events[event] = { 'funcs' : [] }

    if func in events[event]['funcs']:
        return True

    events[event]['funcs'].append(func)
    return True

    logger.debug('Attached event %s to %s' % (event, func))

def detach(event, func):
    '''Remove a function from an event.'''

    global events

    if func not in events[event]['funcs']:
        return False

    events[event]['funcs'].remove(func)

    logger.debug('Detached event %s from %s' % (event, func))
