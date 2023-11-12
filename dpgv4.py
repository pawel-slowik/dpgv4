#!/usr/bin/env python3
"""Convert video files to DPG4 format for MoonShell 2 / Nintendo DS."""

import os
import errno
import re
import struct
import subprocess
import json
import csv
import time
import codecs
import logging
import argparse
from tempfile import TemporaryFile
from io import BytesIO
from shutil import copyfileobj
from shlex import quote
from operator import itemgetter
from contextlib import ExitStack
from enum import Enum
from typing import Sequence, Iterable, Set, IO, Mapping, Tuple, Union, NamedTuple, Optional, Any
from PIL import Image

FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"
FFPROBE_JSON = [FFPROBE, "-hide_banner", "-print_format", "json=sv=replace:svr=\uFFFD"]

# For details see docs/framerates.md.
MPEG_SPEC_FRAMERATES = [23.976, 24, 25, 29.97, 30, 50, 59.94, 60]
MPEG_UNOFFICIAL_FRAMERATES = [float(5), 10, 12, 15]
MPEG_FRAMERATES = MPEG_SPEC_FRAMERATES + MPEG_UNOFFICIAL_FRAMERATES

SCREEN_WIDTH = 256
SCREEN_HEIGHT = 192

AUDIO_SAMPLE_RATE = 32000


class AudioCodec(Enum):
    """Available audio codecs."""
    MP2_2CH = 0
    GSM_1CH = 1
    CSM_2CH = 2
    VORBIS_2CH = 3


class PixelFormats(Enum):
    """Available pixel formats.

    The listed pixel formats are not compatible with MPEG-1 video. However the
    value of 3 / RGB24 seems to work, others are not tested. The value is only
    used in the DPG header, not for encoding. See docs/pixel_formats.md."""
    RGB15 = 0
    RGB18 = 1
    RGB21 = 2
    RGB24 = 3


Font = NamedTuple("Font", [("name", Optional[str]), ("size", Optional[int])])


class ExternalCommandError(Exception):
    """Base for all exceptions related to external commands."""


class ExternalCommandNotFoundError(ExternalCommandError):
    """Raised when an external command couldn't be found.

    For example, when the relevant package is not installed or when the command
    is not in $PATH."""

    def __init__(self, command: Any):
        super().__init__(command)
        self.command = command

    def __str__(self) -> str:
        return "\n".join([
            "command not found:",
            process_args_str(self.command),
            "make sure FFmpeg is installed and available in $PATH"
        ])


class ExternalCommandFailedError(ExternalCommandError):
    """Raised when an external command fails."""

    def __init__(self, return_code: int, command: Any, error_message: Union[str, bytes]):
        super().__init__(return_code, command, error_message)
        self.return_code = return_code
        self.command = command
        self.error_message = error_message

    def __str__(self) -> str:
        if isinstance(self.error_message, str):
            error_message = self.error_message
        else:
            try:
                error_message = self.error_message.decode("ascii")
            except UnicodeDecodeError:
                error_message = str(self.error_message)
        return "\n".join((
            "command failed:",
            process_args_str(self.command),
            f"return code: {self.return_code}",
            f"error message: {error_message}",
        ))


def get_aspect_ratio(filename: str) -> Optional[float]:
    """Read aspect ratio from video metadata."""
    cmd = FFPROBE_JSON + [
        "-show_streams", "-select_streams", "v",
        filename
    ]
    raw_output = run_external_command(cmd)
    output = raw_output.decode("utf-8")
    stream_info = json.loads(output)["streams"][0]
    if "display_aspect_ratio" not in stream_info:
        return None
    match = re.search(r"^(\d+):(\d+)$", stream_info["display_aspect_ratio"])
    if match is None:
        return None
    width, height = (float(match.group(1)), float(match.group(2)))
    if width == 0 or height == 0:
        return None
    return width / height


def get_duration(filename: str) -> float:
    """Get video duration in seconds."""
    cmd = FFPROBE_JSON + [
        "-show_entries", "stream=duration:format=duration",
        filename
    ]
    raw_output = run_external_command(cmd)
    output = raw_output.decode("utf-8")
    json_output = json.loads(output)
    if "duration" in json_output["format"]:
        return float(json_output["format"]["duration"])
    for stream_info in json_output["streams"]:
        if "duration" in stream_info:
            return float(stream_info["duration"])
    raise ValueError(f"can't read duration for file: {filename}")


def count_video_frames(file_object: IO[bytes]) -> int:
    """Get the number of video frames."""
    file_object.seek(0)
    cmd = FFPROBE_JSON + [
        "-show_streams", "-count_frames", "-select_streams", "v",
        "-",
    ]
    raw_output = run_external_command(cmd, file_object)
    output = raw_output.decode("utf-8")
    stream_info = json.loads(output)["streams"][0]
    return int(stream_info["nb_read_frames"])


def calculate_dimensions(input_file: str) -> Tuple[int, int]:
    """Get video dimensions, taking metadata aspect ratio into account."""
    debug_msg = "target video dimensions: width %d, height %d, original aspect ratio %s"
    input_aspect_ratio = get_aspect_ratio(input_file)
    if input_aspect_ratio is None:
        logging.debug(debug_msg, SCREEN_WIDTH, SCREEN_HEIGHT, "unknown")
        return SCREEN_WIDTH, SCREEN_HEIGHT
    screen_aspect_ratio = SCREEN_WIDTH / SCREEN_HEIGHT
    if input_aspect_ratio >= screen_aspect_ratio:
        width = SCREEN_WIDTH
        height = int(SCREEN_WIDTH / input_aspect_ratio)
    else:
        height = SCREEN_HEIGHT
        width = int(input_aspect_ratio * SCREEN_HEIGHT)
    logging.debug(debug_msg, width, height, input_aspect_ratio)
    return width, height


def create_gop(mpeg_file_object: IO[bytes]) -> bytes:
    """Create an index that allows faster seeking.

    Note: as far as I can tell, this is not a standard GOP / group of pictures
    structure. It is an index that maps frame numbers to stream offsets.
    This is referred to as `GOPList` in MoonShell:
    misctools/DPGTools/sources/_encvideo.pas
    and simply as `GOP` in other implementations."""

    def row_to_frame(row: Iterable[str]) -> Mapping[str, str]:
        frame = {}
        for item in row:
            if item in ("frame", "side_data"):
                continue
            key, value = item.split("=", 1)
            frame[key] = value
        return frame

    mpeg_file_object.seek(0)
    cmd = [
        FFPROBE,
        "-hide_banner",
        "-print_format", "compact",
        "-show_frames", "-select_streams", "v",
        "-",
    ]
    gop = b""
    frame_number = 0
    stack = ExitStack()
    try:
        process = stack.enter_context(
            subprocess.Popen(
                cmd,
                stdin=mpeg_file_object,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
        )
    except OSError as os_err:
        if os_err.errno == errno.ENOENT:
            raise ExternalCommandNotFoundError(cmd) from os_err
        raise os_err
    with stack:
        data_stream: IO[str] = process.stdout  # type: ignore # opened with PIPE
        for row in csv.reader(data_stream, delimiter="|"):
            if not row or row[0] != "frame":
                continue
            frame = row_to_frame(row)
            if frame["pict_type"] == "I":
                gop += struct.pack("<l", frame_number)
                gop += struct.pack("<l", int(frame["pkt_pos"]))
            frame_number += 1
        process.wait()
        if process.returncode != 0:
            error_stream: IO[str] = process.stderr  # type: ignore # opened with PIPE
            raise ExternalCommandFailedError(process.returncode, process.args, error_stream.read())
    return gop


def create_screenshot(file_object: IO[bytes], seconds: int) -> bytes:
    """Extract single video frame as an image in raw format."""
    file_object.seek(0)
    shot_cmd = [
        FFMPEG,
        "-hide_banner",
        "-ss", str(seconds),
        "-i", "-",
        "-vframes", "1",
        "-f", "rawvideo",
        "-c:v", "bmp",
        "-",
    ]
    output = run_external_command(shot_cmd, file_object)
    return output


def create_thumbnail(image_bytes: bytes) -> bytes:
    """Resize and convert raw image into a format suitable for the DPG4 thumbnail."""
    image = Image.open(BytesIO(image_bytes))
    if image.width != SCREEN_WIDTH or image.height != SCREEN_HEIGHT:
        thumbnail = image.copy()
        thumbnail.thumbnail((SCREEN_WIDTH, SCREEN_HEIGHT))
        image = Image.new(image.mode, (SCREEN_WIDTH, SCREEN_HEIGHT))
        left = int((image.width - thumbnail.width) / 2)
        top = int((image.height - thumbnail.height) / 2)
        image.paste(thumbnail, (left, top))
    image_data = image.getdata()
    thumbnail_data = []
    for i in range(image.height):
        row = []
        for j in range(image.width):
            red = image_data[i * image.width + j][0]
            green = image_data[i * image.width + j][1]
            blue = image_data[i * image.width + j][2]
            pixel = (1 << 15) | ((blue >> 3) << 10) | ((green >> 3) << 5) | (red >> 3)
            row.append(pixel)
        thumbnail_data.append(row)
    return b"".join(struct.pack("H" * len(row), *row) for row in thumbnail_data)


def create_header(
        frame_count: int,
        framerate: float,
        audio_size: int,
        video_size: int,
        gop_size: int
    ) -> bytes:
    """Create the DPG4 header."""
    audio_start = 98356  # 52 header + 98304 thumbnail
    video_start = audio_start + audio_size
    video_end = video_start + video_size
    header_pack_values = [
        ("4s", b"DPG4"),
        ("<l", frame_count),
        ("<l", int(framerate * 0x100)),
        ("<l", AUDIO_SAMPLE_RATE),
        ("<l", AudioCodec.MP2_2CH.value),
        ("<l", int(audio_start)),
        ("<l", int(audio_size)),
        ("<l", int(video_start)),
        ("<l", int(video_size)),
        ("<l", video_end),
        ("<l", gop_size),
        ("<l", PixelFormats.RGB24.value),
        ("4s", b"THM0"),
    ]
    return b"".join([struct.pack(f, v) for (f, v) in header_pack_values])


def prepare_video_conversion_command(
        input_file: str,
        framerate: float,
        quality: int,
        sid: Optional[int],
        font: Optional[Font],
    ) -> Sequence[str]:
    """Prepare the command for converting the video stream."""
    width, height = calculate_dimensions(input_file)
    v_cmd = [
        FFMPEG,
        "-hide_banner",
        "-i", input_file,
        "-f", "data",
        "-map", "0:v:0",
        "-r", f"{framerate:g}",
        "-sws_flags", "lanczos",
        "-s", f"{width}x{height}",
        "-c:v", "mpeg1video",
    ]
    if framerate not in MPEG_SPEC_FRAMERATES:
        v_cmd += ["-strict", "unofficial"]
    v_cmd += video_quality_options()[quality]
    v_cmd += subtitle_options(input_file, sid, font)
    v_cmd.append("-")
    logging.debug("video encoder command: %s", " ".join(map(quote, v_cmd)))
    return v_cmd


def prepare_audio_conversion_command(input_file: str, aid: Optional[int]) -> Sequence[str]:
    """Prepare the command for converting the audio stream."""
    a_cmd = [
        FFMPEG,
        "-hide_banner",
        "-i", input_file,
        "-f", "data",
        "-map", f"0:a:{0 if aid is None else aid}",
        "-c:a", "mp2",
        "-b:a", "320k",
        "-ac", "2",
        "-ar", str(AUDIO_SAMPLE_RATE),
        "-",
    ]
    logging.debug("audio encoder command: %s", " ".join(map(quote, a_cmd)))
    return a_cmd


def video_quality_options() -> Mapping[int, Iterable[str]]:
    """Map quality settings to libavcodec options.

    Keys are choices for the `-q` CLI parameter. Values are ffmpeg / libavcodec
    encoder options, see https://ffmpeg.org/ffmpeg-codecs.html and
    `ffmpeg -h encoder=mpeg1video`"""
    # libavcodec options shared between both quality settings
    lavcopts_base = [
        "-mbd", "2",
        "-trellis", "1",
        "-mpv_flags", "+cbp_rd",
        "-mpv_flags", "+mv0",
        "-b:v", "512k",
    ]
    return {
        # default quality
        1: lavcopts_base + [
            "-cmp", "2",
            "-subcmp", "2",
            "-precmp", "2",
        ],
        # high quality
        2: lavcopts_base + [
            "-cmp", "6",
            "-subcmp", "6",
            "-precmp", "6",
            "-dia_size", "3",
            "-pre_dia_size", "3",
            "-last_pred", "3",
        ],
    }


def subtitle_options(
        input_file: str,
        sid: Optional[int],
        font: Optional[Font] = None,
    ) -> Iterable[str]:
    """Prepare ffmpeg options for rendering the subtitle stream (hardsub)."""

    def quote_sub_filename(filename: str) -> str:
        # the following characters need to be escaped because they have special meaning in the
        # filtergraph syntax: https://ffmpeg.org/ffmpeg-filters.html
        escape_chars = ["[", "]", "=", ";", ","]
        translation_map = str.maketrans({char: "\\" + char for char in escape_chars})
        return filename.translate(translation_map)

    if sid is None:
        return []
    external_sub_file = find_sub_file(input_file)
    if external_sub_file:
        external_sub_count = len(tuple(list_subtitle_streams(external_sub_file)))
        if sid < external_sub_count:
            sub_file = external_sub_file
            sub_index = sid
        else:
            sub_file = input_file
            sub_index = sid - external_sub_count
    else:
        sub_file = input_file
        sub_index = sid
    filter_options = [
        f"filename={quote_sub_filename(sub_file)}",
        f"stream_index={sub_index}",
    ]
    style = []
    if font:
        if font.name is not None:
            style.append(f"FontName={font.name}")
        if font.size is not None:
            style.append(f"FontSize={font.size}")
    if style:
        filter_options.append(f"force_style='{','.join(style)}'")
    return ["-vf", f"subtitles={':'.join(filter_options)}"]


def parse_subtitle_stream_id(input_file: str, input_sid: Union[int, str, None]) -> Optional[int]:
    """Translate the CLI `-s` parameter into a stream index suitable for subtitle_options()."""
    subtitle_streams = tuple(list_subtitle_streams(input_file))
    external_sub_file = find_sub_file(input_file)
    if input_sid is None:
        return 0 if subtitle_streams or external_sub_file else None
    try:
        stream_index = int(input_sid)
    except ValueError:
        pass
    else:
        return stream_index if stream_index >= 0 else None
    language = str(input_sid)
    if external_sub_file:
        # external subtitles don't have the necessary metadata
        raise ValueError("matching external subtitles to a language code is not supported")
    for index, stream in enumerate(sorted(subtitle_streams, key=itemgetter("index"))):
        if stream_matches_language(stream, language):
            return index
    raise ValueError(f"no subtitles found for language: {language}")


def list_subtitle_streams(input_file: str) -> Iterable[Mapping]:
    """List subtitle streams."""
    cmd = FFPROBE_JSON + [
        "-show_streams", "-select_streams", "s",
        input_file,
    ]
    raw_output = run_external_command(cmd)
    output = raw_output.decode("utf-8")
    return json.loads(output)["streams"]  # type: ignore


def stream_matches_language(stream: Mapping, language: str) -> bool:
    """Check if a stream matches given language."""
    language = language.lower()
    try:
        tags = stream["tags"]
        return bool(
            tags["language"].lower() == language
            or tags["title"].lower() == language
        )
    except KeyError:
        return False


def find_sub_file(filename: str) -> Optional[str]:
    """Find an external subtitle file for a video file.

    For example, a file named `movies/title.srt` (if it exists) is an external
    subtitle file for `movies/title.avi`."""
    basename = os.path.splitext(filename)[0]
    for extension in [".ass", ".srt", ".ssa", ".sub"]:
        if os.path.exists(basename + extension):
            return basename + extension
    return None


def file_size(file_object: IO[bytes]) -> int:
    """Get file size for a file object."""
    return os.stat(file_object.fileno()).st_size


def read_progress(label: str, stream: IO[bytes]) -> str:
    """Read and log progress from ffmpeg encoding command.

    Return a single string with all the lines of the stream that couldn't be
    parsed as progress information, which are most likely error messages."""
    total = None
    time_previous = time.monotonic()
    skipped_lines = []
    reader_factory = codecs.getreader("utf-8")
    for line in reader_factory(stream, errors="backslashreplace"):
        new_total = parse_progress_total(line)
        if total is None:
            total = new_total
        current = parse_progress_current(line)
        if new_total is None and current is None:
            skipped_lines.append(line)
        if total is None or current is None:
            continue
        percent_current = current / total * 100
        time_current = time.monotonic()
        if time_current - time_previous > 5:
            time_previous = time_current
            logging.info("%s encoding progress: %.2f%%", label, percent_current)
    return "".join(skipped_lines)


def parse_progress_current(line: str) -> Optional[float]:
    """Extract time in seconds from ffmpeg progress report line."""
    return parse_progress_line("time=", line)


def parse_progress_total(line: str) -> Optional[float]:
    """Extract time in seconds from ffmpeg summary information line."""
    return parse_progress_line(r"Duration:\s+", line)


def parse_progress_line(prefix: str, line: str) -> Optional[float]:
    """Extract time in seconds from a prefixed string."""
    regexp = prefix + r"(?P<hours>\d+):(?P<minutes>\d{2}):(?P<seconds>\d{2}.\d{2})"
    match = re.search(regexp, line)
    if not match:
        return None
    return (
        int(match.group("hours")) * 3600
        + int(match.group("minutes")) * 60
        + float(match.group("seconds"))
    )


def convert_file(input_file: str, output_file: str, options: Any) -> None:
    """Convert a single video file to the DPG4 format."""
    logging.info("processing file: %s", quote(input_file))
    v_cmd = prepare_video_conversion_command(
        input_file,
        options.framerate, options.quality,
        parse_subtitle_stream_id(input_file, options.sid),
        Font(name=options.font_name, size=options.font_size)
    )
    v_tmp_file = TemporaryFile()
    encode_stream("video", v_cmd, v_tmp_file)
    #Extend file if it's short
    if count_video_frames(v_tmp_file) / options.framerate < 30:
        for i in list(reversed(['-stream_loop','-1','-t','30'])):
            v_cmd.insert(1,i)
        v_tmp_file = TemporaryFile()
        encode_stream("video", v_cmd, v_tmp_file)
    a_cmd = prepare_audio_conversion_command(input_file, options.aid)
    #Create blank audio if no codec exists
    try:
        a_tmp_file = TemporaryFile()
        encode_stream("audio", a_cmd, a_tmp_file)
    except ExternalCommandFailedError:
        a_tmp_file = TemporaryFile()
        for i in list(reversed(['-t',str(count_video_frames(v_tmp_file) / options.framerate),'-f','lavfi','-i','anullsrc'])):
            a_cmd.insert(1,i)
        encode_stream("audio", a_cmd, a_tmp_file)
    gop = create_gop(v_tmp_file)
    thumbnail = create_thumbnail(create_screenshot(v_tmp_file, int(get_duration(input_file) / 10)))
    header = create_header(
        count_video_frames(v_tmp_file),
        options.framerate,
        file_size(a_tmp_file),
        file_size(v_tmp_file),
        len(gop)
    )
    logging.debug("writing output file: %s", quote(output_file))
    if not os.path.exists(os.path.dirname(output_file)):
        os.makedirs(os.path.dirname(output_file))
    v_tmp_file.seek(0)
    a_tmp_file.seek(0)
    with open(output_file, "wb") as outfile:
        outfile.write(header)
        outfile.write(thumbnail)
        copyfileobj(a_tmp_file, outfile)
        copyfileobj(v_tmp_file, outfile)
        outfile.write(gop)
    logging.info("done: %s -> %s", quote(input_file), quote(output_file))


def encode_stream(label: str, command: Sequence[str], output: IO[bytes]) -> None:
    """Run a ffmpeg encoding command."""
    stack = ExitStack()
    try:
        proc = stack.enter_context(
            subprocess.Popen(command, stdout=output, stderr=subprocess.PIPE)
        )
    except OSError as os_err:
        if os_err.errno == errno.ENOENT:
            raise ExternalCommandNotFoundError(command) from os_err
        raise os_err
    with stack:
        progress_stream: IO[bytes] = proc.stderr  # type: ignore # opened with PIPE
        error_message = read_progress(label, progress_stream)
    if proc.returncode != 0:
        raise ExternalCommandFailedError(proc.returncode, proc.args, error_message)


def list_media_files(directory: str) -> Iterable[str]:
    """Recursively list all convertable video files in a directory."""
    media_extensions = [
        "avi",
        "flv",
        "m4v",
        "mkv",
        "mov",
        "mp4",
        "mpeg",
        "mpg",
        "ogm",
        "webm",
        "wmv",
    ]
    for dirpath, _, filenames in os.walk(directory):
        for filename in filenames:
            if os.path.splitext(filename)[1][1:].lower() in media_extensions:
                yield os.path.join(dirpath, filename)


def list_input_files(inputs: Iterable[str]) -> Set[str]:
    """Prepare a list of input files based on CLI arguments.

    This means:
    - replace directories with list of media files in a directory,
    - remove duplicates to avoid encoding a single file more than once,
    - convert to absolute paths."""

    def gen_input_files(inputs: Iterable[str]) -> Iterable[str]:
        for inp in inputs:
            if os.path.isdir(inp):
                yield from list_media_files(inp)
            else:
                yield inp

    return set(map(os.path.abspath, gen_input_files(inputs)))


def create_task_list(input_files: Set[str], output: Optional[str]) -> Iterable[Tuple[str, str]]:
    """Prepare a list of (input_file, output_file) pairs."""

    def output_filename(input_filename: str) -> str:
        return os.path.splitext(input_filename)[0] + ".dpg"

    if output is not None:
        if len(input_files) == 1:
            single_input_file = input_files.copy().pop()
            if output.endswith(".dpg"):
                single_output_file = output
            else:
                single_output_file = os.path.join(
                    output,
                    os.path.basename(output_filename(single_input_file))
                )
            return [(single_input_file, single_output_file)]
        common_input = os.path.commonpath(list(input_files))
        return [
            (
                input_file,
                os.path.join(
                    output,
                    os.path.relpath(output_filename(input_file), common_input)
                )
            )
            for input_file in input_files
        ]
    return [
        (input_file, output_filename(input_file))
        for input_file in input_files
    ]


def run_external_command(command: Sequence[str], stdin: Optional[IO[bytes]] = None) -> bytes:
    """Run an external command.

    The purpose of this wrapper is to make it easier to signal missing dependencies and
    configuration issues. Specialized exceptions are used for this purpose."""
    try:
        with subprocess.Popen(
            command,
            stdin=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        ) as process:
            (stdout, stderr) = process.communicate()
    except OSError as os_err:
        if os_err.errno == errno.ENOENT:
            raise ExternalCommandNotFoundError(command) from os_err
        raise os_err
    if process.returncode != 0:
        raise ExternalCommandFailedError(process.returncode, process.args, stderr)
    return stdout


def process_args_str(args: Any) -> str:
    """Convert subprocess.Popen.args to a string suitable for exceptions / debugging."""
    if isinstance(args, str):
        return args
    if isinstance(args, bytes):
        return str(args)
    if isinstance(args, Sequence) and args:
        if isinstance(args[0], str):
            return " ".join(args)
        if isinstance(args[0], bytes):
            return str(b" ".join(args))
    return repr(args)


def main() -> None:
    """A simple CLI for the module. Run with `-h` for help."""
    parser = argparse.ArgumentParser(
        description="Convert video files to DPG4 format used by MoonShell for Nintendo DS."
    )
    parser.add_argument("files", nargs="+", help="input files and / or directories")
    parser.add_argument("-o", dest="output", help="output file or directory")
    parser.add_argument(
        "-v", action="store_true", dest="verbose", default=False,
        help="increase verbosity"
    )
    video_group = parser.add_argument_group("video options")
    video_group.add_argument(
        "-q", type=int, dest="quality", choices=video_quality_options().keys(), default=2,
        help="quality setting (default: 2)"
    )
    video_group.add_argument(
        "-r", type=float, dest="framerate", choices=MPEG_FRAMERATES, default=24,
        help="framerate (default: 24)"
    )
    audio_group = parser.add_argument_group("audio options")
    audio_group.add_argument(
        "-a", type=int, dest="aid", metavar="AID",
        help="use audio stream AID"
    )
    subtitle_group = parser.add_argument_group("subtitle options")
    subtitle_group.add_argument(
        "-s", dest="sid", metavar="SID",
        help="""
            use subtitle stream SID, specify language code or stream index
            (default: first available stream, -1 to disable)
        """
    )
    subtitle_group.add_argument(
        "-f", dest="font_name", help="font name (libass style FontName)"
    )
    subtitle_group.add_argument(
        "-p", type=int, dest="font_size", default=22,
        help="font size (libass style FontSize, default: 22)"
    )
    args = parser.parse_args()
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.DEBUG if args.verbose else logging.INFO,
    )
    if args.framerate not in MPEG_SPEC_FRAMERATES:
        logging.warning("non standard framerate: %s, sync issues may occur", args.framerate)
    for input_file_or_dir in args.files:
        if not os.path.exists(input_file_or_dir):
            raise ValueError(f"file or directory doesn't exist: {input_file_or_dir}")
    for input_file, output_file in create_task_list(list_input_files(args.files), args.output):
        convert_file(input_file, output_file, args)


if __name__ == "__main__":
    main()
