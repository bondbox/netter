# coding:utf-8

from binascii import hexlify
from ipaddress import IPv4Address
from ipaddress import IPv6Address
from ipaddress import ip_address
from random import randint
import time
from typing import Union

from dns.resolver import LifetimeTimeout
from dns.resolver import NXDOMAIN
from dns.resolver import NoAnswer
from dns.resolver import NoNameservers
from dns.resolver import Resolver
import ping3

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


class dnsprobe():
    '''DNS Prober
    '''

    def __init__(self, address: IPAddress):
        assert isinstance(address, IPAddress), \
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
