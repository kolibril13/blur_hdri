# mostly identical to from https://github.com/BradyAJohnston/MolecularNodes/blob/main/build.py
# run with
# /Applications/Blender.app/Contents/MacOS/Blender -b -P build.py
# and later with
# /Applications/Blender.app/Contents/MacOS/Blender --command extension build --split-platforms

import glob
import os
import subprocess
import sys
from dataclasses import dataclass
from typing import List, Union
import bpy



ADDON_NAME = "blur_hdri" # TO CHANGE
TOML_PATH = f"./{ADDON_NAME}/blender_manifest.toml"
WHL_PATH = f"./{ADDON_NAME}/wheels"

# Instead of reading from pyproject.toml, define the required packages here:
required_packages = [
    "Pillow",
    "OpenEXR",
    "numpy<2.0",
    # Add any other required packages here
]

def run_python(args: str | List[str]):
    python = os.path.realpath(sys.executable)

    if isinstance(args, str):
        args = [python] + args.split(" ")
    elif isinstance(args, list):
        args = [python] + args
    else:
        raise ValueError(
            "Arguments must be a string to split into individual arguments by space"
            "or a list of individual arguments already split"
        )

    subprocess.run(args)


try:
    import tomlkit
except ModuleNotFoundError:
    run_python("-m pip install tomlkit")
    import tomlkit




@dataclass
class Platform:
    pypi_suffix: str
    metadata: str


# tags for blender metadata
# platforms = ["windows-x64", "macos-arm64", "linux-x64", "windows-arm64", "macos-x64"]


windows_x64 = Platform(pypi_suffix="win_amd64", metadata="windows-x64")
linux_x64 = Platform(pypi_suffix="manylinux2014_x86_64", metadata="linux-x64")
macos_arm = Platform(pypi_suffix="macosx_12_0_arm64", metadata="macos-arm64")
macos_intel = Platform(pypi_suffix="macosx_10_16_x86_64", metadata="macos-x64")

build_platforms = [
    windows_x64,
    linux_x64,
    macos_arm,
    macos_intel,
]


def remove_whls():
    for whl_file in glob.glob(os.path.join(WHL_PATH, "*.whl")):
        os.remove(whl_file)


def download_whls(
    platforms: Union[Platform, List[Platform]],
    required_packages: List[str] = required_packages,
    python_version="3.11",
    clean: bool = True,
):
    if isinstance(platforms, Platform):
        platforms = [platforms]

    if clean:
        remove_whls()

    for platform in platforms:
        run_python(
            f"-m pip download {' '.join(required_packages)} --dest {WHL_PATH} --only-binary=:all: --python-version={python_version} --platform={platform.pypi_suffix}"
        )


def update_toml_whls(platforms):
    # Define the path for wheel files
    wheel_files = glob.glob(f"{WHL_PATH}/*.whl")
    wheel_files.sort()

    # Packages to remove
    packages_to_remove = {
        "certifi",
        "charset_normalizer",
        "idna",
        "requests",
        "urllib3",
    }

    # Filter out unwanted wheel files
    to_remove = []
    to_keep = []
    for whl in wheel_files:
        if any(pkg in whl for pkg in packages_to_remove):
            to_remove.append(whl)
        else:
            to_keep.append(whl)

    # Remove the unwanted wheel files from the filesystem
    for whl in to_remove:
        os.remove(whl)

    # Load the TOML file
    with open(TOML_PATH, "r") as file:
        manifest = tomlkit.parse(file.read())

    # Update the wheels list with the remaining wheel files
    manifest["wheels"] = [f"./wheels/{os.path.basename(whl)}" for whl in to_keep]

    # Simplify platform handling
    if not isinstance(platforms, list):
        platforms = [platforms]
    manifest["platforms"] = [p.metadata for p in platforms]

    # Write the updated TOML file
    with open(TOML_PATH, "w") as file:
        file.write(
            tomlkit.dumps(manifest)
            .replace('["', '[\n\t"')
            .replace("\\\\", "/")
            .replace('", "', '",\n\t"')
            .replace('"]', '",\n]')
        )


def clean_files(suffix: str = ".blend1") -> None:
    pattern_to_remove = f"./**/*{suffix}"
    for blend1_file in glob.glob(pattern_to_remove, recursive=True):
        os.remove(blend1_file)


def build_extension(split: bool = True) -> None:
    for suffix in [".blend1", ".MNSession"]:
        clean_files(suffix=suffix)

    if split:
        subprocess.run(
            f"{bpy.app.binary_path} --command extension build"
            f" --split-platforms --source-dir {ADDON_NAME} --output-dir ".split(" ")
        )
    else:
        subprocess.run(
            f"{bpy.app.binary_path} --command extension build "
            f"--source-dir {ADDON_NAME} --output-dir .".split(" ")
        )


def build(platform) -> None:
    download_whls(platform)
    update_toml_whls(platform)
    build_extension()


def main():
    # for platform in build_platforms:
    #     build(platform)
    build(build_platforms)


if __name__ == "__main__":
    main()