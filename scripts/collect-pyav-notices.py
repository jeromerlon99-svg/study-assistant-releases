"""Record the PyAV wheel and FFmpeg library provenance for the Windows installer."""

from ctypes import CDLL, c_char_p
from importlib.metadata import distribution
from pathlib import Path
from shutil import copyfile
from sys import argv

import av


def main(output: Path) -> None:
    package = distribution("av")
    files = package.files or ()
    license_path = next(
        file for file in files if file.name == "LICENSE.txt" and file.parent.name == "licenses"
    )
    libraries = sorted(file.name for file in files if file.suffix.lower() == ".dll")
    codec_path = next(
        file for file in files if file.name.startswith("avcodec-") and file.suffix.lower() == ".dll"
    )
    codec = CDLL(str(package.locate_file(codec_path)))
    codec.avcodec_license.restype = c_char_p
    codec.avcodec_configuration.restype = c_char_p

    copyfile(package.locate_file(license_path), output / "PyAV-LICENSE.txt")
    (output / "PyAV-build.txt").write_text(
        f"PyAV {package.version}\n"
        f"FFmpeg version: {av.ffmpeg_version_info}\n"
        f"FFmpeg license: {codec.avcodec_license().decode()}\n"
        f"FFmpeg configuration: {codec.avcodec_configuration().decode()}\n"
        "DLLs in the installed PyAV wheel:\n"
        + "\n".join(libraries)
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main(Path(argv[1]))
