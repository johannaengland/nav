# -*- coding: utf-8 -*-
#
# Copyright (C) 2008, 2009 UNINETT AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 2 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""ipdevpoll plugin to poll IP prefix information.

This plugin will use the IF-MIB, IP-MIB, IPv6-MIB and
CISCO-IETF-IP-MIB to poll prefix information for both IPv4 and IPv6.

A revised version of the IP-MIB contains the IP-version-agnostic
ipAddressTable which is queried first, although not much equipment
supports this table yet.  It then falls back to the original IPv4-only
ipAddrTable, followed by the IPv6-MIB (which has been superseded by
the updated IP-MIB).  It also tries a Cisco proprietary
CISCO-IETF-IP-MIB, which is based on a draft that later became the
revised IP-MIB.

An interface with an IP address whose name matches the VLAN_PATTERN
will cause the corresponding prefix to be associated with the VLAN id
parsed from the interface name.  Not all dot1q enabled routers name
their interfaces like this, but routing switches from several vendors
do.

"""
import re
import logging

from twisted.internet import defer
from twisted.python.failure import Failure

from IPy import IP

from nav.mibs import reduce_index
from nav.mibs.if_mib import IfMib
from nav.mibs.ip_mib import IpMib, IndexToIpException
from nav.mibs.ipv6_mib import Ipv6Mib
from nav.mibs.cisco_ietf_ip_mib import CiscoIetfIpMib

from nav.ipdevpoll import Plugin
from nav.ipdevpoll import storage, shadows

VLAN_PATTERN = re.compile("Vl(an)?(?P<vlan>\d+)", re.IGNORECASE)

class Prefix(Plugin):
    """
    ipdevpoll-plugin for collecting prefix information from monitored
    equipment.
    """
    def __init__(self, *args, **kwargs):
        super(Prefix, self).__init__(*args, **kwargs)
        self.ignored_prefixes = get_ignored_prefixes(self.config)

    @classmethod
    def can_handle(cls, netbox):
        """
        This plugin handles netboxes
        """
        return True

    @defer.deferredGenerator
    def handle(self):


        self.logger.debug("Collecting prefixes")
        netbox = self.containers.factory(None, shadows.Netbox)

        ipmib = IpMib(self.agent)
        ciscoip = CiscoIetfIpMib(self.agent)
        ipv6mib = Ipv6Mib(self.agent)

        # Retrieve interface names and keep those who match a VLAN
        # naming pattern
        dw = defer.waitForDeferred(self.get_vlan_interfaces())
        yield dw
        vlan_interfaces = dw.getResult()

        # Traverse address tables from IP-MIB, IPV6-MIB and
        # CISCO-IETF-IP-MIB in that order.
        addresses = set()
        for mib in ipmib, ipv6mib, ciscoip:
            self.logger.debug("Trying address tables from %s",
                              mib.mib['moduleName'])
            df = mib.get_interface_addresses()
            # Special case; some devices will time out while building a bulk
            # response outside our scope when it has no proprietary MIB support
            if mib != ipmib:
                df.addErrback(self._ignore_timeout, set())
            waiter = defer.waitForDeferred(df)
            yield waiter
            new_addresses = waiter.getResult()
            self.logger.debug("Found %d addresses in %s: %r",
                              len(new_addresses), mib.mib['moduleName'],
                              new_addresses)
            addresses.update(new_addresses)

        for ifindex, ip, prefix in addresses:
            if self._prefix_should_be_ignored(prefix):
                self.logger.debug("ignoring prefix %s as configured", prefix)
                continue
            self.create_containers(netbox, ifindex, prefix, ip,
                                   vlan_interfaces)


    def create_containers(self, netbox, ifindex, net_prefix, ip,
                          vlan_interfaces):
        """
        Utitilty method for creating the shadow-objects
        """
        interface = self.containers.factory(ifindex, shadows.Interface)
        interface.ifindex = ifindex
        interface.netbox = netbox

        # No use in adding the GwPortPrefix unless we actually found a prefix
        if net_prefix:
            port_prefix = self.containers.factory(ip, shadows.GwPortPrefix)
            port_prefix.interface = interface
            port_prefix.gw_ip = str(ip)

            prefix = self.containers.factory(net_prefix, shadows.Prefix)
            prefix.net_address = str(net_prefix)
            port_prefix.prefix = prefix

            # Always associate prefix with a VLAN record, but set a
            # VLAN number if we can.
            vlan = self.containers.factory(ifindex, shadows.Vlan)
            if ifindex in vlan_interfaces:
                vlan.vlan = vlan_interfaces[ifindex]

            prefix.vlan = vlan

    @defer.deferredGenerator
    def get_vlan_interfaces(self):
        """Get all virtual VLAN interfaces.

        Any interface whose ifName matches the VLAN_PATTERN regexp
        will be included in the result.

        Return value:

          A deferred whose result is a dictionary: { ifindex: vlan }

        """
        ifmib = IfMib(self.agent)
        dw = defer.waitForDeferred(ifmib.retrieve_column('ifName'))
        yield dw
        interfaces = reduce_index(dw.getResult())

        vlan_ifs = {}
        for ifindex, ifname in interfaces.items():
            match = VLAN_PATTERN.match(ifname)
            if match:
                vlan = int(match.group('vlan'))
                vlan_ifs[ifindex] = vlan

        yield vlan_ifs

    def _ignore_timeout(self, failure, result=None):
        """Ignores a defer.TimeoutError in an errback chain.

        The result argument will be returned, and there injected into the
        regular callback chain.

        """
        failure.trap(defer.TimeoutError)
        self.logger.debug("request timed out, ignoring and moving on...")
        return result

    def _prefix_should_be_ignored(self, prefix):
        if prefix is None:
            return False

        for ignored in self.ignored_prefixes:
            if prefix in ignored:
                return True

        return False


def get_ignored_prefixes(config):
    if config is not None:
        raw_string = config.get('prefix', 'ignored', '')
    else:
        return []
    items = raw_string.split(',')
    prefixes = [_convert_string_to_prefix(i) for i in items]
    return [prefix for prefix in prefixes if prefix is not None]

def _convert_string_to_prefix(string):
    try:
        return IP(string)
    except ValueError:
        logging.getLogger(__name__).error(
            "Ignoring invalid prefix in ignore list: %s",
            string)

