## ADDED Requirements

### Requirement: Sentinel mode connection
The system SHALL support connecting to Redis via Sentinel mode, discovering the current master node automatically.

#### Scenario: Configure Sentinel connection
- **WHEN** user selects "Sentinel" as the connection mode in the connection form
- **THEN** the form shows fields for: sentinel node addresses (host:port list, at least one required), master name, and optional auth password for both sentinel and Redis

#### Scenario: Connect via Sentinel
- **WHEN** user opens a Sentinel-mode connection
- **THEN** system queries the configured sentinel nodes to discover the current master, then establishes a connection to the master

#### Scenario: Sentinel connection test
- **WHEN** user clicks "Test Connection" for a Sentinel-mode config
- **THEN** system contacts the sentinel nodes, resolves the master address, sends PING, and reports success with the resolved master host:port

#### Scenario: Sentinel master failover handling
- **WHEN** a Sentinel failover occurs while the connection is active
- **THEN** redis-rs sentinel client automatically reconnects to the new master; the frontend receives a `connection:state` event with state "reconnecting" then "connected"

### Requirement: Cluster mode connection
The system SHALL support connecting to Redis Cluster, routing commands to the correct node automatically.

#### Scenario: Configure Cluster connection
- **WHEN** user selects "Cluster" as the connection mode in the connection form
- **THEN** the form shows fields for: cluster node addresses (host:port list, at least one required as seed node), and optional auth password

#### Scenario: Connect to Cluster
- **WHEN** user opens a Cluster-mode connection
- **THEN** system uses the seed nodes to discover the full cluster topology and establishes a cluster-async client

#### Scenario: Cluster connection test
- **WHEN** user clicks "Test Connection" for a Cluster-mode config
- **THEN** system connects to seed nodes, discovers cluster info, sends PING to each shard master, and reports success with the number of master nodes found

#### Scenario: Cluster mode limitation notice
- **WHEN** user is connected in Cluster mode and opens the key browser
- **THEN** system displays an informational banner: "Cluster mode: key browser shows data from the current node only. Cross-node SCAN will be available in a future version."

## MODIFIED Requirements

### Requirement: 高级连接参数配置
系统必须提供扩展的连接配置界面，支持 Standalone、SSH、TLS、Sentinel 和 Cluster 五种连接模式的参数设置。

#### Scenario: 连接类型选择
- **WHEN** 用户创建新连接
- **THEN** 系统提供连接模式选择（Standalone / SSH 隧道 / TLS / Sentinel / Cluster）并动态显示对应配置表单

#### Scenario: SSH配置分组显示
- **WHEN** 用户选择SSH连接类型
- **THEN** 系统显示SSH隧道配置分组，包括认证方式、端口转发等参数

#### Scenario: TLS配置分组显示
- **WHEN** 用户选择TLS连接类型
- **THEN** 系统显示TLS加密配置分组，包括证书、协议版本等参数

#### Scenario: Sentinel配置分组显示
- **WHEN** 用户选择Sentinel连接模式
- **THEN** 系统显示Sentinel配置分组，包括Sentinel节点列表（host:port，至少一个）和master name必填字段

#### Scenario: Cluster配置分组显示
- **WHEN** 用户选择Cluster连接模式
- **THEN** 系统显示Cluster配置分组，包括Cluster种子节点列表（host:port，至少一个）
