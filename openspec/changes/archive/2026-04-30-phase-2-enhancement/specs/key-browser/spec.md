## MODIFIED Requirements

### Requirement: Key list rendering
The system SHALL render the key list using virtual scrolling, only materializing DOM elements for visible items plus an overscan buffer of 5 items above and below the viewport.

#### Scenario: Render large key set
- **WHEN** the key store contains 100,000+ keys
- **THEN** KeyPanel renders only visible rows (viewport height / 32px row height + 10 overscan items) in the DOM

#### Scenario: Smooth scrolling
- **WHEN** user scrolls through the key list
- **THEN** scrolling maintains 60fps with no visible blank gaps lasting more than one frame

### Requirement: Infinite scroll loading
The system SHALL automatically trigger additional SCAN batches when the user scrolls near the end of currently loaded keys.

#### Scenario: Trigger next SCAN
- **WHEN** user scrolls to within 20 items of the last loaded key AND the SCAN cursor is not 0
- **THEN** system automatically invokes the next SCAN batch and appends results without scroll position jump

#### Scenario: All keys loaded
- **WHEN** user scrolls to the bottom and SCAN cursor is 0
- **THEN** no additional loading is triggered and a subtle "All keys loaded" indicator is shown
