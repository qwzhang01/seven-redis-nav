## 1. Selection State

- [x] 1.1 Adjust key browser store selection anchor semantics so normal clicks, Command/Ctrl-clicks, and Shift-clicks maintain a valid range anchor.
- [x] 1.2 Update range selection to use the current anchor, include all visible keys between anchor and target, and gracefully reset when the anchor is missing from the filtered list.
- [x] 1.3 Ensure normal click clears bulk selection, opens key details, and does not add the clicked key to the bulk selection set.

## 2. Key Panel Presentation

- [x] 2.1 Update key list item classes so bulk mode visually marks only keys in `selectedKeys` as selected.
- [x] 2.2 Suppress or weaken the current detail key active styling while bulk selections exist, without clearing the right-side detail view.
- [x] 2.3 Keep select-all behavior scoped to the focused key panel and aligned with currently loaded filtered keys.

## 3. State Cleanup

- [x] 3.1 Reconcile selection anchor after refresh or type filtering so hidden or missing anchors do not affect later Shift-clicks.
- [x] 3.2 Ensure clearing bulk selection leaves the next Shift-click anchor in a predictable state based on the current detail key when available.

## 4. Verification

- [x] 4.1 Add or update tests for normal click followed by first Shift-click selecting the correct inclusive range.
- [x] 4.2 Add or update tests proving normal click does not show bulk selection count or action bar.
- [x] 4.3 Add or update tests proving bulk mode does not show the current detail key as an extra selected item.
