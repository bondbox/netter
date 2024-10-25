# coding:utf-8

from binascii import hexlify
from enum import IntFlag
from enum import auto
from ipaddress import IPv4Address
from ipaddress import IPv6Address
from ipaddress import ip_address
from random import choice
from random import randint
import time
from typing import Callable
from typing import Dict
from typing import Iterable
from typing import Iterator
from typing import List
from typing import Mapping
from typing import Optional
from typing import Tuple
from typing import Union

from dns.resolver import LifetimeTimeout
from dns.resolver import NXDOMAIN
from dns.resolver import NoAnswer
from dns.resolver import NoNameservers
from dns.resolver import Resolver
import ping3
import requests

ping3.EXCEPTIONS = True
IPAddress = Union[IPv4Address, IPv6Address]

PING_MIN_TO = 1
PING_MAX_TO = 8
RESOLVE_MIN_TO = 0.1
RESOLVE_MAX_TO = 8.0
EXAMPLE_DOMAIN = "example.com"


def ping(address: str, timeout: int = PING_MIN_TO) -> float:
    assert isinstance(timeout, int), f"unexpected type: {type(timeout)}"
    _timeout: int = min(max(PING_MIN_TO, timeout), PING_MAX_TO)
    try:
        return ping3.ping(address, timeout=_timeout, seq=randint(8192, 32767))
    except ping3.errors.Timeout:
        return -float(timeout)


class public_ip():
    '''Query Public IP Address
    '''
    class flags(IntFlag):
        random = 0
        ident = auto()
        ipify = auto()
        ipinfo = auto()
        cloudflare = auto()
        all = ipify | ident | ipinfo | cloudflare

    def __init__(self, address: Mapping[str, Iterable[str]]):
        self.__addrs: Dict[IPAddress, Tuple[str, ...]] = {
            ip_address(k): tuple(s for s in v) for k, v in address.items()
        }

    def __str__(self) -> str:
        return ", ".join(str(addr) for addr in self)

    def __iter__(self) -> Iterator[IPAddress]:
        return iter(self.__addrs.keys())

    def __getitem__(self, key: IPAddress) -> Tuple[str, ...]:
        return self.__addrs[key]

    @classmethod
    def query_from_ident(cls) -> Optional[str]:
        response = requests.get("https://ident.me")
        return response.text.strip() if response.ok else None

    @classmethod
    def query_from_ipify(cls) -> Optional[str]:
        response = requests.get("https://api64.ipify.org?format=json")
        return response.json()["ip"] if response.ok else None

    @classmethod
    def query_from_ipinfo(cls) -> Optional[str]:
        response = requests.get("https://ipinfo.io/ip")
        return response.text.strip() if response.ok else None

    @classmethod
    def query_from_cloudflare(cls) -> Optional[str]:
        def parse_ip(lines: Iterable[str]) -> Optional[str]:
            for line in lines:
                if line.startswith("ip="):
                    return line.split("=")[1]
        response = requests.get("https://www.cloudflare.com/cdn-cgi/trace")
        return parse_ip(response.text.split()) if response.ok else None

    @classmethod
    def query(cls, flag: flags = flags.random) -> "public_ip":
        address: Dict[str, List[str]] = {}
        mapping: Dict[public_ip.flags,
                      Tuple[Callable[[], Optional[str]], str]] = {
            cls.flags.ident: (cls.query_from_ident, "https://ident.me"),
            cls.flags.ipify: (cls.query_from_ipify, "https://api64.ipify.org"),
            cls.flags.ipinfo: (cls.query_from_ipinfo, "https://ipinfo.io/ip"),
            cls.flags.cloudflare: (cls.query_from_cloudflare,
                                   "https://radar.cloudflare.com/ip"),
        }
        if flag is cls.flags.random:
            flag = choice([f for f in mapping.keys()])
        for site, call_site in mapping.items():
            if site in flag:
                addr = call_site[0]()
                if isinstance(addr, str):
                    if addr not in address:
                        address[addr] = []
                    address[addr].append(call_site[1])
        return cls(address)


class dnsprobe():
    '''DNS Prober
    '''

    def __init__(self, address: IPAddress):
        assert isinstance(address, (IPv4Address, IPv6Address)), \
            f"unexpected type: {type(address)}"
        resolver: Resolver = Resolver(configure=False)
        resolver.nameservers = [str(address)]
        self.__resolver: Resolver = resolver
        self.__addr: IPAddress = address

    @property
    def name(self) -> str:
        return hexlify(data=self.__addr.packed).decode()

    @property
    def resolver(self) -> Resolver:
        return self.__resolver

    @property
    def address(self) -> str:
        return str(self.__addr)

    @classmethod
    def from_string(cls, address: str) -> "dnsprobe":
        assert isinstance(address, str), f"unexpected type: {type(address)}"
        return dnsprobe(ip_address(address))

    def ping(self, lifetime: int = PING_MIN_TO) -> float:
        return ping(address=self.address, timeout=lifetime)

    def test(self, qname: str = EXAMPLE_DOMAIN,
             lifetime: float = RESOLVE_MIN_TO) -> float:
        assert isinstance(qname, str), f"unexpected type: {type(qname)}"
        assert isinstance(lifetime, float), \
            f"unexpected type: {type(lifetime)}"
        timeout = min(max(RESOLVE_MIN_TO, lifetime), RESOLVE_MAX_TO)
        _start = time.perf_counter()

        def ok():
            return time.perf_counter() - _start

        try:
            self.resolver.resolve(qname, lifetime=timeout)
            return ok()
        except NXDOMAIN:
            return ok()
        except (NoAnswer, NoNameservers):
            return ok()
        except LifetimeTimeout:
            return -timeout
