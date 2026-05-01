# binary-data-views Specification

## Purpose
TBD - created by archiving change phase3-v0-3-features. Update Purpose after archive.
## Requirements
### Requirement: Hex view for binary data
The system SHALL display binary content as a hex dump when the data is detected as binary.

#### Scenario: Switch to Hex view
- **WHEN** user selects a key whose value is detected as binary and clicks the "Hex" tab
- **THEN** the value is displayed as a hex dump with offset, hex bytes, and ASCII representation (16 bytes per line)

### Requirement: Base64 view for binary data
The system SHALL display binary content as Base64-encoded text when the data is detected as binary.

#### Scenario: Switch to Base64 view
- **WHEN** user clicks the "Base64" tab
- **THEN** the value is displayed as a Base64-encoded string

### Requirement: Text view for binary data
The system SHALL display binary content as UTF-8 text with replacement characters for non-printable bytes.

#### Scenario: Switch to Text view
- **WHEN** user clicks the "文本" tab
- **THEN** the value is displayed as UTF-8 text, with non-printable characters shown as replacement character (�)

### Requirement: Binary content auto-detection
The system SHALL automatically detect binary content and activate the three-view toggle.

#### Scenario: Detect binary via unprintable character ratio
- **WHEN** more than 30% of characters in the value are outside the ASCII 32-126 range
- **THEN** the content is classified as binary and the three-view toggle (Hex/Base64/文本) is activated

#### Scenario: Detect binary via null byte
- **WHEN** the value contains any null byte (0x00)
- **THEN** the content is immediately classified as binary regardless of the unprintable character ratio

#### Scenario: Non-binary content
- **WHEN** the value contains less than 30% unprintable characters and no null bytes
- **THEN** the content is classified as text and displayed in plain text mode (three-view toggle is not shown)

### Requirement: Binary view for Hash fields and List elements
The system SHALL extend binary detection and three-view toggle to Hash field values and individual List elements.

#### Scenario: Hash field value is binary
- **WHEN** a Hash field value is detected as binary
- **THEN** the field value cell shows the three-view toggle (Hex/Base64/文本)

#### Scenario: List element is binary
- **WHEN** a List element value is detected as binary
- **THEN** the element value cell shows the three-view toggle (Hex/Base64/文本)

