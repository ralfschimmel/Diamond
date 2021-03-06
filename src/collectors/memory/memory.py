# coding=utf-8

"""
This class collects data on memory utilization

Note that MemFree may report no memory free. This may not actually be the case,
as memory is allocated to Buffers and Cache as well. See
[this link](http://www.linuxatemyram.com/) for more details.

#### Dependencies

* /host_proc/meminfo or psutil

"""

import diamond.collector
import diamond.convertor
import os

try:
    import psutil
    psutil  # workaround for pyflakes issue #13
except ImportError:
    psutil = None

# _KEY_MAPPING = [
#     'MemTotal',
#     'MemFree',
#     'Buffers',
#     'Cached',
#     'Active',
#     'Dirty',
#     'Inactive',
#     'Shmem',
#     'SwapTotal',
#     'SwapFree',
#     'SwapCached',
#     'VmallocTotal',
#     'VmallocUsed',
#     'VmallocChunk'
# ]

_KEY_MAPPING = [
    'MemTotal',
    'MemFree',
    'Buffers',
    'Cached',
    'SwapFree'
]


class MemoryCollector(diamond.collector.Collector):

    PROC = '/host_proc/meminfo'

    def get_default_config_help(self):
        config_help = super(MemoryCollector, self).get_default_config_help()
        config_help.update({
            'detailed': 'Set to True to Collect all the nodes',
        })
        return config_help

    def get_default_config(self):
        """
        Returns the default collector settings
        """
        config = super(MemoryCollector, self).get_default_config()
        config.update({
            'enabled':  'True',
            'path':     'memory',
            'method':   'Threaded',
            # Collect all the nodes or just a few standard ones?
            # Uncomment to enable
            #'detailed': 'True'
        })
        return config

    def collect(self):
        """
        Collect memory stats
        """
        if os.access(self.PROC, os.R_OK):
            file = open(self.PROC)
            data = file.read()
            file.close()
            actualFree = 0
            for line in data.splitlines():
                try:
                    name, value, units = line.split()
                    name = name.rstrip(':')
                    value = int(value)

                    if (name not in _KEY_MAPPING
                            and 'detailed' not in self.config):
                        continue

                    for unit in self.config['byte_unit']:
                        value = diamond.convertor.binary.convert(value=value,
                                                                 oldUnit=units,
                                                                 newUnit=unit)
                        if (name == 'MemTotal' or name == 'SwapFree'):
                          self.publish(name, value, metric_type='GAUGE')
                        else:
                          # calculate actual free memory: memFree + cached + buffers
                          actualFree += value
                        break
                except ValueError:
                    continue
            self.publish('MemActualFree', actualFree, metric_type='GAUGE')
            return True

        return None
