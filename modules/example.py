# synarere -- a highly modular and stable IRC bot.
# Copyright (C) 2010 Michael Rodriguez.
# Rights to this code are documented in docs/LICENSE.

'''Example module.'''

# Import required source module.
from core import command, shutdown

def on_topic(conn, origin, parv):
    '''Handle the TOPIC command.'''
    
    who = origin.split('!')[0] # the nick of the person who set the topic
    where = parv[0]            # which channel the topic was set in
    what = ' '.join(parv[1:])  # the new topic of the channel
    
    # the bot will have to be in #spying for this to work..
    conn.privmsg('#spying', '%s set the topic of %s to %r!' % (who, where, what))

def chan_example(conn, (nick, user, host), target, message):
    '''Handle the .example channel command.'''
    
    irc.quit_all()

def chanme_example(conn, (nick, user, host), target, message):
    '''Handle the example channel command where the bot is addressed.'''
    
    irc.quit_all()

def module_init():
    '''Module entry point.'''
    
    # There are several types of commands you may create.
    # The following are available:
    #
    # irc -- Raw IRC commands. AWAY, KICK, etc.
    # chan -- Channel commands, for example: '.register'.
    # chanme -- Same as chan, except the bot's nick is prepended. Example: <user> synarere: register
    # priv -- Private message commands.
    # ctcp -- CTCP commands.
    #
    # NOTE: For irc, these are top priority, so you should use command.add_first() instead of command.add()!
    
    command.add_first('TOPIC', on_topic, command.irc)
    command.add('.quit', chan_example, command.chan)
    command.add('quit', chanme_example, command.chanme)

def module_fini():
    '''Module exit point.'''

    # NOTE: You must destroy all you created, else memory will be used unnecessarily!
    
    command.delete_first('TOPIC', on_topic, command.irc)
    command.delete('.quit', chan_quit, command.chan)
    command.delete('quit', chanme_quit, command.chanme)
