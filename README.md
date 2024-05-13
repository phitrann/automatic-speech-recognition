# Automatic Speech Recognition

This project aims to build a system that can automatically transcribe speech to text. The system will be able to transcribe speech from various sources such as YouTube videos, audio files, etc. The system will be built using the `NeMo` toolkit, which is a toolkit for building state-of-the-art conversational AI models.

Supported functions:
- Collect data from YouTube
- Process data
- Automatic Speech Recognition (ASR)
- Speaker Diarization
- Pronunciation/Grammar Assessment

## Getting started
I recommend to use anaconda to create environment
```bash
    conda create -n asr python=3.10
    conda activate asr
```
Clone the repository
```bash
    git clone https://github.com/Foxxy-HCMUS/automatic-speech-recognition.git
```

```bash
    sudo apt-get install ffmpeg

    pip install git+https://github.com/m-bain/whisperX.git@78dcfaab51005aa703ee21375f81ed31bc248560
    pip install dora-search lameenc openunmix wget Cython
    pip install --no-build-isolation "nemo_toolkit[asr]==1.23.0"
    pip install --no-deps git+https://github.com/facebookresearch/demucs#egg=demucs
    pip install git+https://github.com/oliverguhr/deepmultilingualpunctuation.git
    pip install ctranslate2==3.24.0
```

Install requirements
```bash
    # Install in editable mode to avoid constant re-installation
    # Also include all optional dependencies
    python -m pip install -e .[all]

    # Install pre-commit hooks to automatically check/format code on commits
    pre-commit install
```
In case `pytorch` cannot compiled with cuda, please run the following command
```bash
    pip install torch==1.13.1+cu116 torchaudio==0.13.1 torchvision==0.14.1+cu116 --extra-index-url=https://download.pytorch.org/whl/cu116
```


## Guidelines
<!-- Youtube API is free, just have quota limit: https://github.com/ThioJoe/YT-Spammer-Purge/wiki/Understanding-YouTube-API-Quota-Limits -->

### Collect data
```bash
    python /src/asr/collect_data.py
```

### Process data
```bash
    python /src/asr/parser.py
```

### Clean up data
```bash
    ./clean_up.sh
```

## References
- https://github.com/youngwoo-yoon/youtube-gesture-dataset/blob/master/script/download_video.py
- https://github.com/EgorLakomkin/KTSpeechCrawler/blob/master/crawler/process.py
- https://github.com/glut23/webvtt-py/tree/master
- https://github.com/Uberi/speech_recognition
