# pylint: disable=missing-docstring
import os.path

def sample_filename(filename: str) -> str:
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples", filename)
