## Purpose
Data viewer extends type-dispatched rendering for Stream, Bitmap, and HyperLogLog keys, adds JSON auto-detection with CodeMirror 6, and binary three-view toggle.

## MODIFIED Requirements

### Requirement: Extended type dispatch for Stream, Bitmap, HyperLogLog
The system SHALL render type-specific viewers for Stream, Bitmap, and HyperLogLog keys in addition to the existing String/Hash/List/Set/ZSet types.

#### Scenario: View a Stream key
- **WHEN** user selects a key with type Stream
- **THEN** Browser workspace renders StreamViewer showing paginated entries, Consumer Groups tab, and entry operations

#### Scenario: View a Bitmap key (String type with binary flag)
- **WHEN** user selects a String key that has been identified as a Bitmap (via key naming convention or manual toggle)
- **THEN** Browser workspace renders BitmapViewer showing bit grid visualization and quick operation buttons

#### Scenario: View a HyperLogLog key (String type with HLL flag)
- **WHEN** user selects a String key that has been identified as a HyperLogLog (detected via encoding check or manual toggle)
- **THEN** Browser workspace renders HyperLogLogViewer showing cardinality estimate and PFADD/PFMERGE operations

### Requirement: JSON auto-detection in String viewer
The system SHALL automatically detect when a String key's value is valid JSON and switch the display to a CodeMirror 6 JSON editor.

#### Scenario: Auto-detect JSON value
- **WHEN** user selects a String key whose value passes JSON.parse() successfully and is ≤ 1MB
- **THEN** StringViewer switches from plain text mode to CodeMirror 6 JSON editor with syntax highlighting and code folding

#### Scenario: JSON value too large for auto-detection
- **WHEN** user selects a String key whose value is larger than 1MB
- **THEN** auto-detection is skipped, a manual "JSON" toggle button is displayed instead

#### Scenario: Non-JSON String value
- **WHEN** user selects a String key whose value fails JSON.parse()
- **THEN** StringViewer remains in plain text mode with a manual "JSON" toggle button (greyed out / disabled)

### Requirement: Binary three-view toggle in data viewer
The system SHALL provide a Hex / Base64 / 文本 three-view toggle for binary content detected in String values, Hash field values, and List elements.

#### Scenario: Binary content detected
- **WHEN** data is detected as binary (> 30% unprintable characters or contains null bytes)
- **THEN** the three-view toggle (Hex / Base64 / 文本) is activated above the value display area

#### Scenario: Non-binary content
- **WHEN** data is classified as text
- **THEN** the three-view toggle is not shown and content displays in plain text mode
