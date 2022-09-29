# ESRGAN-Tiling-Script
Little Python script for ESRGAN ( Enhanced Super-Resolution Generative Adversarial Networks ) for upscaling very large images by tiling them. 
The script use a margin for not seeing the edges between each tiles.

## Changes for this fork
1. Suggest the following Python dependencies:
    torch torchvision torchaudio opencv-contrib-python glob2

2. Support for upscaling video. The directory for video files to be upscaled is separate from the directory for image files. Upscaled media are all written to the same "results" directory. 

## How to use it

Simply put the 'upscale.py' and 'upscale_video.py' files into the ESRGAN repository and use them instead of the official 'test.py'

Some vars may be tweaked at the beginning of the script.
