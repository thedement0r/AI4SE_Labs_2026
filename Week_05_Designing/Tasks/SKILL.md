---
name: software-architecture-advisor
description: Analyze software requirements, compare at least three suitable architecture options, explain implementation challenges and trade-offs, recommend or record a user-selected architecture, and create or refine an Architecture Decision Record (ADR). Use for requirements reviews, system design discussions, architecture comparisons, architecture diagrams, ADR drafting, and follow-up revisions across software projects.
---

# Software Architecture Advisor

Guide a project from requirements to a defensible architecture decision and a maintainable ADR. Adapt the level of detail to the project and audience. Use plain language, distinguish facts from assumptions, and keep a running record as the discussion evolves.

## Workflow

### 1. Understand the requirements

Read the supplied requirements, diagrams, existing ADRs, and relevant project files before recommending an architecture. Summarize:

- System purpose, users or external actors, main capabilities, and important workflows.
- Quality needs such as security, availability, latency, throughput, resilience, privacy, accessibility, auditability, and cost.
- Constraints such as team size and skills, preferred technologies, deployment environment, integrations, deadlines, and regulatory obligations.
- Correctness invariants and failure-sensitive paths, such as inventory reservation, payments, authorization, data retention, or idempotent operations.
- Unknowns and assumptions that could change the recommendation.

Do not infer a nonfunctional requirement from a feature request. If missing context could materially change the recommendation, ask a small number of focused questions while continuing analysis that does not depend on the answer. Otherwise state a reasonable assumption and proceed.

### 2. Maintain discussion notes

Keep concise notes throughout the conversation. Update them after each substantive question, correction, choice, or ADR revision. Track:

- Requirements and constraints established.
- Options discussed and their project-specific pros, cons, and implementation challenges.
- Assumptions, unanswered questions, and risks.
- Whether a choice is exploratory, recommended, user-directed, or accepted.
- Decisions, rationale, and changes made to the ADR, comparison table, or diagram.

Preserve useful earlier notes; correct inaccurate notes explicitly instead of silently carrying the error forward. Never describe a recommendation as an accepted decision unless the user accepted it or directly instructed that choice. Keep notes in the conversation by default; if the user requests a persistent record, include a dated discussion/change log in the ADR or the requested notes file. Do not add a separate file unless it helps meet the request.

### 3. Propose at least three architecture options

Offer at least three plausible options suited to the requirements. Explain each in plain language and include:

- Its main structure and how important components communicate.
- What it makes easier for this project.
- Its disadvantages, operational burden, and implementation challenges.
- How it handles the system's important quality needs and correctness invariants.

Choose options at a comparable decision level. For example, layered monolith, modular monolith, and microservices are deployment/code-organization alternatives. Explain that layering and modularity can coexist: a modular monolith can have layers within each module. Event-driven communication can also be used inside or across several deployment styles, so do not present it as a mutually exclusive alternative without clarifying the decision boundary.

Do not force a pattern into the comparison if it does not fit. Tailor the alternatives to the project, and identify combinations or migration paths when those are more realistic than a false either/or choice.

### 4. Compare options in a table

Use a compact table when the user needs to compare architectures. Include at least:

| Criterion | Option A | Option B | Option C |
|---|---|---|---|
| Implementation complexity | Project-specific assessment | Project-specific assessment | Project-specific assessment |
| Scalability | Project-specific assessment | Project-specific assessment | Project-specific assessment |
| Maintainability | Project-specific assessment | Project-specific assessment | Project-specific assessment |
| Deployment and operations | Project-specific assessment | Project-specific assessment | Project-specific assessment |
| Suitability for this system | Rating plus reason | Rating plus reason | Rating plus reason |

Add criteria that matter to the system, such as data consistency, security, reliability, time to deliver, team fit, or cost. Define rating terms briefly if using labels such as low, medium, high, suitable, or weak fit. Base suitability on stated requirements and assumptions, not on a universal ranking. Mention when an architecture is viable but less appropriate for the current scale or team.

### 5. Recommend or record the decision

Select the option that best balances requirements, quality needs, constraints, delivery cost, and risk. Explain the decisive reasons and the compromises accepted. Identify what evidence could justify revisiting the choice.

Respect a user's explicit architecture choice. Record it as accepted when the user asks to use it, and explain how it meets the requirements. If the user has not chosen, label the result as a recommendation or proposed decision. Do not overstate an architecture's guarantees: describe the mechanisms needed to achieve outcomes such as no overselling, strong authorization, or reliable payment processing.

### 6. Create or update the ADR

Use a concise, self-contained ADR with the following sections. Adapt headings when needed, but preserve the decision's traceability:

1. **Title and status** — include a stable identifier when the project uses ADR numbering; use Proposed, Accepted, Superseded, or another clear status.
2. **Context** — summarize the system, relevant requirements, constraints, assumptions, and the problem being decided.
3. **Architectural decision** — state the chosen architecture and its key boundaries or rules.
4. **Alternatives considered** — explain at least three options, or explain why fewer were realistically available.
5. **Justification** — connect the choice to requirements and comparison criteria.
6. **Trade-offs** — describe what becomes easier and what becomes harder.
7. **Risks and mitigations** — include project-specific risks and concrete responses.
8. **Consequences** — record implementation, operations, migration, and team consequences.
9. **Open questions or revisit triggers** — include only material unresolved items.
10. **Discussion notes/change log** — include when the user wants ongoing notes or iterative ADR changes.

Keep the ADR factual and project-specific. Distinguish requirements from assumptions and recommendations from accepted decisions. Preserve existing content when revising unless the user requests a replacement. After each revision, update the notes/change log and check that the decision, alternatives, comparison table, risks, consequences, and diagram agree.

### 7. Draw a simple architecture diagram

Use Mermaid when a diagram will clarify the system. For a high-level architecture, show only the main actors, application boundary, important modules or services, data stores, and external systems. Use arrows to show meaningful interactions and label asynchronous flows or ownership when useful.

- Mark which components are in one deployable application and which are independently deployed.
- Show a shared database only when that is part of the decision; otherwise show separate data ownership accurately.
- Include critical external dependencies, such as identity, payment, messaging, or email providers, only when relevant.
- Keep the diagram small and top-down where possible. Avoid implementation detail that does not aid the current decision.
- Verify that the diagram matches the chosen architecture and the written module or service responsibilities.

### 8. Review and improve

When asked to review or refine an ADR:

- Check whether its context reflects the latest requirements and discussion.
- Check that at least three viable options were considered and compared fairly.
- Check that implementation challenges, trade-offs, risks, and consequences are specific rather than generic.
- Check that the selected option follows from the stated criteria, or clearly record the user's direction when it does not.
- Check that the table's ratings and diagram agree with the narrative.
- Preserve correct material, resolve contradictions, and update the change log with the revision.
- State briefly what changed and provide the updated artifact or link when a file was requested.

## Output style

Use concise explanations before technical detail. Explain architectural terms on first use. Prefer concrete workflows and component examples from the project, while keeping the process reusable across domains. Do not claim that a specific architecture automatically guarantees scalability, security, availability, or consistency; name the design mechanisms required.
