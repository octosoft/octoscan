#!/usr/bin/env python
#
# (c) 2019-2023 Octosoft AG, CH-6312 Steinhausen, Switzerland
# This software is provided under the MIT License, see LICENSE.txt
#

from __future__ import print_function

import sys

from optparse import OptionParser
from uuid import uuid1

from lib.octoscan_archive import OctoscanArchive
from lib.octoscan_build import octoscan_build
from lib.scan_linux import scan_linux


def main():
    # guard against execution on python 2.6 - no longer supported

    if sys.version_info[0] == 2 and not sys.version_info[1] == 7:
        raise Exception("Unsupported Python2 Version: " + repr(sys.version_info))

    # guard against execution on python 3.5 or lower - no longer supported
    # SLES 15 requires python 3.6 !!
    if sys.version_info[0] == 3 and sys.version_info[1] < 6:
        raise Exception("Unsupported Python3 Version: " + repr(sys.version_info))

    parser = OptionParser()

    parser.add_option("-o", "--outputfolder", dest="output_folder",
                      default=".",
                      help="write output file to specified directory")

    parser.add_option("-v", "--verbose",
                      action="store_true", dest="verbose", default=False,
                      help="verbose output")

    parser.add_option("-u", "--uuid", dest="uuid",
                      help="specify unique id to use",
                      default=str(uuid1()))

    parser.add_option("-S", "--sudo", dest="sudo",
                      action="store_true",
                      help="use sudo to access protected resources, sudoers has to allow no password access")

    parser.add_option("-J", "--java", dest="java_locations", default="",
                      help="Linux: list of additional folders for java filesystem scan, separated by columns")

    parser.add_option("--debugthrow", dest="debugthrow", action='store_true', default=False,
                      help="do throw critical exceptions (for debugging only)")

    parser.add_option("--version", dest="version",
                      action="store_true", default=False,
                      help="print version information and exit")

    (options, args) = parser.parse_args()

    if options.version:
        print("OctoSAM octoscan " + octoscan_build)
        exit(0)

    with OctoscanArchive(output_folder=options.output_folder,
                         uuid=options.uuid,
                         verbose=options.verbose,
                         sudo=options.sudo
                         ) as scan:

        print(scan.filename)

        try:
            scan_linux(scan, options)

        except Exception as e:
            scan.queue_warning(9001, "Exception: " + repr(e))
            if options.debugthrow:
                raise


if __name__ == '__main__':
    main()
