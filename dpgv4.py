#!/usr/bin/env python3

import os
import errno
import re
import struct
import subprocess
import json
import csv
import logging
from tempfile import TemporaryFile
from io import BytesIO
from shutil import copyfileobj
from shlex import quote
from enum import Enum
from PIL import Image

FFMPEG = "ffmpeg"
FFPROBE = "ffprobe"

# For details see docs/framerates.txt.
MPEG_SPEC_FRAMERATES = [23.976, 24, 25, 29.97, 30, 50, 59.94, 60]
MPEG_UNOFFICIAL_FRAMERATES = [5, 10, 12, 15]
MPEG_FRAMERATES = MPEG_SPEC_FRAMERATES + MPEG_UNOFFICIAL_FRAMERATES

SCREEN_WIDTH = 256
SCREEN_HEIGHT = 192

AUDIO_SAMPLE_RATE = 32000

class AudioCodec(Enum):
    MP2_2CH = 0
    GSM_1CH = 1
    CSM_2CH = 2
    VORBIS_2CH = 3

# The listed pixel formats are not compatible with MPEG-1 video. However the
# value of 3 / RGB24 seems to work, others are not tested. The value is only
# used in the DPG header, not for encoding. See docs/pixel_formats.txt.
class PixelFormats(Enum):
    RGB15 = 0
    RGB18 = 1
    RGB21 = 2
    RGB24 = 3

class ExternalCommandError(Exception):
    pass

class ExternalCommandNotFoundError(ExternalCommandError):
    pass

class ExternalCommandFailedError(ExternalCommandError):
    pass

def get_aspect_ratio(filename):
    cmd = [
        FFPROBE,
        "-print_format", "json",
        "-show_streams", "-select_streams", "v",
        filename
    ]
    output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
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

def get_duration(filename):
    cmd = [
        FFPROBE,
        "-print_format", "json",
        "-show_entries", "stream=duration", "-select_streams", "v",
        filename
    ]
    output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
    stream_info = json.loads(output)["streams"][0]
    return float(stream_info["duration"])

def count_video_frames(file_object):
    file_object.seek(0)
    cmd = [
        FFPROBE,
        "-print_format", "json",
        "-show_streams", "-count_frames", "-select_streams", "v",
        "-",
    ]
    output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL, stdin=file_object)
    stream_info = json.loads(output)["streams"][0]
    return int(stream_info["nb_read_frames"])

def calculate_dimensions(input_file):
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

def create_gop(mpeg_file_object):

    def row_to_frame(row):
        frame = {}
        for item in row:
            if item == "frame":
                continue
            key, value = item.split("=", 1)
            frame[key] = value
        return frame

    mpeg_file_object.seek(0)
    cmd = [
        FFPROBE,
        "-print_format", "compact",
        "-show_frames", "-select_streams", "v",
        "-",
    ]
    gop = b""
    frame_number = 0
    with subprocess.Popen(
            cmd,
            stdin=mpeg_file_object,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            universal_newlines=True,
    ) as process:
        for row in csv.reader(process.stdout, delimiter="|"):
            if not row or row[0] != "frame":
                continue
            frame = row_to_frame(row)
            if frame["pict_type"] == "I":
                gop += struct.pack("<l", frame_number)
                gop += struct.pack("<l", int(frame["pkt_pos"]))
            frame_number += 1
    return gop

def create_screenshot(file_object, seconds):
    file_object.seek(0)
    shot_cmd = [
        FFMPEG,
        "-ss", str(seconds),
        "-i", "-",
        "-vframes", "1",
        "-f", "rawvideo",
        "-c:v", "bmp",
        "-",
    ]
    return subprocess.check_output(shot_cmd, stderr=subprocess.DEVNULL, stdin=file_object)

def create_thumbnail(image_bytes):
    image = Image.open(BytesIO(image_bytes))
    if image.width != SCREEN_WIDTH or image.height != SCREEN_HEIGHT:
        image = image.resize((SCREEN_WIDTH, SCREEN_HEIGHT))
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

def create_header(frame_count, framerate, audio_size, video_size, gop_size):
    audio_start = 98356 # 52 header + 98304 thumbnail
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

def prepare_video_conversion_command(input_file, framerate, quality, sid, font):
    width, height = calculate_dimensions(input_file)
    v_cmd = [
        FFMPEG,
        "-i", input_file,
        "-f", "data",
        "-map", "0:v:0",
        "-r", "%g" % framerate,
        "-sws_flags", "lanczos",
        "-s", "%dx%d" % (width, height),
        "-c:v", "mpeg1video",
    ]
    if framerate not in MPEG_SPEC_FRAMERATES:
        v_cmd += ["-strict", "unofficial"]
    v_cmd += video_quality_options()[quality]
    v_cmd += subtitle_options(input_file, sid, font)
    v_cmd.append("-")
    logging.debug("video encoder command: %s", " ".join(map(quote, v_cmd)))
    return v_cmd

def prepare_audio_conversion_command(input_file, aid):
    a_cmd = [
        FFMPEG,
        "-i", input_file,
        "-f", "data",
        "-map", "0:a:%d" % (0 if aid is None else aid),
        "-c:a", "mp2",
        "-b:a", "128k",
        "-ac", "2",
        "-ar", str(AUDIO_SAMPLE_RATE),
        "-",
    ]
    logging.debug("audio encoder command: %s", " ".join(map(quote, a_cmd)))
    return a_cmd

def video_quality_options():
    # libavcodec options shared between both quality settings
    lavcopts_base = [
        "-mbd", "2",
        "-trellis", "1",
        "-mpv_flags", "+cbp_rd",
        "-mpv_flags", "+mv0",
        "-b:v", "256k",
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

def subtitle_options(input_file, sid, font):

    def quote_sub_filename(filename):
        # the following characters need to be escaped because they have special meaning in the
        # filtergraph syntax: https://ffmpeg.org/ffmpeg-filters.html
        escape_chars = ["[", "]", "=", ";", ","]
        return filename.translate(str.maketrans({char: "\\" + char for char in escape_chars}))

    if sid is None:
        return []
    filter_options = [
        "filename=%s" % quote_sub_filename(input_file),
        "stream_index=%d" % sid,
    ]
    if font is not None:
        filter_options.append("force_style=\"FontName=%s\"" % font)
    return ["-vf", "subtitles=%s" % ":".join(filter_options)]

def count_subtitle_streams(input_file):
    cmd = [
        FFPROBE,
        "-print_format", "json",
        "-show_streams", "-select_streams", "s",
        input_file,
    ]
    output = subprocess.check_output(cmd, stderr=subprocess.DEVNULL)
    return len(json.loads(output)["streams"])

def parse_subtitle_stream_id(input_file, input_sid):
    if input_sid is None:
        return 0 if count_subtitle_streams(input_file) else None
    return input_sid if input_sid >= 0 else None

def file_size(file_object):
    return os.stat(file_object.fileno()).st_size

def convert_file(input_file, options):
    logging.debug("reading input file: %s", quote(input_file))
    v_cmd = prepare_video_conversion_command(
        input_file,
        options.framerate, options.quality,
        parse_subtitle_stream_id(input_file, options.sid), options.font
    )
    v_tmp_file = TemporaryFile()
    v_proc = subprocess.Popen(v_cmd, stdout=v_tmp_file, stderr=subprocess.DEVNULL)
    v_proc.wait()
    a_cmd = prepare_audio_conversion_command(input_file, options.aid)
    a_tmp_file = TemporaryFile()
    a_proc = subprocess.Popen(a_cmd, stdout=a_tmp_file, stderr=subprocess.DEVNULL)
    a_proc.wait()
    gop = create_gop(v_tmp_file)
    thumbnail = create_thumbnail(create_screenshot(v_tmp_file, int(get_duration(input_file)/ 10)))
    header = create_header(
        count_video_frames(v_tmp_file),
        options.framerate,
        file_size(a_tmp_file),
        file_size(v_tmp_file),
        len(gop)
    )
    output_file = os.path.splitext(input_file)[0] + ".dpg"
    logging.debug("writing output file: %s", quote(output_file))
    v_tmp_file.seek(0)
    a_tmp_file.seek(0)
    outfile = open(output_file, "wb")
    outfile.write(header)
    outfile.write(thumbnail)
    copyfileobj(a_tmp_file, outfile)
    copyfileobj(v_tmp_file, outfile)
    outfile.write(gop)
    outfile.close()
    logging.info("done: %s -> %s", quote(input_file), quote(output_file))

def check_external_command(command, expected_output, expected_exit_code):
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL
        )
        (output, _) = process.communicate()
    except OSError as os_err:
        if os_err.errno == errno.ENOENT:
            raise ExternalCommandNotFoundError(command)
        raise os_err
    if process.returncode != expected_exit_code:
        raise ExternalCommandFailedError(command)
    if re.search(expected_output, output) is None:
        raise ExternalCommandFailedError(command)

def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="Convert video files to DPG4 format used by MoonShell for Nintendo DS."
    )
    parser.add_argument("files", nargs="+", help="input files")
    parser.add_argument(
        "-v", action="store_true", dest="verbose", default=False,
        help="increase verbosity"
    )
    video_group = parser.add_argument_group("video options")
    video_group.add_argument(
        "-q", type=int, dest="quality", choices=video_quality_options().keys(), default=1,
        help="quality setting (default: 1)"
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
        "-s", type=int, dest="sid", metavar="SID",
        help="use subtitle stream SID (default: first available stream, -1 to disable)"
    )
    subtitle_group.add_argument(
        "-f", dest="font", help="font for subtitles (libass style FontName)"
    )
    args = parser.parse_args()
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(message)s",
        level=logging.DEBUG if args.verbose else logging.INFO,
    )
    check_external_command([FFMPEG, "-version"], b"^ffmpeg version .*", 0)
    check_external_command([FFPROBE, "-version"], b"^ffprobe version .*", 0)
    if args.framerate not in MPEG_SPEC_FRAMERATES:
        logging.warning("non standard framerate: %s, sync issues may occur", args.framerate)
    for input_file in args.files:
        if not os.path.exists(input_file):
            raise ValueError("file doesn't exist: %s" % input_file)
    for input_file in args.files:
        convert_file(input_file, args)

if __name__ == "__main__":
    main()
