#!/usr/bin/env python
#
# synarere -- a highly modular and stable IRC bot.
# Copyright (C) 2010 Michael Rodriguez.
# Rights to this code are documented in docs/LICENSE.

'''Main program. This does basic routines, and calls core functions.'''

# Import required Python modules.
import getopt, os, signal, sys

# Import required core modules.
from core import module, irc, logger, io, var, confparse, command

# Import required core function.
from core import shutdown

def ctcp_version(conn, (nick, user, host), message):
    '''Handle VERSION requests.'''

    conn.sendq.appendleft('NOTICE %s :\001VERSION synarere-%s\001' % (nick, var.version))
    return

def ctcp_ping(conn, (nick, user, host), message):
    '''Handle PING requests.'''

    conn.sendq.appendleft('NOTICE %s :\001PING %s\001' % (nick, message))
    return

def print_clo_help():
    '''Output command line options and their meanings.'''

    print '-c (--config) <config>: Specify the configuration file to use.'
    print '-h (--help): Output this message.'
    print '-n (--nofork): Do not fork into the background (will output log messages)'
    print '-p (--pydebug): Start in the Python Debugger.'
    print '-v (--version): Output version information.'

def main(argv=sys.argv[1:]):
    '''Our entry point.'''

    # Are we root?
    if os.geteuid() == 0:
        print >> sys.stderr, 'synarere: will not run as root for security reasons'
        sys.exit(0)

    # Parse command line options and parameter list.
    try:
        opts, args = getopt.getopt(argv, 'c:hnpv', ['config=', 'help', 'nofork', 'pydebug', 'version'])
    except getopt.GetoptError, err:
        print >> sys.stderr, '%s\n' % err
        print_clo_help()
        sys.exit(os.EX_USAGE)

    for opt, arg in opts:
        if opt in ('-c', '--config'):
            var.config_file = arg
        elif opt in ('-h', '--help'):
            print_clo_help()
            sys.exit(os.EX_OK)
        elif opt in ('-n', '--nofork'):
            var.fork = False
        elif opt in ('-p', '--pydebug'):
            import pdb
            pdb.set_trace()
        elif opt in ('-v', '--version'):
            print 'synarere: version %s' % var.version
            sys.exit(os.EX_OK)

    # Attach signals to handlers.
    signal.signal(signal.SIGHUP, lambda h: var.conf.rehash(True))
    signal.signal(signal.SIGINT, lambda i: shutdown(signal.SIGINT, 'Caught SIGINT (terminal interrupt)'))
    signal.signal(signal.SIGTERM, lambda t: shutdown(signal.SIGTERM, 'Caught SIGTERM'))
    signal.signal(signal.SIGPIPE, signal.SIG_IGN)
    signal.signal(signal.SIGALRM, signal.SIG_IGN)
    signal.signal(signal.SIGCHLD, signal.SIG_IGN)
    signal.signal(signal.SIGWINCH, signal.SIG_IGN)
    signal.signal(signal.SIGTTIN, signal.SIG_IGN)
    signal.signal(signal.SIGTTOU, signal.SIG_IGN)
    signal.signal(signal.SIGTSTP, signal.SIG_IGN)

    print 'synarere: version %s' % var.version

    # Initialize the configuration parser.
    try:
        var.conf = confparse.ConfigParser(var.config_file)
    except confparse.Exception, errstr:
        print >> sys.stderr, 'synarere: configuration error for %s: %s' % (var.config_file, errstr)
        sys.exit(os.EX_CONFIG)

    # Check to see if we are already running.
    try:
        pid_file = open(var.conf.get('options', 'pidfile')[0], 'r')

        try:
            pid = pid_file.read()

            if pid:
                pid = int(pid)

                try:
                    os.kill(pid, 0)
                except OSError:
                    pass

                print >> sys.stderr, 'synarere: an instance is already running'
                sys.exit(os.EX_SOFTWARE)
        finally:
            pid_file.close()
    except IOError:
        pass

    # Fork into the background.
    if var.fork:
        try:
            pid = os.fork()
        except OSError, e:
            return (e.errno, e.strerror)

        # This is the child process.
        if pid == 0:
            os.setsid()

            # Now the child fork()'s a child in order to prevent acquisition
            # of a controlling terminal.
            try:
                pid = os.fork()
            except OSError, e:
                return (e.errno, e.strerror)

            # This is the second child process.
            if pid == 0:
                os.chdir(os.getcwd())
                os.umask(0)

            # This is the first child.
            else:
                print 'synarere: pid', pid
                print 'synarere: running in background mode from:', os.getcwd()
                os._exit(0)
        else:
            os._exit(0)

        # Try to write the PID file.
        try:
            pid_file = open(var.conf.get('options', 'pidfile')[0], 'w')
            pid_file.write(str(os.getpid()))
            pid_file.close()
        except IOError, e:
            print >> sys.stderr, 'synarere: unable to write pid file:', os.strerror(e.args[0])

        # Try to close all open file descriptors.
        # If we cant find the max number, just close the first 256.
        try:
            maxfd = os.sysconf('SC_OPEN_MAX')
        except (AttributeError, ValueError):
            maxfd = 256

        for fd in range(0, maxfd):
            try:
                os.close(fd)
            except OSError:
                pass

        # Redirect the standard file descriptors to /dev/null.
        os.open('/dev/null', os.O_RDONLY)
        os.open('/dev/null', os.O_RDWR)
        os.open('/dev/null', os.O_RDWR)
    else:
        print 'synarere: pid', os.getpid()
        print 'synarere: running in foreground mode from:', os.getcwd()

    # Initialize the logger.
    logger.init()

    # These have to be in the main file.
    command.add('VERSION', ctcp_version, command.ctcp)
    command.add('PING', ctcp_ping, command.ctcp)

    # Load all modules listed in the configuration.
    module.load_all()

    # Connect to all IRC networks.
    irc.connect_to_all()

    # Start the loop.
    io.io()

    # This should NEVER happen.
    shutdown(os.EX_SOFTWARE, 'Main loop exited (?)')

if __name__ == '__main__':
    main()
