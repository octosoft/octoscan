#
# (c)2019 Octosoft AG, CH-6312 Steinhausen, Switzerland
# This code is licensed under the MIT license see LICENSE.txt
#

from __future__ import print_function
import platform


# noinspection PyUnusedLocal,DuplicatedCode
def scan_windows(scan, options):
    """
    Windows scan is for development and module test only, files cannot be imported
    """
    (distribution, version, distribution_id) = ("Windows", "unknown", "unknown")

    os_elem = scan.create_element("operating_system")
    scan.append_info_element(os_elem, "distribution", "S", distribution)
    scan.append_info_element(os_elem, "version", "S", version)
    scan.append_info_element(os_elem, "id", "S", distribution_id)
    scan.append_info_element(os_elem, "platform", "S", platform.platform())
    scan.append_child(os_elem)
    scan.add_command_output(["ipconfig.exe"], "cmd/ipconfig.txt")
