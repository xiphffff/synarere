# synarere -- a highly modular and stable IRC bot.
# Copyright (C) 2010 Michael Rodriguez.
# Rights to this code are documented in docs/LICENSE.

'''Configuration parser.'''

# Import required Python module.
import os

# Import required source modules.
import logger, irc, var, event

class ConfigBlock(object):
    def __init__ (self, label, values={}):
        self.label = label
        self.vars = {}

        # Copy over any values given during initialization
        for key in values:
            self.vars[key] = values[key]

    def add (self, name, value):
        self.vars[name] = value

    def get (self, name, defval=None):
        return self.vars.get(name, defval)

class ConfigParser:
    def __init__(self, file):
        self.file = file
        self.parse()

    def rehash(self, on_sighup):
        '''Rehash configuration and change synarere to fit the new conditions.'''

        logger.info('Rehashing configuration %s' % ('due to SIGHUP.' if on_sighup else ''))
        self.parse()

        event.dispatch('OnRehash', self.file, on_sighup)

    def parse(self):
        '''Parse our file, and put the data into a dictionary.'''

        lno = 0

        # Attempt to open the file.
        fh = open(self.file, 'r')

        # Parse.
        self.blocks = []

        for line in fh.xreadlines():
            for cno, c in enumerate(line):
                if c == '\n':
                    # Increment the line number.
                    lno += 1

                if c == '#': # Comment until EOL.
                    break
                if c == ':': # Block label.
                    label = line[:cno].strip()
                    self.blocks.append(ConfigBlock(label))
                if c == '=': # Variable.
                    if not self.blocks:  # Skip this line, as no block label was given yet.
                        break
                    varname = line[:cno].strip()
                    varval = line[cno + 1:].strip()
                    self.blocks[-1].add(varname, varval)
                    break

        # Close the file handle
        fh.close()

    def xget(self, block, variable=None):
        '''
        Return whatever is in block:variable. If variable is None,
        we will iterate over mutiple blocks, thus allowing us to
        return multiple values from multiple blocks.
        '''

        if block not in set(b.label for b in self.blocks):
            logger.debug('%r block not in configuration.' % block)

        for i in self.blocks:
            if i.label == block:
                if variable is None: # Just get blocks by this name
                    yield i
                else: # Get a member of blocks by this name.
                    yield i.get(variable)

    def get(self, block, variable=None):
        '''
        Call our iterating generator (xget) and just store all its
        results into a list to return all at once.
        '''

        return [b for b in self.xget(block, variable)]
