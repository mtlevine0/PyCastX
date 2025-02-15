# FFMPEG Video Streaming:
- Stream a webcam: ```ffmpeg -f avfoundation -framerate 30 -i "0" -vf "fps=24,scale=384:192,hflip" -c:v rawvideo -pix_fmt rgb24 -f rawvideo - | python3 client.py```
  - Note: The "-i" flag selects the video source, on mac it's possible to use this to select a stream of a particular application or an entire screen.
- Stream a video: ```ffmpeg -stream_loop -1 -re -i ~/video/path.mp4 -vf "fps=24,scale=384:192" -c:v rawvideo -pix_fmt rgb24 -f rawvideo - | python3 client.py```