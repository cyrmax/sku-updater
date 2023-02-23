import os
import pathlib
import re
import sys
import winreg
import zipfile

from bs4 import BeautifulSoup as Soup
import requests


SKU_URL = "https://duugu.github.io/Sku"


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
    return value[0]


def get_sku_version(sku_path: pathlib.Path) -> float:
    changelog_path = sku_path / "CHANGELOG.md"
    with changelog_path.open("r") as f:
        txt = f.read()
        version_match = re.search(r"^\# Sku \(((\d+\.\d+)|(\d+))\)", txt)
    if not version_match:
        print("Unable to determine Sku version")
        confirmed_exit(1)
    try:
        version = float(version_match.group(1))
    except ValueError:
        print("Unable to determine Sku version")
        confirmed_exit(1)
    return version


def fetch_sku_version() -> tuple[float, str]:
    rre = re.compile(
        r"^https://github.com/Duugu/Sku/releases/download/r(\d+\.\d+)|(\d+)/Sku-r(\d+\.\d+)|(\d+)-.+\.zip$",
        re.I,
    )
    r = requests.get(SKU_URL)
    page = Soup(r.text, features="html.parser")
    links = page.findAll("a", attrs={"href": rre})
    if len(links) < 1:
        print("Unable to fetch latest Sku version info")
        confirmed_exit(1)
    href = links[0].get("href")
    version_match = re.search(
        r"^https://github.com/Duugu/Sku/releases/download/r(\d+\.\d+)|(\d+)/Sku-r((\d+\.\d+)|(\d+))-.+\.zip$",
        href,
    )
    if not version_match:
        print("Unable to fetch latest Sku version")
        confirmed_exit(1)
    version = float(version_match.group(1))
    return (version, href)


def update_sku(sku_info: tuple[float, str], sku_path: pathlib.Path):
    url = sku_info[1]
    local_filename = url.split("/")[-1]
    print("Downloading... ")
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        with open(local_filename, "wb") as f:
            for chunk in r.iter_content(4096):
                f.write(chunk)
    print("Installing...")
    with zipfile.ZipFile(local_filename, "r") as zf:
        zf.extractall(str(sku_path.parent.resolve()))
    print("Cleaning...")
    os.remove(local_filename)


def main():
    print("Searching World of Warcraft Classic installation...")
    try:
        wowc_path = find_wowc()
    except FileNotFoundError:
        print("Unable to find World of Warcraft Classic installation.")
        confirmed_exit(1)
    print(f"Found WoW Classic at path {wowc_path}")
    sku_path = pathlib.Path(wowc_path) / "Interface" / "AddOns" / "Sku"
    if not sku_path.exists():
        print("Couldn't find Sku folder. Check your installation")
        confirmed_exit(1)
    print(f"Found Sku at path {str(sku_path)}")
    sku_version = get_sku_version(sku_path)
    print(f"Current Sku version is {sku_version}")
    print("Checking for updates...")
    info = fetch_sku_version()
    print(f"Latest available Sku version is {info[0]}")
    if info[0] <= sku_version:
        print("Your version of Sku is equal or newer than latest available. Exiting...")
        confirmed_exit(0)
    answer = input(
        "Do you want to update to the latest version? y - yes, n or other letter - no: "
    )
    if answer != "y":
        print("Ok, not updating.")
        confirmed_exit(0)
    print("Updating...")
    update_sku(info, sku_path)
    print("Verifying update...")
    new_version = get_sku_version(sku_path)
    if sku_version == new_version:
        print("Verification failed!")
        confirmed_exit(1)
    print("Update complete!")
    print(f"Sku updated from {sku_version} to {new_version}")
    confirmed_exit(0)


if __name__ == "__main__":
    main()
