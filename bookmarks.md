# 收藏清單

資料日期：2026-10-05。「最後 commit」為 clone 當下讀到的日期；狀態欄的內容皆來自 README，效能數字為作者自測，未重跑。

## Muse 生態

| 名稱 | 連結 | 用途 | 授權 | 最後 commit | 備註 |
|---|---|---|---|---|---|
| awesome-muse-connectors | https://github.com/Anil-matcha/awesome-muse-connectors | Muse 社群連接器清單（150 個 skill + 12 個範本） | MIT | 2026-10-03 | 非 Meta 官方 |
| muse-cli | https://github.com/nikships/muse-cli | 終端機操作 muse.ai 個人 agent | MIT | 2026-10-03 | 用 Chrome cookie 登入、走內部協定 |
| muse-mcp | https://github.com/kleprevost/muse-mcp | 把 muse-cli 包成 MCP server | MIT | 2026-09-17 | README 自述 API 未版本化，可能壞 |
| OpenMuse | https://github.com/CopilotKit/OpenMuse | 開源個人 agent（瀏覽器、終端機、檔案；iOS/Android/Web） | MIT | 2026-10-02 | Alpha；README 查無 Spark/Glimmer 字樣 |

## 短影音

| 名稱 | 連結 | 用途 | 授權 | 最後 commit | 備註 |
|---|---|---|---|---|---|
| video-talkcraft | https://github.com/Vincentwei1021/video-talkcraft | 口播影片 agent skill（Remotion、108 張動效卡） | PolyForm Noncommercial | 2026-10-01 | 不可商用 |
| automate-faceless-content | https://github.com/cporter202/automate-faceless-content | 匿名影片自動化課程 | 未查 | 2026-06-03 | 導向付費產品 ViralWave Studio |

## 本地模型與推論

| 名稱 | 連結 | 用途 | 授權 | 最後 commit | 備註 |
|---|---|---|---|---|---|
| Strata | https://github.com/Niko1221/Strata | 在 12GB+ 顯卡跑 125B 量化模型 | MIT | 2026-10-04 | 需 12GB VRAM、32GB+ RAM；Sword15 規格未確認 |
| TensorFold | https://github.com/ashhart/TensorFold | OpenAI 相容 API 推論（Apple Silicon、NVIDIA） | Apache-2.0 | 2026-10-03 | 需算力 8.9+（RTX 40/50），RTX 30 不支援 |

## Claude Code / agent 工具

| 名稱 | 連結 | 用途 | 授權 | 最後 commit | 備註 |
|---|---|---|---|---|---|
| claudebigimage | https://github.com/joshhu/claudebigimage | Claude Code 外掛，貼圖大尺寸預覽 | MIT（fork 自 claude-image-view） | 2026-10-04 | 寬度需 144 欄以上才自動開 Pane |
| Pi-Bolt | https://github.com/opensec-git/Pi-Bolt | Pi coding agent 的原生編譯版 | MIT | 2026-10-05 | 無 Windows 版；v0.6.1；與 Pi 作者無關 |

## 其他

| 名稱 | 連結 | 狀態 |
|---|---|---|
| freedom-platform PR #108 | https://github.com/FreeTWAI-AI/freedom-platform/pull/108 | 只讀到 commit（遷移、CodeQL 處置等），沒有 PR 描述 |
| HackMD 筆記 | https://hackmd.io/@Ig6LYCGwSVGrVz1PgDBqqg/HJdT02RqGg | 未讀到（網路代理封鎖），內容待補 |

## 參考：OpenClaw Dreaming（記憶鞏固）

- 三階段：淺睡（去重、暫存）→ REM（找主題）→ 深睡（唯一寫入 MEMORY.md）。
- 已查證：三階段與只有深睡寫入長期記憶；官方說法是實驗性、預設關閉。
- 未查證：六個權重數字、凌晨 3 點排程（來源網站被封鎖）。
- 來源：https://dev.to/czmilo/openclaw-dreaming-guide-2026-background-memory-consolidation-for-ai-agents-585e

## 參考：Muse 時間線（查證後）

| 日期 | 事件 | 狀態 |
|---|---|---|
| 2026-04 | Spark 第一版 | 只確認月份 |
| 2026-07-09 | Spark 1.1 | 確認 |
| 2026-08-05 | Spark 1.2 與 Muse Code | 搜尋結果 |
| 2026-08-10 | Muse Glimmer（30B 開放權重，Apache-2.0） | 確認；Glimmer 不等於 Spark 1.2 |
| 2026-09-02 | Spark 1.3 | 確認 |
| 2026-09-08 | Meta Muse App | 未查到 |

## 來自 Reddit 貼文（資料日期 2026-10-08；內容皆為貼文自述，**未驗證**，我沒有讀過這些 repo）

### r/SATNA_PROJECT：「10 個把 LLM 變成自主系統的開源 repo」

注意：發文者在貼文末尾導向自己的 Discord；貼文為社群帳號所發，非官方資料。

| 層 | 名稱 | 連結 | 貼文說的用途 |
|---|---|---|---|
| 控制 | LangGraph | https://github.com/langchain-ai/langgraph | 有狀態、可長時間執行的 agent 工作流編排 |
| 控制 | PydanticAI | https://github.com/pydantic/pydantic-ai | 有型別驗證與結構化輸出的 agent |
| 控制 | Mastra | https://github.com/mastra-ai/mastra | agent、工作流、RAG、記憶的應用框架 |
| 控制 | Agno | https://github.com/agno-agi/agno | 多 agent 系統框架 |
| 記憶 | Cognee | https://github.com/topoteretes/cognee | 把原始資料變成情境知識層 |
| 記憶 | Graphiti | https://github.com/getzep/graphiti | 時間性知識圖譜（事實會隨時間更新） |
| 執行 | Browser Use | https://github.com/browser-use/browser-use | 讓 agent 操作網站 |
| 執行 | E2B | https://github.com/e2b-dev/E2B | 隔離沙盒執行 AI 產生的程式 |
| 可靠性 | Langfuse | https://github.com/langfuse/langfuse | 追蹤、提示管理、評估、可觀測性 |
| 可靠性 | DeepEval | https://github.com/confident-ai/deepeval | LLM 應用的測試與評估 |

- 貼文建議的最小組合：LangGraph + PydanticAI + Browser Use + E2B + Langfuse；需要記憶時再加 Cognee 或 Graphiti。
- 留言提到的 Conscio（https://github.com/Neguiolidas/Conscio）與 Hermes Agent：只是網友推薦，未驗證。
- 與本 repo 的關聯：Graphiti 的「事實隨時間被取代」概念，跟 Dreaming 深睡階段「剔除過期或衝突資訊」相近。

### r/unsloth：「用 Unsloth 在本機訓練 Decision Model（4GB VRAM）」

| 項目 | 貼文自述 |
|---|---|
| 發文者 | u/yoracale（r/unsloth 版主） |
| 主張 | Qwen3.5 0.8B 的三項決策基準總和準確率從 20.7% 升到 74.3%，僅需 4GB VRAM |
| 方法 | Unsloth + LoRA（r=64）+ Clef head，訓練 1 個 epoch；另一句寫下游準確率 30 到 37% 升到 78% |
| 連結 | Unsloth：https://github.com/unslothai/unsloth ；指南：https://unsloth.ai/docs/basics/train-your-own-decision-model-with-unsloth |

- 兩組數字（74.3% 與 78%）基準不同，貼文沒有說明差異；原文未提供基準名稱。
- 「Clef」「Laya」我查不到定義，貼文與留言都沒解釋；細節待讀官方指南。
- 留言有人反映指南沒講清楚訓練資料格式，版主尚未在摘錄內回覆。
- 與 Sword15 的關聯：4GB VRAM 的門檻低於 Strata 的 12GB，但 Sword15 的實際顯卡未確認。

## 補充（資料日期 2026-10-08）

### Alter Zero（已 clone 並讀 README，最後 commit 2026-10-06）

| 項目 | 內容 |
|---|---|
| 連結 | https://github.com/linuztx/alter-zero |
| 是什麼 | Rust 寫的終端機 coding agent，主打能操作互動式終端 session（非一次性 shell 指令） |
| 版本與授權 | 0.12.0；Apache-2.0 |
| 平台 | Linux（x86_64、arm64）、macOS；README 未列 Windows |
| 注意 | 預設開啟每日一次匿名 ping（隨機安裝 ID、版本、OS、架構、Linux 發行版），可用設定、環境變數或 `DO_NOT_TRACK` 關閉（見 TELEMETRY.md） |
| 來源貼文 | r/OpenSourceeAI（作者 u/linuztxx）；留言有人問與 optiq code 的比較，作者未在摘錄中回覆 |

「RAM 效率高」是貼文標題的說法，我沒有量測，未驗證。

### Strata 對其他模型的支援（r/LowEndLocalAI 貼文 + PR #1402）

| 項目 | 內容 | 狀態 |
|---|---|---|
| PR | https://github.com/Niko1221/Strata/pull/1402 ，作者 aflin，2026-10-07 開，**Open、未合併** | 已確認（PR 頁面） |
| 內容 | 讓引擎支援 qwen35moe 架構，新增 Qwen3.6-35B-A3B（UD-IQ4_XS、UD-IQ3_S）與 Ornith-1.5-35B-A3B；定位為 16 到 32GB RAM、6 到 12GB 顯卡 | 已確認（PR 描述） |
| 作者測試 | RTX 4070 Ti 12GB、Linux；短對話 105 tok/s；與 llama.cpp b11438 貪婪輸出一致；未在 AMD 與 Windows 測過 | PR 作者自述 |
| 網友實測 | RTX 2070 8GB + 32GB DDR4：輸出約 80 tok/s（0 context）、20k context 約 65；prompt 讀取 285 tok/s | 單一網友留言，未驗證，未說明量化版本 |
| 留言抱怨 | 有人說 CMakeLists 有錯誤、安裝方式不清楚 | 單一留言，未驗證 |

對 Sword15 的影響（推測）：主線 Strata README 要求 12GB VRAM；若 PR #1402 合併，8 到 12GB 卡才可能適用。目前仍是 PR，尚未合併，Sword15 規格也未確認。

### r/MistralAI：「72% 的智慧，3.8% 的 GPU」

- 這是一張圖表貼文（影片 18 秒），貼文本身沒有文字說明，圖中數字我看不到，無法確認。
- 留言多數質疑指標：GPU 數量不等於 GPU 時數，也忽略 GPU 種類與訓練時間；有人指出缺少中國模型的對照。
- 留言提到 Mistral 新資料中心有 13,800 顆 GB300，來源為網友引用的第三方文章，未驗證。
- 留言裡的具體比例與月數估算（例如「落後 13 個月」）是網友自行推算，沒有來源。
- 結論：這是帶有宣傳性質的圖表加討論串，沒有可收藏的 repo，只留作背景。

### r/SATNA_PROJECT：「建新 agent 前先看的 5 個 repo」（資料日期 2026-10-12；5 個 repo 皆已 clone 並核對）

貼文作者與上一篇相同（文末導向自己的 Discord），屬社群貼文；下表「核對結果」是我讀 repo 的結果。

| 名稱 | 連結 | 授權 | 最後 commit | 核對結果 |
|---|---|---|---|---|
| agency-agents | https://github.com/msitarzewski/agency-agents | MIT | 2026-10-08 | 依部門分類（engineering、design、marketing、sales、security、game-development、healthcare 等目錄皆在）；另有桌面 App（macOS、Linux、Windows），可安裝到 Claude Code、Cursor、Codex 等 |
| wshobson/agents | https://github.com/wshobson/agents | MIT | 2026-10-04 | README 寫「94 個 plugin（92 本地 + 2 外部）、202 agents、184 skills、105 commands」；我數到 skills 184、commands 105 **相符**；agent 檔案我數到 758 個，與 202 不同，原因不明（推測含各工具版本的副本，未驗證） |
| knowledge-work-plugins | https://github.com/anthropics/knowledge-work-plugins | Apache-2.0 | 2026-10-11 | **確認為 Anthropic 官方 org**；為 Claude Cowork 設計，也相容 Claude Code；目錄含 sales、customer-support、product-management、marketing、legal、finance、data 等 |
| claude-quickstarts | https://github.com/anthropics/claude-quickstarts | MIT | 2026-10-07 | **確認為 Anthropic 官方 org**；需 Claude API key；README 明寫部分範例「不是 production code」；貼文提到的 Daily Brief（Slack + GitHub）、Linear、Sentry、Slack 範例都在 `managed-agents/` 下，customer-support-agent、financial-data-analyst 也在 |
| agent-skills | https://github.com/addyosmani/agent-skills | MIT | 2026-10-10 | 貼文說 25 個 skill，我數到 **25 個 SKILL.md，相符**；含 spec-driven-development、test-driven-development、code-review-and-quality、security-and-hardening、ci-cd-and-automation 等 |

- 貼文說「兩個是官方 Anthropic 專案」：核對屬實（knowledge-work-plugins、claude-quickstarts）。
- 這 5 個 repo 我只讀了 README、目錄與計數，沒有安裝或執行任何東西，所以「好不好用」未驗證。
- 與本 repo 的關聯：agent-skills 的「每步要驗證證據才算完成」做法，可對照 Dreaming 深睡階段的「評分過門檻才寫入」。
