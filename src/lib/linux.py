#
# (c)2019 Octosoft AG, CH-6312 Steinhausen, Switzerland
# This code is licensed under the MIT license see LICENSE.txt
#

from __future__ import print_function

import os
import platform
import glob

if 'linux' in platform.system().lower():
    # noinspection PyUnresolvedReferences
    import pwd


# noinspection PyCompatibility
def read_hyperv_parameters():
    kvp_file = "/var/lib/hyperv/.kvp_pool_3"
    params = {}
    if os.path.exists(kvp_file):
        strip = ' \r\n\t\0'
        with open(kvp_file, "rb") as f:
            key = str(f.read(512)).rstrip(strip)
            val = str(f.read(2048)).rstrip(strip)
            if len(key):
                params[key] = val
            while len(val):
                key = str(f.read(512)).rstrip(strip)
                val = str(f.read(2048)).rstrip(strip)
                if len(key):
                    params[key] = val
    return params


# noinspection PyUnusedLocal
def scan_linux_user(scan, options):
    user_elem = scan.create_element("user")
    scan.append_info_element(user_elem, "user_id", "I", str(os.getuid()))
    # noinspection PyBroadException
    try:
        scan.append_info_element(user_elem, "login", "S", os.getlogin())
    except Exception:
        scan.append_info_element(user_elem, "login", "S", pwd.getpwuid(os.getuid())[0])
    scan.append_child(user_elem)


# noinspection PyUnusedLocal
def scan_linux(scan, options):
    """
    Linux scan
    :param options:
    :param scan:
    :return:
    """
    # deprecated in python 3.8 -> distro package
    (distribution, version, distribution_id) = platform.linux_distribution()

    try:
        scan_linux_user(scan, options)
    except Exception as e:
        scan.queue_warning(2001, "scan_linux_user failed:" + repr(e))

    os_elem = scan.create_element("operating_system")
    scan.append_info_element(os_elem, "distribution", "S", distribution)
    scan.append_info_element(os_elem, "version", "S", version)
    scan.append_info_element(os_elem, "id", "S", distribution_id)
    scan.append_info_element(os_elem, "platform", "S", platform.platform())
    scan.append_child(os_elem)

    # collect various _release info files. if systemctl standard os_release is present this
    # will get parsed on import, otherwise some heuristics will be applied on all available release files
    for release_info in glob.glob1("/etc", "*-release"):
        scan.add_file(os.path.join("/etc", release_info), os.path.join("release", release_info))

    # collect debian_version if it exists
    for release_info in glob.glob1("/etc", "*_version"):
        scan.add_file(os.path.join("/etc", release_info), os.path.join("release", release_info))

    for proc_file in ["cpuinfo", "meminfo", "scsi/scsi", "version", "version_signature"]:
        scan.add_file(os.path.join("/proc", proc_file), os.path.join("proc/", proc_file))

    scan.add_folder("/sys/class/dmi/id", "sys/class/dmi/id")

    for oratab in ["/etc/oratab", "/var/opt/oracle/oratab"]:
        if os.path.exists(oratab):
            scan.add_file(oratab, "oracle/oratab")
            break

    if scan.command_exists("dpkg-query"):
        scan.add_command_output(["dpkg-query", "-W", "-f",
                                 '${Package}\t${Version}\t${Architecture}\t${binary:Summary}\n'],
                                "dpkg/installed.txt")
    else:
        scan.add_command_output(["rpm", "-qa", "--queryformat",
                                 '%{name}\t%{version}\t%{release}\t%{arch}\t%{summary}\t%{installtime}\n'],
                                "rpm/installed.txt")

    scan.add_command_output(["ip", "addr"], "cmd/ip_addr")
    scan.add_command_output(["ps", "-ef"], "cmd/ps_ef")
    scan.add_command_output(["hostnamectl", "status"], "cmd/hostnamectl")
    # TODO: test/debug on SLES11
    # scan.add_command_output(["service", "--status-all"], "cmd/service_status_all")
    scan.add_command_output(["systemctl", "list-units", "-all", "--no-page"], "cmd/systemctl_units_all")

    params = read_hyperv_parameters()
    if len(params):
        hyper_elem = scan.create_element("hypervisor")
        scan.append_info_element(hyper_elem, "Type", "S", "Hyper-V")
        for k in params.keys():
            scan.append_info_element(hyper_elem, k, "S", params[k])
        scan.append_child(hyper_elem)
