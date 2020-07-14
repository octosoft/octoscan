#
# (c)2019 Octosoft AG, CH-6312 Steinhausen, Switzerland
# This code is licensed under the MIT license see LICENSE.txt
#

from __future__ import print_function

import sys
import os
import platform
import subprocess

from datetime import datetime
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from socket import getfqdn
from uuid import uuid1
from xml.dom.minidom import Document, Element
from .octoscan_build import octoscan_build


class OctoscanArchive(object):
    """
        A octoscan archive is a zip file that contains multiple files and an XML document octoscan.xml
        OctoscanArchive provides methods to add files, command output and strings to the archive,
        as well as to build the standardized octoscan.xml document.
    """

    def __init__(self, output_folder=".", uuid=None, ext=".scal", verbose=False, sudo=False):
        # type: (str,str,str,bool,bool) -> None
        self._platform = platform.platform()
        self._verbose = verbose
        self._start = datetime.now()
        self._sudo = sudo

        if uuid:
            assert (isinstance(uuid, str))
            self.uuid = uuid
        else:
            self.uuid = str(uuid1())

        # if not os.path.exists(output_folder):
        #    self._eprint("output folder '"+output_folder + "' does not exist")
        #    exit(2)

        # are we on windows (module tests?)

        platform_system = platform.system().lower()

        self._is_windows = "windows" in platform_system
        self._is_darwin = "darwin" in platform_system
        self._is_linux = "linux" in platform_system

        if self.is_windows():
            ext = ".zip"

        if self.is_darwin():
            ext = ".scam"

        if not os.path.exists(output_folder):
            self._eprint("IOError: " + output_folder + ": no such file or directory")
            exit(2)

        if not os.path.isdir(output_folder):
            self._eprint("IOErrror: " + output_folder + ": not a directory")
            exit(2)

        self.filename = os.path.join(output_folder, self.uuid + ext)

        try:
            self.zip = ZipFile(self.filename, 'w')
        except Exception as e:
            # errno 2: output folder does not exist
            # errno 20: output folder is not a directory
            self._eprint(repr(e) + ": " + self.filename)
            exit(2)

        self._warning_list = []

        self._verbose_trace("platform: " + self._platform)
        self._verbose_trace("python: " + platform.python_version())
        self._verbose_trace("build: " + octoscan_build)

        self._doc = Document()
        self._octoscan_element = self._doc.createElement("octoscan")
        self._octoscan_element.setAttribute("uuid", self.uuid)
        self._octoscan_element.setAttribute("python", platform.python_version())
        self._octoscan_element.setAttribute("platform", self._platform)
        self._octoscan_element.setAttribute("system", platform_system)
        self._octoscan_element.setAttribute("build", octoscan_build)
        self._octoscan_element.setAttribute("fqdn", getfqdn())
        self._octoscan_element.setAttribute("timestamp", datetime.utcnow().replace(microsecond=0).isoformat())

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    @staticmethod
    def _eprint(*args, **kwargs):
        print(*args, file=sys.stderr, **kwargs)

    def _verbose_trace(self, *args, **kwargs):
        if self._verbose:
            self._eprint(*args, **kwargs)

    def queue_warning(self, warning_id, message):
        # type: (int,str) -> None
        self._warning_list.append((warning_id, message))

    def is_windows(self):
        # type: () -> bool
        """
        :return: True if the scanner is running on windows. This is exposed mainly for unit testing on windows
        """
        return self._is_windows

    def is_darwin(self):
        # type: () -> bool
        """
        :return: True if the scanner is running on darwin
        """
        return self._is_darwin

    def is_linux(self):
        # type: () -> bool
        """
        :return: True if the scanner is running on linux
        """
        return self._is_linux

    @staticmethod
    def is_executable(path):
        # type: (str) -> bool
        return os.path.isfile(path) and os.access(path, os.X_OK)

    def check_output(self, *popenargs, **kwargs):
        r"""Run command with arguments and return its output as a byte string.
        Backported from Python 2.7 as it's implemented as pure python on stdlib.
        Python 2.6.2
        """
        self._verbose_trace("check_output " + str(popenargs))
        process = subprocess.Popen(stdout=subprocess.PIPE, stderr=subprocess.PIPE, *popenargs, **kwargs)
        output, unused_err = process.communicate()
        retcode = process.poll()
        if retcode:
            cmd = kwargs.get("args")
            if cmd is None:
                cmd = popenargs[0]
            error = subprocess.CalledProcessError(retcode, cmd)
            error.output = output
            raise error

        if sys.version_info >= (3, 0):
            return output.decode()

        return output

    def readlink(self, link):
        # type: (str) -> str
        """
        wrapper for os.readlink and sudo readlink
        :param link:
        :return:
        """
        self._verbose_trace("readlink:  " + link)
        path = ""
        try:
            path = os.readlink(link)
        except OSError as ose:
            if self._sudo:
                try:
                    path = self.check_output(["sudo", "readlink", link]).strip()
                except Exception as e:
                    self.queue_warning(1010, "Exception on sudo readlink " + link + ": " + str(e))
            else:
                self.queue_warning(1010, "Error on readlink " + link + ": " + str(ose))
        return path

    def close(self):
        # type: () -> None
        """
        Close the octoscan archive.
        :return:
        """

        self._verbose_trace("close: " + self.filename + " closing")
        # write queued warnings
        for warning_id, warning in self._warning_list:
            self.append_warning_element(self._octoscan_element, warning_id, warning)

        # write performance
        performance_element = self.create_element("octoscan")
        end = datetime.now()

        self.append_info_element(performance_element, "performance", "S", str(end - self._start))
        self.append_child(performance_element)
        self._doc.appendChild(self._octoscan_element)

        # create zip entry for xml document
        xml_str = self._doc.toprettyxml(indent="    ", encoding="utf-8")
        self.add_str(xml_str, "octoscan.xml")
        self.zip.close()
        self._verbose_trace("close: " + self.filename + " closed")

    # noinspection PyCompatibility
    def add_str(self, str_to_add, name, dt=datetime.now()):
        # type: (str,str,datetime) -> None
        """
        Add a string to the archive as zip entry named 'name'
        :param str_to_add: string to add
        :param name: name of the zip.entry
        :param dt: datetime, optional if not specified, current date time is assumed
        :return: None
        """

        # always use forward slash regardless of platform, this allows the calling
        # code to use os.path.join for names
        if os.pathsep in name:
            name = name.replace(os.pathsep, "/")

        info = ZipInfo()
        info.filename = self.uuid + "/" + name
        info.external_attr = 0o644 << 16
        info.compress_type = ZIP_DEFLATED
        info.date_time = (dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second)
        self.zip.writestr(info, str_to_add)

    def add_file(self, path, name):
        # type: (str,str) -> None
        """
        Add a file specified by path to the archive
        :param path:
        :param name:
        :return:
        """

        if not os.path.exists(path):
            self.queue_warning(1001, "add_file cannot read '" + path + "': file does not exist")
            return
        try:
            with open(path, "r") as f:
                self._verbose_trace("add_file:  " + path)
                self.add_str(f.read(), name, datetime.fromtimestamp(os.path.getmtime(path)))
        except IOError as e:
            if self._sudo:
                self.add_file_sudo(path, name)
            else:
                self.queue_warning(1002, "cannot read " + path + ": " + repr(e))
        except Exception as e:
            self.queue_warning(1003, "cannot read " + path + ": " + repr(e))

    def add_folder(self, path, name):
        # type: (str,str) -> None
        """
        :param path:
        :param name:
        :return:
        """
        self._verbose_trace("add_folder: " + path)
        for f in os.listdir(path):
            if os.path.isfile(os.path.join(path, f)):
                self.add_file(os.path.join(path, f), os.path.join(name, f))

    def add_file2(self, path, name):
        # type: (str,str) -> None
        """
        adds a binary file directly to the zip archive without going through byte
        to string conversions and encodings. delegates decoding and parsing to the import service
        :param path:
        :param name:
        :return:
        """
        if not os.path.exists(path):
            self.queue_warning(1001, "add_file2 cannot read '" + path + "': file does not exist")
            return
        try:
            self.zip.write(path, self.uuid + "/" + name)
        except IOError as e:
            self.queue_warning(1002, "add_file2 cannot read " + path + ": " + repr(e))
        except Exception as e:
            self.queue_warning(1003, "add_file2 cannot read " + path + ": " + repr(e))

    def add_folder2(self, path, name):
        # type: (str,str) -> None
        """
        adds all files in the specified folder binary to the zip archive without going through byte
        to string conversions and encodings. delegates decoding and parsing to the import service
        :param path:
        :param name:
        :return:
        """
        self._verbose_trace("add_folder2: " + path)
        for f in os.listdir(path):
            if os.path.isfile(os.path.join(path, f)):
                self.add_file2(os.path.join(path, f), os.path.join(name, f))

    @staticmethod
    def command_exists(cmd):
        # type: (str) -> bool
        """
        :param cmd: command to test for. On Windows you have to include the suffix (.exe etc) in the name
        :return: True if the command could be found, False otherwise
        """
        return any(
            os.access(os.path.join(path, cmd), os.X_OK)
            for path in os.environ["PATH"].split(os.pathsep)
        )

    def add_file_sudo(self, path, name):
        # type: (str,str) -> None
        """
        :param path: path to a file that can be read only with privileges
        :param name: name where to store the data in the zip archive
        """
        self._verbose_trace("add_file_sudo:  " + path)
        self.add_command_output(["sudo", "cat", path], name)

    def add_command_output(self, cmd, name):
        # type: ([str],str) -> None
        """
        :param cmd:
        :param name:
        :return:
        """
        try:
            if self.command_exists(cmd[0]):
                self._verbose_trace("add_command_output:  " + str(cmd))
                output = self.check_output(cmd)
                self.add_str(output, name)
            else:
                self._verbose_trace("add_command_output:  " + str(cmd) + ": command not found")
        except Exception as e:
            self.queue_warning(1004, "add_command_output exception " + repr(cmd) + ": " + repr(e))

    def add_java_version(self, path, zip_entry_name, features=None):
        """
        adds the stderr of the java -version command to the scan archive
        :param path: path to the java executable
        :param zip_entry_name:
        :param features:
        :return:
        """

        if not path:
            return

        if len(path) < 4:
            return

        if not OctoscanArchive.is_executable(path):
            return

        self._verbose_trace("add_java_version:    '" + path + "'")

        variant = "JRE"

        if not features:
            features = []

        buf = ""

        # noinspection PyBroadException
        try:
            java_dir = os.path.dirname(path)
            if os.path.exists(os.path.join(java_dir, "javac")):
                variant = "JDK"

            buf = "Path:" + path + "\nVariant:" + variant

            # check usage tracker config files
            if os.path.exists(
                    os.path.join(java_dir, "..", "lib", "management", "usagetracker.properties")
            ) or os.path.exists(
                os.path.join(java_dir, "..", "conf", "management", "usagetracker.properties")
            ):
                if len(features):
                    features.append("JavaUsageTrackerHome")

        except Exception:
            pass

        if len(features):
            buf = buf + "\nFeatures:" + ",".join(features)

        buf = buf + "\n\n"

        try:
            # override env as not to inherit JAVA environment from calling process
            sp = subprocess.Popen([path, "-version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, env={})
            out, version = sp.communicate()
            return_code = sp.poll()

            if sys.version_info >= (3, 0):
                version_str = version.decode()
            else:
                version_str = version

            if return_code == 0:
                buf += version_str
            else:
                msg = "java -version failed for '" + path + "', exit code: " + str(return_code)
                buf += "FAILED: " + msg
                buf += version_str
                self.queue_warning(2002, msg)
        except Exception as e:
            msg = "java -version failed for '" + path + "': " + str(e)
            buf += "FAILED: " + msg
            self.queue_warning(2003, msg)

        self.add_str(buf, zip_entry_name)

    def create_element(self, tag_name):
        # type: (str) -> Element
        """
        Creates an XML Element in the embedded octoscan.xml document
        :param tag_name:
        :return:
        """
        self._verbose_trace("create_element: " + tag_name)
        return self._doc.createElement(tag_name)

    def append_info_element(self, element, name, info_type, value):
        # type: (Element,str,str,str) -> None
        """
        Appends an info element to the specified element in the octoscan.xml document
        :param element:
        :param name:
        :param info_type:
        :param value:
        :return:
        """
        assert isinstance(element, Element)
        if self._verbose:
            self._verbose_trace(
                "info: " + element.tagName + "/" + name + " type='" + info_type + "' value='" + value + "'"
            )
        info = self._doc.createElement("info")
        info.setAttribute("name", name)
        info.setAttribute("type", info_type)
        info.setAttribute("value", value)
        element.appendChild(info)

    def append_warning_element(self, element, error_id, message):
        # type: (Element,int,str) -> None
        """
        :param element:
        :param error_id:
        :param message:
        :return:
        """
        assert isinstance(element, Element)
        warning = self._doc.createElement("warning")
        warning.setAttribute("id", str(error_id))
        warning.setAttribute("message", message)
        element.appendChild(warning)

    def append_child(self, element):
        # type: (Element) -> None
        """
        :param element:
        :return:
        """
        assert isinstance(element, Element)
        self._verbose_trace("append_child: " + element.tagName)
        self._octoscan_element.appendChild(element)
