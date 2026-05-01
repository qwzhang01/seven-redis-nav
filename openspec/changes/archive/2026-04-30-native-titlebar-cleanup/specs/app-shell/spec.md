## REMOVED Requirements

### Requirement: Titlebar component
**Reason**: Vue Titlebar 组件与原生 macOS 标题栏功能重叠，浪费垂直空间。改用原生标题栏 + `setTitle()` 动态更新。
**Migration**: 应用名和连接名通过 `window.setTitle()` 显示在原生标题栏；刷新/分享按钮迁移到 Toolbar 组件。

## MODIFIED Requirements

### Requirement: Toolbar visibility based on connection state
The Toolbar component SHALL only be rendered when the user has an active connection. The WelcomePage (login page) SHALL NOT display the Toolbar.

#### Scenario: Toolbar hidden on welcome page
- **WHEN** the application is on the WelcomePage (not connected)
- **THEN** the Toolbar component SHALL NOT be rendered

#### Scenario: Toolbar visible after connection
- **WHEN** the user successfully connects to a Redis instance
- **THEN** the Toolbar component SHALL be rendered with all tabs and controls

### Requirement: Toolbar action buttons
The Toolbar component SHALL include refresh and share action buttons in its right section, migrated from the removed Titlebar component.

#### Scenario: Refresh button in toolbar
- **WHEN** the user is connected and views the Toolbar
- **THEN** a refresh button SHALL be visible in the Toolbar's right section

#### Scenario: Share button in toolbar
- **WHEN** the user is connected and views the Toolbar
- **THEN** a share button SHALL be visible in the Toolbar's right section
