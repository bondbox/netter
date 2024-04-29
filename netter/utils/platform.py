# coding:utf-8

import platform

CURRENT_OS = platform.system()


class UnsupportedOS(OSError):
    def __init__(self, *args: str):
        if len(args) > 1:
            allowed_os: str = ", ".join(args)
            message: str = f"Unsupported OS: {CURRENT_OS} not in {allowed_os}"
        else:
            message: str = f"Unsupported OS: {CURRENT_OS}"
        super().__init__(message)


def is_windows() -> bool:
    return CURRENT_OS == "Windows"


def assert_windows() -> None:
    if not is_windows():
        raise UnsupportedOS()


def is_linux() -> bool:
    return CURRENT_OS == "Linux"


def assert_linux() -> None:
    if not is_linux():
        raise UnsupportedOS()


def is_macos() -> bool:
    return CURRENT_OS == "Darwin"


def assert_macos() -> None:
    if not is_macos():
        raise UnsupportedOS()


def is_unix() -> bool:  # linux and macOS
    return CURRENT_OS in ["Linux", "Darwin"]


def assert_unix() -> None:
    if not is_unix():
        raise UnsupportedOS("Linux", "Darwin")
