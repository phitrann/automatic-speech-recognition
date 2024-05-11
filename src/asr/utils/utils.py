import os
import subprocess
import glob
from pydub import AudioSegment

import config as cfg


def extract_audio_part_segment(
    movie_file, timing_start, timing_end, res_filename, sample_rate=16000
):
    start_h, start_m, start_s, start_msec = (
        timing_start.hour,
        timing_start.minute,
        timing_start.second,
        timing_start.microsecond // 1000,
    )
    end_h, end_m, end_s, end_msec = (
        timing_end.hour,
        timing_end.minute,
        timing_end.second,
        timing_end.microsecond // 1000,
    )
    DEVNULL = open(os.devnull, "wb")
    if os.path.exists(res_filename):
        os.remove(res_filename)
    p = subprocess.Popen(
        [
            "ffmpeg",
            "-i",
            movie_file,
            "-acodec",
            "pcm_s16le",
            "-ac",
            "1",
            "-ar",
            str(sample_rate),
            "-ss",
            "{:02d}:{:02d}:{:02d}.{:03d}".format(start_h, start_m, start_s, start_msec),
            "-to",
            "{:02d}:{:02d}:{:02d}.{:03d}".format(end_h, end_m, end_s, end_msec),
            res_filename,
        ],
        stdout=DEVNULL,
        stderr=DEVNULL,
    )
    out, err = p.communicate()
    p.terminate()
    return None


def get_ts_seconds(time_obj):
    return (
        time_obj.hour * 60 * 60
        + time_obj.minute * 60
        + time_obj.second
        + time_obj.microsecond / 1000000
    )


############################################################################################################


def newest_mp3_filename(base_dir=cfg.AUDIO_RAW_PATH):
    # lists all mp3s in local directory
    list_of_mp3s = glob.glob(f"{base_dir}/*.mp3")
    # returns mp3 with highest timestamp value
    return max(list_of_mp3s, key=os.path.getctime)


def get_video_time_in_ms(video_timestamp):
    vt_split = video_timestamp.split(":")
    if len(vt_split) == 3:  # if in HH:MM:SS format
        hours = int(vt_split[0]) * 60 * 60 * 1000
        minutes = int(vt_split[1]) * 60 * 1000
        seconds = int(vt_split[2]) * 1000
    else:  # MM:SS format
        hours = 0
        minutes = int(vt_split[0]) * 60 * 1000
        seconds = int(vt_split[1]) * 1000
    # time point in miliseconds
    return hours + minutes + seconds


def get_trimmed(mp3_filename, initial, final=""):
    if not mp3_filename:
        # raise an error to immediately halt program execution
        raise Exception("No MP3 found in local directory.")
    # reads mp3 as a PyDub object
    sound = AudioSegment.from_mp3(mp3_filename)
    t0 = get_video_time_in_ms(initial)
    print("Beginning trimming process for file ", mp3_filename, ".\n")
    print("Starting from ", initial, "...")
    if len(final) > 0:
        print("...up to ", final, ".\n")
        t1 = get_video_time_in_ms(final)
        return sound[t0:t1]  # t0 up to t1
    return sound[t0:]  # t0 up to the end


# def main():
#     initial = "1:00"
#     final = "4:00"
#     # filename = newest_mp3_filename()
#     filename = "/space/hotel/phit/personal/asr/data/audios/SCWFVd_FiAU.mp3"
#     trimmed_file = get_trimmed(filename, initial, final)
#     trimmed_filename = "".join([filename.split(".mp3")[0], "- TRIM.mp3"])
#     print("Process concluded successfully. Saving trimmed file as ", trimmed_filename)
#     # saves file with newer filename
#     trimmed_file.export(trimmed_filename, format="mp3")


# if __name__ == "__main__":
#     main()
