from charms.reactive import hook
from charms.reactive import when
from charms.reactive import when_not
from charms.reactive import set_state
from charms.reactive import remove_state
from charmhelpers.fetch import configure_sources
from charmhelpers.core.hookenv import status_set
from charmhelpers.core.unitdata import kv
from elasticbeats import principal_unit_cache


@hook('beats-host-joined')
def assign_our_shipping_id():
    principal_unit_cache()


@when_not('beats.repo.available')
def install_beats_repo():
    configure_sources(update=True)
    set_state('beats.repo.available')


@when('config.changed')
def config_changed():
    set_state('beat.render')


@when('config.changed.install_sources')
@when('config.changed.install_keys')
def reinstall_filebeat():
    remove_state('beats.repo.available')


@when_not('logstash.connected', 'elasticsearch.connected')
def blocked_messaging():
    status_set('blocked', 'Waiting on relationship: elasticsearch or logstash')


@when('logstash.available')
def cache_logstash_data(logstash):
    units = logstash.list_unit_data()
    cache = kv()
    if cache.get('beat.logstash'):
        hosts = cache.get('filebeat.logstash')
    else:
        hosts = []
    for unit in units:
        host_string = "{0}:{1}".format(unit['private_address'],
                                       unit['port'])
        if host_string not in hosts:
            hosts.append(host_string)

    cache.set('beat.logstash', hosts)
    set_state('beat.render')


@when('elasticsearch.available')
def cache_elasticsearch_data(elasticsearch):
    units = elasticsearch.list_unit_data()
    cache = kv()
    if cache.get('beat.elasticsearch'):
        hosts = cache.get('beat.elasticsearch')
    else:
        hosts = []
    for unit in units:
        host_string = "{0}:{1}".format(unit['host'],
                                       unit['port'])
        if host_string not in hosts:
            hosts.append(host_string)

    cache.set('beat.elasticsearch', hosts)
    set_state('beat.render')
