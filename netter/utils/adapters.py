# coding:utf-8

from typing import Any
from typing import Dict
from typing import Iterable
from typing import Iterator
from typing import Optional
from typing import Tuple

from psutil import AF_LINK
from psutil import net_if_addrs
from psutil._common import snicaddr

from .format import MACAddress
from .platform import assert_unix
from .platform import assert_windows
from .platform import is_unix
from .platform import is_windows

if is_windows():
    import wmi


ADDRESSES = Tuple[str, ...]
NAMESERVERS = ADDRESSES


class Context:
    def __init__(self):
        self.__interfaces: Dict[str, Any] = {}
        self.__nameservers: Optional[NAMESERVERS] = None

    @property
    def nameservers(self) -> NAMESERVERS:
        assert_unix()
        if self.__nameservers is None:
            with open("/etc/resolv.conf", "r", encoding="utf-8") as rhdl:
                self.__nameservers = tuple(
                    line.split()[1]
                    for line in rhdl.readlines()
                    if "nameserver" in line
                )
        return self.__nameservers

    def parse_windows_all_network_adapters(self):
        assert_windows()
        client = wmi.WMI()
        for iface in client.Win32_NetworkAdapterConfiguration(IPEnabled=True):
            if isinstance(iface.MACAddress, str):
                addr: str = MACAddress(iface.MACAddress).colon
                self.__interfaces[addr] = iface

    def parse_windows_network_adapter(self, mac_address: MACAddress):
        addr: str = mac_address.colon
        if addr not in self.__interfaces:
            self.parse_windows_all_network_adapters()
        return self.__interfaces[addr] if addr in self.__interfaces else None

    def parse_description(self, name: str, mac_address: MACAddress) -> str:
        if is_windows():
            interface = self.parse_windows_network_adapter(mac_address)
            if interface is not None:
                interface.Description
        return name

    def parse_nameservers(self, mac_address: MACAddress) -> NAMESERVERS:
        if is_windows():
            interface = self.parse_windows_network_adapter(mac_address)
            nameservers = interface.DNSServerSearchOrder\
                if interface is not None else ()
            return nameservers if isinstance(nameservers, tuple) else ()
        elif is_unix():
            return self.nameservers
        return ()


class NetworkInterface:
    def __init__(self, name: str, addresses: Iterable[snicaddr],
                 context: Optional[Context] = None):
        self.__name: str = name
        self.__desc: str = name
        self.__mac_addrs: Tuple[MACAddress, ...] = tuple(
            MACAddress(addr.address) for addr in addresses
            if addr.family == AF_LINK)
        self.__ipv4_addrs: Tuple[snicaddr, ...] = tuple(
            addr for addr in addresses if addr.family.name == "AF_INET")
        self.__ipv6_addrs: Tuple[snicaddr, ...] = tuple(
            addr for addr in addresses if addr.family.name == "AF_INET6")
        self.__ip_addrs: Tuple[snicaddr, ...] = self.__ipv4_addrs + \
            self.__ipv6_addrs
        self.__nameservers: NAMESERVERS = ()

        if self.mac_enabled:
            ctx: Context = context or Context()
            self.__desc = ctx.parse_description(self.name, self.mac_address)
            self.__nameservers = ctx.parse_nameservers(self.mac_address)

    @property
    def name(self) -> str:
        return self.__name

    @property
    def description(self) -> str:
        return self.__desc

    @property
    def mac_enabled(self) -> bool:
        return len(self.__mac_addrs) > 0

    @property
    def mac_address(self) -> MACAddress:
        if len(self.__mac_addrs) > 0:
            return self.__mac_addrs[0]
        raise LookupError(f"Interface '{self.name}' MAC address not found.")

    @property
    def ip_enabled(self) -> bool:
        return len(self.__ip_addrs) > 0

    @property
    def ip_address(self) -> ADDRESSES:
        return tuple(addr.address for addr in self.__ip_addrs)

    @property
    def ipv4_address(self) -> ADDRESSES:
        return tuple(addr.address for addr in self.__ipv4_addrs)

    @property
    def ipv6_address(self) -> ADDRESSES:
        return tuple(addr.address for addr in self.__ipv6_addrs)

    @property
    def dns_enabled(self) -> bool:
        return len(self.__nameservers) > 0

    @property
    def nameservers(self) -> NAMESERVERS:
        return self.__nameservers

    def detail_name(self) -> str:
        return self.name if self.description == self.name\
            else f"{self.name}({self.description})"

    @classmethod
    def load(cls) -> "Iterator[NetworkInterface]":
        context: Context = Context()
        for name, addrs in net_if_addrs().items():
            yield cls(name, addrs, context)
