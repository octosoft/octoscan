#
# (c)2019-2023 Octosoft AG, CH-6312 Steinhausen, Switzerland
# This code is licensed under the MIT license see LICENSE.txt
#

from __future__ import print_function

import os
import platform
import glob
import subprocess

if 'linux' in platform.system().lower():
    # noinspection PyUnresolvedReferences
    import pwd


# noinspection PyUnusedLocal
def scan_linux_user(scan, options):
    user_elem = scan.create_element("user")
    scan.append_info_element(user_elem, "user_id", "I", str(os.getuid()))
    scan.append_info_element(user_elem, "effective_user_id", "I", str(os.geteuid()))
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
        "/usr/lib64"
        "/usr/java",
    ]

    if len(options.java_locations) > 0:
        for loc in options.java_locations.split(":"):
            if os.path.exists(loc):
                locations.append(loc)

    find_command = ["/usr/bin/find"]

    for loc in locations:
        if os.path.exists(loc):
            find_command.append(loc)

    # exclude /proc /sys /run /dev /etc and non-readable folders
    # this is to make sure we do not recurse in there when the user specifies "/" to scan (not recommended anyway)
    #
    # a special case is when the java command is a link for example ibm java links the java command from bin/java to
    # jre/bin/java. if we would only consider real files, we could not find the jdk installation with our trivial

    # alpine linux uses BusyBox, the find command is much less powerful
    # this implies that starting octoscan under another user than root is not supported

    if os.path.exists("/etc/alpine-release"):

        find_command.extend([
            "-executable", "-type", "f", "-name", "java",
            "-print"
        ])

    else:
        find_command.extend([
            "(", "-path", "/dev", "-o",
            "-path", "/proc", "-o",
            "-path", "/run", "-o",
            "-path", "/sys", "-o",
            "-path", "/etc", "-o",
            "!", "-readable", ")",
            "-prune",
            "-o", "(", "(", "-type", "f", "-o", "-type", "l", ")",
            "-executable", "-name", "java",
            ")",
            "-print"
        ])

    # noinspection PyBroadException
    try:
        opt_java = subprocess.check_output(find_command).decode(encoding='utf-8')
        i = 0
        for line in sorted(set(opt_java.strip().split('\n'))):
            i = i + 1
            scan.add_java_version(line.strip(), "java/static/opt_" + str(i) + "/version", features)
    except Exception as ex:
        pass

    if os.geteuid() == 0 or options.sudo:
        output = subprocess.check_output(["ps", "-e", "-o", "pid,comm"]).decode(encoding='utf-8')
    else:
        try:
            user = os.getlogin()
            output = subprocess.check_output(["ps", "-u", user, "-o", "pid,comm"]).decode(encoding='utf-8')
        except FileNotFoundError:
            # os.getlogin() may fail on WSL / containers
            # see https://stackoverflow.com/questions/74187896/os-getlogin-in-docker-container-throws-filenotfounderror
            output = subprocess.check_output(["ps", "-o", "pid,comm"]).decode(encoding='utf-8')

    for line in output.split('\n'):
        token = line.strip().split(' ')
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
    # noinspection PyDeprecation

    try:
        scan_linux_user(scan, options)
    except Exception as e:
        scan.queue_warning(2001, "scan_linux_user failed:" + repr(e))

    os_elem = scan.create_element("operating_system")
    scan.append_info_element(os_elem, "platform", "S", platform.platform())
    scan.append_child(os_elem)

    config_elem = scan.create_element("configuration")
    scan.append_info_element(config_elem, "tag", "S", options.tag)
    if options.machine:
        scan.append_info_element(config_elem, "machine", "S", options.machine)
    if options.host:
        scan.append_info_element(config_elem, "host", "S", options.host)
    if options.cluster:
        scan.append_info_element(config_elem, "cluster", "S", options.cluster)
    if options.container:
        scan.append_info_element(config_elem, "container", "B", str(options.container))
    if options.virt:
        scan.append_info_element(config_elem, "virt", "S", options.virt)
    scan.append_child(config_elem)

    # collect various _release info files. if systemctl standard os_release is present this
    # will get parsed on import, otherwise some heuristics will be applied on all available release files
    for release_info in glob.glob1("/etc", "*-release"):
        scan.add_file(os.path.join("/etc", release_info), os.path.join("release", release_info))

    # fallback on /usr/lib/*-release
    for release_info in glob.glob1("/usr/lib", "*-release"):
        scan.add_file(os.path.join("/usr/lib", release_info), os.path.join("release-usrlib", release_info))

    # collect debian_version if it exists
    for release_info in glob.glob1("/etc", "*_version"):
        scan.add_file(os.path.join("/etc", release_info), os.path.join("release", release_info))

    for proc_file in ["cpuinfo", "meminfo", "scsi/scsi", "version", "version_signature"]:
        f = os.path.join("/proc", proc_file)
        if os.path.exists(f):
            scan.add_file(f, os.path.join("proc/", proc_file))

    #
    # try to get hardware ids of the system
    #
    # both variants do not return the system_uuid when we are not root
    # this uuid could be used for vm to host mapping for virtual machines under vmware
    # it's recommended to run the server scan under root
    #
    dmi_folder = "/sys/class/dmi/id"
    if os.path.exists(dmi_folder):
        scan.add_folder(dmi_folder, "sys/class/dmi/id")
        if scan.command_exists("udevadm"):
            scan.add_command_output(["udevadm", "info", "-a", dmi_folder], "cmd/udevadm_dmi_id")

    for oratab in ["/etc/oratab", "/var/opt/oracle/oratab"]:
        if os.path.exists(oratab):
            scan.add_file(oratab, "oracle/oratab")
            break

    if scan.command_exists("dpkg-query"):
        scan.add_command_output(["dpkg-query", "-W", "-f",
                                 '${Package}\t${Version}\t${Architecture}\t${binary:Summary}\n'],
                                "dpkg/installed.txt")
    else:

        if scan.command_exists("apk"):
            scan.add_command_output(["apk", "list", "--installed"], "apk/installed.txt")
        else:
            fmt = '%{name}\t%{version}\t%{release}\t%{arch}\t%{summary}\t%{installtime}\t%{vendor}\t%{packager}\n'
            scan.add_command_output(["rpm", "-qa", "--queryformat", fmt], "rpm/installed.txt")

    scan.add_command_output(["ip", "addr"], "cmd/ip_addr")
    scan.add_command_output(["ip", "route"], "cmd/ip_route")
    scan.add_command_output(["ps", "-ef"], "cmd/ps_ef")

    if scan.command_exists("hostnamectl"):
        scan.add_command_output(["hostnamectl", "status"], "cmd/hostnamectl")

    # ipcs can be useful to detect server products such as oracle db (detect oracle sga)
    if scan.command_exists("ipcs"):
        scan.add_command_output(["ipcs", "-a"], "cmd/ipcs")

    #
    # systemd-detect-virt show on what virtualization / container environment we are runnting
    # not available on alpine, some alpine images have a dummy command that returns 'docker' or similar
    #
    if scan.command_exists("systemd-detect-virt"):
        scan.add_command_output(["systemd-detect-virt"], "cmd/systemd-detect-virt")

    # scan.add_command_output(["service", "--status-all"], "cmd/service_status_all")
    scan.add_command_output(["systemctl", "list-units", "-all", "--no-page"], "cmd/systemctl_units_all")

    # modern: just copy hyperv kvp files
    kvp_folder = "/var/lib/hyperv"

    if os.path.exists(kvp_folder):
        scan.add_folder2(kvp_folder, "hyperv")

    scan_linux_memory_size(scan, options)

    scan_linux_java(scan, options)
