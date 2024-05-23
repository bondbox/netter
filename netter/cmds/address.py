# coding:utf-8

from xarg import add_command
from xarg import argp
from xarg import commands
from xarg import run_command

from ..utils import public_ip


@ add_command("public-ip", help="query public ip address")
def add_cmd_public_ip(_arg: argp):
    mgrp = _arg.add_mutually_exclusive_group()
    mgrp.add_argument("--all", action="store_true",
                      help="query from all sites")
    mgrp.add_argument("--ident", action="store_true",
                      help="query from ident.me")
    mgrp.add_argument("--ipify", action="store_true",
                      help="query from ipify.org")
    mgrp.add_argument("--ipinfo", action="store_true",
                      help="query from ipinfo.io")
    _arg.add_opt_on("-v", "--verbose", help="verbose mode")


@ run_command(add_cmd_public_ip)
def run_cmd_public_ip(cmds: commands) -> int:
    query_site = public_ip.flags.cloudflare
    if cmds.args.all:
        query_site = public_ip.flags.all
    elif cmds.args.ident:
        query_site = public_ip.flags.ident
    elif cmds.args.ipify:
        query_site = public_ip.flags.ipify
    elif cmds.args.ipinfo:
        query_site = public_ip.flags.ipinfo
    public: public_ip = public_ip.query(query_site)
    if cmds.args.verbose:
        for addr in public:
            sites: str = ", ".join(site for site in public[addr])
            cmds.stdout(f"{addr} from {sites}")
    else:
        cmds.stdout(public)
    return 0
