# ------------------------------------------------------------------------------
# Copyright (c) ETRI. All rights reserved.
# Licensed under the BSD 3-Clause License.
# This file is part of Youtube-Gesture-Dataset, a sub-project of AIR(AI for Robots) project.
# You can refer to details of AIR project at https://aiforrobots.github.io
# Written by Youngwoo Yoon (youngwoo@etri.re.kr)
# ------------------------------------------------------------------------------
# https://github.com/youngwoo-yoon/youtube-gesture-dataset/blob/master/script/download_video.py
# Customized by Phi Tran (hoanganh6758@gmail.com)

from __future__ import unicode_literals

import glob
import json
import os
import traceback
import sys

import yt_dlp as youtube_dl
import urllib.request
from googleapiclient.discovery import build
from datetime import datetime, timedelta
from rich import progress

import config as my_config


YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

RESUME_VIDEO_ID = (
    "zoEtcR5EW08"  # resume downloading from this video, set empty string to start over
)


# TODO
# "FpuiovvSPYc": 2 SPEAKER VIDEO
# ["54AYOd5S7uo", "Y8tlFLIjyMU"]: VIDEO IN ASSESSMENT


def fetch_video_ids(channel_id, search_start_time):  # load video ids in the channel
    youtube = build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        developerKey=my_config.DEVELOPER_KEY,
    )

    start_time = search_start_time
    td = timedelta(days=15)
    end_time = start_time + td

    res_items = []

    # multiple quires are necessary to get all results surely
    while start_time < datetime.now():
        start_string = str(start_time.isoformat()) + "Z"
        end_string = str(end_time.isoformat()) + "Z"

        res = (
            youtube.search()
            .list(
                part="id",
                channelId=channel_id,
                maxResults="50",
                publishedAfter=start_string,
                publishedBefore=end_string,
            )
            .execute()
        )
        res_items += res["items"]

        while True:  # paging
            if len(res["items"]) < 50 or "nextPageToken" not in res:
                break

            next_page_token = res["nextPageToken"]
            res = (
                youtube.search()
                .list(
                    part="id",
                    channelId=channel_id,
                    maxResults="50",
                    publishedAfter=start_string,
                    publishedBefore=end_string,
                    pageToken=next_page_token,
                )
                .execute()
            )
            res_items += res["items"]

        print(
            "    {} to {}, no of videos: {}".format(
                start_string, end_string, len(res_items)
            )
        )

        start_time = end_time
        end_time = start_time + td

    # collect video ids
    vid_list = []
    for i in res_items:
        vid = (i.get("id")).get("videoId")
        if vid is not None:
            vid_list.append(vid)

    return vid_list


def video_filter(info):
    passed = True

    exist_proper_format = False
    format_data = info.get("formats")
    for i in format_data:
        if (
            i.get("ext") == "mp4"
            and i.get("height") >= 720
            and i.get("acodec") != "none"
        ):
            exist_proper_format = True
    if not exist_proper_format:
        passed = False

    if passed:
        duration_hours = info.get("duration") / 3600.0
        if duration_hours > 1.0:
            passed = False

    if passed:
        if len(info.get("automatic_captions")) == 0 and len(info.get("subtitles")) == 0:
            passed = False

    return passed


def audio_filter(info):
    passed = True

    # exist_proper_format = False
    # format_data = info.get("formats")
    # for i in format_data:
    #     if i.get("ext") == "mp3":
    #         exist_proper_format = True
    # if not exist_proper_format:
    #     passed = False

    # if passed:
    #     duration_hours = info.get("duration") / 3600.0
    #     if duration_hours > 1.0:
    #         passed = False

    if passed:
        if len(info.get("automatic_captions")) == 0 and len(info.get("subtitles")) == 0:
            passed = False

    return passed


def download_subtitle(url, filename, postfix):
    urllib.request.urlretrieve(
        url, "{}/{}-{}.vtt".format(my_config.SUBTITLE_RAW_PATH, filename, postfix)
    )


def parse_subtitle(subtitle):
    lines = subtitle.split("\n")
    parsed = []
    count = 0
    for i in progress.track(range(len(lines)), description="parsing"):
        if "-->" in lines[i]:
            start = lines[i].split(" --> ")[0]
            end = lines[i].split(" --> ")[1]
            text = ""
            for j in range(i + 1, len(lines)):
                if "-->" in lines[j]:
                    break
                text += lines[j] + " "
            parsed.append(
                {"id": count, "speaker": "", "start": start, "end": end, "text": text}
            )
            count += 1
    return {"data": parsed}


def download_and_parse_subtitle(url, filename, postfix):
    # DEPRECATED: dont work for automatic captions
    download_subtitle(url, filename, postfix)
    with open(
        "{}/{}-{}.vtt".format(my_config.SUBTITLE_RAW_PATH, filename, postfix), "r"
    ) as file:
        subtitle = file.read()
    # os.remove("{}/{}-{}.vtt".format(my_config.SUBTITLE_RAW_PATH, filename, postfix))
    parsed_subtitle = parse_subtitle(subtitle)
    with open(
        "{}/{}-{}.json".format(my_config.SUBTITLE_RAW_PATH, filename, postfix), "w"
    ) as file:
        json.dump(parsed_subtitle, file, indent=2)


def download(vid_list):
    ydl_opts = {
        "format": "bestaudio/best",
        "writesubtitles": True,
        "writeautomaticsub": True,
        # "outtmpl": f"{my_config.AUDIO_RAW_PATH}/%(id)s.%(ext)s",
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "192",
            }
        ],
    }  # download options

    language = my_config.LANG

    download_count = 0
    skip_count = 0
    sub_count = 0
    log = open("download_log.txt", "w", encoding="utf-8")

    if len(RESUME_VIDEO_ID) < 10:
        skip_index = 0
    else:
        skip_index = vid_list.index(RESUME_VIDEO_ID)

    for i in range(len(vid_list)):
        error_count = 0
        print(vid_list[i])
        if i < skip_index:
            continue

        # rename video (vid.mp4)
        # ydl_opts["outtmpl"] = my_config.VIDEO_PATH + "/" + vid_list[i] + ".mp4"

        ydl_opts["outtmpl"] = my_config.AUDIO_RAW_PATH + "/" + vid_list[i]  # + ".mp3"

        # check existing file
        if os.path.exists(ydl_opts["outtmpl"]) and os.path.getsize(
            ydl_opts["outtmpl"]
        ):  # existing and not empty
            print("video file already exists ({})".format(vid_list[i]))
            continue

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            vid = vid_list[i]
            url = "https://youtu.be/{}".format(vid)

            info = ydl.extract_info(url, download=False)
            if audio_filter(info):
                with open(
                    f"{my_config.METADATA_PATH}/{vid}.json", "w", encoding="utf-8"
                ) as js:
                    json.dump(info, js, indent=4)
                while 1:
                    if error_count == 3:
                        print("Exit...")
                        sys.exit()
                    try:
                        ydl.download([url])
                    except (
                        youtube_dl.utils.DownloadError,
                        youtube_dl.utils.ContentTooShortError,
                        youtube_dl.utils.ExtractorError,
                    ):
                        error_count += 1
                        print("  Retrying... (error count : {})\n".format(error_count))
                        traceback.print_exc()
                        continue
                    else:

                        def get_subtitle_url(subtitles, language, ext):
                            subtitles = subtitles.get(language)
                            url = None
                            for sub in subtitles:
                                if sub.get("ext") == ext:
                                    url = sub.get("url")
                                    break
                            return url

                        if (
                            info.get("subtitles") != {}
                            and (info.get("subtitles")).get(language) is not None
                        ):
                            sub_url = get_subtitle_url(
                                info.get("subtitles"), language, "vtt"
                            )
                            # download_and_parse_subtitle(
                            #     sub_url, vid, language
                            # )
                            download_subtitle(sub_url, vid, language)
                            sub_count += 1
                        elif info.get("automatic_captions") != {}:
                            auto_sub_url = get_subtitle_url(
                                info.get("automatic_captions"), language, "vtt"
                            )
                            # download_and_parse_subtitle(
                            #     auto_sub_url, vid, language + "-auto"
                            # )
                            download_subtitle(auto_sub_url, vid, language + "-auto")

                        log.write("{} - downloaded\n".format(str(vid)))
                        download_count += 1
                        break
            else:
                log.write("{} - skipped\n".format(str(info.get("id"))))
                skip_count += 1

        print("  downloaded: {}, skipped: {}".format(download_count, skip_count))

    log.write("\nno of subtitles : {}\n".format(sub_count))
    log.write("downloaded: {}, skipped : {}\n".format(download_count, skip_count))
    log.close()


def create_path(path):
    if not os.path.exists(path):
        os.makedirs(path)


def main():
    create_path(my_config.SUBTITLE_RAW_PATH)
    create_path(my_config.AUDIO_RAW_PATH)
    create_path(my_config.METADATA_PATH)

    os.chdir(my_config.DATA_PATH)
    vid_list = []

    # read video list
    try:
        rf = open("video_ids.txt", "r")
    except FileNotFoundError:
        print("fetching video ids...")
        vid_list = fetch_video_ids(
            my_config.YOUTUBE_CHANNEL_ID, my_config.VIDEO_SEARCH_START_DATE
        )
        # vid_list =
        wf = open("video_ids.txt", "w")
        for j in vid_list:
            wf.write(str(j))
            wf.write("\n")
        wf.close()
    else:
        while 1:
            value = rf.readline()[:11]
            if value == "":
                break
            vid_list.append(value)
        rf.close()

    print("downloading videos...")
    download(vid_list)
    print("finished downloading videos")

    print("removing unnecessary subtitles...")
    for f in glob.glob(f"{my_config.AUDIO_RAW_PATH}/*.en.vtt"):
        os.remove(f)

    assert len(os.listdir(my_config.AUDIO_RAW_PATH)) == len(
        os.listdir(my_config.SUBTITLE_RAW_PATH)
    ), "audio and subtitle files are not matched"


def test_fetch():
    vid_list = fetch_video_ids(
        my_config.YOUTUBE_CHANNEL_ID, my_config.VIDEO_SEARCH_START_DATE
    )
    print(vid_list)
    print(len(vid_list))


if __name__ == "__main__":
    # test_fetch()
    main()
