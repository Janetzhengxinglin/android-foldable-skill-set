# 安卓折叠屏适配审查 Skill Set

用于 Codex 的安卓折叠屏录屏审查工具包。安装整套后，只需调用总入口，Codex 会依次整理录屏、逐页审查、汇总并交付报告。

## 安装

在 Codex 中发送以下内容，让 agent 下载并安装整套：

```text
请使用 $skill-installer 安装完整的安卓折叠屏适配审查 Skill Set，并检查依赖、完成联动检查。
仓库：https://github.com/Janetzhengxinglin/android-foldable-skill-set
分支：codex/main
请一次安装 skills/ 下的三个 skill，保持同级；已有同名版本先备份。
```

安装完成后，调用总入口 `$android-foldable-adaptation-review` 即可串联页面采集、规范审查和报告交付。

<details>
<summary>手动下载安装</summary>

1. [下载默认分支最新 ZIP](https://github.com/Janetzhengxinglin/android-foldable-skill-set/archive/refs/heads/codex/main.zip)，解压到任意工作目录；也可点击 **Code → Download ZIP**。
2. 在解压目录运行：

   ```bash
   python3 install_skills.py --check
   ```

   Windows 可用 `py -3 install_skills.py --check`。脚本默认安装到 `$CODEX_HOME/skills`，未设置时使用 `~/.codex/skills`。已有同名 skill 会整目录备份到相邻的 `skill-backups/`，备份路径在安装结果中显示。

3. 在 Codex 开始新对话，让新安装的 skills 被发现。

发行版 ZIP 的三个 skill 位于压缩包根目录，也可运行同一安装脚本。手动安装时，将三个 skill 文件夹一起复制到 `CODEX_HOME/skills/` 下，保持同级；不要只安装总入口。

使用其他目录时：

```bash
python3 install_skills.py --target /path/to/codex-home/skills --check
```

安装只复制本工具包的三个 skill，不安装外部程序、不改其他 skills。若 `--check` 提示缺依赖，skills 已安装；补齐依赖后可运行 `python3 check_install.py`。

</details>

## 开始审查

在 Codex 提交本地录屏，并调用：

```text
$android-foldable-adaptation-review
审查这个安卓折叠屏录屏。设备为展开横屏、4:3。请把报告放到我提供的 Figma 文件。
视频：/path/to/recording.mp4
Figma：https://www.figma.com/design/YOUR_FILE_KEY
```

设备比例、内外屏或方向不知道时可说明未知；不要推测技术参数。提供多个录屏时，采用集中批量流程：脚本批量抽帧，按流程筛选清晰代表图并集中观察，再批量生成审核记录、重点回查问题和报告、统一输出报告。默认将截图质量和适配巡检合并，通过清晰整页拼图覆盖全部页面，疑点打开原图；仅回查问题和报告，不强制两轮全量原图复读。需要严格双轮时可选择 two-pass。不为每张截图或组件建立独立任务。

Codex 会根据素材关联性和工作量选择执行方式：简单或连续流程由主智能体处理；可独立处理且有明确收益时使用子智能体按阶段分工，复杂审查可增加独立复查。各任务使用固定证据和独立结果目录，最终由主智能体核对完整覆盖并发布。环境不支持子智能体时按相同覆盖要求继续执行。

三个 skill 安装在同一层级，入口按顺序联动：

| Skill | 负责内容 | 交接 |
| --- | --- | --- |
| `android-foldable-page-capture` | 录屏采样、稳定页面与状态清单、选帧来源 | `capture.json` |
| `android-foldable-design-guidelines` | Google 基础适配的全页清晰巡检、问题重点回查 | `review.json` |
| `android-foldable-adaptation-review` | 调用前两环节、同类归组、完整问题汇总与报告交付 | Figma 或指定文档 |

“自动串联”指总入口 skill 指示 Codex 调用另外两个环节，安装脚本一次安装完整兄弟目录。它不是后台机器人；脚本也不自动判断图片或替代真实视觉审查。

## 依赖和交付

- Codex：能发现本地 skills、执行 Python、读取图片；图片批量处理仍遵守每批和累计预算。
- Python **3.9+**、`ffmpeg`、`ffprobe`：加入 `PATH`。Python 脚本使用标准库，不需要 Pillow 或 OpenCV。
- Figma 交付：在 Codex 连接可用的官方 Figma 工具和对应工具 skill，并提供可编辑的目标文件。飞书交付需要相应文档工具。没有写入工具时保留本地报告草稿并说明未发布。

macOS 可用 `brew install ffmpeg`；Ubuntu/Debian 可用系统包管理器安装 `ffmpeg`；Windows 可从 [FFmpeg 官方下载页](https://ffmpeg.org/download.html) 获取构建并加入 `PATH`。

默认只审查录屏中已提供状态的可见显示。页面覆盖不等于整个 App 覆盖，也不等于动态功能、真实点击热区或完整 Google Play 认证。官方示意用于解释规范，不替代 App 原图证明缺陷。

## 更新与恢复

下载新版本后重新运行安装命令。旧版完整保留在安装结果给出的备份目录中。需要恢复时，先把当前同名目录移动到其他位置，再将备份中的三个目录移回原 `skills/` 目录；不要删除唯一内容。

代码许可见 [LICENSE](LICENSE)，第三方官方文字、图示与资料许可范围见 [NOTICE.md](NOTICE.md)。
