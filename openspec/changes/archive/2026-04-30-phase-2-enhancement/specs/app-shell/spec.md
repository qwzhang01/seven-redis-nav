## MODIFIED Requirements

### Requirement: Workspace tab routing
The system SHALL route Toolbar tab clicks to their corresponding workspace components, replacing placeholder components with fully functional workspace implementations.

#### Scenario: Navigate to Monitor tab
- **WHEN** user clicks the "Monitor" tab in the Toolbar
- **THEN** the workspace area renders the MonitorWorkspace component (not a placeholder)

#### Scenario: Navigate to Slowlog tab
- **WHEN** user clicks the "Slowlog" tab in the Toolbar
- **THEN** the workspace area renders the SlowlogWorkspace component

#### Scenario: Navigate to Pub/Sub tab
- **WHEN** user clicks the "Pub/Sub" tab in the Toolbar
- **THEN** the workspace area renders the PubsubWorkspace component

#### Scenario: Navigate to Config tab
- **WHEN** user clicks the "Config" tab in the Toolbar
- **THEN** the workspace area renders the ServerConfigWorkspace component

#### Scenario: Tab switch cleanup
- **WHEN** user switches away from Monitor or Pub/Sub tab while a session is active
- **THEN** the active session (MONITOR/SUBSCRIBE) continues running in the background; switching back restores the stream view
