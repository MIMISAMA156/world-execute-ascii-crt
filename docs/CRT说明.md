# CRT 显示与字体说明

## 显示链路

播放器在给定音频时刻生成字符网格，将字符、颜色和光标控制编码为 ANSI 文本。Windows Terminal 先用配置中的字体绘制这些文字，再对绘制结果应用内置复古效果。因此字体决定字符轮廓，CRT 效果决定扫描线和柔化的文字边缘。

普通 PowerShell / CMD 里的字符输出本身不能产生跨字符单元的模糊。要看到本工程的 CRT 效果，应使用 `run-crt-terminal.cmd` 打开的专用 Windows Terminal 窗口。

内置效果使用 `experimental.retroTerminalEffect: true`。微软文档还支持 `experimental.pixelShaderPath` 指向自定义着色器；如果另行配置该项，自定义着色器会替代内置复古效果。本版本使用内置效果，没有提供自定义 HLSL 着色器。

参考：[Windows Terminal 外观配置](https://learn.microsoft.com/en-us/windows/terminal/customize-settings/profile-appearance#retro-terminal-effects)。

## 字体的两种设置方式

CRT 入口把字体交给 Windows Terminal 的 `font` 配置，因此自动传递 `--keep-font`。这里的 `font.size` 单位是 pt，默认 14。

传统控制台入口通过 Windows 控制台字体 API 临时选择 Lucida Console、常规字重 400、像素高度 22，并在退出时恢复原字体与代码页。这里的像素高度与 Windows Terminal 的 pt 字号不是同一个单位。

中文和特殊符号可能由系统回退字体显示。各电脑的系统字体、缩放比例和显卡可能使最终外观不同。

## 常见问题

| 现象 | 处理 |
| --- | --- |
| 提示便携终端缺失 | 运行 `setup.cmd`，确认首次下载成功，再启动 CRT 入口 |
| 提示动画依赖缺失 | 运行 `setup.cmd`；网络错误时可稍后重试，已有正确摘要的下载会复用 |
| 音频文件不存在 | 准备 `media/song.wav`；或使用 `--silent` 无声预览 |
| 字符太大，提示窗口太小 | 在专用配置的 `font.size` 中减小字号，或最大化窗口 |
| 没看到复古效果 | 确认打开的是专用 CRT 入口，并检查实际 `settings.json` 中开关为 `true`，且没有设置 `experimental.pixelShaderPath` |
| 字幕与音乐不同步 | 使用约 211.907 秒的原时间轴版本；带额外前奏或不同剪辑的音轨需自行调整时间轴 |
| 复制工程后无法启动 | 重新完整解压并运行 `setup.cmd`；启动脚本按当前工程位置传入工作目录 |
| 其他电脑找不到 Python | 安装 Python 3.10+ 并加入 PATH；本机 Codex 的 Python 路径不属于跨电脑依赖 |

首次依赖安装需要联网。依赖和本地音轨准备好后，运行播放入口不需要联网。安装脚本保留已有终端外观设置；如果希望恢复模板，应先备份实际 `settings.json`，再手动将模板参数写回。
