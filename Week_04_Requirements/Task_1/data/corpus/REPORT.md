# Requirements

## Run script
1. Install dependencies: python -m pip install -r requirements.txt
2. Set OpenAI key: $env:OPENAI_API_KEY = {input_key}
3. Run command from folder where are py scripts: python graph.py . --output ./output --exclude "Task_1.md" --exclude "README*.md" --exclude "requirements.txt" --exclude "requirements_output.md" --exclude "REPORT.md"

## Purpose

The program turns emails, interviews, surveys, and meeting notes into one
structured software requirements document. The example documents describe
the PINES/Evergreen library system.

## How it works

1. **File loader — no AI.** Python reads `.txt`, `.md`, and plain-text `.eml`
   files from the input directory and its subdirectories. Individual source
   paths are not hard-coded. The output directory is excluded.
2. **Extractor — `gpt-4o-mini`.** Finds candidate requirements in each source
   and adds supporting quotations. 
   (Note after failed run: If a quotation does not match the source,
   the model selects source line numbers and Python copies the original text.
   Up to two evidence repair attempts are allowed.)
3. **Consolidator — `gpt-5-mini`.** Combines duplicate candidates, writes
   requirements, assigns ID and priorities, and records their sources.
   Requirements rejected with justification are placed in a blacklist.
4. **Validator — `gpt-6-luna`.** Compares the document with the sources and
   checks for contradictions, duplicates, and unsupported claims.
   Python also checks IDs, source names, and candidate coverage.
5. **Document renderer — no AI.** Python creates `requirements_output.md`.
   A separate `run_details.json` stores technical data and review history.

When issues are found, the Consolidator receives the previous draft and the
feedback, revises the document, and sends it for another review. The default
limit is three reviews in total. The loop also stops after approval or when
a rejected draft remains unchanged. Unresolved issues are recorded, and an
unapproved result is clearly marked as a draft.

## Design choices

Separate roles allow one agent to collect information, another to organize it,
and a third to review the result. The feedback loop provides a way to correct
mistakes. Pydantic validates the response structure, while Python renders
Markdown to keep document formatting consistent.

`state.py` defines shared state and data formats.
`nodes.py` contains the nodes and prompts. 
`graph.py` defines execution order, routing, and program startup.

## Network requirements coverage

| Specification | How it is addressed |
| --- | --- |
| ANS1 — At least 3 LLM-invoking nodes | Extractor, Consolidator, and Validator |
| ANS2 — At least 1 deterministic node | File loading and Markdown rendering |
| ANS3 — At least 1 feedback loop | The Validator sends feedback to the Consolidator for revision |
| ANS4 — At least 3 different models | `gpt-4o-mini`, `gpt-5-mini`, and `gpt-6-luna` |
| ANS5 — Python LangGraph | Nodes and transitions are implemented using `StateGraph` |

## Output requirements coverage

| Specification | How it is addressed |
| --- | --- |
| OS1 — Single structured document | The main result is `requirements_output.md` |
| OS2 — Unique requirement IDs | Requirements use IDs such as `REQ-001`; Python checks for duplicate IDs |
| OS3 — No semantic duplicates | The Consolidator merges duplicates; the Validator checks for remaining overlap |
| OS4 — Traceability | Requirements list source documents and extracted candidate IDs |
| OS5 — Name and explanation | Each requirement has a short name and an explanatory paragraph |
| OS6 — Priority and explained scale | High, Medium, and Low are defined; each assignment includes a reason |
| OS7 — Consistency | Prompts and review checks address contradictions and consistent terminology |
| OS8 — Completeness | Candidate coverage is checked, and the document is compared with original sources |
| OS9 — Blacklist | Rejected statements are recorded separately with reasons and sources |

Priority scale: **High** means explicitly mandatory or critical; **Medium**
means requested functionality without an explicit priority; **Low** means
an explicitly optional feature. Inferred priorities need stakeholder confirmation.

## Run results and limitations

The supplied output uses **20 source documents** and contains **46 requirements**
with unique IDs and **4 blacklist entries**. After **three reviews**, execution
stopped with `max_rounds_reached` (param). The document is marked
`DRAFT — NEEDS HUMAN REVIEW`, so it did not receive automated approval.

Remaining issues include overlapping requirements, inaccurate source mappings,
and insufficient detail in parts of the reporting catalog. These are listed
under `Outstanding validation issues`.
