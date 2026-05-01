## ADDED Requirements

### Requirement: Lua 脚本编辑器工作区
系统 SHALL 在 Toolbar 新增第 7 个 Tab "Lua"（图标 `ri-code-s-slash-line`），点击后渲染 `LuaWorkspace.vue`，包含：左侧脚本列表面板（200px）+ 右侧编辑器主区。

#### Scenario: 打开 Lua Tab
- **WHEN** 用户点击 Toolbar 的 "Lua" Tab 按钮
- **THEN** 工作区切换到 LuaWorkspace，左侧显示脚本历史列表，右侧显示 CodeMirror 6 编辑器（Lua 语法高亮），底部显示 KEYS/ARGV 参数表单和执行按钮

### Requirement: Lua 脚本编辑
系统 SHALL 提供基于 CodeMirror 6 + `@codemirror/lang-lua` 的代码编辑器，支持语法高亮、括号匹配、行号显示、自动缩进。

#### Scenario: 编辑 Lua 脚本
- **WHEN** 用户在编辑器中输入 Lua 代码
- **THEN** 编辑器实时显示 Lua 语法高亮，括号自动匹配，Tab 键插入 2 个空格

#### Scenario: 脚本模板
- **WHEN** 用户点击"新建脚本"按钮
- **THEN** 编辑器填入默认模板：`local key = KEYS[1]\nlocal val = redis.call('GET', key)\nreturn val`

### Requirement: KEYS 和 ARGV 参数表单
系统 SHALL 在编辑器下方提供 KEYS 和 ARGV 参数输入表单，支持动态增减参数行。

#### Scenario: 添加 KEYS 参数
- **WHEN** 用户点击 KEYS 区域的 "+" 按钮
- **THEN** 新增一行 KEYS 输入框，占位符为 `KEYS[N]`，N 为当前行号

#### Scenario: 添加 ARGV 参数
- **WHEN** 用户点击 ARGV 区域的 "+" 按钮
- **THEN** 新增一行 ARGV 输入框，占位符为 `ARGV[N]`，N 为当前行号

### Requirement: EVAL 执行
系统 SHALL 通过 `lua_eval` IPC 命令执行当前编辑器中的 Lua 脚本，传入 KEYS 和 ARGV 参数，在结果面板显示执行结果。

#### Scenario: 执行成功
- **WHEN** 用户点击"执行"按钮（或按 ⌘+Enter）
- **THEN** 后端执行 `EVAL script numkeys key1 key2 ... arg1 arg2 ...`，结果面板显示返回值（按 RESP 类型着色：整数橙色、字符串绿色、数组缩进展示、错误红色）

#### Scenario: 执行失败
- **WHEN** Lua 脚本执行出错（语法错误或 Redis 错误）
- **THEN** 结果面板显示红色错误信息，包含错误类型和行号（如有）

#### Scenario: 空脚本执行
- **WHEN** 编辑器内容为空时用户点击"执行"
- **THEN** 执行按钮处于禁用状态，不触发 IPC 调用

### Requirement: EVALSHA 执行
系统 SHALL 支持通过 `lua_evalsha` IPC 命令执行已加载到 Redis 的脚本（通过 SHA1 哈希）。

#### Scenario: 加载脚本并获取 SHA
- **WHEN** 用户点击"加载脚本（SCRIPT LOAD）"按钮
- **THEN** 后端执行 `SCRIPT LOAD script`，返回 SHA1 哈希，显示在编辑器顶部信息栏

#### Scenario: 通过 SHA 执行
- **WHEN** 用户切换到"EVALSHA 模式"并点击执行
- **THEN** 后端执行 `EVALSHA sha1 numkeys ...`，结果显示在结果面板

### Requirement: 脚本历史管理
系统 SHALL 将执行过的脚本保存到 SQLite `lua_scripts` 表，在左侧列表展示，支持命名、删除、重新加载。

#### Scenario: 自动保存脚本
- **WHEN** 用户成功执行一个脚本
- **THEN** 脚本内容自动保存到历史，列表顶部新增一条记录，显示时间戳和脚本前 50 个字符

#### Scenario: 命名脚本
- **WHEN** 用户双击历史列表中的脚本名称
- **THEN** 名称变为可编辑输入框，回车确认保存新名称到 SQLite

#### Scenario: 加载历史脚本
- **WHEN** 用户点击历史列表中的某条脚本
- **THEN** 编辑器内容替换为该脚本内容，KEYS/ARGV 表单清空

#### Scenario: 删除历史脚本
- **WHEN** 用户点击历史列表中某条脚本的删除按钮
- **THEN** 弹出确认对话框，确认后从 SQLite 删除该记录，列表更新
