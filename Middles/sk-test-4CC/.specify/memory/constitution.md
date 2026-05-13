<!--
Sync Impact Report
==================
Version change: [TEMPLATE] → 1.0.0 (initial concrete constitution)
Modified principles: N/A (first version)
Added sections:
  - Core Principles (5 principles filled from template placeholders)
  - Development Standards (filled from SECTION_2)
  - Quality Gates (filled from SECTION_3)
  - Governance (filled from GOVERNANCE_RULES)
Removed sections: None
Templates requiring updates:
  - .specify/templates/plan-template.md: ✅ No update needed (Constitution Check is dynamic)
  - .specify/templates/spec-template.md: ✅ No update needed (generic template)
  - .specify/templates/tasks-template.md: ✅ No update needed (generic template)
  - .specify/templates/checklist-template.md: ✅ No update needed (generic template)
  - CLAUDE.md: ✅ Already contains Speckit placeholder
Follow-up TODOs: None
-->

# sk-test-4CC Constitution

## Core Principles

### I. Simplicity First

Every feature MUST start with the simplest possible implementation that satisfies the
requirements. YAGNI applies at all levels: no abstractions, no frameworks, no patterns
without a concrete, demonstrated need. Complexity MUST be justified in the plan's
Complexity Tracking table.

**Rationale**: Premature abstraction increases cognitive load, slows iteration, and is
frequently wrong. Simple code is easier to test, review, and change.

### II. Clear Contracts

Every module, service, or library MUST define its interface contract before
implementation begins. Contracts specify inputs, outputs, error modes, and side
effects. For CLI tools, text in/out protocol applies: stdin/args → stdout, errors →
stderr. For APIs, contracts live in `contracts/` as machine-readable specifications.

**Rationale**: Contracts enable independent development, testing, and verification.
They serve as the single source of truth between producers and consumers.

### III. Test-Driven Development

TDD is NON-NEGOTIABLE for all feature work. The cycle is: write tests → get user
approval on test coverage → verify tests fail → implement → verify tests pass.
Contract tests and integration tests MUST cover cross-component boundaries. Unit
tests cover internal logic.

**Rationale**: Tests written first define expected behavior unambiguously, prevent
regression, and serve as executable documentation. The fail-first step proves the
test is testing something real.

### IV. Documentation as Code

Documentation lives alongside source code in version control. Every feature MUST
include a `quickstart.md` that lets a new developer exercise the feature end-to-end.
Design decisions are captured in `research.md` and `data-model.md`. CLI tools MUST
provide `--help` output; APIs MUST include OpenAPI or equivalent specs.

**Rationale**: Documentation that drifts from code is worse than no documentation.
Co-locating docs with code makes drift visible in code review and keeps docs current.

### V. Continuous Validation

Every change MUST be independently verifiable. User stories are designed so that
any single story can be tested, deployed, and demonstrated in isolation. Checkpoints
after each user story phase gate progress: if a story doesn't work standalone, the
next story does not start.

**Rationale**: Independent validation prevents hidden coupling, enables parallel work,
and means the project always has a working MVP regardless of how many stories are done.

## Development Standards

- **Language**: As specified in the implementation plan's Technical Context section.
- **Version Control**: Git with feature branches following `[###-feature-name]` naming.
- **Commit Discipline**: Commit after each logical task completion. Commit messages
  describe the "why", not the "what".
- **Code Review**: All changes go through a review process. The Constitution Check in
  the implementation plan serves as the pre-review gate.
- **Code Style**: Configure linting and formatting during project setup (Phase 1).
  Style rules are enforced automatically; no manual style nits in review.

## Quality Gates

Every feature passes through these gates in order:

1. **Constitution Check** (Plan Phase 0): Verify alignment with all Core Principles
   before research begins. Violations require explicit justification in Complexity
   Tracking.
2. **Design Review** (Plan Phase 1): Contracts, data model, and quickstart reviewed
   before implementation.
3. **Test Gate** (Per User Story): Tests written, fail, then pass. No story merges
   with failing tests.
4. **Independent Validation** (Story Checkpoint): Each story demonstrated working in
   isolation before the next story begins.
5. **Polish Gate** (Final Phase): Quickstart validation, code cleanup, security
   hardening, and performance check before marking the feature complete.

## Governance

This Constitution supersedes all other development practices and conventions.
Amendments require:

1. A documented proposal describing the change and its rationale.
2. Impact assessment on existing features, templates, and workflows.
3. Version increment per semantic versioning (MAJOR for principle
   removal/redefinition, MINOR for new principles/sections, PATCH for
   clarifications and wording).
4. Propagation of changes to all dependent templates and command files.

All plan Constitution Checks, code reviews, and retrospectives MUST verify
compliance. Non-compliance discovered in review is a blocking issue. The
CLAUDE.md file provides runtime development guidance and MUST be consulted
for technology-specific instructions.

**Version**: 1.0.0 | **Ratified**: 2026-05-12 | **Last Amended**: 2026-05-12
