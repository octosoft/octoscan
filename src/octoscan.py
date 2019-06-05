#!/usr/bin/env python
#
# (c) 2019 Octosoft AG, CH-6312 Steinhausen, Switzerland
# This software is provided under the MIT License, see LICENSE.txt
#

from __future__ import print_function

from optparse import OptionParser
from uuid import uuid1

from lib.octoscan import OctoscanArchive


def scan_platform(scan, options):
    if scan.is_windows():
        from lib.windows import scan_windows
        scan_windows(scan, options)
    elif scan.is_darwin():
        from lib.darwin import scan_darwin
        scan_darwin(scan, options)
    elif scan.is_linux():
        from lib.linux import scan_linux
        scan_linux(scan, options)


def main():

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

    (options, args) = parser.parse_args()

    with OctoscanArchive(output_folder=options.output_folder,
                         uuid=options.uuid,
                         verbose=options.verbose,
                         sudo=options.sudo
                         ) as scan:

        print(scan.filename)

        try:
            scan_platform(scan, options)
        except Exception as e:
            # noinspection PyProtectedMember
            scan.queue_warning(9001, "Exception: " + repr(e))


if __name__ == '__main__':
    main()
