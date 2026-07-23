# Python Core package candidates

状态：候选清单，尚未加入 `app-catalog.json` 或自动安装器。

这份清单服务于本机 Python 工作流和后续多台 Mac bootstrap。当前
`install_my_macos_apps` 的 catalog/installer 原生支持 Homebrew formula、
Homebrew cask 和 CLI，不支持直接把 PyPI wheel 当作独立 catalog item；因此
先记录政策和分层，不把未经审核的 pip 安装塞进 Core 安装流程。

## Runtime 与边界

当前共享环境使用 Python 3.14。共享环境不等于所有依赖都属于默认 Core；依赖按 uv dependency groups 管理。

| 类型 | 包/工具 | 用途 | 备注 |
|---|---|---|---|
| Runtime | Python 3.14 | MLX/Python 主运行时 | 共享环境为 `~/.local/share/python/core/.venv` |
| Runtime | `uv` | Python 环境、依赖、lock 管理 | 建议 Homebrew formula；不是 wheel |
| System | `ffmpeg` | m4a/wav/mp3 解码、重采样、切片 | 建议 Homebrew formula；不是 wheel |
| ML | `mlx-whisper==0.4.3` | Apple Silicon 本地转写 | `audio` group |
| Model | Hugging Face Hub | 下载和缓存 MLX 模型 | 模型本身不进入 Git |
| Numerical | `numpy` | 数值数组基础 | 由 `mlx-whisper` 解析版本 |
| Numerical | `scipy` | 音频/科学计算 | 由 `mlx-whisper` 解析版本 |
| ML support | `numba`, `llvmlite` | `mlx-whisper` 的运行依赖 | 不单独 pin，随 resolver 管理 |
| ML support | `mlx` | Apple Silicon MLX runtime | 由 `mlx-whisper` 解析版本 |
| Text/audio | `tiktoken` | Whisper tokenizer | 由 `mlx-whisper` 解析版本 |
| CLI | `tqdm`, `more-itertools` | 进度和迭代工具 | 由 `mlx-whisper` 解析版本 |
| Data | `PyYAML` | job manifest/YAML 配置 | 默认 Core |

### Core 安装原则

优先把 `mlx-whisper` 作为一个 package set 的入口，而不是手动分别安装
所有传递依赖。当前 `mlx-whisper 0.4.3` 的直接依赖包括：

```text
mlx>=0.11
numba
numpy
torch
tqdm
more-itertools
tiktoken
huggingface_hub
scipy
```

版本应由 `pyproject.toml` + `uv.lock` 管理。Core bootstrap 不应把
`torch`、`cuda-*`、`triton` 等 lock 文件中的平台/传递条目逐个登记为
macOS 应用；在 Apple Silicon 上只记录 resolver 实际安装的 macOS 包。

## 已批准的 groups

当前 manifest 已批准以下工作流分组：

| group | 主要包 | 用途 |
|---|---|---|
| `audio` | `mlx-whisper==0.4.3` | Apple Silicon 本地转写 |
| `data` | `pandas`, `polars`, `pyarrow`, `duckdb`, `scikit-learn` | 数据分析、SQL、传统 ML |
| `data` | `matplotlib`, `seaborn`, `jupyterlab`, `ipykernel` | 可视化与 Notebook |
| `llm` | `mlx-lm`, `openai` | 本地 MLX LLM 与云端 SDK |
| `agent` | `pydantic-ai` | 类型安全 Agent 与结构化输出 |
| `dev` | `pytest`, `pytest-asyncio`, `respx`, `hypothesis`, `ruff`, `tenacity` | 测试、mock、lint 与重试 |

## 暂不加入 Core

以下包暂不加入共享环境，会由具体项目触发：

- `whisperx`、`pyannote.audio`：说话人识别和 forced alignment，需单独评估模型、许可和 GPU/CPU 成本。
- `librosa`：功能较大；当前先用 ffmpeg、AVFoundation 和 mlx-whisper。
- `transformers`、`datasets`、`sentence-transformers`：通用模型与 embedding 生态，依赖和模型缓存较大。
- `qdrant-client`、`chromadb`：向量数据库客户端，先用 DuckDB/SQLite 验证 RAG 需求。
- `langgraph`、`litellm`、`ollama`：Agent 编排、多 provider 路由和本地服务，避免同时预装多个框架。
- `streamlit`、`gradio`：交互式 demo/UI，不属于基础运行时。
- `dask`、`ray`：大规模并行计算，等数据规模确认后再装。
- `mlflow`、`langfuse`、`arize-phoenix`：实验追踪和观测平台，先用本地 JSONL/SQLite。
- `openpyxl`：表格/报价工作流按需加入。
- `torch`、`cuda-*`、`triton`：作为 `mlx-whisper` 的 resolver 依赖处理，不单独作为 macOS Core 清单项。
- `whisperx`、`pyannote.audio`、`librosa`：说话人识别、对齐和音频分析需单独评估。

## 推荐的共享 Core 形态

不要在 `app-catalog.json` 里登记十几个 PyPI wheel。当前采用一个受控的
共享 Python package set：

```yaml
component_id: python-local-mlx
tier: core
runtime: python@3.14
manager: uv
manifest: references/python-core/pyproject.toml
lockfile: references/python-core/uv.lock
environment: ~/.local/share/python/core/.venv
install_command: UV_PROJECT_ENVIRONMENT=~/.local/share/python/core/.venv uv sync --locked --all-groups
verify_command: ~/.local/share/python/core/.venv/bin/python -c "import mlx, mlx_whisper, pandas, polars, duckdb, pydantic_ai"
```

该环境不属于任何单一 repo，供本机所有工作流共享。各 repo 仍保留自己
的 `pyproject.toml`/`uv.lock` 作为声明或兼容性记录，但默认不再为同一组
Core 包创建重复 `.venv`。如果只需要部分能力，可以使用
`uv sync --locked --group audio --group llm` 等命令。

安装脚本应记录 `download_bytes`、`installed_bytes`、版本和时间到 ignored
machine-local state，与 Skill 对 Core 组件的测量规则一致；密码、token、Hugging Face
凭据和个人音频不得写入 catalog、Markdown 或 Git。
