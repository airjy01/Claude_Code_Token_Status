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
