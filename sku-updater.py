from argparse import ArgumentParser
from datetime import datetime as dt
from functools import total_ordering
import json
import logging
import os
import pathlib
import platform
import re
import sys
from time import time
import winreg
import zipfile

import requests

import build_info

SKU_URL = "https://api.github.com/repos/Duugu/Sku/releases/latest"
TITLE_UPDATE_TIMESTAMP = time()


def update_title(downloaded_size: int, total_size: int):
    global TITLE_UPDATE_TIMESTAMP
    if TITLE_UPDATE_TIMESTAMP + 1 >= time():
        return
    os.system(
        f"title {downloaded_size / (1024 * 1024):.2f} MB of {total_size / (1024 * 1024):.2f} MB, {downloaded_size / total_size * 100:.2f}%. Sku Updater"
    )
    TITLE_UPDATE_TIMESTAMP = time()


def handle_exception(exc_type, exc_value, tb):
    logging.fatal("Uncaught exception occurred", exc_info=(exc_type, exc_value, tb))
    sys.__excepthook__(exc_type, exc_value, tb)


@total_ordering
class Version:
    major: int
    minor: int

    def __init__(self, version_string: str):
        if not version_string:
            raise ValueError("Empty version string")
        components = version_string.split(".")
        self.major = int(components[0])
        self.minor = int(components[1]) if len(components) > 1 else 0

    def __eq__(self, other) -> bool:
        return self.major == other.major and self.minor == other.minor

    def __lt__(self, other) -> bool:
        if self.major != other.major:
            return self.major < other.major
        else:
            return self.minor < other.minor

    def __gt__(self, other) -> bool:
        if self.major != other.major:
            return self.major > other.major
        else:
            return self.minor > other.minor

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}"

    def __repr__(self):
        return str(self)


def confirmed_exit(code: int):
    print("Press enter to exit program")
    input()
    sys.exit(code)


def find_wowc() -> str:
    key = winreg.OpenKey(
        winreg.HKEY_LOCAL_MACHINE,
        r"SOFTWARE\WOW6432Node\Blizzard Entertainment\World of Warcraft",
    )
    value = winreg.QueryValueEx(key, "InstallPath")
    path = pathlib.Path(value[0]).parent / "_classic_"
    return str(path)


def get_sku_version(sku_path: pathlib.Path) -> Version:
    changelog_path = sku_path / "CHANGELOG.md"
    with changelog_path.open("r") as f:
        txt = f.read()
        version_match = re.search(r"^\# Sku \(((\d+\.\d+)|(\d+))\)", txt)
    if not version_match:
        print("Unable to determine Sku version")
        confirmed_exit(1)
    try:
        version = Version(version_match.group(1))
    except ValueError:
        print("Unable to determine Sku version")
        confirmed_exit(1)
    return version


def fetch_sku_version() -> tuple[Version, str]:
    logging.debug("Fetching latest Sku version")
    r = requests.get(SKU_URL)
    logging.debug(f"Fetched Sku latest release info with response {r.status_code}")
    if r.status_code != 200:
        print("Unable to fetch latest Sku version")
        confirmed_exit(1)
    data = json.loads(r.text)
    version_re = re.compile(r"^r([\d\.]+)$")
    version_match = version_re.search(data["tag_name"])
    if not version_match:
        print("Unable to determine latest Sku version")
        logging.error("Unable to determine latest Sku version")
        confirmed_exit(1)
    version = Version(version_match.group(1))
    asset_url = None
    for asset in data["assets"]:
        if asset["name"].endswith(".zip"):
            asset_url = asset["browser_download_url"]
            break
    if asset_url is None:
        print("Unable to determine latest Sku version")
        logging.error("Unable to determine latest Sku version")
        confirmed_exit(1)
    return (version, asset_url)


def update_sku(sku_info: tuple[float, str], sku_path: pathlib.Path):
    logging.debug("Downloading and updating Sku")
    url = sku_info[1]
    local_filename = url.split("/")[-1]
    print("Downloading... ")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        downloaded_size = 0
        total_size = int(r.headers["Content-Length"])
        print(f"{total_size / (1024 * 1024):.2f} MB will be downloaded")
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(16384):
                f.write(chunk)
                f.flush()
                downloaded_size += len(chunk)
                update_title(downloaded_size, total_size)
    print("Installing...")
    os.system("title installing Sku. Sku Updater")
    with zipfile.ZipFile(local_filename, "r") as zf:
        zf.extractall(str(sku_path.parent.resolve()))
    print("Cleaning...")
    os.remove(local_filename)


def main():
    logging.basicConfig(
        filename="sku-updater.log",
        encoding="utf-8",
        level=logging.DEBUG,
        format="%(levelname)s: %(message)s",
    )
    sys.excepthook = handle_exception
    parser = ArgumentParser()
    parser.add_argument(
        "-f",
        "--force",
        help="Force update even if local version is equal or never than latest available. Mainly used for testing purposes.",
        action="store_true",
    )
    parser.add_argument(
        "--diagnostic",
        help="Just save diagnostic information to log file and exit without updating.",
        action="store_true",
    )
    args = parser.parse_args()
    logging.info(f"Sku Updater started at {dt.now()}")
    logging.info(f"Running on {platform.platform()}")
    logging.info(f"Using Python version {sys.version}")
    logging.info(f"Sku Updater version is {build_info.sku_updater_version}")
    logging.debug(f"Sku Updater was build on {build_info.build_platform}")
    logging.debug(
        f"Sku Updater was build with Python version {build_info.build_python_version}"
    )
    logging.debug(
        f"Sku was build with the following packages in build environment:\n{build_info.pip_freeze_output}"
    )
    logging.info(f"Command line parameters: {args}")
    os.system("title Sku Updater")
    if args.diagnostic:
        print(
            "Diagnostic info saved to sku-updater.log file. If necessary, send it to the developer."
        )
        confirmed_exit(0)
    print("Searching World of Warcraft Classic installation...")
    logging.debug("Searching World of Warcraft Classic installation...")
    try:
        wowc_path = find_wowc()
    except FileNotFoundError:
        print("Unable to find World of Warcraft Classic installation.")
        logging.warning("Unable to find World of Warcraft Classic installation.")
        confirmed_exit(1)
    print(f"Found WoW Classic at path {wowc_path}")
    logging.info(f"Found WoW Classic at path {wowc_path}")
    sku_path = pathlib.Path(wowc_path) / "Interface" / "AddOns" / "Sku"
    logging.debug(f"Expecting Sku installation at path {sku_path}")
    if not sku_path.exists():
        print("Couldn't find Sku folder. Check your installation")
        logging.warning("Could not find Sku installation.")
        confirmed_exit(1)
    print(f"Found Sku at path {str(sku_path)}")
    logging.info(f"Found Sku at path {str(sku_path)}")
    sku_version = get_sku_version(sku_path)
    print(f"Current Sku version is {sku_version}")
    logging.info(f"Current Sku version is {sku_version}")
    print("Checking for updates...")
    info = fetch_sku_version()
    print(f"Latest available Sku version is {info[0]}")
    logging.info(f"Latest available Sku version is {info[0]}")
    if info[0] <= sku_version and not args.force:
        print("Your version of Sku is equal or newer than latest available. Exiting...")
        confirmed_exit(0)
    answer = input(
        "Do you want to update to the latest version? y - yes, n or other letter - no: "
    )
    if answer != "y":
        print("Ok, not updating.")
        logging.warning(f'User declined update with answer "{answer}"')
        confirmed_exit(0)
    print("Updating...")
    logging.debug("Updating Sku")
    update_sku(info, sku_path)
    print("Verifying update...")
    logging.debug("Verifying update")
    new_version = get_sku_version(sku_path)
    if sku_version == new_version:
        print("Verification failed!")
        logging.warning("Verification failed")
        confirmed_exit(1)
    print("Update complete!")
    logging.debug("Update complete")
    print(f"Sku updated from {sku_version} to {new_version}")
    logging.info(f"Sku updated from {sku_version} to {new_version}")
    confirmed_exit(0)


if __name__ == "__main__":
    main()
