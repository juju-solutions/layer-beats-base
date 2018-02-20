from charms.templating.jinja2 import render
from charmhelpers.core.hookenv import config, juju_version, principal_unit
from charmhelpers.core.unitdata import kv

from subprocess import check_call

from os import getenv


def render_without_context(source, target):
    """ Render beat template from global state context. """
    cache = kv()
    context = dict(config())
    connected = False

    # Add deployment attributes
    model_info_cache()
    principal_unit_cache()
    context['juju_model_name'] = cache.get('model_name')
    context['juju_model_uuid'] = cache.get('model_uuid')
    context['juju_principal_unit'] = cache.get('principal_name')

    logstash_hosts = cache.get('beat.logstash')
    elasticsearch_hosts = cache.get('beat.elasticsearch')
    kafka_hosts = cache.get('beat.kafka')

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

    # Transform some config options into proper lists if they aren't already.
    # Do this only for non-empty values for proper jinja templating.
    for key in ('fields', 'logpath'):
        if (key in context.keys() and context[key] and not
                isinstance(context[key], list)):
            context[key] = context[key].split(' ')

    render(source, target, context)
    return connected


def model_info_cache():
    """ Cache the model info for this deployment.

    This info will not change over the lifetime of the deployment, so we
    only need to set it once.
    """
    cache = kv()
    if not (cache.get('model_name') and cache.get('model_uuid')):
        juju_major_version = int(juju_version().split('.')[0])

        juju_info = {}
        if juju_major_version >= 2:
            juju_info['model_name'] = getenv('JUJU_MODEL_NAME')
            juju_info['model_uuid'] = getenv('JUJU_MODEL_UUID')
        else:
            juju_info['model_name'] = getenv('JUJU_ENV_NAME')
            juju_info['model_uuid'] = getenv('JUJU_ENV_UUID')

        cache.update(juju_info)


def principal_unit_cache():
    """ Cache the principal unit that a beat is related to.

    This info will not change over the lifetime of the deployment, so we
    only need to set it once.
    """
    cache = kv()
    if not cache.get('principal_name'):
        principal_name = principal_unit()
        if principal_name:
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
