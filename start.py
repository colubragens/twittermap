#!/usr/bin/env python
import sys, socket, IPython.kernel.client
from secrets import MEC_OPTIONS
mec = IPython.kernel.client.MultiEngineClient(*MEC_OPTIONS)

# Read configuration from file
config = dict()
execfile('viewer/config', config, config)

# Define the nodes.
# - entries in consumesFrom are actually prepended by the top-level name (like "twitter")
# - the classes are instantiated as c(router, node), where node is this dictionary.
tstream = dict(name='stream',  consumesFrom=[],          classType='twitternet.TwitterStream')
sstream = dict(name='stream',  consumesFrom=[],          classType='twitternet.SpecificStream')
bstream = dict(name='stream',  consumesFrom=[],          classType='twitternet.BlogStream')
tproc   = dict(name='process', consumesFrom=['stream'],  classType='twitternet.TwitterProcess')
bproc   = dict(name='process', consumesFrom=['stream'],  classType='twitternet.BlogProcess')
tsom    = dict(name='som',     consumesFrom=['process'], classType='twitternet.TwitterSom', _somsize=config['somsize'])
rsom    = dict(name='som',     consumesFrom=['process'], classType='twitternet.RfbfSom',    _somsize=config['somsize'])
rvec    = dict(name='vec',     consumesFrom=['process'], classType='twitternet.RfbfVec')

def nodes_for(net_name):
    def disamb(node, **kwargs):
        '''Prepend net_name to the producer and consumer names.'''
        return dict(node,
                    name=net_name + node['name'],
                    consumesFrom=[net_name + s for s in node['consumesFrom']],
                    **kwargs)

    # Determine which processing elements to use based on the configuration.
    if net_name in config['fishes']:
        info = config['fishes'][name]
        # Default to a RfbfVec processing a TwitterProcess processing a TwitterSteam.
        newNodes = [ rvec,    tproc, tstream ]
        # Override in case we have blogs or specific Twitter topics.
        if '_blogs' in info:
            newNodes[-2:] = [ bproc, bstream ]
        elif '_topics' in info:
            newNodes[-1:] = [        sstream ]
        return [ disamb(node, **info) for node in newNodes ]
    elif name in config['twitter']:
        return [ disamb(tsom), disamb(tproc), disamb(sstream, _topics=config['twitter'][name]) ]
    else:
        return [ disamb(tsom), disamb(tproc), disamb(tstream) ]

localNodes = []
for name in set(sys.argv[1:] or ['twitter']):
  localNodes += nodes_for(name)

# TODO: allow processing to happen on other hosts.
my_hostname = socket.gethostname()

graph = {
    my_hostname : {
        'tags' : ['twittermap'],
        'localNodes' : localNodes
    }
}
#mec.activate()
mec.push(dict(graph=graph))
mec.execute('import os, vectornet.router')
mec.execute("os.environ['DJANGO_SETTINGS_MODULE'] = 'vectornet.settings'")
mec.execute('vectornet.router.startNetwork(graph)')

#import pprint
#pprint.pprint(graph)

#import os, vectornet.router
#os.environ['DJANGO_SETTINGS_MODULE'] = 'vectornet.settings'
#vectornet.router.startNetwork(graph)
