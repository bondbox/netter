# coding:utf-8

from typing import Dict
from typing import Iterable
from typing import List
from typing import Set
from typing import Union

from dns.resolver import Answer
from dns.resolver import LifetimeTimeout
from dns.resolver import NXDOMAIN
from dns.resolver import NoAnswer
from dns.resolver import NoNameservers
from ping3.errors import HostUnknown
from xarg import add_command
from xarg import argp
from xarg import commands
from xarg import form
from xarg import run_command
from xarg import tabulate

from ..utils import Context
from ..utils import EXAMPLE_DOMAIN
from ..utils import NetworkInterface
from ..utils import PING_MAX_TO
from ..utils import RESOLVE_MAX_TO
from ..utils import dnsprobe
from ..utils import is_unix
from ..utils import is_windows
from ..utils import ping


def query_domain_name(domain: str, nameservers: Iterable[str],
                      enable_aaaa: bool = False) -> form:
    title: List[str] = ["nameserver", "type", "answer"]
    table: form[str, Union[str, Answer]] = form(name=domain, header=title)

    def query(prober: dnsprobe, rdtype: str):
        prefix: List[str] = [prober.address, rdtype]
        try:
            answer: Answer = prober.resolver.resolve(
                qname=domain, rdtype=rdtype,
                lifetime=RESOLVE_MAX_TO)
            table.append(prefix + [answer])
        except NXDOMAIN:
            table.append(prefix + ["NXDOMAIN"])
        except NoAnswer:
            table.append(prefix + ["No Answer"])
        except NoNameservers:
            table.append(prefix + ["No Nameservers"])
        except LifetimeTimeout:
            table.append(prefix + ["Timeout"])

    for nameserver in nameservers:
        prober: dnsprobe = dnsprobe.from_string(nameserver)
        query(prober, "A")
        if enable_aaaa:
            query(prober, "AAAA")

    return table


def add_domain_and_nameserver(_arg: argp):
    _arg.add_argument("--domain", nargs=1, metavar="NAME",
                      default=[EXAMPLE_DOMAIN],
                      help="domain name")
    _arg.add_argument(dest="nameservers", nargs="*", metavar="NS", default=[],
                      help="nameserver")


@add_command("query", help="query domain name")
def add_cmd_query(_arg: argp):
    # TODO: add --ipv6 (AAAA)
    # TODO: add --ping (ping ipaddress)
    add_domain_and_nameserver(_arg)


@run_command(add_cmd_query)
def run_cmd_query(cmds: commands) -> int:
    nameservers: List[str] = cmds.args.nameservers
    if len(nameservers) > 0:
        domain = cmds.args.domain[0]
        querys = query_domain_name(domain, nameservers)
        addresses: Dict[str, Set[str]] = {}

        addrs: form[str, str] = form(
            name=f"query {querys.name}",
            header=["nameserver", "type", "ip_address"])
        for mapping in querys.mappings:
            if mapping["type"] not in ["A", "AAAA"]:
                continue
            answer: Union[str, Answer] = mapping["answer"]
            if isinstance(answer, Answer):
                nameserver: str = mapping["nameserver"]
                address: List[str] = [rdata.address for rdata in answer]
                for addr in address:
                    if addr not in addresses:
                        addresses[addr] = set()
                    addresses[addr].add(nameserver)
                mapping["ip_address"] = "\n".join(addr for addr in address)
            else:
                mapping["ip_address"] = answer
            addrs.append(addrs.reflection(mapping))
        cmds.stdout(f"query {querys.name}")
        cmds.stdout(tabulate(addrs, fmt="simple_grid"))

        pings: form[str, str] = form(
            name=f"ping {querys.name}",
            header=["ip_address", "ping(ms)", "nameservers"])
        for _address, _nameservers in addresses.items():
            description: str = "\n".join(_nameservers)
            try:
                delay = ping(address=_address, timeout=PING_MAX_TO)
                pings.append([_address, f"{delay * 1000:.2f}", description])
            except HostUnknown:
                pings.append([_address, "Host Unknown", description])
        cmds.stdout(f"\nping {querys.name}")
        cmds.stdout(tabulate(pings, fmt="simple_grid"))
    return 0


@ add_command("probe", help="ping and resolve")
def add_cmd_probe(_arg: argp):
    add_domain_and_nameserver(_arg)


@ run_command(add_cmd_probe)
def run_cmd_probe(cmds: commands) -> int:
    nameservers: List[str] = cmds.args.nameservers
    if len(nameservers) > 0:
        domain = cmds.args.domain[0]
        title: List[str] = ["nameserver", "ping", "resolve"]
        table: form[str, str] = form(f"probe {domain}", title)
        for nameserver in nameservers:
            prober = dnsprobe.from_string(nameserver)
            ping = prober.ping(lifetime=PING_MAX_TO)
            test = prober.test(qname=domain, lifetime=RESOLVE_MAX_TO)
            ping_delay = f"{ping * 1000:.2f}ms" if ping >= 0 else "Timeout"
            test_delay = f"{test * 1000:.2f}ms" if test >= 0 else "Timeout"
            table.append([nameserver, ping_delay, test_delay])
        cmds.stdout(tabulate(table))
    return 0


@ add_command("nameserver",
              help="view and probe nameservers, query domain name")
def add_cmd_nameserver(_arg: argp):
    pass


@ run_command(add_cmd_nameserver, add_cmd_probe, add_cmd_query)
def run_cmd_nameserver(cmds: commands) -> int:
    nameservers: List[str] = []
    if is_windows():
        for iface in NetworkInterface.load():
            if iface.mac_enabled and iface.ip_enabled and iface.dns_enabled:
                servers = iface.nameservers
                nameservers.extend(servers)
                if not cmds.has_sub(add_cmd_nameserver):
                    cmds.stdout(f"{iface.detail_name()}: {', '.join(servers)}")
    elif is_unix():
        servers = Context().nameservers
        nameservers.extend(servers)
        if not cmds.has_sub(add_cmd_nameserver):
            for namespace in servers:
                cmds.stdout(namespace)
    if hasattr(cmds.args, "nameservers"):
        cmds.args.nameservers.extend(nameservers)
    else:
        cmds.args.nameservers = nameservers
    return 0
