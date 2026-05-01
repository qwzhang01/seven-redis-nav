## ADDED Requirements

### Requirement: Virtual scroll for key list
The system SHALL render the key list in KeyPanel using virtual scrolling, only rendering visible items plus a small overscan buffer.

#### Scenario: Large key set rendering
- **WHEN** KeyPanel contains 100,000+ keys loaded via SCAN
- **THEN** only the visible rows (viewport height / row height + overscan) are rendered in the DOM, maintaining smooth 60fps scrolling

#### Scenario: Scroll performance
- **WHEN** user rapidly scrolls through the key list
- **THEN** frame rate remains above 30fps and no visible blank gaps appear for more than one frame

### Requirement: Dynamic row height support
The system SHALL support variable row heights in the virtual scroll list to accommodate different key name lengths.

#### Scenario: Long key names
- **WHEN** a key name exceeds the panel width
- **THEN** the row height adjusts to accommodate the wrapped text, and virtual scroll calculations account for the variable height

### Requirement: Maintain selection state during scroll
The system SHALL preserve the selected key highlight when scrolling causes the selected item to be virtualized (removed from DOM) and then re-rendered.

#### Scenario: Scroll away and back
- **WHEN** user selects a key, scrolls far away, then scrolls back
- **THEN** the previously selected key retains its selected visual state

### Requirement: Scroll to specific key
The system SHALL support programmatic scrolling to a specific key by index or name.

#### Scenario: Scroll to key after search
- **WHEN** user searches for a key and selects a result
- **THEN** the virtual scroll list scrolls to position that key in the visible viewport

### Requirement: Incremental loading integration
The system SHALL integrate with the existing SCAN cursor-based loading, triggering additional SCAN when the user scrolls near the bottom of loaded keys.

#### Scenario: Load more on scroll
- **WHEN** user scrolls to within 20 items of the last loaded key and more keys are available (cursor != 0)
- **THEN** system automatically triggers the next SCAN batch and appends results to the list without scroll position jump
