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
def scan_linux_memory_size(scan, options):
    """
    Try to find out the real physical memory size. dmidecode needs root, proc/meminfo does not show the real
    physical memory.
    :param scan:
    :param options:
    :return:
    """
    # noinspection PyBroadException
    try:
        if os.path.exists("/sys/devices/system/memory/block_size_bytes"):
            with open("/sys/devices/system/memory/block_size_bytes") as f:
                block = str(f.read()).strip()
                block_size = int(block, 16)

            total_memory_bytes = 0

            for m in glob.glob("/sys/devices/system/memory/memory*"):
                with open(os.path.join(m, "online")) as f:
                    online = str(f.read()).strip()
                    if online == "1":
                        total_memory_bytes = total_memory_bytes + block_size
            scan.add_str(str(total_memory_bytes) + "\n", "sys/devices/system/memory/octoscan_total_memory")
    except Exception as e:
        pass


# noinspection PyUnusedLocal
def scan_linux_java(scan, options):
    """
    get running java processes and dump their version info
    :param scan:
    :param options:
    :return:
    """

    features = []
    # find global usage tracker

    if os.path.exists("/etc/oracle/java/usagetracker.properties"):
        features.append("JavaFeatureUsageTrackerGlobal")

    # noinspection PyBroadException
    try:
        default_java = scan.check_output(["which", "java"])
        default_java = default_java.strip()
        if len(default_java):
            scan.add_java_version(default_java.strip(), "java/static/default_java/version", features)
    except Exception as e:
        pass

    try:
        java_home = os.environ["JAVA_HOME"]
        scan.add_java_version(os.path.join(java_home, "bin", "java"), "java/static/java_home/version", features)
    except KeyError as e:
        pass

    # noinspection PyBroadException

    locations = [
        "/opt",
        "/usr/lib",
        "/usr/java"
    ]

    if len(options.java_locations) > 0:
        for loc in options.java_locations.split(":"):
            if os.path.exists(loc):
                locations.append(loc)

    find_command = ["/usr/bin/find"]

    for loc in locations:
        if os.path.exists(loc):
            find_command.append(loc)

    # exclude /proc /sys /run /dev and non readable folders
    # this is to make sure we do not recurse in there when the user specifies "/" to scan (not recommended anyway)

    find_command.extend([
        "(", "-path", "/dev", "-o",
        "-path", "/proc", "-o",
        "-path", "/run", "-o",
        "-path", "/sys", "-o",
        "!", "-readable", ")",
        "-prune",
        "-o", "-type", "f",
        "-executable", "-name", "java",
        "-print"
    ])

    # noinspection PyBroadException
    try:
        opt_java = scan.check_output(find_command)
        i = 0
        for l in opt_java.strip().split('\n'):
            i = i + 1
            scan.add_java_version(l.strip(), "java/static/opt_" + str(i) + "/version", features)
    except Exception as ex:
        pass

    if os.geteuid() == 0 or options.sudo:
        output = scan.check_output(["ps", "-e", "-o", "pid,comm"])
    else:
        user = os.getlogin()
        output = scan.check_output(["ps", "-u", user, "-o", "pid,comm"])

    for l in output.split('\n'):
        token = l.strip().split(' ')
        if len(token) > 1:
            pid = token[0]
            cmd = token[1].lower()
            if cmd == "java":
                try:
                    path = scan.readlink(os.path.join("/proc", pid, "exe"))
                    if len(path) > 0:
                        scan.add_java_version(path, "java/dynamic/" + pid + "/version", features)
                        scan.add_file(os.path.join("/proc", pid, "cmdline"), "java/dynamic/" + pid + "/cmdline")
                        scan.add_file(os.path.join("/proc", pid, "environ"), "java/dynamic/" + pid + "/environ")
                except Exception as e:
                    scan.queue_warning(2002, "cannot readlink proc/" + pid + "/exe: " + str(e))


# noinspection PyUnusedLocal,DuplicatedCode
def scan_linux(scan, options):
    """
    Linux scan
    :param options:
    :param scan:
    :return:
    """
    # deprecated in python 3.8 -> distro package
    # noinspection PyDeprecation
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
        f = os.path.join("/proc", proc_file)
        if os.path.exists(f):
            scan.add_file(f, os.path.join("proc/", proc_file))

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

    scan_linux_memory_size(scan, options)

    scan_linux_java(scan, options)
