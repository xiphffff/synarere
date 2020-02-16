# synarere -- a highly modular and stable IRC bot.
# Copyright (C) 2010 Michael Rodriguez.
# Rights to this code are documented in docs/LICENSE.

'''This handles connections to IRC, sending/receiving data, dispatching commands and more.'''

# Import required Python modules.
import asyncore, traceback, os, re, socket, time
from collections import deque
from core import shutdown

# Import required core modules.
import logger, var, timer, command, event, misc

# A regular expression to match and dissect IRC protocol messages.
# This is actually around 60% faster than not using RE.
pattern = r'''
           ^              # beginning of string
           (?:            # non-capturing group
               \:         # if we have a ':' then we have an origin
               ([^\s]+)   # get the origin without the ':'
               \s         # space after the origin
           )?             # close non-capturing group
           (\w+)          # must have a command
           \s             # and a space after it
           (?:            # non-capturing group
               ([^\s\:]+) # a target for the command
               \s         # and a space after it
           )?             # close non-capturing group
           (?:            # non-capturing group
               \:?        # if we have a ':' then we have freeform text
               (.*)       # get the rest as one string without the ':'
           )?             # close non-capturing group
           $              # end of string
           '''

# Note that this doesn't match *every* IRC message,
# just the ones we care about. It also doesn't match
# every IRC message in the way we want. We get what
# we need. The rest is ignored.
#
# Here's a compact version if you need it:
#     ^(?:\:([^\s]+)\s)?(\w+)\s(?:([^\s\:]+)\s)?(?:\:?(.*))?$
pattern = re.compile(pattern, re.VERBOSE)

class Connection(asyncore.dispatcher):
    '''Provide an event based IRC connection.'''

    def __init__(self, server):
        asyncore.dispatcher.__init__(self)

        self.server = server
        self.holdline = None
        self.last_recv = time.time()
        self.pinged = False

        self.sendq = deque()
        self.recvq = deque()

        # Add ourself to the connections list.
        var.conns.append(self)

    def writable(self):
        '''See if we need to send data.'''

        return len(self.sendq) > 0

    def handle_read(self):
        '''Handle data read from the connection.'''

        data = self.recv(8192)
        self.last_recv = time.time()


        if not data:
            # This means the connection was closed.
            # handle_close() takes care of all of this.
            return

        datalines = data.split('\r\n')


        if not datalines[-1]:
            # Get rid of the empty element at the end.
            datalines.pop()

        if self.holdline:
            # Check to see if we got part of a line previously.
            # If we did, prepend it to the first line this time.
            datalines[0] = self.holdline + datalines[0]
            self.holdline = None

        if not data.endswith('\r\n'):
            # Check to make sure we got a full line at the end.
            self.holdline = datalines[-1]
            datalines.pop()

        # Add this jazz to the recvq.
        self.recvq.extend([line for line in datalines])

        # Send it off to the parser.
        self.parse()

    def handle_write(self):
        '''Write the first line in the sendq to the socket.'''

        # Grab the first line from the sendq.
        line = self.sendq[-1] + '\r\n'
        stripped_line = misc.stripunicode(line)

        # Try to send it.
        num_sent = self.send(stripped_line)

        # If it didn't all send we have to work this out.
        if num_sent == len(stripped_line):
            logger.debug('%s: %s <- %s' % (self.server['id'], self.server['address'], self.sendq.pop()))
            event.dispatch('OnSocketWrite', self.server, line)
        else:
            logger.warning('%s: Incomplete write (%d byte%s written instead of %d)' % (self.server['id'], num_sent, 's' if num_sent != 1 else '', len(stripped_line)))
            event.dispatch('OnIncompleteSocketWrite', self.server, num_sent, stripped_line)
            self.sendq[-1] = self.sendq[-1][num_sent:]

    def handle_connect(self):
        '''Log into the IRC server.'''

        logger.info('%s: Connection established.' % (self.server['id']))

        self.server['connected'] = True
        event.dispatch('OnConnect', self.server)

        if self.server['pass']:
            self.sendq.appendleft('PASS %s' % self.server['pass'])

        self.sendq.appendleft('NICK %s' % self.server['nick'])
        self.sendq.appendleft('USER %s 2 3 :%s' % (self.server['ident'], self.server['gecos']))

    def handle_close(self):
        asyncore.dispatcher.close(self)

        logger.info('%s: Connection lost.' % self.server['id'])
        self.server['connected'] = False

        event.dispatch('OnConnectionClose', self.server)

        if self.server['recontime']:
            logger.info('%s: Reconnecting in %d second%s.' % (self.server['id'], self.server['recontime'], 's' if self.server['recontime'] != 1 else ''))
            timer.add('io.reconnect', True, connect, self.server['recontime'], self.server)

            event.dispatch('OnPostReconnect', self.server)
        else:
            # Remove us from the connections list.
            try:
                var.conns.remove(self)
            except ValueError:
                logger.error('%s: Could not find myself in the connectons list (BUG)' % self.server['address'])

    # I absolutely despise `compact_traceback()`.
    def handle_error(self):
        '''Record the traceback and exit.'''

        logger.critical('Internal asyncore failure, writing traceback to %s' % var.conf.get('options', 'tbfile')[0])

        try:
            tracefile = open(var.conf.get('options', 'tbfile')[0], 'w')
            traceback.print_exc(file=tracefile)
            tracefile.close()

            # Print one to the screen if we're not forked.
            if not var.fork:
                traceback.print_exc()
        except:
            raise

        shutdown(os.EX_SOFTWARE, 'asyncore failure')

    def parse(self):
        '''Parse IRC protocol and call methods based on the results.'''

        global pattern

        # Go through every line in the recvq.
        while len(self.recvq):
            line = self.recvq.popleft()

            event.dispatch('OnParse', self.server, line)

            logger.debug('%s: %s -> %s' % (self.server['id'], self.server['address'], line))
            parv = []

            # Split this crap up with the help of RE.
            try:
                origin, cmd, target, message = pattern.match(line).groups()
            except AttributeError:
                continue

            # Make an IRC parameter argument vector.
            if target:
                parv.append(target)

            parv.append(message)

            # Now see if the command is handled by the hash table.
            try:
                command.irc[cmd]
            except KeyError:
                pass

            if var.conf.get('options', 'irc_cmd_thread')[0]:
                command.dispatch(True, command.irc, cmd, self, origin, parv)
            else:
                command.dispatch(False, command.irc, cmd, self, origin, parv)

            if cmd == 'PING':
                event.dispatch('OnPING', self.server, parv[0])
                self.sendq.appendleft('PONG :%s' % parv[0])

            if cmd == '001':
                for i in self.server['chans']:
                    self.sendq.appendleft('JOIN %s' % i)
                    event.dispatch('OnJoinChannel', self.server, i)

            if cmd == 'PRIVMSG':
                try:
                    n, u, h = dissect_origin(origin)
                except:
                   return

                # Check to see if it's a channel.
                if parv[0].startswith('#') or parv[0].startswith('&'):
                    # Do the `chan_cmd` related stuff.
                    cmd = parv[1].split()

                    if not cmd:
                        return

                    # Chop the command off, as we don't want that.
                    message = cmd[1:]
                    message = ' '.join(message)
                    cmd = cmd[0].upper()

                    # Have we been addressed?
                    # If so, do the `chanme_cmd` related stuff.
                    if parv[1].startswith(self.server['nick']):
                        message = message.split()

                        if not message:
                            return

                        cmd = message[0].upper()
                        del message[0]
                        message = ' '.join(message)

                        # Call the handlers.
                        try:
                            command.chanme[cmd]
                        except KeyError:
                            return

                        if var.conf.get('options', 'chanme_cmd_thread')[0]:
                            command.dispatch(True, command.chanme, cmd, self, (n, u, h), parv[0], message)
                        else:
                            command.dispatch(False, command.chanme, cmd, self, (n, u, h), parv[0], message)
                    else:
                         # Call the handlers.
                         try:
                             command.chan[cmd]
                         except KeyError:
                             return

                         if var.conf.get('options', 'chan_cmd_thread')[0]:
                             command.dispatch(True, command.chan, self.server['trigger'] + cmd, self, (n, u, h), parv[0], message)
                         else:
                             command.dispatch(False, command.chan, self.server['trigger'] + cmd, self, (n, u, h), parv[0], message)
                else:
                     # CTCP?
                     if parv[1].startswith('\1'):
                         parv[1] = parv[1].strip('\1')
                         cmd = parv[1].split()

                         if not cmd:
                             return

                         message = cmd[1:]
                         message = ' '.join(message)
                         cmd = cmd[0].upper()

                         # Call the handlers.
                         try:
                             command.ctcp[cmd]
                         except KeyError:
                             return

                         if var.conf.get('options', 'ctcp_cmd_thread')[0]:
                             command.dispatch(True, command.ctcp, cmd, self, (n, u, h), message)
                         else:
                             command.dispatch(False, command.ctcp, cmd, self, (n, u, h), message)
                     else:
                          cmd = parv[1].split()

                          if not cmd:
                              return

                          message = cmd[1:]
                          message = ' '.join(message)
                          cmd = cmd[0].upper()

                          # Call the handlers.
                          try:
                             command.priv [cmd]
                          except KeyError:
                              try:
                                  cmd = cmd[1:]
                                  command.priv[cmd]
                              except KeyError:
                                 return

                              if var.conf.get('options', 'priv_cmd_thread')[0]:
                                  command.dispatch(True, command.priv, cmd, self, (n, u, h), message)
                              else:
                                  command.dispatch(False, command.priv, cmd, self, (n, u, h), message)

    def privmsg(self, where, text):
        '''PRIVMSG 'where' with 'text'.'''

        self.sendq.appendleft('PRIVMSG %s :%s' % (where, text))
        event.dispatch('OnPRIVMSG', self.server, where, text)
        return

    def notice(self, where, text):
        '''NOTICE 'where' with 'text'.'''

        self.sendq.appendleft('NOTICE %s :%s' % (where, text))
        event.dispatch('OnNOTICE', self.server, where, text)
        return

    def join(self, channel, key=None):
        '''Join 'channel' with 'key' if present.'''

        if not key:
            event.dispatch('OnJoinChannel', self.server, channel)
            self.sendq.appendleft('JOIN %s' % channel)
            return

        self.sendq.appendleft('JOIN %s :%s' % (channel, key))
        event.dispatch('OnJoinChannelWithKey', self.server, channel, key)
        return

    def part(self, channel, reason=None):
        '''Part 'channel' with 'reason' if present.'''

        if not reason:
            event.dispatch('OnPartChannel', self.server, channel)
            self.sendq.appendleft('PART %s' % channel)
            return

        event.dispatch('OnPartChannelWithReason', self.server, channel, reason)
        self.sendq.appendleft('PART %s :%s' % (channel, reason))
        return

    def quit(self, reason=None):
        '''QUIT the server with 'reason'. This offers no reconnection.'''

        if not reason:
            self.sendq.appendleft('QUIT')
            event.dispatch('OnQuit', self.server)
            return

        self.sendq.appendleft('QUIT :%s' % reason)
        event.dispatch('OnQuitWithReason', self.server, reason)
        return

    def push(self, data):
        '''Push raw data onto the server.'''

        self.sendq.appendleft('%s' % data)
        return

def connect(server):
    '''Connect to an IRC server.'''

    if server['connected']:
        return

    logger.info('%s: Connecting to %s:%d' % (server['id'], server['address'], server['port']))
    conn = Connection(server)

    event.dispatch('OnPreConnect', server)

    # This step is low-level to permit IPv6.
    af, type, proto, canon, sa = socket.getaddrinfo(server['address'], server['port'], 0, 1)[0]
    conn.create_socket(af, type)

    # If there's a vhost, bind to it.
    if server['vhost']:
        conn.bind((server['vhost'], 0))

    # Now connect to the IRC server.
    conn.connect(sa)

def connect_to_all():
    '''Connect to all servers in the configuration.'''

    for i in var.conf.get('network'):
        serv = { 'id'        : i.get('id'),
                 'address'   : i.get('address'),
                 'port'      : int(i.get('port')),
                 'nick'      : i.get('nick'),
                 'ident'     : i.get('ident'),
                 'gecos'     : i.get('gecos'),
                 'vhost'     : i.get('vhost'),
                 'chans'     : [],
                 'connected' : False,
                 'pass'      : i.get('pass'),
                 'recontime' : 0,
                 'trigger'   : i.get('trigger') }

        serv['chans'].append(i.get('chans'))

        if i.get('recontime'):
            serv['recontime'] = int(i.get('recontime'))

        var.servers.append(serv)

        event.dispatch('OnNewServer', serv)

        try:
            connect(serv)
        except socket.error, e:
            logger.error('%s: Unable to connect - (%s)' % (serv['id'], serv['address'], serv['port'], os.strerror(e.args[0])))

def dissect_origin(origin):
    '''Split nick!user@host into nick, user, host.'''

    try:
        n, uh = origin.split('!')
        u, h = uh.split('@')

        return n, u, h
    except ValueError:
        pass

def quit_all(reason):
    '''Quit all IRC networks.'''

    for i in var.conns:
        if isinstance(i, Connection):
            i.quit(reason)
