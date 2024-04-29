# coding:utf-8

from typing import Tuple


class MACAddress:
    def __init__(self, mac_address: str):
        cleaned_mac: str = mac_address.replace(":", "").replace("-", "")
        bytes_mac: bytes = bytes.fromhex(cleaned_mac)
        if not isinstance(bytes_mac, bytes) or len(bytes_mac) != 6:
            raise ValueError(f"Invalid MAC address: {mac_address}")
        mac: Tuple[str, ...] = tuple(f"{b:02X}" for b in bytes_mac)
        self.__colon_mac = ":".join(mac)
        self.__dash_mac = "-".join(mac)

    def __str__(self) -> str:
        return self.colon

    def __eq__(self, value: object) -> bool:
        return isinstance(value, MACAddress) and self.colon == value.colon

    @property
    def colon(self) -> str:
        """colon-separated hexadecimal (XX:XX:XX:XX:XX:XX)
        """
        return self.__colon_mac

    @property
    def dash(self) -> str:
        """dash-separated hexadecimal (XX-XX-XX-XX-XX-XX)
        """
        return self.__dash_mac
