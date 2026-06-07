# 小六 YouTube 字幕批量下载

本目录用于从 **小六 SixPoker**（[@SixPoker666](https://www.youtube.com/@SixPoker666)）YouTube 频道批量下载公开字幕，并转成纯文本，供本专案 **`xiao-liu-perspective` Skill** 作为本地语料使用。

---

## 在本专案中已做过的事（总览）

以下是为「德州扑克学习 + 小六视角 Skill」所完成的相关工作，与本脚本直接相关部分标有 ★。

| 项目 | 说明 | 位置 |
|------|------|------|
| ★ **YouTube 字幕批量下载脚本** | 本目录：`batch_download.py`、`run.ps1` | `scripts/xiao-liu-youtube/` |
| ★ **Whisper 音轨转写** | 无字幕视频：下载音轨 → faster-whisper → transcript | `batch_whisper.py` |
| ★ **cookies.txt 认证** | 用浏览器导出的 Cookie 下载年龄限制视频（比 `--cookies-browser` 稳定） | 本目录 `cookies.txt` |
| ★ **字幕 → 纯文本** | SRT/VTT 清洗为 transcript | `srt_utils.py` |
| ★ **输出与清单** | SRT、transcript、`manifest.json` | 见下方「输出目录」 |
| **小六视角 Skill（女娲蒸馏）** | 基于公开资料蒸馏的扑克思维框架 Skill | `.agents/skills/xiao-liu-perspective/` |
| **女娲 skill（huashu-nuwa）** | 用于蒸馏人物/主题 Skill 的工具 | `.agents/skills/huashu-nuwa/` |
| **本机 LLM（Ollama）** | 本地 `deepseek-r1:8b`，可辅助分析手牌 | `doc/llm-guide.md`、`doc/llm-api.md` |

**典型工作流：**

1. 用本脚本下载小六 YouTube 字幕 → transcript  
2. **若无字幕**：用 `batch_whisper.py` 从音轨转写  
3. 语料存入 `xiao-liu-perspective/references/sources/`  
4. 在 Cursor 中激活 **小六视角 Skill** 或调用本机 LLM 做扑克分析  

---

## 本目录文件说明

| 文件 | 用途 |
|------|------|
| `batch_download.py` | 主程序：列出频道视频、下载字幕、转换 transcript、更新 manifest |
| `batch_all.py` | **一键全频道**：字幕下载 + Whisper 补全 |
| `batch_whisper.py` | 无字幕：音轨 → Whisper 转写 + **自动生成 SRT** |
| `whisper_to_srt.py` | 已有 whisper_meta → 重新生成 SRT |
| `restore_transcript.py` | 从 `whisper_meta` 恢复被覆盖的 raw transcript |
| `ytdlp_common.py` | yt-dlp、路径、manifest 共用逻辑 |
| `llm_polish.py` | 可选：Ollama 整理 Whisper 转写文本 |
| `run.ps1` | PowerShell 快捷入口（含 UTF-8 终端设置） |
| `srt_utils.py` | SRT ↔ 纯文本；Whisper segments → SRT |
| `cookies.txt` | **你自行导出**的 YouTube 登录 Cookie（勿提交 Git） |
| `cookies.txt.example` | Cookie 文件格式与导出说明示例 |
| `README.md` | 本说明 |

---

## 依赖

### 字幕下载（必需）

```powershell
cd C:\Users\s9200\Desktop\ray\side_project\poker_learning_tool
uv sync
# 或: pip install yt-dlp
```

**另需 Node.js（LTS）**：yt-dlp 2026 起需 Node.js 通过 YouTube 的 JS 验证（n challenge）。  
脚本会自动使用 `--remote-components ejs:github` + `--js-runtimes node`。  
若未安装：https://nodejs.org

### Whisper 音轨转写（可选）

```powershell
cd C:\Users\s9200\Desktop\ray\side_project\poker_learning_tool
uv sync --extra whisper
# 或: pip install faster-whisper
```

| 组件 | 说明 |
|------|------|
| **faster-whisper** | GPU 加速转写（会安装 PyTorch，体积较大） |
| **NVIDIA GPU** | RTX 4070 Ti 16GB 可用 `--model large-v3` 或默认 `medium` |
| **Ollama** | `--llm-polish` 时用于标点整理（需已运行 `deepseek-r1:8b`） |
| **ffmpeg** | 非必需；yt-dlp 可直接下载 m4a/webm 音轨 |

安装 ffmpeg（可选，用于其他音频处理）：

```powershell
winget install ffmpeg
```

---

## 使用前：准备 cookies.txt（一次性）

小六许多视频有 **年龄限制**，下载字幕需要已登录 YouTube 的 Cookie。

### Chrome 或 Edge 均可

1. 安装扩展 **Get cookies.txt LOCALLY**  
   - [Chrome 商店](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)  
   - [Edge 商店](https://microsoftedge.microsoft.com/addons/detail/get-cookiestxt-locally/)
2. 在**同一浏览器**打开 https://www.youtube.com 并 **登录**
3. 点击右上角 **扩展图标** → **Export** / **Download**
4. 将下载的文件放到**本目录**，并改名为：

   ```
   cookies.txt
   ```

完整路径：

```
C:\Users\s9200\Desktop\ray\side_project\poker_learning_tool\scripts\xiao-liu-youtube\cookies.txt
```

> **安全**：`cookies.txt` 等于登录凭证，不要分享、不要上传 Git（已加入 `.gitignore`）。

---

## 使用方法

### 下载全部视频语料（推荐）

频道 `@SixPoker666` 目前约 **286 支**公开视频。一键流程：

```powershell
cd C:\Users\s9200\Desktop\ray\side_project\poker_learning_tool\scripts\xiao-liu-youtube

# 1. 预览（看会处理多少支）
.\run.ps1 all --dry-run

# 2. 建议先试 10 支
.\run.ps1 all --limit 10

# 3. 下载全部（字幕 + 无字幕则 Whisper，已下载的自动跳过）
.\run.ps1 all

# 只下载字幕，暂不 Whisper
.\run.ps1 all --skip-whisper
```

**流程说明：**

| 步骤 | 做什么 | 输出 |
|------|--------|------|
| Step 1 | 尝试下载 YouTube 字幕 | `youtube/srt/*.srt` → `transcripts/*.txt` |
| Step 2 | 尚无 transcript 的视频用 Whisper | `youtube/audio/` + `transcripts/*.txt` + **`youtube/srt/*.whisper.srt`** |

**耗时预估（286 支，小六多数无 CC）：**

- Step 1 字幕探测：约 30–60 分钟（每支几秒）
- Step 2 Whisper（GPU medium）：约 **10–15 小时**（每支约 2–4 分钟）
- 可分批：`.\run.ps1 all --limit 50`，跑完再跑 `./run.ps1 all`（自动跳过已有）

**前置条件：** 同目录有 `cookies.txt`；已 `uv sync --extra whisper`；CUDA 12 已装（GPU 转写）。

---

### 分步操作

```powershell
cd C:\Users\s9200\Desktop\ray\side_project\poker_learning_tool\scripts\xiao-liu-youtube

# 列出最新 5 支（不下载，不需要 cookies）
python batch_download.py --dry-run --limit 5

# 下载最新 5 支字幕（自动读取同目录 cookies.txt）
python batch_download.py --limit 5

# 下载整个频道（跳过已下载）
python batch_download.py

# 指定 cookies 路径
python batch_download.py --cookies "D:\path\cookies.txt" --limit 5

# 只把已有 SRT 转成 transcript
python batch_download.py --convert-only

# 使用快捷脚本（推荐，含 UTF-8）
.\run.ps1 --limit 5
```

### Whisper 转写 → SRT 字幕（带时间轴）

Whisper 转写后会自动生成 **SRT 字幕**（含每句起止时间），可用 PotPlayer / VLC 加载对照。

```powershell
# 转写时自动生成 *.whisper.srt
.\run.ps1 whisper --limit 1

# 已有 whisper_meta，单独生成/更新 SRT
.\run.ps1 to-srt
.\run.ps1 to-srt 6ibZiZb2-2k
```

**输出示例**（`youtube/srt/6ibZiZb2-2k.whisper.srt`）：

```srt
1
00:00:01,740 --> 00:00:34,380
因為其實我今年生意事業比較忙碌

2
00:00:34,380 --> 00:00:35,880
我比較少打牌
```

文件名 `{video_id}.whisper.srt` 与 YouTube 官方字幕区分；`transcripts/*.txt` 仍为无时间轴纯文本。

---

### Whisper 音轨转写（无字幕视频）

小六许多视频**未开启 YouTube CC**，需用 Whisper 从音轨转文字：

```powershell
# 试跑：列出待处理视频
.\run.ps1 whisper --dry-run --limit 3

# 只转写 manifest 里已标记「无字幕」的视频
.\run.ps1 whisper --only-no-subs

# 转写最新 1 支（建议先试 1 支，长视频较慢）
.\run.ps1 whisper --limit 1

# 转写 + Ollama 整理标点（需 Ollama 运行中）
.\run.ps1 whisper --limit 1 --llm-polish

# 指定 Whisper 模型（4070 Ti 16GB 可试 large-v3）
python batch_whisper.py --limit 1 --model large-v3
```

> **警告：** `--llm-polish` 可能把万字 transcript **总结成千字并覆盖**原文件。Skill 语料请保留 Whisper raw。若误覆盖：`python restore_transcript.py VIDEO_ID`

| 参数 | 说明 |
|------|------|
| `whisper` | `run.ps1` 子命令，切换到 `batch_whisper.py` |
| `--only-no-subs` | 只处理 manifest 中 `status: no_subs` 的视频 |
| `--model` | Whisper 模型：`tiny` / `medium`（默认）/ `large-v3` |
| `--device` | `cuda`（默认）或 `cpu` |
| `--llm-polish` | 转写后用本机 Ollama 加标点、分段 |
| `--video-id ID` | 只处理单支视频 |
| `--no-skip-existing` | 强制重新转写（覆盖已有 transcript） |

### 命令参数

| 参数 | 说明 |
|------|------|
| `--dry-run` | 只列出将处理的视频，不下载 |
| `--limit N` | 最多处理 N 支（0 = 全部） |
| `--cookies PATH` | 指定 cookies.txt（默认：本目录 `cookies.txt` 若存在） |
| `--cookies-browser edge` | 从浏览器读 Cookie（Windows 上常失败，不推荐） |
| `--convert-only` | 仅转换已有 SRT/VTT |
| `--url URL` | 指定频道/播放列表/单支视频 URL |

---

## 输出目录

| 类型 | 路径 |
|------|------|
| 原始字幕 (SRT/VTT) | `.../youtube/srt/`（YouTube 官方或 `*.whisper.srt`） |
| 音轨缓存 (m4a/webm) | `.agents/skills/xiao-liu-perspective/references/sources/youtube/audio/` |
| 纯文本 transcript | `.agents/skills/xiao-liu-perspective/references/sources/transcripts/` |
| Whisper 分段元数据 | `.agents/skills/xiao-liu-perspective/references/sources/youtube/whisper_meta/` |
| 下载清单 | `.agents/skills/xiao-liu-perspective/references/sources/youtube/manifest.json` |

`manifest.json` 记录每支视频的标题、下载/转写状态；Whisper 成功后会写入 `transcript_source: whisper`、`whisper_model` 等字段。

---

## 常见问题

### 终端中文乱码

```powershell
chcp 65001
# 或直接使用
.\run.ps1 --dry-run --limit 5
```

### `n challenge solving failed` / JavaScript runtime

YouTube 加强了反爬验证。请确认：

1. 已安装 **Node.js LTS**（https://nodejs.org）
2. 重新运行脚本（会自动加 EJS 组件，**首次需联网**从 GitHub 下载验证脚本）
3. 终端应显示：`YouTube 验证: EJS + Node.js node.exe`

### 显示「无字幕」而非失败

部分小六视频**未开启** YouTube 字幕/CC，验证通过后仍会显示「该视频未提供字幕」，属正常。  
**下一步**：运行 `.\run.ps1 whisper --only-no-subs` 用 Whisper 从音轨转写。

### Whisper 转写很慢 / 显存不足 / CUDA 报错

- 先用 `--limit 1` 试一支短视频  
- 若出现 `cublas64_12.dll is not found`：安装 [CUDA Toolkit 12](https://developer.nvidia.com/cuda-downloads)（实测 v12.6 可用）；脚本会自动把 `CUDA\v12.x\bin` 加入 PATH  
- 若仍失败，脚本会**自动改 CPU 转写**（较慢）  
- 显存不够时改用 `--model medium` 或 `--device cpu`  
- 长视频（30+ 分钟）在 CPU 上可能需 30–60 分钟  

### `Could not copy Chrome cookie database`

不要用 `--cookies-browser`，改用 **cookies.txt**（见上文）。

### YouTube 限流（rate-limited）

连续请求太多时会出现：

```text
rate-limited by YouTube for up to an hour
```

**脚本已内置防限流（默认 `--sleep 5`）：**

```powershell
# 等 1～2 小时后再跑；只重试上次失败（跳过会员专属）
.\run.ps1 whisper --retry-failed --sleep 5

# 分批跑（推荐）
.\run.ps1 whisper --limit 10 --sleep 5

# 遇到限流会自动停止本轮，避免越跑越糟
```

| 错误类型 | 处理 |
|----------|------|
| `rate_limited` | 等 1 小时 → `--retry-failed` |
| `members_only` | 需 YouTube 频道会员，自动跳过 |
| `age_restricted` | 重新导出 `cookies.txt` |

### `Sign in to confirm your age`

- 确认 `cookies.txt` 在本目录且为**已登录 YouTube** 的浏览器导出  
- Cookie 过期 → 重新登录并再导出  

### 下载成功但想更新小六 Skill

语料下载完成后，可在 Cursor 中对 Agent 说：

- 「根据 `references/sources/transcripts/` 更新小六 Skill」  
- 「用小六的视角分析这手牌」  

Skill 本体：`.agents/skills/xiao-liu-perspective/SKILL.md`

---

## 法律与用途说明

- 仅下载 **YouTube 公开视频** 的字幕，用于 **个人学习** 与 Skill 语料整理  
- **勿** 爬取小六 **付费课程**（course.sixpoker666.com）视频或讲义  
- 遵守 YouTube 服务条款；勿公开再分发完整 transcript  

---

## 相关文档

- 专案总览：`../../readme.md`  
- 本机 LLM：`../../doc/llm-guide.md`  
- 小六 Skill：../../.agents/skills/xiao-liu-perspective/SKILL.md  
