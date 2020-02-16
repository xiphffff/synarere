# synarere -- a highly modular and stable IRC bot.
# Copyright (C) 2010 Michael Rodriguez.
# Rights to this code are documented in docs/LICENSE.

'''Main loop.'''

# Import required Python modules.
import asyncore, time

# Import required core modules.
import timer, var

def io():
    '''Infinite loop to handle routines.'''

    while True:
        # Check for timers.
        delay = timer.next_run()

        if delay <= time.time():
            timer.run()

        # We don't want to poll on no connections because it makes CPU usage skyrocket.
        # Instead, just sleep.
        if len(var.conns) == 0:
            time.sleep(1)
        else:
            asyncore.poll(1)
