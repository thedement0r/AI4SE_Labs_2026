# PINES Management Processes — Consolidated Reporting & Management Requirements (Rev. Reviewed)

**Status:** DRAFT — NEEDS HUMAN REVIEW
**Stop reason:** max_rounds_reached
**Review rounds:** 3

## Scope

Requirements for the Management Processes (reporting and administrative management tools) of the PINES Evergreen-based Integrated Library System. Covers operating environment, design/implementation constraints, user documentation, user management, reporting and query capabilities, inventory and patron reporting, financial reporting and audit, data retention, and related administrative utilities. UI and detailed data models will be specified later via iterative design and prototyping; this document focuses on functional and constraint-level requirements drawn from the supplied sources.

## Priority scale

High: explicitly mandatory, critical, or high-priority in the sources. Medium: requested functionality without an explicit priority (inferred default). Low: explicitly optional or nice-to-have. Each requirement states its rationale; inferred priorities require stakeholder confirmation.

## Requirements

### REQ-001 — Support Consortium Scale; non-disruptive reporting is a strong operational objective

The Management Processes shall support operation at consortium scale as documented in the sources (example reference numbers: 286 library locations; ~17 million annual circulations; purchasing/processing ~900,000 items per year). Separately, stakeholders strongly desire that searches and reports be executed without disrupting patron-facing services during open hours (for example by using background processing, queuing, or reporting replicas). The scale support is mandatory; the non-disruption outcome is a required operational objective to be achieved by appropriate architecture (decision open — see open questions).

**Priority:** High. Consortium-scale support is explicitly required in the early draft and meeting notes; protecting OPAC/production from reporting disruption is repeatedly identified as an essential operational objective by sysadmins and the working group (needs architecture decision).
**Sources:** early_draft_srs_galecia.txt, interview_sysadmin_2009-05-10.txt, meeting_minutes/meeting_2009-07-20_minutes.txt, evergreen_reference_2009.txt
**Candidate IDs:** CAND-0001, CAND-0118, CAND-0119, CAND-0120, CAND-0264, CAND-0086

### REQ-002 — Server Platform Compatibility

The Management Processes shall be deployable on the server platforms used by PINES production and DR sites: Linux and Solaris. Implementations shall be validated on both environments and deployment documentation shall identify any platform-specific differences in configuration or operation.

**Priority:** High. Early draft marks Linux/Solaris support as High and sysadmin/meeting records confirm both platforms are used in PINES environments.
**Sources:** early_draft_srs_galecia.txt, interview_sysadmin_2009-05-10.txt, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0002, CAND-0117, CAND-0265

### REQ-003 — Client Access Options; conditional browser support

The system shall be accessible via either a web browser or a Windows-compatible client to support PINES local environments. If deployed as a web-browser-based system, it shall support Microsoft Internet Explorer (6.0 and later) and Mozilla Firefox (2.0 and later) to match PINES installed browser baselines; the browser compatibility obligation is conditional on choosing web deployment and is recorded as a Medium-priority compatibility constraint in the sources. Implementers should explicitly confirm target browser support for each deployment. (Note: implementation documentation is expected as usual for deployments, but the supplied sources require only platform/browser compatibility as a functional constraint.)

**Priority:** High. General client-access is treated as a High-priority operational requirement in the sources; the specific browser list (IE6+/Firefox2+) is an explicit conditional compatibility constraint (Medium in the original draft) and is documented in the description for clarity and stakeholder confirmation.
**Sources:** early_draft_srs_galecia.txt, interview_sysadmin_2009-05-10.txt, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0003, CAND-0004, CAND-0121, CAND-0266, CAND-0267

### REQ-004 — Accessibility and Standards-Compliant HTML

The Management Processes shall comply with applicable accessibility obligations identified in the sources (Section 508 is explicitly referenced). The system shall interoperate with common assistive technologies (screen readers such as JAWS/NVDA, screen magnifiers such as ZoomText, and other assistive software). Web-based UI and report HTML output shall be standards-compliant (W3C) and include semantic structure and attributes needed by assistive technologies (alt text, appropriate ARIA roles, headings, and labels).

**Priority:** High. Accessibility is described as non-negotiable in technical interviews and is explicitly marked High in the early draft (OE-5); standards-compliant HTML is tied to the accessibility and cross-browser compatibility goals.
**Sources:** early_draft_srs_galecia.txt, interview_sysadmin_2009-05-10.txt, meeting_tech_subcommittee_2009-06-30.txt, meeting_minutes/meeting_2009-07-20_minutes.txt, evergreen_reference_2009.txt
**Candidate IDs:** CAND-0005, CAND-0122, CAND-0123, CAND-0124, CAND-0137, CAND-0268, CAND-0085

### REQ-005 — Relational Database Back-End (and working with relational model)

The system shall use a fully relational database back-end and shall be designed to work with the relational data model used by PINES (PostgreSQL is the existing PINES choice). Reporting components shall work with the relational schema and data model; while denormalization is discouraged by PINES IT (per sources) as a preference, architectures that include replicas or reporting schemas may be considered provided they meet the business needs and preserve data integrity and retention policies (see open questions for architecture tradeoffs).

**Priority:** High. The early draft marks a relational back-end as High and PINES technical staff explicitly require compatibility with PostgreSQL and the relational model.
**Sources:** early_draft_srs_galecia.txt, interview_sysadmin_2009-05-10.txt, meeting_tech_subcommittee_2009-06-30.txt, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0006, CAND-0125, CAND-0134, CAND-0135, CAND-0136, CAND-0269, CAND-0127

### REQ-007 — Development and Training Environments with Migration

Separate development, training, and production environments shall be available. The system shall provide export/import or migration mechanisms for report templates, saved queries, permission settings and other configuration so that configurations and templates developed or tested in non-production environments can be migrated to production reliably. The training environment must be isolated from production so staff can practice without risking production data (safe/test dataset or sandboxing).

**Priority:** Medium. The early draft marks this as Medium; technical staff and meeting notes request separate environments and migration capability to support safe testing and training.
**Sources:** early_draft_srs_galecia.txt, interview_sysadmin_2009-05-10.txt, meeting_tech_subcommittee_2009-06-30.txt, meeting_minutes/meeting_2009-07-20_minutes.txt, evergreen_reference_2009.txt
**Candidate IDs:** CAND-0008, CAND-0128, CAND-0129, CAND-0138, CAND-0139, CAND-0271, CAND-0087

### REQ-008 — Role-Based Access Control (security groups/roles)

User rights and privileges shall be managed through security groups and/or named roles that can be assigned to individuals or groups. The system shall permit administrators to create/manage roles and apply role assignments to change permissions for users (changing a user's role assignment shall be the primary administrative method to change an individual's effective permissions). Shared folders and folder-level access controls for reports shall be supported to simplify administrative control over which staff can view/run templates.

**Priority:** High. The early draft marks role-based access control as High Priority; multiple interviews and meeting notes confirm this as essential operational functionality.
**Sources:** early_draft_srs_galecia.txt, email_staff_login.eml, interview_sysadmin_2009-05-10.txt, meeting_tech_subcommittee_2009-06-30.txt, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0009, CAND-0075, CAND-0076, CAND-0077, CAND-0080, CAND-0126, CAND-0140, CAND-0141, CAND-0272, CAND-0127

### REQ-009 — Do not constrain or degrade OPAC functionality

Management Processes must not constrain or degrade the functionality or responsiveness of the Online Public Access Catalog (OPAC). Reporting workloads must be architected to avoid interfering with patron-facing operations (for example via background processing, replicas, or other architectural measures).

**Priority:** High. The early draft explicitly requires that management reporting not constrain OPAC; technical staff emphasize protecting the OPAC as a primary concern.
**Sources:** early_draft_srs_galecia.txt, interview_sysadmin_2009-05-10.txt, meeting_tech_subcommittee_2009-06-30.txt, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0010, CAND-0131, CAND-0142, CAND-0273

### REQ-010 — Complete Data Specifications and Dictionaries

The developer shall provide complete data specifications and data dictionaries for records accessed by Management Processes: authority records, bibliographic records, order records, item records, hold/request records, patron records, financial/debt records and related schema details (field names, data types, relationships) to support query building and accurate report definitions.

**Priority:** High. UD-1 is explicitly High in the early draft and staff need data dictionaries to create accurate queries and templates.
**Sources:** early_draft_srs_galecia.txt, meeting_tech_subcommittee_2009-06-30.txt, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0011, CAND-0143, CAND-0274

### REQ-011 — High-Level Process Descriptions (selected processes)

The developer shall provide high-level descriptions of major processes relevant to Management Processes (for example: bibliographic record import/export, validation of bibliographic records against authority sources, and definitions of standard reports). (Note: sources requested these process descriptions; inclusion of detailed acquisition flows was not established in the supplied sources and is therefore not required here unless confirmed by stakeholders.)

**Priority:** Medium. UD-2 in the early draft is Medium priority; staff asked for process documentation to support data provenance and query design.
**Sources:** early_draft_srs_galecia.txt, meeting_tech_subcommittee_2009-06-30.txt, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0012, CAND-0144, CAND-0275

### REQ-012 — Online Hierarchical Help and Actionable Error Feedback

The system shall provide an online, hierarchical, cross-linked, searchable HTML help system describing system functions and common workflows. The system shall provide meaningful high-level error messages to users and low-level, actionable, diagnostic feedback to Local and Global System Administrators to help diagnose failed reports or queries (for example: identify table/field and error type in administrator diagnostics).

**Priority:** High. Help and diagnostic feedback are explicitly requested and flagged High for the help system in the early draft; administrators require low-level diagnostic capability.
**Sources:** early_draft_srs_galecia.txt, interview_sysadmin_2009-05-10.txt, meeting_tech_subcommittee_2009-06-30.txt, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0013, CAND-0014, CAND-0132, CAND-0133, CAND-0145, CAND-0146, CAND-0276, CAND-0277

### REQ-013 — User Authentication Options (streamlined login + fallback) and auditability

The system shall support optional streamlined staff login methods (for example card-swipe/employee badge) as a convenience and shall also require/support traditional username/password authentication as a fallback. The streamlined method must not be required. The system shall always record the identity of the logged-in staff member (for auditing) and map effective permissions via assigned roles.

**Priority:** Medium. Staff across branches requested streamlined login as an operational convenience; the early draft requested this and asked that the streamlined method not be required. Auditability is a mandatory operational constraint.
**Sources:** early_draft_srs_galecia.txt, email_staff_login.eml, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0015, CAND-0074, CAND-0078, CAND-0079

### REQ-014 — Report Templates and Template Management (publish, clone, restrict)

Administrators shall be able to create, publish, and manage report templates. Templates shall be runnable as-delivered and clonable to create variants. Administrators shall be able to restrict which filters and display fields staff may alter on published templates to ensure consistent, certified outputs for key reports. Template management shall include the ability to save and share templates in folder structures with controlled access; templates shall support controlled editing for display options where administrators permit it.

**Priority:** Medium. Report templates and clone functionality are requested by many stakeholder sources and the survey shows high demand; treated as Medium pending stakeholder confirmation of detailed policy choices.
**Sources:** early_draft_srs_galecia.txt, email_report_features.eml, survey_results_2009.txt, meeting_minutes/meeting_2009-07-20_minutes.txt, evergreen_reference_2009.txt
**Candidate IDs:** CAND-0016, CAND-0063, CAND-0072, CAND-0073, CAND-0160, CAND-0062, CAND-0095

### REQ-015 — Fine-Grained Report Permissions and Shared Folders (create/clone/run control)

The system shall provide fine-grained permissions for reports, including control over who may create, clone, run, schedule, and access templates. Administrators shall be able to create shared folders and assign folder-level permissions to staff groups and roles. The emphasis in sources is on controlling creation/cloning and run access and on ease of role-based administration; additional privilege types (e.g., edit/delete) should be defined and confirmed with stakeholders prior to mandating any specific administrative model.

**Priority:** Medium. Fine-grained permission management is widely requested; original sources emphasized creation/cloning and run access specifically, so the broader edit/delete scheduling privileges are deferred pending confirmation.
**Sources:** early_draft_srs_galecia.txt, email_report_features.eml, survey_results_2009.txt, meeting_minutes/meeting_2009-07-20_minutes.txt, evergreen_reference_2009.txt
**Candidate IDs:** CAND-0017, CAND-0064, CAND-0068, CAND-0070, CAND-0161, CAND-0162, CAND-0082

### REQ-016 — User-Friendly Query Builder (field selection, Boolean, regex, saved queries)

The system shall provide a user-friendly query builder capable of constructing queries across record types (bibliographic, item, patron, transaction, money/financial). The interface shall support selecting fields, picklists for common values, Boolean logic (AND/OR), regular-expression matching, saving and reusing queries, and administrator control over which tables/fields are exposed to staff. Administrators shall be able to limit access to sensitive fields. This requirement reflects multiple stakeholder requests; inferred priority is Medium and requires stakeholder confirmation.

**Priority:** Medium. Multiple interviews, the survey, and the early draft requested a full-featured query tool; sources did not uniformly mark it High, so Medium is used as the inferred default while stakeholders confirm.
**Sources:** early_draft_srs_galecia.txt, email_report_features.eml, evergreen_reference_2009.txt, survey_results_2009.txt, meeting_minutes/meeting_2009-07-20_minutes.txt, interview_cataloging_2009-05-08.txt, conversations/conv_pines023_patron_characteristics.eml
**Candidate IDs:** CAND-0018, CAND-0062, CAND-0088, CAND-0089, CAND-0091, CAND-0108, CAND-0109, CAND-0160, CAND-0236, CAND-0090

### REQ-017 — Report Queue Visibility, Status, Prioritization and Cancellation

The system shall provide a report job queue and job status indicators that show submission time, current position in queue, and job state (waiting, running, completed, failed). Authorized users shall be able to cancel scheduled or running reports, and authorized roles shall be able to elevate the priority of critical reports to reduce wait time (policy on who may elevate priority to be confirmed). Cancellation should be implemented so running jobs can detect cancellation and terminate cleanly.

**Priority:** Medium. Queue visibility and job-state reporting are frequently requested; cancellation and priority elevation were discussed by technical staff as feasible and requested by users; priority is Medium pending SLA/policy confirmation.
**Sources:** early_draft_srs_galecia.txt, email_report_features.eml, survey_results_2009.txt, meeting_tech_subcommittee_2009-06-30.txt, evergreen_reference_2009.txt
**Candidate IDs:** CAND-0023, CAND-0068, CAND-0069, CAND-0071, CAND-0083, CAND-0149, CAND-0163

### REQ-018 — Multiple Output Formats, Scheduling and Delivery

Reports shall be exportable to multiple formats including CSV, HTML, and Excel-compatible output (for pivot-table use). The system shall support scheduling reports to run asap or recurring intervals (hourly, daily, weekly, monthly, yearly) and shall support download delivery. Email delivery is a requested capability (with address-book convenience noted in sources); the implementation and delivery options (email, push, or download) should be agreed with stakeholders and may be provided as deployment-configurable features.

**Priority:** Medium. This feature set was repeatedly requested and is identified as a capability gap in Evergreen; scheduling and delivery are important for users but the exact delivery/address-book behavior is an implementation detail requiring confirmation.
**Sources:** early_draft_srs_galecia.txt, email_report_features.eml, evergreen_reference_2009.txt, survey_results_2009.txt, meeting_tech_subcommittee_2009-06-30.txt
**Candidate IDs:** CAND-0151, CAND-0147, CAND-0093, CAND-0094, CAND-0065, CAND-0066, CAND-0167, CAND-0084

### REQ-019 — Canned, On-Demand and Open Template Reporting Interfaces

The system shall provide three reporting interface modes: (a) canned/pre-defined reports (delivered as templates and runnable or schedulable), (b) on-demand reports (preset templates editable for selection/display), and (c) open template/ad-hoc reporting that exposes attributes from circulation, items, patrons, bills, and bib records for arbitrary filtering and display. Administrators shall be able to manage which canned templates are available to which users/roles.

**Priority:** Medium. Sources (early draft Appendix B and multiple stakeholder threads) request these three interface styles; treated as Medium for confirmation of UI design and delivery details.
**Sources:** early_draft_srs_galecia.txt, email_report_features.eml, evergreen_reference_2009.txt, survey_results_2009.txt, meeting_minutes/meeting_2009-07-20_minutes.txt, meeting_tech_subcommittee_2009-06-30.txt
**Candidate IDs:** CAND-0025, CAND-0063, CAND-0151, CAND-0072, CAND-0073

### REQ-020 — Query Criteria Display and Inclusion of Nulls

Report outputs shall include the selection criteria (including date ranges and report name) used to generate them to make results self-describing. Report results shall explicitly include null and blank fields rather than silently excluding records with missing values (treatment of nulls—whether shown as 'Unknown' or null—should be documented and confirmed with users).

**Priority:** Medium. Users repeatedly requested criteria display and explicit null handling; technical notes show SQL defaults but explicit behavior is required for consistent outputs.
**Sources:** early_draft_srs_galecia.txt, email_report_features.eml, survey_results_2009.txt, meeting_tech_subcommittee_2009-06-30.txt, evergreen_reference_2009.txt
**Candidate IDs:** CAND-0022, CAND-0150, CAND-0067, CAND-0095

### REQ-021 — Reporting Output Enhancements (pivot-ready, MARC flattening, list upload)

The reporting system shall provide output and input conveniences requested by users: pivot-table-compatible Excel exports, the ability to flatten MARC bibliographic fields onto a single-row per-bib output where required, the ability to upload plain text lists (barcodes or transaction control numbers) for use as report filters, and generally 'tested and proven' business-user outputs. Specific behaviors should be validated with test cases.

**Priority:** Medium. These enhancements were requested in the fine-grained appendix and survey; treated as Medium until test cases and acceptance criteria are agreed.
**Sources:** early_draft_srs_galecia.txt, email_report_features.eml, evergreen_reference_2009.txt, survey_results_2009.txt, meeting_tech_subcommittee_2009-06-30.txt
**Candidate IDs:** CAND-0151, CAND-0153, CAND-0095, CAND-0147, CAND-0150, CAND-0151

### REQ-022 — Transaction History Retention, Archiving and Privacy

Transaction history retention policies shall be configurable: detailed transaction history retained for a configurable number of days, with monthly and annual aggregates retained indefinitely. Transaction archiving shall protect patron privacy and comply with applicable state law; archived data shall support anonymized demographic statistics. Financial and accounting retention requirements (e.g., multi-year retention for audits) shall be supported according to jurisdictional needs (open question: confirm exact retention durations).

**Priority:** High. Transaction archiving, privacy protection, and compliance are emphasized as critical by both the early draft and finance stakeholders; legal/auditing implications raise priority.
**Sources:** early_draft_srs_galecia.txt, email_financial_reports.eml, survey_results_2009.txt, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0039, CAND-0020, CAND-0061, CAND-0152, CAND-0158

### REQ-023 — Transaction Groupings and Detailed Transaction Types

Transactions shall be reportable and groupable by hour, by terminal/workstation, by branch, and by system. The system shall count and report check-in types (book-drop, by terminal, by user/self-service) and check-out types (staff checkout, self-checkout, staff renewal, self-checkout renewal, online/OPAC renewal) individually and cumulatively. Holds reporting shall include method of placement (staff desk, public computer, remote).

**Priority:** Medium. Requested in survey and early draft; important for backroom statistics and operational analysis and thus treated as Medium pending prioritization among many reporting needs.
**Sources:** early_draft_srs_galecia.txt, survey_results_2009.txt, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0040, CAND-0041, CAND-0042, CAND-0043, CAND-0153, CAND-0154, CAND-0155, CAND-0156

### REQ-024 — Transactions Report (scope: patron, library, groups, system, county)

The system shall be able to generate transaction reports (holds placed, holds filled, check-outs) scoped by patron, by library, by selected group of libraries, by system, and by county. Holds shall be subtotaled by hold type (active, frozen, frozen-until, etc.), and per-patron subtotals shall be available where requested.

**Priority:** Medium. Frequently requested capability among staff and directors; important for planning and service metrics.
**Sources:** early_draft_srs_galecia.txt, survey_results_2009.txt
**Candidate IDs:** CAND-0044, CAND-0157

### REQ-025 — Demographic and Patron Behavior Analytics (anonymized outputs)

The system shall provide demographic statistics and analytic outputs to support patron behavior analysis (examples: average return times, renewal likelihood, percent renewals) and group results by geography and configurable age ranges. Outputs used for demographics shall be anonymized to remove personally identifying information in accordance with policy and law.

**Priority:** Medium. Requested in the early draft and survey for planning; privacy considerations require anonymization and confirmation of acceptable data fields.
**Sources:** early_draft_srs_galecia.txt, survey_results_2009.txt, email_report_features.eml
**Candidate IDs:** CAND-0026, CAND-0027, CAND-0158, CAND-0159

### REQ-026 — Material Volume Reporting (point-in-time and historical)

The system shall provide a Material Volume Report that reports volume of material for a given library at a specific point in time or over a time range, based on new acquisitions, items on shelf (checked in), and items out in circulation. The report shall allow breakdowns into categories such as total items, number of holds, adult fiction, board books, and other categories; making category definitions configurable is a stakeholder preference and should be confirmed before mandating. The report shall support date-range filters and historical snapshots.

**Priority:** Medium. Requested by branch managers and catalogers and used regularly; treated as Medium pending confirmation of customization policy for categories.
**Sources:** early_draft_srs_galecia.txt, conversations/conv_pines014_material_volume.eml, survey_results_2009.txt, interview_cataloging_2009-05-08.txt
**Candidate IDs:** CAND-0028, CAND-0164, CAND-0165, CAND-0166, CAND-0167, CAND-0168, CAND-0169, CAND-0111, CAND-0266

### REQ-027 — System Capacity Interface (dashboard with drill-down and trends)

The system shall provide an interface (dashboard) showing capacity-related metrics for branches with a high-level overview of all branches and the ability to drill down into individual branches. The interface shall support sorting and filtering (region, library type, current load), provide trend views (growth/shrink patterns), and allow export to CSV. Because 286 locations can crowd a single view, the interface shall support grouping or filtering to keep the view usable (grouping/filtering approach to be decided — see open questions about exact capacity metrics and presentation). (User concern about overcrowding in a single view is preserved as an open design concern.)

**Priority:** Medium. Requested by branch managers and covered in working-group discussions; exact capacity metrics and presentation choices remain open and require stakeholder confirmation.
**Sources:** early_draft_srs_galecia.txt, conversations/conv_pines015_capacity_interface.eml, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0029, CAND-0170, CAND-0171, CAND-0172, CAND-0173, CAND-0174, CAND-0175, CAND-0176, CAND-0178, CAND-0177, CAND-0179

### REQ-028 — Shelf Space Utilization Report

For each genre and format the system shall provide a Shelf Space Report comparing: percentage of total circulations, percentage of the collection, and percentage of total shelf space. The report shall run per library and per system, support date-range filters and optional side-by-side comparison views. If shelf-space is not tracked directly in the data, the system shall provide and document an estimation approach (for example item-count proxy or use of physical measurements) and seek stakeholder confirmation of the chosen approach (estimation method is an open question).

**Priority:** Medium. Requested by cataloging and collection staff for allocation decisions; the manner of representing shelf space requires confirmation and is therefore not prescriptively mandated here.
**Sources:** early_draft_srs_galecia.txt, interview_cataloging_2009-05-08.txt, conversations/conv_pines016_shelf_space.eml
**Candidate IDs:** CAND-0030, CAND-0116, CAND-0180, CAND-0181, CAND-0182, CAND-0183, CAND-0184, CAND-0185, CAND-0186, CAND-0187

### REQ-029 — Uncataloged Material Tracking

The system shall provide facilities to track and count transactions for uncataloged material (e.g., paperback assortments, children's board books) so they can be quickly distributed, counted in circulation statistics, and managed with minimal branch labor. Support includes the ability to identify, count, and report activity on uncataloged items and to incorporate those counts into circulation statistics and reports. Design details for entry workflows shall be confirmed with cataloging staff to minimize branch labor.

**Priority:** Medium. Cataloging staff requested this functionality to support branch workflows that process uncataloged materials.
**Sources:** early_draft_srs_galecia.txt, interview_cataloging_2009-05-08.txt
**Candidate IDs:** CAND-0031, CAND-0098, CAND-0115

### REQ-030 — Item Transfer Utility (batch transfers, tracking, revert)

The system shall provide a utility to transfer batches of items between branches supporting: query-building for candidate materials; saving and reusing queries; manual selection from query results; batch update of item location (database change) with safe transactional handling and pull-list generation; printable transit labels; transfer history logging; permission control limiting transfer actions to authorized roles; preview/confirmation prior to commit; undo/rollback where feasible; and auto-revert mechanisms based on configured time periods or event criteria. Batch updates shall be implemented efficiently (for example processing in smaller controlled batches) to avoid long locks on production tables in large collections.

**Priority:** Medium. Requested repeatedly by cataloging and branch staff; technical concerns (large collection sizes) require explicit performance constraints and efficient batch processing.
**Sources:** early_draft_srs_galecia.txt, interview_cataloging_2009-05-08.txt, conversations/conv_pines018_item_transfer.eml, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0032, CAND-0108, CAND-0109, CAND-0113, CAND-0192, CAND-0193, CAND-0194, CAND-0195, CAND-0196, CAND-0197, CAND-0198, CAND-0199, CAND-0200, CAND-0201, CAND-0202, CAND-0188, CAND-0189, CAND-0190, CAND-0191, CAND-0104

### REQ-031 — Missing and Damaged Items Reporting

The system shall provide reports of missing and damaged items per branch (and per system where required). Reports shall support configurable date ranges for trend analysis and may include item condition notes where available (for example 'water damage' or 'vandalism') to assist root-cause analysis and auditing.

**Priority:** Medium. Branch staff consistently requested missing/damaged reports for monthly audits and collection management; date-range and condition notes are useful additions and are documented as requested features.
**Sources:** early_draft_srs_galecia.txt, interview_cataloging_2009-05-08.txt, conversations/conv_pines019_020_missing_intransit.eml, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0033, CAND-0099, CAND-0203, CAND-0206, CAND-0208, CAND-0110

### REQ-032 — In-Transit Items Report (threshold and merged view)

The system shall generate an In-Transit Items Report listing items that have been in-transit longer than a configurable threshold (X days). Reports shall be available per branch and per system and shall merge transit-to and transit-from data into a single view for front-line convenience. Reports shall be sortable by criteria such as due date to prioritize follow-up.

**Priority:** Medium. Circulation and delivery staff requested this capability to identify delayed transfers; configurability of threshold and merged view are explicit user requirements.
**Sources:** early_draft_srs_galecia.txt, interview_cataloging_2009-05-08.txt, conversations/conv_pines019_020_missing_intransit.eml
**Candidate IDs:** CAND-0034, CAND-0100, CAND-0204, CAND-0205, CAND-0207, CAND-0107

### REQ-033 — Item Record Purging and Conversion Utilities (with safeguards)

The system shall provide utilities and reports to identify candidate item records for purging or conversion based on customizable criteria (status, time-in-status, last-circulation age). The solution shall support batch status conversion workflows and include safeguards: candidate-side read-only reports, a distinct confirmation step prior to destructive actions, an audit trail recording operator and time, and the ability to preview affected records as an optional user step. Utilities shall also support removing volume entries with associated copy entries and identifying orphaned bib records with no attached items. Scheduling of purge operations is a requested option and should be treated as configurable (confirm before mandating automatic scheduled purges).

**Priority:** Medium. Cataloging staff requested robust weeding and purging tools; safety measures were strongly emphasized in the sources.
**Sources:** early_draft_srs_galecia.txt, interview_cataloging_2009-05-08.txt, conversations/conv_pines021_item_purging.eml
**Candidate IDs:** CAND-0035, CAND-0101, CAND-0106, CAND-0114, CAND-0209, CAND-0210, CAND-0212, CAND-0213, CAND-0214, CAND-0215, CAND-0216, CAND-0218, CAND-0217, CAND-0111, CAND-0105

### REQ-034 — Last-Copy Reporting (branch and system scope)

The system shall provide a Last Copy Report that identifies last copies at the branch and at the consortium/system level. The report shall be available at both per-branch and per-system scopes and shall be used to prevent accidental deletion of the only copy in a scope and to assist catalogers with WorldCat updates.

**Priority:** High. Cataloging stakeholders labelled the last-copy report as critical to avoid loss of unique holdings; this is mission-critical for collection stewardship.
**Sources:** early_draft_srs_galecia.txt, interview_cataloging_2009-05-08.txt, conversations/conv_pines021_item_purging.eml
**Candidate IDs:** CAND-0103, CAND-0211, CAND-0217

### REQ-035 — Deletion Tracking and Deletion Audit Logging

The system shall log record deletions (item, patron, bibliographic records) and shall provide reporting interfaces that aggregate deletions by period, type, location, and user. The deletion log shall include record type, record id, deletion timestamp, user who performed deletion, and the user's location/branch. Attempted/denied deletion attempts are recommended to be logged for compliance and troubleshooting; the storage/trigger implementation is an implementation detail but the logged fields and reporting behavior are required.

**Priority:** Medium. Administrators and auditors requested deletion tracking for accountability; the existing Evergreen lacked deletion logs by default and stakeholders emphasize the need for auditing.
**Sources:** early_draft_srs_galecia.txt, conversations/conv_pines022_deletions.eml, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0036, CAND-0219, CAND-0220, CAND-0221, CAND-0222, CAND-0223, CAND-0224, CAND-0225, CAND-0226, CAND-0227, CAND-0228, CAND-0229, CAND-0230, CAND-0231, CAND-0232, CAND-0233, CAND-0102

### REQ-036 — Patron Characteristic Filtering and Grouping

The system shall support filtering and grouping of queries and reports by patron characteristics including configurable age ranges (derived from birth_date), zip code, county of residence, home branch, patron type, and preferred language. Filters shall be combinable with AND/OR logic and null values shall be included explicitly in results unless the user chooses to exclude them; age-range buckets shall be configurable per report.

**Priority:** Medium. Survey, interviews, and meeting notes emphasize program planning and outreach needs for demographic grouping; functionality is essential for managers though not uniformly marked High across sources.
**Sources:** early_draft_srs_galecia.txt, conversations/conv_pines023_patron_characteristics.eml, survey_results_2009.txt, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0037, CAND-0234, CAND-0235, CAND-0236, CAND-0237, CAND-0238

### REQ-037 — Inactive Patrons Report and Outreach Data

The system shall produce lists of patrons with no circulation or electronic activity in the last configurable X days (X configurable), scoped to system/home library/county/etc. 'Electronic activity' shall include OPAC login, online hold placement, online renewals, and logged digital resource access where available. The report shall include current mailing addresses (when present), allow exclusions (e.g., staff, VIPs, opt-outs), support CSV export, and be designed to run as a background job for performance at large scale.

**Priority:** Medium. Requested by outreach and managers; performance considerations and integration of electronic-access logs make the feature operationally important and medium priority pending confirmation of exact inclusions and policies.
**Sources:** early_draft_srs_galecia.txt, conversations/conv_pines024_inactive_patrons.eml, survey_results_2009.txt
**Candidate IDs:** CAND-0038, CAND-0239, CAND-0240, CAND-0241, CAND-0242, CAND-0243, CAND-0244, CAND-0245, CAND-0246, CAND-0247, CAND-0248, CAND-0249, CAND-0250

### REQ-038 — Value of Items Reporting (aggregate valuation)

The system shall provide Value of Items reports that aggregate value/purchase-price fields stored on item records over a definable scope (entire collection or subsets) and allow filtering by status, format, shelving location, or other criteria (examples: value of 'longoverdue' items, value of all DVDs in children's collection). Implementations shall document which item field is used for valuation (purchase price or other).

**Priority:** Medium. Finance staff requested valuation reports; sources indicate valuation data exists on item records and the capability is needed for financial reporting and audits.
**Sources:** early_draft_srs_galecia.txt, email_financial_reports.eml, evergreen_reference_2009.txt
**Candidate IDs:** CAND-0045, CAND-0050, CAND-0054

### REQ-039 — Financial Reports and Reconciliation Queries

The system shall provide financial reporting including: patron account balances by patron/home library/system; fines and charges accrued over configurable time periods (last 12 months, YTD, last month) broken down by charge type; fines waived per time period and per branch; payments received per time period and by payment method and collection channel (staff desk, self-check station, OPAC); and support queries to find patron accounts with balances greater than a configured threshold. Financial reporting shall be able to join patron payment/debt data with related item records for necessary views. Financial information used in reconciliation shall be updatable in a timely manner to reflect front-desk payments (stakeholders request immediate reflection; implementers should aim for minimal latency consistent with transactional integrity).

**Priority:** High. Finance stakeholders emphasized the operational need for financial reporting and reconciliation; auditability and timely updates are critical for accounting and branch reconciliation activities.
**Sources:** early_draft_srs_galecia.txt, email_financial_reports.eml, survey_results_2009.txt
**Candidate IDs:** CAND-0048, CAND-0051, CAND-0055, CAND-0056, CAND-0057, CAND-0059, CAND-0047, CAND-0058

### REQ-040 — Financial Audit Trail / Payment Ledger

The system shall maintain a financial ledger/audit trail of patron payments and shall record which payments were applied to which charges to permit reconciliation and audit. The audit trail shall allow tracing every payment back to the specific charge(s) it was applied to and shall be reportable for audit and reconciliation purposes.

**Priority:** High. Finance staff described the audit trail as CRITICAL for proper reconciliation and auditing; this is a high priority requirement.
**Sources:** email_financial_reports.eml, early_draft_srs_galecia.txt
**Candidate IDs:** CAND-0049, CAND-0052, CAND-0060

### REQ-041 — Accounting and Auditing Compliance

All reports, financial recordkeeping, and data archiving shall comply with standard accounting practices and with applicable state, county, and municipal auditing requirements. Retention policies that implement required retention durations for financial and transactional data shall be supported (exact retention durations to be confirmed by stakeholders and local law).

**Priority:** High. Compliance with accounting/auditing requirements is explicitly required by finance stakeholders and the early draft and is therefore High priority.
**Sources:** early_draft_srs_galecia.txt, email_financial_reports.eml
**Candidate IDs:** CAND-0046, CAND-0053, CAND-0061

### REQ-042 — Report Types Coverage and Appendix Preservation

The system shall provide coverage for the range of canned and fine-grained report types enumerated in Appendix A and Appendix B of the early draft (circulation, items, bibliographic records, patrons, holds, transits, bills, and associated examples) and support the user-specified filters and display options described in the fine-grained list (recurring reports, comparative-period columns, pivot outputs, MARC field flattening, notice runs, etc.). Each specific Appendix item requires mapping to an implementable report and acceptance criteria; this requirement preserves the business need to implement the Appendix A/B report catalog and to validate each report type with owners.

**Priority:** Medium. Appendices provide a comprehensive list of desired report types; preserving them as business needs is required, but detailed prioritization/test criteria must be established for each report type.
**Sources:** early_draft_srs_galecia.txt, evergreen_reference_2009.txt, survey_results_2009.txt, interview_cataloging_2009-05-08.txt, meeting_tech_subcommittee_2009-06-30.txt
**Candidate IDs:** CAND-0024, CAND-0021, CAND-0144, CAND-0081, CAND-0097, CAND-0096, CAND-0019, CAND-0112, CAND-0105, CAND-0110, CAND-0144

### REQ-043 — Reporting Separation Options (replica/warehouse/background processing)

To support heavy analytical workloads without impacting production, the system shall provide options and architecture patterns for separating reporting workloads from production, such as background report processing, read-only reporting replicas, and/or a reporting data warehouse for historical/snapshot reporting. The business need is to avoid disruption while supporting historical snapshots; the architectural approach (replica vs warehouse vs background processing) is an open decision and must be documented and confirmed by stakeholders.

**Priority:** Medium. Technical subcommittee discussed several alternatives; separation is required as a business need, but the specific architecture is a design decision requiring stakeholder confirmation.
**Sources:** interview_sysadmin_2009-05-10.txt, meeting_tech_subcommittee_2009-06-30.txt, evergreen_reference_2009.txt
**Candidate IDs:** CAND-0119, CAND-0136, CAND-0086, CAND-0148

### REQ-044 — Help/Error Reporting and Troubleshooting Information

When reports or queries fail, the system shall present meaningful error information to administrators (for example: table/field referenced, error type, and guidance). The help system shall include troubleshooting guidance, links to data dictionaries, and guidance for interpreting diagnostic messages. High-level messages for non-admin users shall be user-friendly while administrators shall be able to retrieve low-level diagnostics.

**Priority:** Medium. Administrators requested low-level diagnostics and actionable messages to reduce help-desk load; this is valuable for operations and troubleshooting.
**Sources:** early_draft_srs_galecia.txt, meeting_tech_subcommittee_2009-06-30.txt, interview_sysadmin_2009-05-10.txt
**Candidate IDs:** CAND-0014, CAND-0146, CAND-0132, CAND-0133, CAND-0144

### REQ-045 — Export/Import and Configuration Migration

The system shall provide export/import mechanisms for report templates, saved queries, and permission settings enabling configurations created in development or training environments to be migrated to production reliably. Migration tooling, versioning guidance, and documentation shall be provided.

**Priority:** Medium. Technical meetings repeatedly requested migration capabilities to manage separate environments and deployments.
**Sources:** interview_sysadmin_2009-05-10.txt, meeting_tech_subcommittee_2009-06-30.txt, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0130, CAND-0139, CAND-0271

### REQ-046 — Selection by Survey Name (user-friendly survey filtering)

Reporting shall allow selection/filtering by survey name (user-friendly) rather than requiring survey IDs; the system shall resolve survey names to IDs internally to support user-friendly filter selection. This is a usability enhancement requested in the fine-grained list and should be confirmed as optional or required by stakeholders.

**Priority:** Low. Requested as a user convenience in the fine-grained appendix; useful but not critical to core reporting functionality.
**Sources:** early_draft_srs_galecia.txt, meeting_tech_subcommittee_2009-06-30.txt
**Candidate IDs:** CAND-0151

### REQ-047 — Include Selection Metadata in Results (date range & report name)

Report outputs shall include the selection criteria used (date ranges and filter selections) and the report name in a header or footer so consumers quickly see the date-range and criteria for the output. This is requested in Appendix B and fine-grained requirements to aid interpretation of historical reports.

**Priority:** Medium. Users requested that report outputs be self-describing so recipients can understand selection context; included in fine-grained appendices and user feature lists.
**Sources:** early_draft_srs_galecia.txt, email_report_features.eml, survey_results_2009.txt, meeting_tech_subcommittee_2009-06-30.txt
**Candidate IDs:** CAND-0150, CAND-0067, CAND-0022, CAND-0150

## Blacklist

### BL-001 — Working-group mission items (not product requirements)

Requirements that assert the Reports Working Group mission tasks (documenting functionality as a working-group activity, becoming the reports testing group, compiling executive report lists, creating templates for all PINES libraries) as product-level requirements.
**Reason:** These items describe the Reports Working Group's organizational mission and project governance tasks rather than product behavior to be implemented by the software. They belong in project governance documentation (meeting_minutes/meeting_2009-03-15_minutes.txt) rather than the product requirements list. The product requirements document preserves the business needs raised by the working group but excludes organizational mission statements as product requirements.
**Sources:** meeting_minutes/meeting_2009-03-15_minutes.txt, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0251, CAND-0252, CAND-0253, CAND-0254

### BL-002 — Editorial/audience guidance (not product requirements)

Editorial or audience guidance (for example: 'The SRS should aim for a high level of readability for a non-technical audience', 'Documentation must include contributions from library managers and staff', and other meeting-administration statements) treated as product functional requirements.
**Reason:** These statements concern document preparation, audience or project process, not product functionality. They are preserved in meeting minutes as project guidance, but are not software requirements to be implemented. Product requirements may reference the need for documentation (data dictionaries, help systems) but not the editorial guidance itself.
**Sources:** meeting_minutes/meeting_2009-03-15_minutes.txt, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0261, CAND-0262, CAND-0263

### BL-003 — Assumptions-as-functional-requirements (context only)

Assumptions and dependencies listed as product-level functional requirements (for example, statements that Management Processes are part of an enterprise ILS or interact with vendor APIs).
**Reason:** AS/DE items are important context/constraints and are preserved in the SRS 'Assumptions and Dependencies' section of the document. They are not direct product behavior requirements to implement. Keeping these as assumptions retains necessary context for design without incorrectly treating them as product features.
**Sources:** early_draft_srs_galecia.txt, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0278, CAND-0279, CAND-0280, CAND-0281, CAND-0282

### BL-004 — Duplicate requirement: Standards-compliant HTML output (merged into accessibility requirement)

CO-2 / REQ-006: The system must produce standards-compliant HTML output for web-based components (treated separately from accessibility).
**Reason:** Standards-compliant HTML output is required but was already merged with accessibility obligations in REQ-004. To avoid duplicate product-level requirements and preserve all sources, REQ-006's content has been consolidated into REQ-004 and REQ-006 is rejected as a separate requirement to prevent redundancy. The business need is preserved under REQ-004 with all sources retained.
**Sources:** early_draft_srs_galecia.txt, meeting_tech_subcommittee_2009-06-30.txt, meeting_minutes/meeting_2009-07-20_minutes.txt
**Candidate IDs:** CAND-0007, CAND-0137, CAND-0270


## Open questions

- Define the exact metrics that constitute 'capacity' for the System Capacity Interface (e.g., physical shelf-space, item count vs configured limit, current 'load' measured by circulation velocity). Sources: conversations/conv_pines015_capacity_interface.eml (CAND-0177).
- Decide preferred architecture for heavy reporting workloads: use read-only reporting replicas, a reporting data warehouse with ETL snapshots, or background processing against production with safeguards. Each option appears in sources but no consensus decision recorded. Sources: interview_sysadmin_2009-05-10.txt, meeting_tech_subcommittee_2009-06-30.txt (CAND-0119, CAND-0136, CAND-0086, CAND-0148).
- Specify how shelf-space should be represented in the Shelf Space Report: whether to estimate from item dimensions, use item-count as proxy, or require manual shelf-space configuration per shelving location. Sources: conversations/conv_pines016_shelf_space.eml (CAND-0184).
- Confirm retention durations (X) for transaction detail retention and archived financial records (e.g., whether 7 years retention applies to all financial tables or selected aggregates) and which records require long-term retention for audits. Sources: early_draft_srs_galecia.txt, email_financial_reports.eml (CAND-0039, CAND-0061).
- Clarify expected SLA and priority policy for report prioritization (who can elevate reports, permitted priority levels) and whether queue-priority preemption is allowed. Sources: email_report_features.eml, meeting_tech_subcommittee_2009-06-30.txt (CAND-0069, CAND-0071, CAND-0149).
- Decide null-handling semantics for aggregations and group-bys (treat null as separate bucket vs. coalesce to 'Unknown') and document for report consumers. Sources: meeting_tech_subcommittee_2009-06-30.txt, conversations/conv_pines023_patron_characteristics.eml (CAND-0150, CAND-0237).
- Clarify which external digital-resource access events should be considered 'electronic activity' for inactive patron reports (which vendor logs are integrated and expected integration semantics). Sources: conversations/conv_pines024_inactive_patrons.eml (CAND-0245).
- Confirm whether email delivery and address-book delivery for scheduled reports are mandatory or optional deployment features; document privacy and security implications if email delivery is enabled. Sources: early_draft_srs_galecia.txt Appendix B and email_report_features.eml (CAND-0151, CAND-0167, CAND-0094).
- Determine presentation strategy for the 'all-branches' capacity dashboard (how to avoid overcrowding with 286 locations: grouping, paging, regional rollups, filtering defaults). Sources: conversations/conv_pines015_capacity_interface.eml (CAND-0179).

## Outstanding validation issues

- REQ-018: missing source for CAND-0167
- REQ-026: missing source for CAND-0266
- REQ-035: missing source for CAND-0102
- Candidates silently omitted: ['CAND-0092', 'CAND-0255', 'CAND-0256', 'CAND-0257', 'CAND-0258', 'CAND-0259', 'CAND-0260']
- Candidates both accepted and rejected: ['CAND-0137']
- The supplied deterministic issues are substantive: REQ-018 cites CAND-0167 for output formats and scheduling, but CAND-0167 is a proposed volume-report capability from conversations/conv_pines014_material_volume.eml; REQ-026 cites CAND-0266, which concerns browser access in meeting_minutes/meeting_2009-07-20_minutes.txt, not material-volume reporting; and REQ-035 cites CAND-0102 from interview_cataloging_2009-05-08.txt while omitting it from that requirement’s source list. Correct the candidate mappings and source lists. CAND-0092 is an existing-system queue-visibility gap in evergreen_reference_2009.txt, not itself a new requirement; record it as context or explicitly exclude it while tracing the actual queue requirement. CAND-0255–0260 are scope/objective statements from meeting_minutes/meeting_2009-03-15_minutes.txt; preserve them as scope/context or explain their disposition rather than silently omitting them. CAND-0137 is both mapped to REQ-004 and rejected in BL-004; resolve that inconsistency.
- Several candidate evidence_quotes do not support their raw_text. In evergreen_reference_2009.txt, CAND-0082 through CAND-0087 quote only conclusion item 1 (“Expand the available report types…”), which does not establish the distinct permissions, queue, formats, accessibility, architecture, or environment statements in those candidates. CAND-0019’s quote stops before the Georgia Annual Report reference; CAND-0029 quotes only a heading; and meeting_minutes/meeting_2009-07-20_minutes.txt CAND-0264’s quote omits the open-hours/non-disruption sentence included in its raw_text. Replace these with the precise supporting passages or narrow the raw_text to what the quote establishes.
- There are additional inaccurate or incomplete candidate mappings. REQ-005 includes CAND-0127 (role assignment), unrelated to relational databases. REQ-038 includes CAND-0054 (joining patron and item financial data), not item valuation. REQ-018 maps CAND-0151 (survey-name filtering) to output/scheduling, and REQ-021 maps unrelated transaction/null/survey candidates to pivot-ready output, MARC flattening, and uploaded filter lists. In early_draft_srs_galecia.txt Appendix B, the relevant requested features include Excel/HTML/CSV output, scheduling, pivot output, MARC fields on one row, and uploading text files for filtering. Correct the mappings and ensure each claimed feature has source evidence that actually supports it.
- REQ-042 does not adequately preserve or make verifiable the extensive reporting catalog in early_draft_srs_galecia.txt, Appendices A and B. A blanket statement that the system shall cover the appendices is not a traceable, testable substitute for the listed reports and detailed behaviors. Examples needing explicit disposition or implementable mapping include circulation breakdowns by Dewey/MARC/county/age, bib and item edited reports, patron survey and expiration reports, hold and in-house-use reports, bills reports, and Appendix B’s comparative-period columns, notice runs, total-use date ranges, real-time/historical reporting, snapshot bills, separate last-circulation/check-in dates, transaction-by-time/workstation/staff reporting, and cancellation. Decompose the appendix coverage into traceable requirements or a report catalog with acceptance criteria; identify any deliberate exclusions.
- REQ-015 makes permission to schedule reports a required fine-grained permission, although the supplied sources specify permissions to create/clone reports and control who may run reports; they do not require schedule-specific permission. The description itself says unrequested privilege types should be confirmed. Remove scheduling from the mandated permission list or leave it explicitly open for stakeholder decision. Also separate genuinely requested permissions from implementation-policy additions.
- REQ-030 turns a number of requested or suggested transfer features into mandatory “shall” behavior without preserving their stated status. In conversations/conv_pines018_item_transfer.eml, transfer delay alerts, printable labels, undo, permission limits, and event-based reversion are raised as additional requests or questions; the summary calls them “Additional features requested.” Retain their provenance and distinguish agreed requirements from optional or unconfirmed requests. The current requirement also omits the explicitly requested transfer-delay alerts (CAND-0201) from its behavior despite mapping that candidate.
- The reporting requirements contain material semantic duplication without clear ownership: REQ-012 and REQ-044 both require error diagnostics/help troubleshooting; REQ-007 and REQ-045 both require environment configuration migration; and REQ-020 and REQ-047 both require selection metadata in outputs. Consolidate each pair or clearly partition the requirements so each has a distinct, non-duplicative scope and source trace.
- The source-status distinction is not consistently preserved. REQ-027 turns a technical suggestion in conversations/conv_pines015_capacity_interface.eml (CAND-0176: “Maybe we should group by system/region? Or allow filtering?”) into required grouping/filtering to prevent crowding, though the source treats this as a design consideration; retain it as an open presentation decision. Likewise, REQ-037 mandates background-job design and REQ-030 mandates specific implementation/performance measures in places where the sources give technical recommendations or feasibility notes; state the business outcome as required and keep implementation choices advisory unless confirmed.
- Some descriptions add unsupported specifics. REQ-004 mandates headings and “appropriate ARIA roles,” whereas interview_sysadmin_2009-05-10.txt specifies alt tags, ARIA labels, semantic HTML, and assistive-technology compatibility, not those additional particulars. REQ-003 requires implementers to confirm/document target browser support, which is not stated as a deliverable in the sources. Remove these additions or label them as proposals for confirmation rather than source-derived mandates.
- The financial retention requirement weakens a concrete source detail. In email_financial_reports.eml, George Tuttle states that some data needs to be retained for 7 years for audit purposes and that the system needs to enforce retention policies. REQ-022 and REQ-041 make all durations an open question without retaining that stated 7-year need. Preserve it as a known stakeholder retention requirement for the applicable data, while leaving which data it applies to and any jurisdiction-specific variation as an explicit decision; do not generalize it to all records.
- BL-003 says assumptions and dependencies are preserved in an SRS “Assumptions and Dependencies” section, but the supplied SRS document has no such section. CAND-0278–0282 are excluded from product requirements, which may be appropriate, but the document does not in fact preserve them as stated. Add a context/assumptions section or correct the blacklist rationale and ensure relevant dependencies—especially vendor interfaces and the OPAC/ILS relationship—remain documented.
- REQ-036 adds that users may choose to exclude null values, whereas conversations/conv_pines023_patron_characteristics.eml says nulls should be included and the consolidated requirement specifies inclusion. The sources do not request an exclusion option. Do not state that extra behavior as a requirement unless it is explicitly marked as a proposed option for confirmation.

## Input documents

- early_draft_srs_galecia.txt
- email_financial_reports.eml
- email_report_features.eml
- email_staff_login.eml
- evergreen_reference_2009.txt
- interview_cataloging_2009-05-08.txt
- interview_sysadmin_2009-05-10.txt
- meeting_tech_subcommittee_2009-06-30.txt
- survey_results_2009.txt
- conversations/conv_pines014_material_volume.eml
- conversations/conv_pines015_capacity_interface.eml
- conversations/conv_pines016_shelf_space.eml
- conversations/conv_pines018_item_transfer.eml
- conversations/conv_pines019_020_missing_intransit.eml
- conversations/conv_pines021_item_purging.eml
- conversations/conv_pines022_deletions.eml
- conversations/conv_pines023_patron_characteristics.eml
- conversations/conv_pines024_inactive_patrons.eml
- meeting_minutes/meeting_2009-03-15_minutes.txt
- meeting_minutes/meeting_2009-07-20_minutes.txt
