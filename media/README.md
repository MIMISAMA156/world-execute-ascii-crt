# 本地音频

将自己有权使用的音轨转换为 `song.wav` 放在此目录：双声道、44.1 kHz、16-bit PCM WAV。

```powershell
python tools/prepare_audio.py --input "D:/Music/world.execute(me).mp3" --ffmpeg "D:/Tools/ffmpeg.exe"
```

如果已安装 `imageio-ffmpeg` 或 FFmpeg 已加入 PATH，可以省略 `--ffmpeg`。动画时间轴对应约 211.907 秒版本；不同剪辑可能与字幕不同步。

音频文件已被 `.gitignore` 排除。无声预览无需音轨：`run-crt-terminal.cmd --silent`。
