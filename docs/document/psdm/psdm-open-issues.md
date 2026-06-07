# PSDM Open Issues Document

## Overview
This document tracks all open issues, bugs, and enhancement requests for the PSDM (Presentation Structured Document Model) implementation. Issues are prioritized by impact and urgency.

## Issue Tracking Format
- **ID**: Unique identifier (PSDM-XXX)
- **Title**: Brief descriptive title
- **Description**: Detailed explanation of the issue
- **Priority**: Critical/High/Medium/Low
- **Status**: Open/In Progress/Resolved/Closed
- **Affected Component**: Model/Parser/Writer/Documentation
- **Standard Reference**: Related ISO/IEC 29500 section (if applicable)
- **Estimated Effort**: Time estimate to resolve
- **Dependencies**: Other issues that must be resolved first
- **Suggested Approach**: Recommended solution

## Critical Issues (P0 - Must Fix for Release)

### PSDM-001: Missing Handout Master and Notes Master
- **Description**: The PSDM model lacks handout master and notes master definitions which are required for complete PPTX round-trip fidelity according to ISO/IEC 29500-1.
- **Priority**: Critical
- **Status**: Open
- **Affected Component**: PSDM Model
- **Standard Reference**: ISO/IEC 29500-1:2016, Sections 11.3.4 (Notes Master) and 11.3.6 (Handout Master)
- **Estimated Effort**: 8 hours
- **Dependencies**: None
- **Suggested Approach**: 
  1. Add `handout_master: HandoutMaster | None = None` field to PSDMDocument class
  2. Add `notes_master: NotesMaster | None = None` field to PSDMDocument class
  3. Create HandoutMaster and NotesMaster classes similar to SlideMaster
  4. Update parser to handle handout/master and notes/master parts
  5. Update writer to output handout/master and notes/master when present

### PSDM-002: Missing Print Settings
- **Description**: Presentation print settings (paper size, orientation, scale, print quality, etc.) are not modeled in PresentationProperties.
- **Priority**: Critical
- **Status**: Open
- **Affected Component**: PresentationProperties
- **Standard Reference**: ISO/IEC 29500-1:2016, Section 11.3.8.35 (Presentation Properties)
- **Estimated Effort**: 6 hours
- **Dependencies**: None
- **Suggested Approach**:
  1. Add print settings fields to PresentationProperties class:
     - paper_size: str | None = None
     - paper_width: float | None = None
     - paper_height: float | None = None
     - scale: int | None = None (percentage)
     - use_first_slide_number: bool | None = None
     - first_slide_number: int | None = None
     - orientation: str | None = None ('portrait' or 'landscape')
     - and other relevant print settings per ISO/IEC 29500-1
  2. Update parser to read print settings from presentation.xml
  3. Update writer to output print settings to presentation.xml

### PSDM-003: Missing Custom Shows Support
- **Description**: Custom shows (user-defined slide sequences for custom presentations) are not supported.
- **Priority**: High
- **Status**: Open
- **Affected Component**: PSDMDocument
- **Standard Reference**: ISO/IEC 29500-1:2016, Section 11.3.8.16 (Custom Show List)
- **Estimated Effort**: 10 hours
- **Dependencies**: None
- **Suggested Approach**:
  1. Create CustomShow and CustomShowCollection classes
  2. Add `custom_shows: CustomShowCollection = field(default_factory=CustomShowCollection)` to PSDMDocument
  3. Update parser to read custom show list from presentation.xml
  4. Update writer to output custom show list to presentation.xml

### PSDM-004: Missing Slide Synchronization
- **Description**: Slide synchronization capabilities (for controlling multiple presentations) are not modeled.
- **Priority**: High
- **Status**: Open
- **Affected Component**: PSDMDocument
- **Standard Reference**: ISO/IEC 29500-1:2016, Section 11.3.8.40 (Slide Synchronization)
- **Estimated Effort**: 8 hours
- **Dependencies**: None
- **Suggested Approach**:
  1. Add slide synchronization fields to PresentationProperties:
     - sync_id: str | None = None
     - scroll_outside: bool | None = None
     - zoom_outside: bool | None = None
  2. Update parser to read slide synchronization settings
  3. Update writer to output slide synchronization settings

### PSDM-005: Limited Header/Footer Control
- **Description**: While headers/footers are supported via placeholder shapes, explicit control flags for showing/hiding default header/footer elements from slide master are not modeled.
- **Priority**: Medium
- **Status**: Open
- **Affected Component**: Slide class
- **Standard Reference**: ISO/IEC 29500-1:2016, Section 11.3.8.25 (Show Properties)
- **Estimated Effort**: 4 hours
- **Dependencies**: None
- **Suggested Approach**:
  1. Add boolean flags to Slide class:
     - show_header: bool | None = None
     - show_footer: bool | None = None
     - show_date: bool | None = None
     - show_slide_number: bool | None = None
  2. Update parser to read these properties from slide.xml show properties
  3. Update writer to output these properties to slide.xml

### PSDM-006: Incomplete Comment Metadata Handling
- **Description**: While SlideComment model exists, parsing/writing may not fully capture all comment metadata fields like author initials, comment timestamp precision, etc.
- **Priority**: Medium
- **Status**: Open
- **Affected Component**: SlideComment model, parsers, writers
- **Standard Reference**: ISO/IEC 29500-1:2016, Section 11.3.8.12 (Comments)
- **Estimated Effort**: 6 hours
- **Dependencies**: None
- **Suggested Approach**:
  1. Review SlideComment model against ISO/IEC 29500-1 comment specification
  2. Add missing fields if needed (author initials, etc.)
  3. Verify parser captures all comment attributes
  4. Verify writer outputs all comment attributes
  4. Add comprehensive comment tests

## High Priority Issues (P1 - Should Fix Soon)

### PSDM-007: Missing Slide Layout Following Master
- **Description**: No explicit tracking of whether a slide strictly follows its layout or has overrides.
- **Priority**: Medium
- **Status**: Open
- **Affected Component**: Slide class
- **Estimated Effort**: 2 hours
- **Suggested Approach**: Add `follow_layout: bool = True` field to Slide class if needed for tracking overrides.

### PSDM-008: Limited Shape Geometry Validation
- **Description**: Shape content lacks validation for geometric constraints (negative dimensions, etc.).
- **Priority**: Low
- **Status**: Open
- **Affected Component**: ShapeContent model
- **Estimated Effort**: 3 hours
- **Suggested Approach**: Add validators to ShapeContent fields to ensure geometric validity.

## Resolved Issues

### PSDM-001: Initial Model Missing Placeholder Support - RESOLVED
- **Description**: Initial PSDM model lacked proper placeholder shape support.
- **Resolution**: Added placeholder metadata to ShapeContent model and updated parser/writer to handle placeholders correctly.
- **Date Resolved**: 2026-06-01

## Closed Issues (Won't Fix)

### PSDM-002: VBA Macro Support - CLOSED (Won't Fix)
- **Description**: Request to support VBA macros in presentations.
- **Resolution**: VBA macro support is out of scope for PSDM as it represents binary content that would break document portability and security model. Users should extract macros separately if needed.
- **Date Closed**: 2026-06-01

## Metrics
- Total Issues: 8
- Critical: 2
- High: 2
- Medium: 3
- Low: 1
- Resolved: 1
- Closed: 1
- Open: 6

## How to Report New Issues
Please use the issue tracking system at: [repository-url]/issues
Include:
1. Clear title and description
2. Steps to reproduce (for bugs)
3. Expected vs actual behavior
4. Sample files if applicable
5. Priority assessment