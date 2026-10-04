# 来源与许可范围

本仓库的 MIT 许可证适用于提交在本仓库中的 Windows 适配代码、CRT 配置、安装与构建工具和说明文档。

## 动画工程

- 原作者：**yym8224961**。
- 原工程：[world.execute-me-ascii](https://github.com/yym8224961/world.execute-me-ascii)。
- 固定版本：`9d8e815281a104ccb648ec2f2df88cd9f0cb8c12`。
- 动画场景、字幕时间轴、频谱、字符渲染引擎来自原工程。本仓库的 Windows 播放器调用这些依赖，动画编排不属于本仓库原创。
- 整理时上游仓库没有声明开源许可证。公开可访问不代表本仓库可以替上游授予 MIT 许可。本仓库通过安装脚本从固定提交获取依赖并在使用者本机生成 `source/engine.py`，这些文件由 `.gitignore` 排除，也不属于本仓库 MIT 许可范围。使用这些内容应遵循原作者和相应权利人的授权条件。

## 音乐与歌词

原曲与歌词为 **Mili《world.execute(me);》**。上游 README 明确未对原曲、歌词或其他第三方素材授予额外使用许可。本仓库不包含音乐文件、嵌入音乐的 HTML、成片视频或上游 Release 播放包。播放所需音频由使用者自行提供；本仓库的 MIT 许可证不涵盖音乐、歌词或字幕。

## Windows Terminal 与字体

安装脚本从 [Microsoft 官方 Release](https://github.com/microsoft/terminal/releases/tag/v1.24.11911.0) 获取 Windows Terminal 便携版，校验固定 SHA-256。Windows Terminal 及其依赖适用各自的许可证；其发布包内的 `NOTICE.html` 在解压时完整保留。Windows Terminal 源码的许可见 [官方 LICENSE](https://github.com/microsoft/terminal/blob/main/LICENSE)。本仓库不将终端运行时二进制重新授予 MIT 许可。

Lucida Console、Consolas、微软雅黑等字体从 Windows 系统读取，不复制或发布字体文件；字体使用适用其原有许可。
