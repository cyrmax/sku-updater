# Sku Updater

Sku Updater is a tiny program which allows you to update your installation of Sku addon without opening browser, checking for latest release, downloading, unpacking and copying addon files manually.

[Sku](https://duugu.github.com/Sku) is an addon which adds accessibility to Blizzard's World of Warcraft Classic online RPG game.


## Usage

To use Sku Updater just download prebuilt binary executable from releases page or build the program from sources.


## Using source and building executable

As Sku Updater is a Python3 program you can use it without building executable. 
But to use raw source script you need Python version 3.10 or newer installed on your computer.

To build Sku Updater executable file you should execute following steps:

* Install Python version 3.10 or newer;
* Clone this repository with git clone https://github.com/cyrmax/sku-updater or just download source code as zip archive and unpack it;
* Open windows command prompt inside repository directory;
* Create Python virtual environment (python -m venv .venv);
* Activate virtual environment (.venv\scripts\activate);
* Install runtime requirements (pip install -r requirements.txt);

If you want to use raw source script, this is enough. Now you can launch the program by executing python sku-updater.py. 
Note that you have to keep virtual environment active or else script will fail.

If you want to compile an executable version of Sku Updater to be run without any Python installation, do the following:

* Activate virtual environment created earlier if you have closed command prompt;
* Install build requirements either for pyinstaller or for nuitka (pip install -r build-requirements-pyi.txt or pip install -r build-requirements-pyi.txt);
* Execute one of the following commands: pyinstaller sku-updater.spec or nuitka --onefile --standalone --lto=yes sku-updater.py.

Note that current nuitka version 1.2.4 does not support Python 3.11.
So to build with latest Python you will have to use pyinstaller.
