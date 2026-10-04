# world.execute(me); · Windows ASCII / CRT

在 Windows 终端中播放 Mili《world.execute(me);》的 ASCII 动画，使用 Windows Terminal 的内置复古效果呈现扫描线和柔化的文字边缘。

本仓库提供 **Windows 适配播放器、原生音频时钟、CRT 配置和安装／构建工具**。动画编排、字符场景、字幕和频谱来自 [yym8224961/world.execute-me-ascii](https://github.com/yym8224961/world.execute-me-ascii)，固定在提交 `9d8e815281a104ccb648ec2f2df88cd9f0cb8c12`。本仓库使用 MIT 许可开放新增代码；上游依赖及音乐的许可范围见 [来源与许可说明](THIRD_PARTY_NOTICES.md)。

## 快速开始

需要 Windows 10 2004 或更新版本／Windows 11、64 位系统和 **Python 3.10+**。首次安装需要连接 GitHub；依赖准备完成后，播放不需要网络。终端播放器仅使用 Python 标准库。

1. 克隆本仓库，或点击 GitHub 的 **Code → Download ZIP** 并完整解压。
2. 双击 `setup.cmd`，或在工程目录运行它。安装脚本会下载固定版本的上游动画文件和微软官方 Windows Terminal 便携版，并核对每个下载文件的 SHA-256。
3. 双击 `run-crt-terminal.cmd`；**按空格开始播放**。

第一次可先无声预览，无需准备音乐：

```powershell
git clone https://github.com/MIMISAMA156/world-execute-ascii-crt.git
cd world-execute-ascii-crt
.\setup.cmd
.\run-crt-terminal.cmd --silent
```

带音乐播放前，将自己有权使用的音轨准备为 `media/song.wav`：**44.1 kHz、16-bit PCM、双声道**。使用约 211.907 秒的版本，以匹配动画时间轴。可以直接放入符合格式的 WAV，也可以转换本地 MP3：

```powershell
python tools/prepare_audio.py --input "D:/Music/world.execute(me).mp3" --ffmpeg "D:/Tools/ffmpeg.exe"
.\run-crt-terminal.cmd
```

安装 `imageio-ffmpeg` 后可省略 FFmpeg 路径：

```powershell
python -m pip install imageio-ffmpeg==0.6.0
python tools/prepare_audio.py --input "D:/Music/world.execute(me).mp3"
```

本仓库不提供歌曲下载。音频、下载的依赖和生成的成片都已被 `.gitignore` 排除。

## 播放与操作

```powershell
.\run-crt-terminal.cmd                         # CRT 窗口，按空格开始
.\run-crt-terminal.cmd --start 24 --autoplay   # 从 24 秒直接播放
.\run-crt-terminal.cmd --silent               # 无声预览
.\run-terminal.cmd                           # 当前终端内播放
.\run-crisp-terminal.cmd                     # 独立的传统 Windows 控制台
```

| 按键 | 操作 |
| --- | --- |
| 空格／Enter | 开始、暂停、继续 |
| 左／右方向键 | 后退／前进 5 秒 |
| `1`–`5` | 跳转五个章节 |
| `R` | 从头播放 |
| `+`／`-` | 调整音量 |
| `H` | 打开／关闭帮助 |
| `Q`／Esc | 退出 |

默认等待按键，不自动放出音乐。窗口大小变化时重新布局；最低 64 列 × 24 行，推荐 128 列 × 44 行以上。`--fps 12` 可以降低刷新率。播放器使用 Windows `waveOut` PCM 音频设备返回的位置驱动画面，暂停、跳转和恢复时跟随音频时钟。

## CRT 效果和字体

默认配置为 **Lucida Console Regular、14 pt、黑色背景**，缺省文字颜色为琥珀色 `#DDB366`。场景的颜色由原动画的 ANSI 输出决定。字体选择是依据 BIOS 风格参考图做的近似，未确认原视频的实际字体名称。

`crt-profile.json` 中启用了：

```json
{
  "font": { "face": "Lucida Console", "size": 14, "weight": 400 },
  "background": "#080602",
  "foreground": "#DDB366",
  "experimental.retroTerminalEffect": true
}
```

微软将这个效果定义为 CRT 扫描线和模糊文字，参见 [Windows Terminal 外观设置](https://learn.microsoft.com/en-us/windows/terminal/customize-settings/profile-appearance#retro-terminal-effects)。它是终端的显示后处理，动画输出仍然是可编辑的 ASCII 字符。

安装后修改实际配置文件：

```text
terminal-runtime/terminal-1.24.11911.0/settings/settings.json
```

在名为 `world.execute(me) / CRT` 的配置中调整 `font.size` 或 `font.face`；将 `experimental.retroTerminalEffect` 改为 `false` 可以关闭复古效果。再次运行安装脚本会保留现有配置。根目录的 `crt-profile.json` 是首次安装用的配置模板。

终端使用 [微软官方便携模式](https://learn.microsoft.com/en-us/windows/terminal/distributions#portable-mode)：运行时旁有 `.portable` 标记，设置保存在工程内的 `settings` 目录。无需将这个终端安装到系统或设为系统默认终端。

## 工程结构

```text
terminal_player.py          Windows 播放器、按键和画面刷新
run-crt-terminal.cmd        CRT 播放入口
run-terminal.cmd            当前终端播放入口
run-crisp-terminal.cmd      传统控制台入口
crt-profile.json            CRT 配置模板
dependencies.lock.json      上游提交、下载地址和 SHA-256
setup.cmd                   Windows 安装入口
tools/setup.py              获取依赖、生成纯渲染引擎和终端配置
tools/prepare_audio.py      转换用户本地音轨
source/win_audio.py         Windows waveOut PCM 音频时钟
source/console_font.py      传统控制台临时字体设置与恢复
source/render.py            可选 HTML／MP4 导出
source/player-template.html 浏览器播放器模板
docs/CRT说明.md             CRT 显示原理和故障处理
docs/验证记录.md            已验证项目与验证边界
```

`source/engine.py`、`scenes.py`、`config.json`、`lyrics.json` 和 `spectrum.json` 由安装脚本从固定上游版本准备在本地，不提交到本仓库。每个文件的下载摘要见 `dependencies.lock.json`。不要将 MIT 许可证误用于这些第三方依赖。

## 可选：导出 HTML 和 MP4

完成安装后，把自己的音轨放为 `media/song.mp3`，安装渲染依赖并执行：

```powershell
python -m pip install -r requirements.txt
python source/render.py
```

也可指定 `python source/render.py --ffmpeg "D:/Tools/ffmpeg.exe"`。导出文件位于 `build/`：单文件 HTML 内嵌字符帧、栅格字库和所提供的音乐；MP4 为 1920×1080、24 fps。导出使用 Windows 系统字体，并保留原来的栅格字库风格；Windows Terminal 的 CRT 配置只作用于终端窗口，不会自动烧入导出视频。

修改安装后本地 `source/scenes.py` 可以调整场景，修改字幕 JSON 可以调整时刻；再次运行 `setup.cmd` 会重新生成这些依赖文件，因此应自行备份修改内容。

## 验证与来源

安装与启动记录见 [验证记录](docs/验证记录.md)。已验证配置和启动链路；由于窗口读取工具没有返回 Windows Terminal，CRT 光晕外观尚未通过终端截图核验。参考 B 站视频没有在制作环境成功播放，也未做逐帧一致性比较。

参考视频：[BV1Jwhy6BEMJ](https://www.bilibili.com/video/BV1Jwhy6BEMJ/)。原曲与歌词：Mili《world.execute(me);》。动画作者：yym8224961。Windows / CRT 适配由 YTY0529 整理发布，使用 Codex 辅助开发。
