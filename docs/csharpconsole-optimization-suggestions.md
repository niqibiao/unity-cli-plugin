# com.zh1zh1.csharpconsole 优化建议

> 生成日期: 2026-04-07
> 基于版本: 1.0.0
> 关联仓库: unity-cli-plugin (CLI 对接侧)
> 状态更新: 2026-04-07 — 全部建议已实现

---

## 汇总

| # | 优先级 | 建议 | 状态 |
|---|--------|------|------|
| 1 | P0 | ReplServiceRegistry Key 碰撞修复 | **已实现** |
| 2 | P0 | MainThreadRequestRunner 死锁防护 | **已实现** |
| 3 | P0 | CommandRouter Discovery 重试 | **已实现** |
| 4 | P1 | Health Endpoint 版本信息 | **已实现** — 返回 packageVersion, protocolVersion, unityVersion |
| 5 | P1 | Batch Command Endpoint | **已实现** — `/batch` endpoint with stopOnError |
| 6 | P1 | CommandArgumentBinder List\<T\> 支持 | **已实现** |
| 7 | P1 | 超时可配置化 (ConsoleServiceConfig) | **已实现** — MainThreadTimeoutMs, HttpClientTimeoutMs |
| 8 | P1 | Session 过期清理 (EvictIdleSessions) | **已实现** — 在 health 请求时自动清理 |
| 9 | P2 | Refresh 整合 PlayMode | **已实现** — exitPlayModeIfNeeded 参数 |
| 10 | P2 | transport_http.py 合并重复 | **已实现** — 统一 _post() 内部函数 |
| 11 | P2 | client_base.py 超时常量化 | **已实现** — 命名常量 + 注释 |
| 12 | P2 | response_parser.py 用 type 字段 | **已实现** — TYPE_* 常量, classify_response_text 降级为 legacy fallback |
| 13 | P2 | package.json 元数据补充 | **已实现** |

CLI 对接侧 (unity-cli-plugin) 已完成相应适配：batch 子命令、--timeout 参数、status 版本显示、refresh --exit-playmode、连接重试。
