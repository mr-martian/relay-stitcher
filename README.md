# relay-stitcher

This script essentially turns a slideshow with voiceovers into a video file.
It was originally used for the LCC11 Translation Relay summary video.

## Requirements

- ffmpeg
- [ffmpeg-normalize](https://github.com/slhck/ffmpeg-normalize)
  - ensures all audio clips are roughly the same volume
- Open Office
  - PPTX → PDF
- Ghostscript
  - PDF → PNG

## Usage

Create a CSV file with the following format:

| Step | Person | Slide | Slide Number | Audio | Video | Chapter |
|------|--------|-------|--------------|-------|-------|---------|
| 1 | Alice | alice.pptx | 2 | alice.wav | | Torch 1 |
| 2c | Bob | bob.pptx | | bob_commentary.mp3 | | Torch 2 |
| 2t | Bob | bob.pptx | | bob_reading.mp3 | | |
| 3 | Carol | | | | carol.mp4 | Torch 3 |
| 4 | David | david.pptx | `0:00\|0:12\|0:40` | david.wav | | Torch 4 |

Then, in the directory where those files are (or from which the paths are valid), run:

```bash
$ python3 stitch.py ring1.csv ring1
```

The first argument is the CSV file, and the second is the prefix for the output files.
This command will create 3 directories: `images`, `normalized`, and `output`.
The `output` directory will then contain the following:

- `ring1_1.mp4`: video displaying the second slide of `alice.pptx` with the audio of `alice.wav`
- `ring1_2c.mp4`: video displaying the first slide of `bob.pptx` with the audio of `bob_commentary.mp3`
- `ring1_2t.mp4`: video displaying the first slide of `bob.pptx` with the audio of `bob_reading.mp3`
- `ring1_3.mp4`: normalized copy of `carol.mp4`
- `ring1_4_0.mp4`: video displaying the first slide of `david.pptx` with the audio of the first 12 seconds of `david.wav`
- `ring1_4_1.mp4`: video displaying the second slide of `david.pptx` with the audio of `david.wav` from 0:12 to 0:40
- `ring1_4_2.mp4`: video displaying the third slide of `david.pptx` with the audio of `david.wav` from 0:40 onwards
- `ring1.mp4`: a concatenation of the preceding 7 files
- `ring1_chapters.txt`: the timestamp of the beginning of each person's section with the labels given in the `Chapter` column in the appropriate format to generate chapter breaks in a YouTube video

All audio will have its loudness normalized according to the default settings of ffmpeg-normalize and all images and videos will be rescaled to 1920x1440.

## TODO

Currently, most of the format conversion happens in the final concatenation step, so it's the most intensive (LCC11 was concatenating 105 clips into a 97 minute video and got up to 8.6 GB of RAM).
It's possible that doing the conversion of each step and then using the [concat demuxer](https://trac.ffmpeg.org/wiki/Concatenate) would have higher average load but much lower peak load.

Background noise reduction is also a desirable feature.
Based on [this SO post](https://superuser.com/questions/733061/reduce-background-noise-and-optimize-the-speech-from-an-audio-clip-using-ffmpeg), it's possible that adding `-e="-af highpass=f=200,lowpass=f=1000"` or similar to the `ffmpeg-normalize` command in `norm_audio` would achieve this.
