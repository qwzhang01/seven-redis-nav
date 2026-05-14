## MODIFIED Requirements

### Requirement: Multi-select keys in key panel
The system SHALL support multi-select of keys in the key panel via keyboard modifiers and select-all shortcut, while keeping the current detail key separate from the bulk-operation selection set.

#### Scenario: Command-click to toggle selection
- **WHEN** user holds ⌘ or Ctrl and clicks a key item
- **THEN** that key is added to the bulk selection set without deselecting others; clicking again removes it from the bulk selection set

#### Scenario: Shift-click range selection after a normal click
- **WHEN** user first clicks key A without modifier keys and then holds Shift and clicks key C
- **THEN** all currently visible keys between key A and key C, inclusive, are added to the bulk selection set

#### Scenario: Shift-click range selection after another bulk selection action
- **WHEN** user holds Shift and clicks a key item after a previous Command-click, Ctrl-click, or Shift-click established a range anchor
- **THEN** all currently visible keys between the anchor key and the clicked key are added to the bulk selection set

#### Scenario: Shift-click with unavailable range anchor
- **WHEN** user holds Shift and clicks a key item but the range anchor is missing or no longer exists in the current filtered key list
- **THEN** only the clicked key is added to the bulk selection set and it becomes the next range anchor

#### Scenario: Select all with ⌘A
- **WHEN** user presses ⌘A or Ctrl+A while the key panel is focused
- **THEN** all currently loaded and filtered keys are added to the bulk selection set

#### Scenario: Normal click opens details without entering bulk selection
- **WHEN** user clicks a key item without any modifier key
- **THEN** all previous bulk selections are cleared, the clicked key detail is shown in the workspace, and the clicked key is not counted as a bulk-selected key

#### Scenario: Bulk mode displays only bulk-selected keys as selected
- **WHEN** one or more keys are in the bulk selection set
- **THEN** the key list visually marks only keys in the bulk selection set as selected and does not show the current detail key as an additional selected item

#### Scenario: Selection count badge
- **WHEN** one or more keys are in the bulk selection set
- **THEN** a bulk action bar appears at the bottom of the key panel showing the count of bulk-selected keys and available actions
