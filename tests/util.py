import os.path

def sample_filename(filename):
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), "samples", filename)
