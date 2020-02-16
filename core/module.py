# synarere -- a highly modular and stable IRC bot.
# Copyright (C) 2010 Michael Rodriguez.
# Rights to this code are documented in docs/LICENSE.

'''Module operations.'''

# Import required Python function.
from imp import load_source

# Import required core modules.
import logger, var, event

def load(module):
    '''Load a module.'''

    try:
        mod = load_source(module, module)
    except ImportError, e:
        logger.error('Unable to load module %s: %s' % (module, e))
        return

    # Check to make sure the module has init/fini functions.
    if not hasattr(mod, 'module_init'):
        logger.error('Unable to use module %s: No entry point has been defined.' % mod.__name__)
        return

    if not hasattr(mod, 'module_fini'):
        logger.error('Unable to use module %s: No exit point has been defined.' % mod.__name__)
        return

    mod.module_init()
    logger.info('Module %s loaded.' % mod.__name__)

    # Add the module to the loaded modules list.
    var.modules_loaded.append(mod)
    event.dispatch('OnModuleLoad', module)

def unload(module):
    '''Unload a module.'''

    # Make sure it is in the modules loaded list.
    if module not in var.modules_loaded:
        logger.warning('%s is not in the loaded modules list.' % module)
        return

    module.module_fini()

    # Remove the module from the loaded modules list.
    var.modules_loaded.remove(module)
    event.dispatch('OnModuleUnload', module)

def load_all():
    '''Load all modules listed in the configuration.'''

    for i in var.conf.get('module'):
        name = i.get('name')

        if name != None:
           load(name)

        event.dispatch('OnLoadAllModules', name)

def unload_all():
    '''Unload all loaded modules.'''

    logger.info('Unloading all modules.')

    for i in var.modules_loaded:
        unload(i)

    event.dispatch('OnUnloadAllModules')
