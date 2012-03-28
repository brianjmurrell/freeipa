# Authors:
#   Pavel Zuna <pzuna@redhat.com>
#
# Copyright (C) 2010  Red Hat
# see file 'COPYING' for use and warranty information
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""
Test the `ipalib/plugins/dns.py` module.
"""

import nose
from ipalib import api, errors
from ipalib.dn import *
from tests.test_xmlrpc import objectclasses
from xmlrpc_test import Declarative, fuzzy_digits, fuzzy_uuid

dnszone1 = u'dnszone.test'
dnszone1_dn = DN(('idnsname',dnszone1),('cn','dns'),api.env.basedn)
dnszone1_mname = u'ns1.%s.' % dnszone1
dnszone1_mname_dn = DN(('idnsname','ns1'), dnszone1_dn)
dnszone1_rname = u'root.%s.' % dnszone1
dnszone2 = u'dnszone2.test'
dnszone2_dn = DN(('idnsname',dnszone2),('cn','dns'),api.env.basedn)
dnszone2_mname = u'ns1.%s.' % dnszone2
dnszone2_rname = u'root.%s.' % dnszone2
revdnszone1 = u'15.142.80.in-addr.arpa.'
revdnszone1_ip = u'80.142.15.0/24'
revdnszone1_dn = DN(('idnsname',revdnszone1),('cn','dns'),api.env.basedn)
dnsres1 = u'testdnsres'
dnsres1_dn = DN(('idnsname',dnsres1), dnszone1_dn)
dnsrev1 = u'80'
dnsrev1_dn = DN(('idnsname',dnsrev1), revdnszone1_dn)
dnsrev2 = u'81'
dnsrev2_dn = DN(('idnsname',dnsrev2), revdnszone1_dn)

class test_dns(Declarative):

    @classmethod
    def setUpClass(cls):
        super(test_dns, cls).setUpClass()

        if not api.Backend.xmlclient.isconnected():
            api.Backend.xmlclient.connect(fallback=False)
        try:
           api.Command['dnszone_add'](dnszone1,
               idnssoamname = dnszone1_mname,
               idnssoarname = dnszone1_rname,
               force = True,
           )
           api.Command['dnszone_del'](dnszone1)
        except errors.NotFound:
            raise nose.SkipTest('DNS is not configured')
        except errors.DuplicateEntry:
            pass

    cleanup_commands = [
        ('dnszone_del', [dnszone1], {}),
        ('dnsrecord_del', [dnszone1, dnsres1], {'del_all' : True}),
        ('dnszone_del', [dnszone2], {}),
        ('dnszone_del', [revdnszone1], {}),
        ('dnsconfig_mod', [], {'idnsforwarders' : None,
                               'idnsforwardpolicy' : None,
                               'idnsallowsyncptr' : None,
                               'idnszonerefresh' : None,
                               })
    ]

    tests = [

        dict(
            desc='Try to retrieve non-existent zone %r' % dnszone1,
            command=('dnszone_show', [dnszone1], {}),
            expected=errors.NotFound(reason='DNS zone not found'),
        ),


        dict(
            desc='Try to update non-existent zone %r' % dnszone1,
            command=('dnszone_mod', [dnszone1], {'idnssoamname': u'foobar'}),
            expected=errors.NotFound(reason='DNS zone not found'),
        ),


        dict(
            desc='Try to delete non-existent zone %r' % dnszone1,
            command=('dnszone_del', [dnszone1], {}),
            expected=errors.NotFound(reason='DNS zone not found'),
        ),


        dict(
            desc='Try to create zone with invalid name',
            command=(
                'dnszone_add', [u'invalid zone'], {
                    'idnssoamname': dnszone1_mname,
                    'idnssoarname': dnszone1_rname,
                    'ip_address' : u'1.2.3.4',
                }
            ),
            expected=errors.ValidationError(name='idnsname', error=''),
        ),


        dict(
            desc='Create zone %r' % dnszone1,
            command=(
                'dnszone_add', [dnszone1], {
                    'idnssoamname': dnszone1_mname,
                    'idnssoarname': dnszone1_rname,
                    'ip_address' : u'1.2.3.4',
                }
            ),
            expected={
                'value': dnszone1,
                'summary': None,
                'result': {
                    'dn': unicode(dnszone1_dn),
                    'idnsname': [dnszone1],
                    'idnszoneactive': [u'TRUE'],
                    'idnssoamname': [dnszone1_mname],
                    'nsrecord': [dnszone1_mname],
                    'idnssoarname': [dnszone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [fuzzy_digits],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowdynupdate': [u'FALSE'],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                    'objectclass': [u'top', u'idnsrecord', u'idnszone'],
                },
            },
        ),


        dict(
            desc='Try to create duplicate zone %r' % dnszone1,
            command=(
                'dnszone_add', [dnszone1], {
                    'idnssoamname': dnszone1_mname,
                    'idnssoarname': dnszone1_rname,
                    'ip_address' : u'1.2.3.4',
                }
            ),
            expected=errors.DuplicateEntry(),
        ),

        dict(
            desc='Try to create a zone with nonexistent NS entry',
            command=(
                'dnszone_add', [dnszone2], {
                    'idnssoamname': dnszone2_mname,
                    'idnssoarname': dnszone2_rname,
                }
            ),
            expected=errors.NotFound(reason='Nameserver \'%s\' does not have a corresponding A/AAAA record' % (dnszone2_mname)),
        ),

        dict(
            desc='Create a zone with nonexistent NS entry with --force',
            command=(
                'dnszone_add', [dnszone2], {
                    'idnssoamname': dnszone2_mname,
                    'idnssoarname': dnszone2_rname,
                    'force'       : True,
                }
            ),
            expected={
                'value': dnszone2,
                'summary': None,
                'result': {
                    'dn': unicode(dnszone2_dn),
                    'idnsname': [dnszone2],
                    'idnszoneactive': [u'TRUE'],
                    'idnssoamname': [dnszone2_mname],
                    'nsrecord': [dnszone2_mname],
                    'idnssoarname': [dnszone2_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [fuzzy_digits],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowdynupdate': [u'FALSE'],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                    'objectclass': [u'top', u'idnsrecord', u'idnszone'],
                },
            },
        ),

        dict(
            desc='Delete zone %r' % dnszone2,
            command=('dnszone_del', [dnszone2], {}),
            expected={
                'value': dnszone2,
                'summary': None,
                'result': {'failed': u''},
            },
        ),

        dict(
            desc='Retrieve zone %r' % dnszone1,
            command=('dnszone_show', [dnszone1], {}),
            expected={
                'value': dnszone1,
                'summary': None,
                'result': {
                    'dn': unicode(dnszone1_dn),
                    'idnsname': [dnszone1],
                    'idnszoneactive': [u'TRUE'],
                    'nsrecord': [dnszone1_mname],
                    'idnssoamname': [dnszone1_mname],
                    'idnssoarname': [dnszone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [fuzzy_digits],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                },
            },
        ),


        dict(
            desc='Update zone %r' % dnszone1,
            command=('dnszone_mod', [dnszone1], {'idnssoarefresh': 5478}),
            expected={
                'value': dnszone1,
                'summary': None,
                'result': {
                    'idnsname': [dnszone1],
                    'idnszoneactive': [u'TRUE'],
                    'nsrecord': [dnszone1_mname],
                    'idnssoamname': [dnszone1_mname],
                    'idnssoarname': [dnszone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [u'5478'],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                },
            },
        ),


        dict(
            desc='Create reverse zone %r' % revdnszone1,
            command=(
                'dnszone_add', [revdnszone1], {
                    'idnssoamname': dnszone1_mname,
                    'idnssoarname': dnszone1_rname,
                    'ip_address' : u'1.2.3.4',
                }
            ),
            expected={
                'value': revdnszone1,
                'summary': None,
                'result': {
                    'dn': unicode(revdnszone1_dn),
                    'idnsname': [revdnszone1],
                    'idnszoneactive': [u'TRUE'],
                    'idnssoamname': [dnszone1_mname],
                    'nsrecord': [dnszone1_mname],
                    'idnssoarname': [dnszone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [fuzzy_digits],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowdynupdate': [u'FALSE'],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                    'objectclass': [u'top', u'idnsrecord', u'idnszone'],
                },
            },
        ),


        dict(
            desc='Search for zones with name server %r' % (dnszone1_mname),
            command=('dnszone_find', [], {'idnssoamname': dnszone1_mname}),
            expected={
                'summary': None,
                'count': 2,
                'truncated': False,
                'result': [{
                    'dn': unicode(revdnszone1_dn),
                    'idnsname': [revdnszone1],
                    'idnszoneactive': [u'TRUE'],
                    'nsrecord': [dnszone1_mname],
                    'idnssoamname': [dnszone1_mname],
                    'idnssoarname': [dnszone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [fuzzy_digits],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                },
                {
                    'dn': unicode(dnszone1_dn),
                    'idnsname': [dnszone1],
                    'idnszoneactive': [u'TRUE'],
                    'nsrecord': [dnszone1_mname],
                    'idnssoamname': [dnszone1_mname],
                    'idnssoarname': [dnszone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [u'5478'],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                }],
            },
        ),


        dict(
            desc='Search for zones with name server %r with --forward-only' % dnszone1_mname,
            command=('dnszone_find', [], {'idnssoamname': dnszone1_mname, 'forward_only' : True}),
            expected={
                'summary': None,
                'count': 1,
                'truncated': False,
                'result': [{
                    'dn': unicode(dnszone1_dn),
                    'idnsname': [dnszone1],
                    'idnszoneactive': [u'TRUE'],
                    'nsrecord': [dnszone1_mname],
                    'idnssoamname': [dnszone1_mname],
                    'idnssoarname': [dnszone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [u'5478'],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                }],
            },
        ),


        dict(
            desc='Delete reverse zone %r' % revdnszone1,
            command=('dnszone_del', [revdnszone1], {}),
            expected={
                'value': revdnszone1,
                'summary': None,
                'result': {'failed': u''},
            },
        ),


        dict(
            desc='Disable zone %r' % dnszone1,
            command=('dnszone_disable', [dnszone1], {}),
            expected={
                'value': dnszone1,
                'summary': u'Disabled DNS zone "%s"' % dnszone1,
                'result': True,
            },
        ),


        dict(
            desc='Check if zone %r is really disabled' % dnszone1,
            command=('dnszone_show', [dnszone1], {}),
            expected={
                'value': dnszone1,
                'summary': None,
                'result': {
                    'dn': unicode(dnszone1_dn),
                    'idnsname': [dnszone1],
                    'idnszoneactive': [u'FALSE'],
                    'nsrecord': [dnszone1_mname],
                    'idnssoamname': [dnszone1_mname],
                    'idnssoarname': [dnszone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [fuzzy_digits],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                },
            },
        ),


        dict(
            desc='Enable zone %r' % dnszone1,
            command=('dnszone_enable', [dnszone1], {}),
            expected={
                'value': dnszone1,
                'summary': u'Enabled DNS zone "%s"' % dnszone1,
                'result': True,
            },
        ),


        dict(
            desc='Check if zone %r is really enabled' % dnszone1,
            command=('dnszone_show', [dnszone1], {}),
            expected={
                'value': dnszone1,
                'summary': None,
                'result': {
                    'dn': unicode(dnszone1_dn),
                    'idnsname': [dnszone1],
                    'idnszoneactive': [u'TRUE'],
                    'nsrecord': [dnszone1_mname],
                    'idnssoamname': [dnszone1_mname],
                    'idnssoarname': [dnszone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [fuzzy_digits],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                },
            },
        ),


        dict(
            desc='Try to retrieve non-existent record %r in zone %r' % (dnsres1, dnszone1),
            command=('dnsrecord_show', [dnszone1, dnsres1], {}),
            expected=errors.NotFound(reason='DNS resource record not found'),
        ),


        dict(
            desc='Try to delete non-existent record %r in zone %r' % (dnsres1, dnszone1),
            command=('dnsrecord_del', [dnszone1, dnsres1], {'del_all' : True}),
            expected=errors.NotFound(reason='DNS resource record not found'),
        ),


        dict(
            desc='Try to delete root zone record \'@\' in %r' % (dnszone1),
            command=('dnsrecord_del', [dnszone1, u'@'], {'del_all' : True}),
            expected=errors.ValidationError(name='del_all', error=''),
        ),


        dict(
            desc='Try to create record with invalid name in zone %r' % dnszone1,
            command=('dnsrecord_add', [dnszone1, u'invalid record'], {'arecord': u'127.0.0.1'}),
            expected=errors.ValidationError(name='idnsname', error=''),
        ),


        dict(
            desc='Create record %r in zone %r' % (dnszone1, dnsres1),
            command=('dnsrecord_add', [dnszone1, dnsres1], {'arecord': u'127.0.0.1'}),
            expected={
                'value': dnsres1,
                'summary': None,
                'result': {
                    'dn': unicode(dnsres1_dn),
                    'idnsname': [dnsres1],
                    'objectclass': [u'top', u'idnsrecord'],
                    'arecord': [u'127.0.0.1'],
                },
            },
        ),


        dict(
            desc='Search for all records in zone %r' % dnszone1,
            command=('dnsrecord_find', [dnszone1], {}),
            expected={
                'summary': None,
                'count': 3,
                'truncated': False,
                'result': [
                    {
                        'dn': unicode(dnszone1_dn),
                        'nsrecord': (dnszone1_mname,),
                        'idnsname': [u'@'],
                    },
                    {
                        'dn': unicode(dnszone1_mname_dn),
                        'idnsname': [u'ns1'],
                        'arecord': [u'1.2.3.4'],
                    },
                    {
                        'dn': unicode(dnsres1_dn),
                        'idnsname': [dnsres1],
                        'arecord': [u'127.0.0.1'],
                    },
                ],
            },
        ),


        dict(
            desc='Add A record to %r in zone %r' % (dnsres1, dnszone1),
            command=('dnsrecord_add', [dnszone1, dnsres1], {'arecord': u'10.10.0.1'}),
            expected={
                'value': dnsres1,
                'summary': None,
                'result': {
                    'dn': unicode(dnsres1_dn),
                    'idnsname': [dnsres1],
                    'arecord': [u'127.0.0.1', u'10.10.0.1'],
                    'objectclass': [u'top', u'idnsrecord'],
                },
            },
        ),


        dict(
            desc='Remove A record from %r in zone %r' % (dnsres1, dnszone1),
            command=('dnsrecord_del', [dnszone1, dnsres1], {'arecord': u'127.0.0.1'}),
            expected={
                'value': dnsres1,
                'summary': None,
                'result': {
                    'idnsname': [dnsres1],
                    'arecord': [u'10.10.0.1'],
                },
            },
        ),


        dict(
            desc='Add AAAA record to %r in zone %r using dnsrecord_mod' % (dnsres1, dnszone1),
            command=('dnsrecord_mod', [dnszone1, dnsres1], {'aaaarecord': u'::1'}),
            expected={
                'value': dnsres1,
                'summary': None,
                'result': {
                    'idnsname': [dnsres1],
                    'arecord': [u'10.10.0.1'],
                    'aaaarecord': [u'::1'],
                },
            },
        ),


        dict(
            desc='Modify AAAA record in %r in zone %r' % (dnsres1, dnszone1),
            command=('dnsrecord_mod', [dnszone1, dnsres1], {'aaaarecord': u'ff02::1'}),
            expected={
                'value': dnsres1,
                'summary': None,
                'result': {
                    'idnsname': [dnsres1],
                    'arecord': [u'10.10.0.1'],
                    'aaaarecord': [u'ff02::1'],
                },
            },
        ),


        dict(
            desc='Remove AAAA record from %r in zone %r using dnsrecord_mod' % (dnsres1, dnszone1),
            command=('dnsrecord_mod', [dnszone1, dnsres1], {'aaaarecord': u''}),
            expected={
                'value': dnsres1,
                'summary': None,
                'result': {
                    'idnsname': [dnsres1],
                    'arecord': [u'10.10.0.1'],
                },
            },
        ),

        dict(
            desc='Try to add invalid MX record to zone %r using dnsrecord_add' % (dnszone1),
            command=('dnsrecord_add', [dnszone1, u'@'], {'mxrecord': dnszone1_mname }),
            expected=errors.ValidationError(name='mxrecord', error=''),
        ),

        dict(
            desc='Add MX record to zone %r using dnsrecord_add' % (dnszone1),
            command=('dnsrecord_add', [dnszone1, u'@'], {'mxrecord': u"0 %s" % dnszone1_mname }),
            expected={
                'value': u'@',
                'summary': None,
                'result': {
                    'objectclass': [u'top', u'idnsrecord', u'idnszone'],
                    'dn': unicode(dnszone1_dn),
                    'idnsname': [dnszone1],
                    'mxrecord': [u"0 %s" % dnszone1_mname],
                    'nsrecord': [dnszone1_mname],
                },
            },
        ),

        dict(
            desc='Try to add invalid SRV record to zone %r using dnsrecord_add' % (dnszone1),
            command=('dnsrecord_add', [dnszone1, u'_foo._tcp'], {'srvrecord': dnszone1_mname}),
            expected=errors.ValidationError(name='srvrecord', error=''),
        ),

        dict(
            desc='Try to add invalid SRV record via parts to zone %r using dnsrecord_add' % (dnszone1),
            command=('dnsrecord_add', [dnszone1, u'_foo._tcp'], {'srv_part_priority': 0,
                                                                 'srv_part_weight' : 0,
                                                                 'srv_part_port' : 123,
                                                                 'srv_part_target' : u'foo bar'}),
            expected=errors.ValidationError(name='srv_part_target', error=''),
        ),

        dict(
            desc='Try to add SRV record to zone %r both via parts and a raw value' % (dnszone1),
            command=('dnsrecord_add', [dnszone1, u'_foo._tcp'], {'srv_part_priority': 0,
                                                                 'srv_part_weight' : 0,
                                                                 'srv_part_port' : 123,
                                                                 'srv_part_target' : u'foo.bar.',
                                                                 'srvrecord': [u"1 100 1234 %s" \
                                                                     % dnszone1_mname]}),
            expected=errors.ValidationError(name='srv_target',
                error='Raw value of a DNS record was already set by a_rec option'),
        ),

        dict(
            desc='Add SRV record to zone %r using dnsrecord_add' % (dnszone1),
            command=('dnsrecord_add', [dnszone1, u'_foo._tcp'], {'srvrecord': u"0 100 1234 %s" % dnszone1_mname}),
            expected={
                'value': u'_foo._tcp',
                'summary': None,
                'result': {
                    'objectclass': [u'top', u'idnsrecord'],
                    'dn': unicode(DN(('idnsname', u'_foo._tcp'), dnszone1_dn)),
                    'idnsname': [u'_foo._tcp'],
                    'srvrecord': [u"0 100 1234 %s" % dnszone1_mname],
                },
            },
        ),

        dict(
            desc='Try to modify SRV record in zone %r without specifying modified value' % (dnszone1),
            command=('dnsrecord_mod', [dnszone1, u'_foo._tcp'], {'srv_part_priority': 1,}),
            expected=errors.RequirementError(name='srvrecord'),
        ),

        dict(
            desc='Try to modify SRV record in zone %r with non-existent modified value' % (dnszone1),
            command=('dnsrecord_mod', [dnszone1, u'_foo._tcp'], {'srv_part_priority': 1,
                                                  'srvrecord' : [u"0 100 1234 does.not.exist."] }),
            expected=errors.AttrValueNotFound(attr='SRV', value=u'0 100 1234 ns1.dnszone.test.'),
        ),

        dict(
            desc='Try to modify SRV record in zone %r with invalid part value' % (dnszone1),
            command=('dnsrecord_mod', [dnszone1, u'_foo._tcp'], {'srv_part_priority': 100000,
                                                  'srvrecord' : [u"0 100 1234 %s" % dnszone1_mname] }),
            expected=errors.ValidationError(name='srv_priority', error=u'can be at most 65535'),
        ),

        dict(
            desc='Modify SRV record in zone %r using parts' % (dnszone1),
            command=('dnsrecord_mod', [dnszone1, u'_foo._tcp'], {'srv_part_priority': 1,
                                                  'srvrecord' : [u"0 100 1234 %s" % dnszone1_mname] }),
            expected={
                'value': u'_foo._tcp',
                'summary': None,
                'result': {
                    'idnsname': [u'_foo._tcp'],
                    'srvrecord': [u"1 100 1234 %s" % dnszone1_mname],
                },
            },
        ),

        dict(
            desc='Try to add invalid LOC record to zone %r using dnsrecord_add' % (dnszone1),
            command=('dnsrecord_add', [dnszone1, u'@'], {'locrecord': u"91 11 42.4 N 16 36 29.6 E 227.64" }),
            expected=errors.ValidationError(name='locrecord', error=''),
        ),

        dict(
            desc='Add LOC record to zone %r using dnsrecord_add' % (dnszone1),
            command=('dnsrecord_add', [dnszone1, u'@'], {'locrecord': u"49 11 42.4 N 16 36 29.6 E 227.64" }),
            expected={
                'value': u'@',
                'summary': None,
                'result': {
                    'objectclass': [u'top', u'idnsrecord', u'idnszone'],
                    'dn': unicode(dnszone1_dn),
                    'idnsname': [dnszone1],
                    'mxrecord': [u"0 %s" % dnszone1_mname],
                    'nsrecord': [dnszone1_mname],
                    'locrecord': [u"49 11 42.400 N 16 36 29.600 E 227.64"],
                },
            },
        ),

        dict(
            desc='Try to add invalid CNAME record %r using dnsrecord_add' % (dnsres1),
            command=('dnsrecord_add', [dnszone1, dnsres1], {'cnamerecord': u'-.example.com' }),
            expected=errors.ValidationError(name='cnamerecord', error=''),
        ),

        dict(
            desc='Add CNAME record to %r using dnsrecord_add' % (dnsres1),
            command=('dnsrecord_add', [dnszone1, dnsres1], {'cnamerecord': u'foo-1.example.com.' }),
            expected={
                'value': dnsres1,
                'summary': None,
                'result': {
                    'objectclass': [u'top', u'idnsrecord'],
                    'dn': unicode(dnsres1_dn),
                    'idnsname': [dnsres1],
                    'arecord': [u'10.10.0.1'],
                    'cnamerecord': [u'foo-1.example.com.'],
                },
            },
        ),

        dict(
            desc='Try to add invalid KX record %r using dnsrecord_add' % (dnsres1),
            command=('dnsrecord_add', [dnszone1, dnsres1], {'kxrecord': u'foo-1.example.com' }),
            expected=errors.ValidationError(name='kxrecord', error=''),
        ),

        dict(
            desc='Add KX record to %r using dnsrecord_add' % (dnsres1),
            command=('dnsrecord_add', [dnszone1, dnsres1], {'kxrecord': u'1 foo-1' }),
            expected={
                'value': dnsres1,
                'summary': None,
                'result': {
                    'objectclass': [u'top', u'idnsrecord'],
                    'dn': unicode(dnsres1_dn),
                    'idnsname': [dnsres1],
                    'arecord': [u'10.10.0.1'],
                    'cnamerecord': [u'foo-1.example.com.'],
                    'kxrecord': [u'1 foo-1'],
                },
            },
        ),

        dict(
            desc='Add TXT record to %r using dnsrecord_add' % (dnsres1),
            command=('dnsrecord_add', [dnszone1, dnsres1], {'txtrecord': u'foo bar' }),
            expected={
                'value': dnsres1,
                'summary': None,
                'result': {
                    'objectclass': [u'top', u'idnsrecord'],
                    'dn': unicode(dnsres1_dn),
                    'idnsname': [dnsres1],
                    'arecord': [u'10.10.0.1'],
                    'cnamerecord': [u'foo-1.example.com.'],
                    'kxrecord': [u'1 foo-1'],
                    'txtrecord': [u'foo bar'],
                },
            },
        ),

        dict(
            desc='Add NSEC record to %r using dnsrecord_add' % (dnsres1),
            command=('dnsrecord_add', [dnszone1, dnsres1], {
                'nsec_part_next': dnszone1,
                'nsec_part_types' : [u'TXT', u'A']}),
            expected={
                'value': dnsres1,
                'summary': None,
                'result': {
                    'objectclass': [u'top', u'idnsrecord'],
                    'dn': unicode(dnsres1_dn),
                    'idnsname': [dnsres1],
                    'arecord': [u'10.10.0.1'],
                    'cnamerecord': [u'foo-1.example.com.'],
                    'kxrecord': [u'1 foo-1'],
                    'txtrecord': [u'foo bar'],
                    'nsecrecord': [dnszone1 + u' TXT A'],
                },
            },
        ),

        dict(
            desc='Try to add unresolvable NS record to %r using dnsrecord_add' % (dnsres1),
            command=('dnsrecord_add', [dnszone1, dnsres1], {'nsrecord': u'does.not.exist'}),
            expected=errors.NotFound(reason=u"Nameserver 'does.not.exist' does not have a corresponding A/AAAA record"),
        ),

        dict(
            desc='Add unresolvable NS record with --force to %r using dnsrecord_add' % (dnsres1),
            command=('dnsrecord_add', [dnszone1, dnsres1], {'nsrecord': u'does.not.exist',
                                                            'force' : True}),
            expected={
                'value': dnsres1,
                'summary': None,
                'result': {
                    'objectclass': [u'top', u'idnsrecord'],
                    'dn': unicode(dnsres1_dn),
                    'idnsname': [dnsres1],
                    'arecord': [u'10.10.0.1'],
                    'cnamerecord': [u'foo-1.example.com.'],
                    'kxrecord': [u'1 foo-1'],
                    'txtrecord': [u'foo bar'],
                    'nsecrecord': [dnszone1 + u' TXT A'],
                    'nsrecord': [u'does.not.exist'],
                },
            },
        ),

        dict(
            desc='Delete record %r in zone %r' % (dnsres1, dnszone1),
            command=('dnsrecord_del', [dnszone1, dnsres1], {'del_all': True }),
            expected={
                'value': dnsres1,
                'summary': u'Deleted record "%s"' % dnsres1,
                'result': {'failed': u''},
            },
        ),


        dict(
            desc='Try to create a reverse zone from invalid IP',
            command=(
                'dnszone_add', [], {
                    'name_from_ip': u'foo',
                    'idnssoamname': dnszone1_mname,
                    'idnssoarname': dnszone1_rname,
                    'ip_address' : u'1.2.3.4',
                }
            ),
            expected=errors.ValidationError(name='name_from_ip', error='invalid format'),
        ),

        dict(
            desc='Create reverse from IP %s zone using name_from_ip option' % revdnszone1_ip,
            command=(
                'dnszone_add', [], {
                    'name_from_ip': revdnszone1_ip,
                    'idnssoamname': dnszone1_mname,
                    'idnssoarname': dnszone1_rname,
                    'ip_address' : u'1.2.3.4',
                }
            ),
            expected={
                'value': revdnszone1,
                'summary': None,
                'result': {
                    'dn': unicode(revdnszone1_dn),
                    'idnsname': [revdnszone1],
                    'idnszoneactive': [u'TRUE'],
                    'idnssoamname': [dnszone1_mname],
                    'nsrecord': [dnszone1_mname],
                    'idnssoarname': [dnszone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [fuzzy_digits],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowdynupdate': [u'FALSE'],
                    'idnsallowtransfer': [u'none;'],
                    'idnsallowquery': [u'any;'],
                    'objectclass': [u'top', u'idnsrecord', u'idnszone'],
                },
            },
        ),


        dict(
            desc='Try to add invalid PTR %r to %r using dnsrecord_add' % (dnsrev1, revdnszone1),
            command=('dnsrecord_add', [revdnszone1, dnsrev1], {'ptrrecord': u'-.example.com' }),
            expected=errors.ValidationError(name='ptrrecord', error=''),
        ),

        dict(
            desc='Add PTR record %r to %r using dnsrecord_add' % (dnsrev1, revdnszone1),
            command=('dnsrecord_add', [revdnszone1, dnsrev1], {'ptrrecord': u'foo-1.example.com' }),
            expected={
                'value': dnsrev1,
                'summary': None,
                'result': {
                    'objectclass': [u'top', u'idnsrecord'],
                    'dn': unicode(dnsrev1_dn),
                    'idnsname': [dnsrev1],
                    'ptrrecord': [u'foo-1.example.com.'],
                },
            },
        ),


        dict(
            desc='Update global DNS settings',
            command=('dnsconfig_mod', [], {'idnsforwarders' : [u'80.142.15.80'],}),
            expected={
                'value': u'',
                'summary': None,
                'result': {
                    'idnsforwarders': [u'80.142.15.80'],
                },
            },
        ),


        dict(
            desc='Try to add invalid allow-query to zone %r' % dnszone1,
            command=('dnszone_mod', [dnszone1], {'idnsallowquery': u'localhost'}),
            expected=errors.ValidationError(name='idnsallowquery', error=''),
        ),

        dict(
            desc='Add allow-query ACL to zone %r' % dnszone1,
            command=('dnszone_mod', [dnszone1], {'idnsallowquery': u'!10/8;any'}),
            expected={
                'value': dnszone1,
                'summary': None,
                'result': {
                    'idnsname': [dnszone1],
                    'idnszoneactive': [u'TRUE'],
                    'nsrecord': [dnszone1_mname],
                    'mxrecord': [u'0 ns1.dnszone.test.'],
                    'locrecord': [u"49 11 42.400 N 16 36 29.600 E 227.64"],
                    'idnssoamname': [dnszone1_mname],
                    'idnssoarname': [dnszone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [u'5478'],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowquery': [u'!10.0.0.0/8;any;'],
                    'idnsallowtransfer': [u'none;'],
                },
            },
        ),


        dict(
            desc='Try to add invalid allow-transfer to zone %r' % dnszone1,
            command=('dnszone_mod', [dnszone1], {'idnsallowtransfer': u'10.'}),
            expected=errors.ValidationError(name='idnsallowtransfer', error=''),
        ),

        dict(
            desc='Add allow-transer ACL to zone %r' % dnszone1,
            command=('dnszone_mod', [dnszone1], {'idnsallowtransfer': u'80.142.15.80'}),
            expected={
                'value': dnszone1,
                'summary': None,
                'result': {
                    'idnsname': [dnszone1],
                    'idnszoneactive': [u'TRUE'],
                    'nsrecord': [dnszone1_mname],
                    'mxrecord': [u'0 ns1.dnszone.test.'],
                    'locrecord': [u"49 11 42.400 N 16 36 29.600 E 227.64"],
                    'idnssoamname': [dnszone1_mname],
                    'idnssoarname': [dnszone1_rname],
                    'idnssoaserial': [fuzzy_digits],
                    'idnssoarefresh': [u'5478'],
                    'idnssoaretry': [fuzzy_digits],
                    'idnssoaexpire': [fuzzy_digits],
                    'idnssoaminimum': [fuzzy_digits],
                    'idnsallowquery': [u'!10.0.0.0/8;any;'],
                    'idnsallowtransfer': [u'80.142.15.80;'],
                },
            },
        ),


        dict(
            desc='Try to create duplicate PTR record for %r with --a-create-reverse' % dnsres1,
            command=('dnsrecord_add', [dnszone1, dnsres1], {'arecord': u'80.142.15.80',
                                                            'a_extra_create_reverse' : True}),
            expected=errors.DuplicateEntry(message=u''),
        ),


        dict(
            desc='Create A record %r in zone %r with --a-create-reverse' % (dnsres1, dnszone1),
            command=('dnsrecord_add', [dnszone1, dnsres1], {'arecord': u'80.142.15.81',
                                                            'a_extra_create_reverse' : True}),
            expected={
                'value': dnsres1,
                'summary': None,
                'result': {
                    'dn': unicode(dnsres1_dn),
                    'idnsname': [dnsres1],
                    'objectclass': [u'top', u'idnsrecord'],
                    'arecord': [u'80.142.15.81'],
                },
            },
        ),


        dict(
            desc='Check reverse record for %r created via --a-create-reverse' % dnsres1,
            command=('dnsrecord_show', [revdnszone1, dnsrev2], {}),
            expected={
                'value': dnsrev2,
                'summary': None,
                'result': {
                    'dn': unicode(dnsrev2_dn),
                    'idnsname': [dnsrev2],
                    'ptrrecord': [dnsres1 + '.' + dnszone1 + '.'],
                },
            },
        ),


        dict(
            desc='Delete zone %r' % dnszone1,
            command=('dnszone_del', [dnszone1], {}),
            expected={
                'value': dnszone1,
                'summary': None,
                'result': {'failed': u''},
            },
        ),

    ]

