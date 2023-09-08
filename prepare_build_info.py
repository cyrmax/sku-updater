# This file scans the environment before build process starts and populates build_info.py file with current installed package versions and operating system info.
# Information from build_info.py is later shown to the end user when the program starts and also is written to the log file.

import platform
import os
import sys

try:
    from pip._internal.operations import freeze
except ImportError:
    from pip.operations import freeze

print("Generating and populating build_info.py")
with open("build_info.py", "w", encoding="utf8") as f:
    f.write(
        "# This file contains all necessary debug information about the build process.\n"
    )
    f.write(
        "# This file should be regenerated directly before build process for to contain actual info about build environment.\n"
    )
    f.write(
        f'sku_updater_version = "{os.environ.get("GITHUB_REF_NAME", sys.argv[1])}"\n'
    )
    f.write(f'build_platform = "{platform.platform()}"\n')
    f.write(f'build_python_version = "{sys.version}"\n')
    f.write('pip_freeze_output = """\n')
    f.write("\n".join(pkg for pkg in freeze.freeze()))
    f.write('\n"""\n')

print("Finished generating build_info.py")
