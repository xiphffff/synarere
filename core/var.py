# synarere -- a highly modular and stable IRC bot.
# Copyright (C) 2010 Michael Rodriguez.
# Rights to this code are documented in docs/LICENSE.

'''Global variables.'''

# Configuration file.
config_file = 'conf/synarere.conf'

# Fork into the background? We do so by default.
fork = True

# Configuration parser and logger instance.
conf, log = None, None

# Servers, connections, modules loaded, dead connections, and timers list.
servers, conns, modules_loaded, dead_conns, timers = [], [], [], [], []

# Our version.
version = '1.2'
