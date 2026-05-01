# 变更日志

本项目的所有重要变更都会记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)，
版本号遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

---

## [0.1.0] - 2026-04-22

### 新增

- 🔌 **多连接管理** — 保存、切换多个 Redis 连接，密码通过系统 Keychain 安全存储
- 🗂️ **Key 浏览器** — 支持 String / Hash / List / Set / ZSet 类型的查看与编辑
- 🔍 **搜索过滤** — Key 模糊搜索与模式匹配
- 💻 **CLI 终端** — 内置 Redis 命令行终端，支持历史记录与自动补全
- ⚙️ **TTL 管理** — 查看 / 设置 / 移除过期时间
- 📊 **实时监控** — MONITOR 命令实时流式展示服务器命令流
- 📡 **Pub/Sub** — 可视化订阅频道，实时接收消息
- 🐢 **慢日志** — 查看 SLOWLOG，快速定位慢查询
- ⚙️ **服务器配置** — 在线查看与修改 Redis CONFIG

## [0.2.0] - 2026-04-29

### 新增

- 🔐 **SSH 隧道** — 通过跳板机 SSH 隧道安全连接内网 Redis，支持密码和私钥认证
- 🔒 **TLS 加密** — 支持 TLS/SSL 加密连接，可配置 CA 证书、客户端证书和最低 TLS 版本
- 📤 **配置导入导出** — 支持连接配置的 JSON 导入导出，方便团队共享

---

[0.2.0]: https://github.com/qwzhang01/seven-redis-nav/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/qwzhang01/seven-redis-nav/releases/tag/v0.1.0
