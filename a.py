import subprocess

cmd = ["ffmpeg", "-i", "pipe:0", "-ar", "48000", "-ac", "2", "-f", "s16le", "pipe:1"]

with open("out.wav", mode="rb") as f:
    p = subprocess.run(cmd, stdin=f, stdout=subprocess.PIPE)
