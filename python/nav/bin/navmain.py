#!/usr/bin/env python
# -*- testargs: list -*-
#
# Copyright (C) 2006, 2011, 2016, 2017 Uninett AS
#
# This file is part of Network Administration Visualized (NAV).
#
# NAV is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License version 3 as published by
# the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.  You should have received a copy of the GNU General Public
# License along with NAV. If not, see <http://www.gnu.org/licenses/>.
#
"""Command line program to control NAV processes"""

import sys
import os
import os.path
import argparse
import textwrap

from nav import colors

try:
    from nav.startstop import ServiceRegistry, CommandFailedError, CrontabError
except ImportError:
    print(
        "Fatal error: Could not find the nav.startstop module.\nIs your "
        "PYTHONPATH environment correctly set up?",
        file=sys.stderr,
    )
    sys.exit(1)

try:
    SERVICES = ServiceRegistry()
except (OSError, CrontabError) as _error:
    print(
        "A problem occurred, which prevented this command from running.\n"
        + str(_error),
        file=sys.stderr,
    )
    sys.exit(1)


def main(args=None):
    """Main execution point"""
    if args is None:
        parser = make_argparser()
        args = parser.parse_args()
    try:
        args.func(args)
    except AttributeError:
        parser.print_help(sys.stderr)
        sys.exit(0)


def make_argparser():
    """Builds and returns an ArgumentParser instance for this program"""
    parser = argparse.ArgumentParser(
        description="This command is your interface to start, stop and query "
        "NAV services.",
        epilog="The selected command will be applied to all known services, "
        "unless you specify a list of services after the command.",
    )
    parser.add_argument(
        "--nonroot",
        action="store_true",
        help="don't complain about not having root privileges",
    )
    parser.add_argument(
        "--verbose",
        "-V",
        action="store_true",
        help="let output from subcommands pass through",
    )

    self = sys.modules[__name__]
    commands = sorted(
        (name.replace('c_', ''), func)
        for name, func in vars(self).items()
        if name.startswith('c_') and callable(func)
    )
    all_services = sorted(SERVICES.keys())
    subparsers = parser.add_subparsers()
    for command, func in commands:
        subp = subparsers.add_parser(command, help=func.__doc__)
        subp.add_argument("service", nargs="*", default=all_services)
        subp.set_defaults(func=func)

    _add_bespoke_subparsers(subparsers)

    return parser


def _add_bespoke_subparsers(subparsers):
    config = subparsers.add_parser(
        "config", help="query or manipulate NAV configuration"
    )
    config_sub = config.add_subparsers()
    where = config_sub.add_parser(
        "where",
        help="find and report the location of the main NAV configuration file",
    )
    where.set_defaults(func=command_config_where)

    path = config_sub.add_parser(
        "path",
        help="prints a list of filesystem locations "
        "where NAV will search for configuration "
        "files",
    )
    path.set_defaults(func=command_config_path)

    install = config_sub.add_parser(
        "install",
        help="installs a copy of the default NAV "
        "configuration file tree in a target "
        "directory",
    )
    install.add_argument(
        'target_directory', help="the directory in which to install the config files"
    )
    install.add_argument(
        '--overwrite',
        action="store_true",
        help="overwrite existing config files in target directory",
    )
    install.add_argument(
        '--verbose',
        '-v',
        action="store_true",
        help="print the full path of all copied files",
    )
    install.set_defaults(func=command_config_install)


def verify_root():
    """Verifies that a user has root privileges, if they are needed"""
    if os.geteuid() != 0:
        print("You should be root to run this command.", file=sys.stderr)
        sys.exit(10)


def service_iterator(query_list, func):
    """Iterate through a list of service names, look up each service instance
    and call func using this instance as its argument.
    """
    unknowns = []
    for name in query_list:
        if name in SERVICES:
            func(SERVICES[name])
        else:
            unknowns.append(name)
    if len(unknowns):
        sys.stderr.write("Unknown services: %s\n" % " ".join(unknowns))


def action_iterator(query_list, action, ok_string, fail_string, verbose=False):
    """Iterates through a list of service names, performing an action on each
    of them.
    """
    failed = []
    unknowns = []
    errors = []

    any_ok = False
    for name in query_list:
        if name in SERVICES:
            method = getattr(SERVICES[name], action)
            try:
                if method(silent=not verbose):
                    if not any_ok:
                        any_ok = True
                        print(ok_string + ":", end=' ')
                    colors.print_color(name + ' ', colors.COLOR_GREEN, newline=False)
                    sys.stdout.flush()
                else:
                    failed.append(name)
            except CommandFailedError as error:
                errors.append((name, error))
        else:
            unknowns.append(name)
    if any_ok:
        print()

    if len(failed):
        print("%s:" % fail_string, end=' ')
        colors.print_color(" ".join(failed), colors.COLOR_RED)
    if len(unknowns):
        print("Unknown: %s" % " ".join(unknowns))
    if len(errors):
        print("Errors:", end=' ')
        print(" ".join(["%s (%s)" % error for error in errors]))


#
# This group of commands work with services
#


def c_info(args):
    """lists each service and their associated description"""
    matched_services = []
    max_length = 0
    terminal_width = colors.get_terminal_width() or 79

    def _service_printer(service):
        name = ("{:<%s} " % max_length).format(service.name)
        colors.print_color(name, colors.COLOR_GREEN, newline=False)

        kind = service.__class__.__name__
        if kind.endswith("Service"):
            kind = kind.removesuffix("Service").lower()
        kind = "({})".format(kind)
        kind = "{:>8}".format(kind)
        colors.print_color(kind, colors.COLOR_YELLOW, newline=False)

        indent = " " * (max_length + 11)
        info = textwrap.wrap(
            service.info or "N/A",
            width=terminal_width,
            initial_indent=indent,
            subsequent_indent=indent,
        )
        info = "\n".join(info)
        print(": " + info.strip())

    def _append_to_service_list(service):
        matched_services.append(service)

    service_iterator(args.service, _append_to_service_list)
    max_length = max(len(s.name) for s in matched_services) if matched_services else 0
    for svc in matched_services:
        _service_printer(svc)


def c_list(args):
    """lists all the available service names"""
    service_iterator(args.service, lambda service: print(service.name))


def c_start(args):
    """starts services"""
    if not args.nonroot:
        verify_root()
    from nav import config

    try:
        config.verify_nav_config(config.NAV_CONFIG)
    except config.ConfigurationError as error:
        sys.exit("There is a problem with nav.conf:\n{}".format(error))

    action_iterator(args.service, "start", "Starting", "Failed", verbose=args.verbose)


def c_stop(args):
    """stops services"""
    if not args.nonroot:
        verify_root()
    action_iterator(args.service, "stop", "Stopping", "Failed", verbose=args.verbose)


def c_restart(args):
    """restarts services"""
    if not args.nonroot:
        verify_root()
    c_stop(args)
    c_start(args)


def c_status(args):
    """reports the status of services"""
    if not args.nonroot:
        verify_root()
    action_iterator(args.service, "is_up", "Up", "Down", verbose=args.verbose)


#
# This group of commands do not work with services, and may or may not take
# arguments from the command line.
#


def c_version(_args):
    """reports the currently installed NAV version"""
    from nav import buildconf

    print("NAV %s" % buildconf.VERSION)


def command_config_where(_args):
    """reports the location of NAV's main configuration file"""
    from nav.config import find_config_file, CONFIG_LOCATIONS

    path = find_config_file('nav.conf')
    if path:
        print(path)
    else:
        sys.exit(
            "Could not find nav.conf in any of these locations:\n{}".format(
                '\n'.join(CONFIG_LOCATIONS)
            )
        )


def command_config_path(_args):
    """Prints the list of file system locations NAV will search for config"""
    from nav.config import CONFIG_LOCATIONS

    for path in CONFIG_LOCATIONS:
        print(path)


def command_config_install(args):
    """Installs a copy of the example config files in a target directory"""
    from nav.config import install_example_config_files

    callback = print if args.verbose else None

    try:
        install_example_config_files(
            args.target_directory, overwrite=args.overwrite, callback=callback
        )
    except (OSError, IOError) as error:
        sys.exit(error)


##############
# begin here #
##############
if __name__ == '__main__':
    main()
