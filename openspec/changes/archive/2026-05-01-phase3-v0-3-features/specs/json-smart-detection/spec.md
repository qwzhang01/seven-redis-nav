## Purpose
JSON smart detection automatically detects JSON content in String keys and provides CodeMirror 6-based editing with format/compress capabilities.

## ADDED Requirements

### Requirement: JSON automatic detection
The system SHALL automatically detect when a String key's value is valid JSON and switch to a CodeMirror 6 JSON editor.

#### Scenario: Auto-detect JSON value
- **WHEN** user selects a String key whose value passes JSON.parse() successfully
- **THEN** StringViewer switches from plain text mode to CodeMirror 6 JSON editor with syntax highlighting and code folding

#### Scenario: JSON value too large for auto-detection
- **WHEN** user selects a String key whose value is larger than 1MB
- **THEN** auto-detection is skipped, a manual "JSON" toggle button is displayed instead

#### Scenario: Non-JSON String value
- **WHEN** user selects a String key whose value fails JSON.parse()
- **THEN** StringViewer remains in plain text mode with a manual "JSON" toggle button (greyed out / disabled)

### Requirement: CodeMirror 6 JSON editor features
The system SHALL provide a full-featured JSON editor experience using CodeMirror 6.

#### Scenario: Syntax highlighting
- **WHEN** JSON editor is active
- **THEN** JSON keys, strings, numbers, booleans, and null are color-coded

#### Scenario: Code folding
- **WHEN** user clicks the fold icon next to an opening brace/bracket
- **THEN** the corresponding block is collapsed into a single line

#### Scenario: Search within JSON
- **WHEN** user presses ⌘F or uses the search bar
- **THEN** CodeMirror 6 search panel opens, allowing keyword search with match highlighting

#### Scenario: Beautify JSON
- **WHEN** user clicks the "美化" button
- **THEN** the JSON content is reformatted with proper indentation and line breaks

#### Scenario: Minify JSON
- **WHEN** user clicks the "压缩" button
- **THEN** the JSON content is reformatted into a single line without unnecessary whitespace

### Requirement: JSON detection for Hash field values and List elements
The system SHALL extend JSON auto-detection to Hash field values and List elements when viewed individually.

#### Scenario: Hash field value is JSON
- **WHEN** user views a Hash field whose value is valid JSON
- **THEN** the field value cell switches to CodeMirror 6 JSON editor

#### Scenario: List element is JSON
- **WHEN** user views a List element whose value is valid JSON
- **THEN** the element value switches to CodeMirror 6 JSON editor
