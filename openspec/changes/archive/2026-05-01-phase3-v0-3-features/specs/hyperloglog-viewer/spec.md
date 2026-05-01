## Purpose
HyperLogLog viewer provides visualization and operations for Redis HyperLogLog keys, including cardinality display, PFADD, and PFMERGE.

## ADDED Requirements

### Requirement: HyperLogLog cardinality display
The system SHALL display the estimated cardinality (count of unique elements) of a HyperLogLog key.

#### Scenario: View HyperLogLog key
- **WHEN** user selects a HyperLogLog key in the Browser workspace
- **THEN** HyperLogLogViewer renders showing the estimated cardinality via `pfcount` IPC, displayed prominently as a large number with "≈" prefix

#### Scenario: Cardinality with low precision indicator
- **WHEN** the HLL is created with sparse encoding and has few registers set
- **THEN** display shows a warning badge "低精度" indicating the estimate may have higher relative error

### Requirement: HyperLogLog PFADD operation
The system SHALL allow users to add elements to a HyperLogLog key.

#### Scenario: Add elements via PFADD
- **WHEN** user clicks "添加元素" button
- **THEN** system shows a text area where user enters elements (one per line), clicks "提交", system calls `pfadd` IPC with the key and element list

### Requirement: HyperLogLog PFMERGE operation
The system SHALL allow users to merge multiple HyperLogLog keys into one.

#### Scenario: Merge HLL keys
- **WHEN** user clicks "合并" button
- **THEN** system shows a key selector (multi-select from keys of type String with HyperLogLog encoding), user selects source keys and target key, clicks "合并", system calls `pfmerge` IPC

### Requirement: HyperLogLog key detail metadata
The system SHALL display HyperLogLog-specific metadata in the key detail header.

#### Scenario: HyperLogLog metadata display
- **WHEN** a HyperLogLog key is selected
- **THEN** metadata bar shows: 类型: HyperLogLog, 编码: dense/sparse, 基数估算: ≈N, 寄存器数: 16384 (dense) / variable (sparse)
