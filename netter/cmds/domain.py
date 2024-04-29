# coding:utf-8

from xarg import add_command
from xarg import argp
from xarg import commands
from xarg import run_command

from ..utils import Context
from ..utils import NetworkInterface
from ..utils import is_unix
from ..utils import is_windows


@ add_command("nameserver",
              help="view and probe nameservers, query domain name")
def add_cmd_nameserver(_arg: argp):
    pass


@run_command(add_cmd_nameserver)
def run_cmd_nameserver(cmds: commands) -> int:
    if is_windows():
        for iface in NetworkInterface.load():
            if iface.mac_enabled and iface.ip_enabled and iface.dns_enabled:
                nameservers = ", ".join(iface.nameservers)
                cmds.stdout(f"{iface.detail_name()}: {nameservers}")
    elif is_unix():
        for namespace in Context().nameservers:
            cmds.stdout(namespace)
    return 0
