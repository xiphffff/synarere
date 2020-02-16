# synarere -- a highly modular and stable IRC bot.
# Copyright (C) 2010 Michael Rodriguez.
# Rights to this code are documented in docs/LICENSE.

# You're going to want to have this one threaded.

from core import command, shutdown
import pprint

def list_end(conn, origin, parv):
    global channels
    pprint.pprint(channels)
    del channels
    
def list_chan(conn, origin, parv):
    global channels
    groups = re.match(r'^(.+) (\d+) :(.*)', parv[1]).groups()
    channels.append(groups)

def cmd_list(conn, (nick, user, host), target, message):
    global channels
    channels = []
    command.add('323', list_end, command.irc)
    command.add('322', list_chan, command.irc)
    conn.push('LIST')

def module_init():
    command.add('.list', cmd_list, command.chan)

def module_fini():
    command.delete('.list', cmd_list, command.chan)
