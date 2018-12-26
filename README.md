dpgv4 is a [FFmpeg](https://www.ffmpeg.org/) wrapper for converting video files
to DPG4 format. The DPG format is used by the
[MoonShell 2](https://wiki.gbatemp.net/wiki/Moonshell) media player for the
[Nintendo DS](https://en.wikipedia.org/wiki/Nintendo_DS_family) handheld
console.

## Installation

There is no installation script yet. The script runs on Linux, should also run
on BSD variants. Clone this repository and make sure you have Python 3.x,
[Pillow](https://python-pillow.org/) and FFmpeg installed.

## Usage

Run:

	~/path/dpgv4.py *.mp4

Run with `--help` for a list of options.

Run with `-v` to see the ffmpeg commands used for reencoding. Note that the
ffmpeg commands write binary audio / video data to STDOUT, so if you decide to
run them e.g. for debugging purposes, you should probably redirect the output
to a file.

## Similar projects

- [DPG for X](http://dpg4x.sourceforge.net/) - GUI
- [dpgconv](https://github.com/artm/dpgconv) - CLI

How is this project different?

- uses FFmpeg (ffmpeg and ffprobe) instead of mplayer / mencoder / mpeg_stat,
- only supports version 4 of the DPG format,
- less options / quality settings to play with,
- better temporary file handling with tempfile.TemporaryFile,
- modern code structure: small, hopefully easy to understand functions, tests,
  pylint.
