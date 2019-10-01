#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set sw=4 expandtab:
#
# Created: 2019-08-06
# Main authors:
#     - Marc Dorval <marc.dorval@silabs.com>
#
# Copyright (c) 2019, Silicon Laboratories
# See license terms contained in COPYING file
#

# Generate PTA bytes from input parameters
#

from __future__ import print_function

# If you modify this file, please don't forget to increment version number.
__version__ = "0.1"

import sys
import argparse


class PtaSettings(object):
    def __init__(self):
        super().__init__()
        self.pta_cmd = None


class WfxPtaData(object):

    settings_parameters = [
        #  Parameter, type, bytes, choices, default, help
        ('Config', str, 1, ['3W_NOT_COMBINED_BLE', '3W_COMBINED_BLE', '3W_NOT_COMBINED_ZIGBEE', '3W_COMBINED_ZIGBEE'],
         None, """
              Preset configurations for common use cases
                  (presets required non-default 'settings' options,
                  these can then be overwritten using options listed below)"""),
        ('PtaMode', str, 1, {'1W_WLAN_MASTER': 0, '1W_COEX_MASTER': 1, '2W': 2, '3W': 3, '4W': 4}, '1W_WLAN_MASTER', """
              PTA mode selection"""),
        ('RequestSignalActiveLevel', str, 1, {'LOW': 0, 'HIGH':  1}, 'HIGH', """
              Active level on REQUEST signal, provided by Coex to request the RF"""),
        ('PrioritySignalActiveLevel', str, 1, {'LOW': 0, 'HIGH':  1}, 'HIGH', """
              Active level on PRIORITY signal, provided by Coex to set the priority of the request"""),
        ('FreqSignalActiveLevel', str, 1, {'LOW': 0, 'HIGH':  1}, 'HIGH', """
              Active level on FREQ signal, provided by Coex in 4-wire mode 
              when Coex and Wlan share the same band"""),
        ('GrantSignalActiveLevel', str, 1, {'LOW': 0, 'HIGH':  1}, 'LOW', """
              Active level on GRANT signal, generated by PTA 
              to grant the RF to Coex"""),
        ('CoexType', str, 1, {'GENERIC': 0, 'BLE': 1}, 'GENERIC', """
              Coex type"""),
        ('DefaultGrantState', str, 1, {'NO_GRANT': 0, 'GRANT': 1}, 'GRANT', """
              State of the GRANT signal before arbitration at GrantValidTime"""),
        ('SimultaneousRxAccesses', str, 1, {'FALSE': 0, 'TRUE': 1}, 'FALSE', """
          (uint8),  Boolean to allow both Coex and Wlan to receive concurrently, 
              also named combined mode"""),
        ('PrioritySamplingTime', int, 1, None, 9, """
          (uint8),  Time in microseconds from the Coex request to the sampling of the
          priority on PRIORITY signal (1 to 31),"""),
        ('TxRxSamplingTime', int, 1, None, 50, """
          (uint8),  Time in microseconds from the Coex request to the 
              sampling of the directionality on PRIORITY signal (PrioritySamplingTime to 63)"""),
        ('FreqSamplingTime', int, 1, None, 70, """
          (uint8),  Time in microseconds from the Coex request to the 
              sampling of the freq-match information on FREQ signal (1 to 127)"""),
        ('GrantValidTime', int, 1, None, 72, """
          (uint8),  Time in microseconds from Coex request to the 
              GRANT signal assertion (max(TxRxSamplingTime, FreqSamplingTime), to 0xFF),"""),
        ('FemControlTime', int, 1, None, 140, """
          (uint8),  Time in microseconds from Coex request to the 
              control of FEM (GrantValidTime to 0xFF),"""),
        ('FirstSlotTime', int, 1, None, 150, """
          (uint8),  Time in microseconds from the Coex request to the 
              beginning of reception or transmission (GrantValidTime to 0xFF),"""),
        ('PeriodicTxRxSamplingTime', int, 2, None, 1, """
          (uint16), Period in microseconds from FirstSlotTime of following samplings of the 
              directionality on PRIORITY signal (1 to 1023),"""),
        ('CoexQuota', int, 2, None, 0, """
          (uint16), Duration in microseconds for which RF is granted to Coex 
              before it is moved to Wlan"""),
        ('WlanQuota', int, 2, None, 0, """
          (uint16), Duration in microseconds for which RF is granted to Wlan 
              before it is moved to Coex""")
    ]

    priority_parameters = [
        #  Parameter, type, bytes,  choices, default, help
        ('PriorityMode', str, 4, {'COEX_MAXIMIZED': 0x0562, 'COEX_HIGH':0x0462, 'BALANCED':0x1461, 'WLAN_HIGH':0x1851, 'WLAN_MAXIMIZED': 0x1A51}, None, """
            COEX_MAXIMIZED = 0x0562 : Maximizes priority to COEX, WLAN connection is not ensured.  
            COEX_HIGH      = 0x0462 : High priority to COEX, targets low-latency to COEX. 
            BALANCED       = 0x1461 : Balanced PTA arbitration, WLAN acknowledge receptions are protected. 
            WLAN_HIGH      = 0x1851 : High priority to WLAN, protects WLAN transmissions. 
            WLAN_MAXIMIZED = 0x1A51 : Maximizes priority to WLAN""")
    ]

    state_parameters = [
        #  Parameter, type, bytes,  choices, default, help
        ('State', str, 4, {'ON': 0, 'OFF': 1}, 'OFF', """
            PTA state on/off""")
    ]

    def __init__(self, mode=None, **kwargs):
        self.g_settings = PtaSettings
        self.g_settings.pta_cmd = None
        self.sysargs = sys.argv[1:]
        self.mode = mode if mode else 'quiet'

    def set_args(self, args=None):
        if args is not None:
            self.sysargs = args.split(' ')
        else:
            self.sysargs = []

    def print_if_verbose(self, txt, end=None):
        if self.mode == 'verbose':
            print(txt, end=end)

    def data(self):
        self.print_if_verbose(self.sysargs)
        self.g_settings = PtaSettings
        self.g_settings.pta_cmd = None
        user_options = self.parse_cmdline(self, self.sysargs)
        # self.print_if_verbose(user_options)
        self.apply_options(self, user_options)
        return self.pta_bytes()

    @staticmethod
    def print_keys(self, c, name=None):
        for k in c.__dict__.keys():
            if '__' not in k:
                if name is None:
                    self.print_if_verbose("%-30s %s" % (k, c.__dict__[k]))
                else:
                    self.print_if_verbose("%s.%-30s %s" % (name, k, c.__dict__[k]))

    @staticmethod
    def parse_cmdline(self, args):
        parser = argparse.ArgumentParser(usage="%(prog)s <settings/priority/state> [options]...",
                                         formatter_class=argparse.RawDescriptionHelpFormatter,
                                         description="""
        Prepare and send PTA parameters depending on the selected pta_cmd
        """, epilog="""
        Examples:
        python wfx_pta.py settings --Config 3W_COMBINED_BLE
        python wfx_pta.py settings --Config 3W_NOT_COMBINED_BLE --FirstSlotTime 123
        python wfx_pta.py settings --Config 3W_NOT_COMBINED_BLE --FirstSlotTime 123 --PrioritySamplingTime 12
        python wfx_pta.py priority --PriorityMode BALANCED
        python wfx_pta.py state --State ON
        python wfx_pta.py state --State OFF
        """)
        parser.add_argument("pta_cmd", choices=['settings', 'priority', 'state'],
                            help="pta_cmd <settings/priority/state>")
        parser.add_argument('--version', action='version',
                            version='%(prog)s {version}'.format(version=__version__))

        parser_settings = parser.add_argument_group('settings options')
        for item in self.settings_parameters:
            _name, _type, _bytes, _choices, _default, _help = item
            if _default is None:
                parser_settings.add_argument('--' + _name, type=_type, default=_default, choices=_choices, help=_help)
            else:
                parser_settings.add_argument('--' + _name, type=_type, default=_default, choices=_choices, help=_help +
                                             ' (default ' + str(_default) + ')')

        parser_priority = parser.add_argument_group('priority options')
        for item in self.priority_parameters:
            _name, _type, _bytes, _choices, _default, _help = item
            parser_priority.add_argument('--' + _name, type=_type, default=_default, choices=_choices, help=_help)

        parser_state = parser.add_argument_group('state options')
        for item in self.state_parameters:
            _name, _type, _bytes, _choices, _default, _help = item
            parser_state.add_argument('--' + _name, type=_type, default=_default, choices=_choices, help=_help)

        return parser.parse_args(args)

    @staticmethod
    def settings_by_config(self, config):

        if config == '3W_COMBINED_ZIGBEE':
            self.print_if_verbose('Configuring for %s' % config)
            self.g_settings.PtaMode = '3W'
            self.g_settings.CoexType = 'GENERIC'
            self.g_settings.SimultaneousRxAccesses = 'TRUE'
            self.g_settings.PrioritySamplingTime = 10
            self.g_settings.TxRxSamplingTime = 30
            self.g_settings.GrantValidTime = 40
            self.g_settings.FemControlTime = 40
            self.g_settings.FirstSlotTime = 40

        if config == '3W_NOT_COMBINED_ZIGBEE':
            self.print_if_verbose('Configuring for %s' % config)
            self.g_settings.PtaMode = '3W'
            self.g_settings.CoexType = 'GENERIC'
            self.g_settings.SimultaneousRxAccesses = 'FALSE'
            self.g_settings.PrioritySamplingTime = 10
            self.g_settings.GrantValidTime = 20
            self.g_settings.FemControlTime = 20

        if config == '3W_COMBINED_BLE':
            self.print_if_verbose('Configuring for %s' % config)
            self.g_settings.PtaMode = '3W'
            self.g_settings.CoexType = 'BLE'
            self.g_settings.SimultaneousRxAccesses = 'TRUE'
            self.g_settings.PrioritySamplingTime = 10

        if config == '3W_NOT_COMBINED_BLE':
            self.print_if_verbose('Configuring for %s' % config)
            self.g_settings.PtaMode = '3W'
            self.g_settings.CoexType = 'BLE'
            self.g_settings.SimultaneousRxAccesses = 'FALSE'
            self.g_settings.PrioritySamplingTime = 10

    @staticmethod
    def apply_options(self, options):
        # filling defaults and self.g_settings with default values
        defaults = self.parse_cmdline(self, args=['settings'])
        self.g_settings = self.parse_cmdline(self, args=['settings'])
        if options.Config is not None:
            self.settings_by_config(self, options.Config)
            # Tracing modified values after applying Config
            for k in self.g_settings.__dict__.keys():
                if '__' not in k:
                    config_value = self.g_settings.__dict__[k]
                    default_value = defaults.__dict__[k]
                    if config_value != default_value:
                        self.print_if_verbose("%-30s %8s => %8s" % (k, default_value, config_value))
        self.g_settings.pta_cmd = options.pta_cmd
        if options.pta_cmd == 'priority':
            self.g_settings.PriorityMode = options.PriorityMode
        if options.pta_cmd == 'state':
            self.g_settings.State = options.State
        # Applying user 'settings' options on top of current settings
        for k in options.__dict__.keys():
            if '__' not in k and k != 'Config':
                user_value = options.__dict__[k]
                default_value = defaults.__dict__[k]
                config_value = self.g_settings.__dict__[k]
                if user_value != default_value:
                    if config_value != user_value:
                        self.print_if_verbose("%-30s %8s -> %8s" % (k, config_value, user_value))
                        self.g_settings.__dict__[k] = user_value

    def pta_bytes(self):
        header = []
        payload = list()
        nb_bytes = 4
        cmd_id = 0
        # self.print_if_verbose("PTA command: %s" % self.g_settings.pta_cmd)
        if self.g_settings.pta_cmd == 'settings':
            cmd_id = 0x002b
            for item in self.settings_parameters:
                _name, _type, _bytes, _choices, _default, _help = item
                if _name != 'Config':
                    item_value = self.g_settings.__dict__[_name]
                    if str(item_value).isnumeric():
                        int_value = int(item_value)
                    else:
                        int_value = int(_choices[item_value])
                    if _bytes == 1:
                        payload.append(str.format(r"\x%02x" % (int_value & 0x00FF)))
                    if _bytes == 2:
                        payload.append(str.format(r"\x%02x" % (int_value & 0x00FF)))
                        payload.append(str.format(r"\x%02x" % int((int_value & 0xFF00) >> 8)))
                    self.print_if_verbose(str.format("%-30s %-10s " % (_name, item_value)), end='')
                    self.print_if_verbose(''.join(payload[(nb_bytes-4):]))
                    nb_bytes += _bytes
        if self.g_settings.pta_cmd == 'priority':
            cmd_id = 0x002c
            for item in self.priority_parameters:
                _name, _type, _bytes, _choices, _default, _help = item
                item_value = self.g_settings.__dict__[_name]
                if str(item_value).isnumeric():
                    int_value = int(item_value)
                else:
                    int_value = int(_choices[item_value])
                payload.append(str.format(r"\x%02x" % ((int_value & 0x000000FF) >> 0)))
                payload.append(str.format(r"\x%02x" % ((int_value & 0x0000FF00) >> 8)))
                payload.append(str.format(r"\x%02x" % ((int_value & 0x00FF0000) >> 16)))
                payload.append(str.format(r"\x%02x" % ((int_value & 0xFF000000) >> 24)))
                self.print_if_verbose(str.format("%-30s %-10s " % (_name, item_value)), end='')
                self.print_if_verbose(''.join(payload[(nb_bytes - 4):]))
                nb_bytes += _bytes
        if self.g_settings.pta_cmd == 'state':
            cmd_id = 0x002d
            for item in self.state_parameters:
                _name, _type, _bytes, _choices, _default, _help = item
                item_value = self.g_settings.__dict__[_name]
                if str(item_value).isnumeric():
                    int_value = int(item_value)
                else:
                    int_value = int(_choices[item_value])
                payload.append(str.format(r"\x%02x" % ((int_value & 0x000000FF) >> 0)))
                payload.append(str.format(r"\x%02x" % ((int_value & 0x0000FF00) >> 8)))
                payload.append(str.format(r"\x%02x" % ((int_value & 0x00FF0000) >> 16)))
                payload.append(str.format(r"\x%02x" % ((int_value & 0xFF000000) >> 24)))
                self.print_if_verbose(str.format("%-30s %-10s " % (_name, item_value)), end='')
                self.print_if_verbose(''.join(payload[(nb_bytes-4):]))
                nb_bytes += _bytes
        header.append(str.format(r"\x%02x" % int(nb_bytes & 0x00FF)))
        header.append(str.format(r"\x%02x" % int(nb_bytes & 0xFF00)))
        header.append(str.format(r"\x%02x" % int(cmd_id & 0x00FF)))
        header.append(str.format(r"\x%02x" % int(cmd_id & 0xFF00)))
        data_bytes = r''.join(header + payload)
        return data_bytes


if __name__ == '__main__':
    sys.exit(WfxPtaData().data())
