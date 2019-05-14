#
# (c)2019 Octosoft AG, CH-6312 Steinhausen, Switzerland
# This code is licensed under the MIT license see LICENSE.txt
#

from __future__ import print_function

import os
import subprocess
import platform

if 'darwin' in platform.system().lower():
    # noinspection PyUnresolvedReferences
    from SystemConfiguration import SCDynamicStoreCreate, SCDynamicStoreCopyValue


# noinspection PyUnusedLocal
def scan_darwin(scan, options):
    """
    Darwin scan
    :param options:
    :param scan:
    :return:
    """

    scan.add_command_output(
        [
            "/usr/sbin/system_profiler",
            "-xml",
            "SPApplicationsDataType",
            "SPSoftwareDataType",
            "SPMemoryDataType",
            "SPHardwareDataType",
            "SPDiagnosticsDataType",
            "SPDisplaysDataType",
            "SPDiscBurningDataType",
            "SPEthernetDataType",
            "SPPrintersDataType",
            "SPNetworkDataType",
            "SPSerialATADataType"
        ], "system_profiler.xml"
    )

    # active directory information for macs joined to AD (if avaliable)
    dynamic_store = SCDynamicStoreCreate(None, "net", None, None)

    stores = {"com.apple.opendirectoryd.ActiveDirectory": "active_directory",
              "State:/Network/NetBIOS": "netbios",
              "com.apple.smb": "smb"
              }

    for store in stores.keys():
        sc = SCDynamicStoreCopyValue(dynamic_store, store)
        if sc:
            elem = scan.create_element(stores[store])
            for key in sc:
                # noinspection PyCompatibility
                scan.append_info_element(elem, key, "S", unicode(sc[key]))
            scan.append_child(elem)

    # add os level user information
    user_elem = scan.create_element('user')
    scan.append_info_element(user_elem, 'login', 'S', os.getlogin())
    scan.append_info_element(user_elem, 'user_id', 'I', str(os.getuid()))

    # simplistic test to see if the user is Kerberos (Active Directory) enabled
    # this needs to be more elaborate in scenarios with multiple directories
    # multiple domains etc.

    try:

        authority = subprocess.check_output(
            [
                "/usr/bin/dscl",
                ".",
                "read",
                "/Users/" + os.getlogin(),
                "AuthenticationAuthority",
            ], stderr=subprocess.STDOUT
        )

        if 'Kerberosv5' in authority:
            scan.append_info_element(user_elem, 'kerberos', 'B', 'true')

    except subprocess.CalledProcessError as e:
        pass

    scan.append_child(user_elem)

    if scan.command_exists('brew'):
        scan.add_command_output(['brew', 'info', '--json=v1', '--installed'], 'cmd/brew.json')
