## Purpose
Pub/Sub export allows users to export received messages to a local file in JSON or NDJSON format.

## ADDED Requirements

### Requirement: Export messages to local file
The system SHALL allow users to export received Pub/Sub messages to a local file in JSON or NDJSON format.

#### Scenario: Open export dialog
- **WHEN** user clicks the "💾 导出" button in the message stream controls
- **THEN** an export dialog appears with format selection (JSON array / NDJSON) and scope selection (all messages / filtered messages / selected channel)

#### Scenario: Export as JSON array
- **WHEN** user selects "JSON 数组" format and clicks "导出"
- **THEN** system writes a JSON file containing an array of message objects with fields { timestamp, channel, pattern, message }

#### Scenario: Export as NDJSON
- **WHEN** user selects "NDJSON" format and clicks "导出"
- **THEN** system writes a file with one JSON object per line, each containing { timestamp, channel, pattern, message }

#### Scenario: Export filtered messages only
- **WHEN** a keyword filter is active and user selects "仅筛选结果" scope
- **THEN** only messages matching the current filter are included in the export

#### Scenario: Export single channel messages
- **WHEN** user selects a specific channel from the scope dropdown
- **THEN** only messages from that channel are included in the export

#### Scenario: Export empty result
- **WHEN** no messages match the export scope
- **THEN** system shows a warning "没有可导出的消息" and disables the export button
