# asr

```bash
    sudo apt-get install ffmpeg
```

Clean up data
```bash
    ./clean_up.sh
```

Collect data
```bash
   python /src/asr/utils.py
```

Youtube API is free, just have quota limit: https://github.com/ThioJoe/YT-Spammer-Purge/wiki/Understanding-YouTube-API-Quota-Limits

```json
{
    "wireMagic": "pb3",
    "pens": [
        {}
    ],
    "wsWinStyles": [
        {},
        {
            "mhModeHint": 2,
            "juJustifCode": 0,
            "sdScrollDir": 3
        }
    ],
    "wpWinPositions": [
        {},
        {
            "apPoint": 6,
            "ahHorPos": 20,
            "avVerPos": 100,
            "rcRows": 2,
            "ccCols": 40
        }
    ],
    "events": [
        {
            "tStartMs": 0,
            "dDurationMs": 576800,
            "id": 1,
            "wpWinPosId": 1,
            "wsWinStyleId": 1
        },
        {
            "tStartMs": 4960,
            "dDurationMs": 6960,
            "wWinId": 1,
            "segs": [
                {
                    "utf8": "imagine",
                    "acAsrConf": 0
                },
                {
                    "utf8": " any",
                    "tOffsetMs": 1000,
                    "acAsrConf": 0
                },
                {
                    "utf8": " movie",
                    "tOffsetMs": 1280,
                    "acAsrConf": 0
                },
                {
                    "utf8": " like",
                    "tOffsetMs": 1959,
                    "acAsrConf": 0
                },
                {
                    "utf8": " James",
                    "tOffsetMs": 2160,
                    "acAsrConf": 0
                },
                {
                    "utf8": " Bond",
                    "tOffsetMs": 2479,
                    "acAsrConf": 0
                }
            ]
        },
        {
            "tStartMs": 8390,
            "dDurationMs": 3530,
            "wWinId": 1,
            "aAppend": 1,
            "segs": [
                {
                    "utf8": "\n"
                }
            ]
        },
        {
            "tStartMs": 8400,
            "dDurationMs": 6479,
            "wWinId": 1,
            "segs": [
                {
                    "utf8": "mission",
                    "acAsrConf": 0
                },
                {
                    "utf8": " impossible",
                    "tOffsetMs": 440,
                    "acAsrConf": 0
                },
                {
                    "utf8": " or",
                    "tOffsetMs": 1440,
                    "acAsrConf": 0
                },
                {
                    "utf8": " Jack",
                    "tOffsetMs": 1600,
                    "acAsrConf": 0
                },
                {
                    "utf8": " Ryan",
                    "tOffsetMs": 2239,
                    "acAsrConf": 0
                },
                {
                    "utf8": " and",
                    "tOffsetMs": 3239,
                    "acAsrConf": 0
                }
            ]
        },
        ...
    ]
}
```