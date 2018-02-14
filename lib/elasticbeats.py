from charms.templating.jinja2 import render
from charmhelpers.core.hookenv import config
from charmhelpers.core.unitdata import kv

from subprocess import check_call

from os import getenv


def render_without_context(source, target):
    ''' Render beat template from global state context '''
    cache = kv()
    context = dict(config())
    connected = False

    logstash_hosts = cache.get('beat.logstash')
    elasticsearch_hosts = cache.get('beat.elasticsearch')
    kafka_hosts = cache.get('beat.kafka')
    context['principal_unit'] = cache.get('principal_name')

    if logstash_hosts:
        connected = True
    context.update({'logstash': logstash_hosts})
    if context['logstash_hosts']:
        connected = True
    if elasticsearch_hosts:
        connected = True
    context.update({'elasticsearch': elasticsearch_hosts})
    if kafka_hosts:
        connected = True
    context.update({'kafka': kafka_hosts})
    if context['kafka_hosts']:
        connected = True

    if 'protocols' in context.keys():
        context.update({'protocols': parse_protocols()})

    # Split space delimited config items
    if ('fields' in context.keys() and context['fields'] and not
            isinstance(context['fields'], list)):
        context['fields'] = context['fields'].split(' ')
    if ('logpath' in context.keys() and context['logpath'] and not
            isinstance(context['logpath'], list)):
        context['logpath'] = context['logpath'].split(' ')

    render(source, target, context)
    return connected


def principal_unit_cache():
    principal_name = getenv('JUJU_REMOTE_UNIT')
    cache = kv()
    cache.set('principal_name', principal_name)


def enable_beat_on_boot(service):
    """ Enable the beat to start automaticaly during boot """
    check_call(['update-rc.d', service, 'defaults', '95', '10'])


def push_beat_index(elasticsearch, service):
    cmd = ["curl",
           "-XPUT",
           "http://{0}/_template/{1}".format(elasticsearch, service),
           "-d@/etc/{0}/{0}.template.json".format(service)]  # noqa

    check_call(cmd)


def parse_protocols():
    protocols = config('protocols')
    bag = {}
    for protocol in protocols.split(' '):
        proto, port = protocol.strip().split(':')
        if proto in bag:
            bag[proto].append(int(port))
        else:
            bag.update({proto: []})
            bag[proto].append(int(port))
    return bag
