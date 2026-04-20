---
name: create-plan
description: Create detailed implementation plans through interactive research and iteration. Use when Codex needs to turn a task, ticket, spec, or referenced file into a thorough implementation plan with codebase research, iterative clarification, phased execution steps, concrete file references, and explicit automated versus manual verification criteria.
---

# Implementation Plan

Create detailed implementation plans through an interactive, iterative process. Be skeptical, thorough, and collaborative so the final specification is technically grounded and actionable.

## Initial Response

When this skill is invoked:

1. Check whether parameters were provided.
   - If a file path or ticket reference was provided, skip the default message.
   - Immediately read any provided files fully.
   - Begin the research process.
2. If no parameters were provided, respond with:

```text
I'll help you create a detailed implementation plan. Let me start by understanding what we're building.

Please provide:
1. The task/ticket description (or reference to a ticket file)
2. Any relevant context, constraints, or specific requirements
3. Links to related research or previous implementations

I'll analyze this information and work with you to create a comprehensive plan.

Tip: You can also invoke this skill with a ticket file directly: `$create-plan thoughts/allison/tickets/eng_1234.md`
For deeper analysis, try: `Use $create-plan and think deeply about thoughts/allison/tickets/eng_1234.md`
```

Then wait for the user's input.

## Process Steps

### Step 1: Context Gathering And Initial Analysis

1. Read all mentioned files immediately and fully.
   - Ticket files such as `thoughts/allison/tickets/eng_1234.md`
   - Research documents
   - Related implementation plans
   - Any JSON or data files mentioned
   - Read entire files, not partial excerpts.
   - Do not spawn subagents before reading explicitly mentioned files in the main context.
2. Spawn initial research tasks to gather context before asking the user any questions.
   - Use focused research subagents for codebase location, codebase analysis, thoughts lookup, and ticket lookup when relevant.
   - If the source workflow references specialized agents such as `codebase-locator`, `codebase-analyzer`, `thoughts-locator`, or `linear-ticket-reader`, use the closest available subagent pattern in the current environment.
   - Have those subagents find relevant source files, configs, and tests.
   - Have them identify the directories to focus on.
   - Have them trace data flow and key functions.
   - Require detailed explanations with `file:line` references.
3. Read all files identified by the research tasks.
   - Read every file they identify as relevant.
   - Read them fully into the main context before proceeding.
4. Analyze and verify understanding.
   - Cross-reference the ticket requirements with the actual code.
   - Identify discrepancies or misunderstandings.
   - Note assumptions that need verification.
   - Determine true scope based on codebase reality.
5. Present informed understanding and focused questions:

```text
Based on the ticket and my research of the codebase, I understand we need to [accurate summary].

I've found that:
- [Current implementation detail with file:line reference]
- [Relevant pattern or constraint discovered]
- [Potential complexity or edge case identified]

Questions that my research couldn't answer:
- [Specific technical question that requires human judgment]
- [Business logic clarification]
- [Design preference that affects implementation]
```

Only ask questions that genuinely cannot be answered through code investigation.

### Step 2: Research And Discovery

After getting initial clarifications:

1. If the user corrects any misunderstanding:
   - Do not just accept the correction.
   - Run follow-up research to verify the corrected information.
   - Read the specific files or directories they mention.
   - Proceed only after independently verifying the facts.
2. Create a research todo list using the available todo or planning tool, or track it explicitly in the conversation if no such tool exists.
3. Spawn parallel sub-tasks for comprehensive research.
   - Create multiple subagents to research different aspects concurrently.
   - Use the right prompt for each type of research.

For deeper investigation:
- Use a codebase-location pass to find more specific files.
- Use a codebase-analysis pass to understand implementation details.
- Use a pattern-finding pass to find similar features to model after.

For historical context:
- Use a thoughts-location pass to find existing research, plans, or decisions about the area.
- Use a thoughts-analysis pass to extract key insights from the most relevant documents.

For related tickets:
- Use a ticket or issue search pass to find similar issues or past implementations.

Each subagent should:
- Find the right files and code patterns.
- Identify conventions and patterns to follow.
- Look for integration points and dependencies.
- Return specific `file:line` references.
- Find tests and examples.

4. Wait for all sub-tasks to complete before proceeding.
5. Present findings and design options:

```text
Based on my research, here's what I found:

Current State:
- [Key discovery about existing code]
- [Pattern or convention to follow]

Design Options:
1. [Option A] - [pros/cons]
2. [Option B] - [pros/cons]

Open Questions:
- [Technical uncertainty]
- [Design decision needed]

Which approach aligns best with your vision?
```

### Step 3: Plan Structure Development

Once aligned on approach:

1. Create an initial plan outline:

```text
Here's my proposed plan structure:

## Overview
[1-2 sentence summary]

## Implementation Phases:
1. [Phase name] - [what it accomplishes]
2. [Phase name] - [what it accomplishes]
3. [Phase name] - [what it accomplishes]

Does this phasing make sense? Should I adjust the order or granularity?
```

2. Get feedback on structure before writing details.

### Step 4: Detailed Plan Writing

After structure approval:

1. Write the plan to `thoughts/shared/plans/YYYY-MM-DD-ENG-XXXX-description.md`.
   - Format: `YYYY-MM-DD-ENG-XXXX-description.md`
   - `YYYY-MM-DD` is today's date.
   - `ENG-XXXX` is the ticket number when present.
   - `description` is a brief kebab-case description.
   - Examples:
     - With ticket: `2025-01-08-ENG-1478-parent-child-tracking.md`
     - Without ticket: `2025-01-08-improve-error-handling.md`
2. Use this template structure:

````markdown
# [Feature/Task Name] Implementation Plan

## Overview

[Brief description of what we're implementing and why]

## Current State Analysis

[What exists now, what's missing, key constraints discovered]

## Desired End State

[A specification of the desired end state after this plan is complete, and how to verify it]

### Key Discoveries:
- [Important finding with file:line reference]
- [Pattern to follow]
- [Constraint to work within]

## What We're NOT Doing

[Explicitly list out-of-scope items to prevent scope creep]

## Implementation Approach

[High-level strategy and reasoning]

## Phase 1: [Descriptive Name]

### Overview
[What this phase accomplishes]

### Changes Required:

#### 1. [Component/File Group]
**File**: `path/to/file.ext`
**Changes**: [Summary of changes]

```[language]
// Specific code to add/modify
```

### Success Criteria:

#### Automated Verification:
- [ ] Migration applies cleanly: `make migrate`
- [ ] Unit tests pass: `make test-component`
- [ ] Type checking passes: `npm run typecheck`
- [ ] Linting passes: `make lint`
- [ ] Integration tests pass: `make test-integration`

#### Manual Verification:
- [ ] Feature works as expected when tested via UI
- [ ] Performance is acceptable under load
- [ ] Edge case handling verified manually
- [ ] No regressions in related features

**Implementation Note**: After completing this phase and all automated verification passes, pause here for manual confirmation from the human that the manual testing was successful before proceeding to the next phase.

---

## Phase 2: [Descriptive Name]

[Similar structure with both automated and manual success criteria...]

---

## Testing Strategy

### Unit Tests:
- [What to test]
- [Key edge cases]

### Integration Tests:
- [End-to-end scenarios]

### Manual Testing Steps:
1. [Specific step to verify feature]
2. [Another verification step]
3. [Edge case to test manually]

## Performance Considerations

[Any performance implications or optimizations needed]

## Migration Notes

[If applicable, how to handle existing data/systems]

## References

- Original ticket: `thoughts/allison/tickets/eng_XXXX.md`
- Related research: `thoughts/shared/research/[relevant].md`
- Similar implementation: `[file:line]`
````

### Step 5: Sync And Review

1. Sync the thoughts directory.
   - If the environment provides `humanlayer thoughts sync`, run it after creating or updating the plan.
   - Otherwise use the closest available sync or indexing workflow, or explicitly note that syncing could not be performed.
2. Present the draft plan location:

```text
I've created the initial implementation plan at:
`thoughts/shared/plans/YYYY-MM-DD-ENG-XXXX-description.md`

Please review it and let me know:
- Are the phases properly scoped?
- Are the success criteria specific enough?
- Any technical details that need adjustment?
- Missing edge cases or considerations?
```

3. Iterate based on feedback.
   - Add missing phases when needed.
   - Adjust the technical approach.
   - Clarify success criteria, including both automated and manual checks.
   - Add or remove scope items.
   - Re-run sync if the environment supports it.
4. Continue refining until the user is satisfied.

## Important Guidelines

1. Be skeptical.
   - Question vague requirements.
   - Identify potential issues early.
   - Ask why and what about.
   - Do not assume; verify with code.
2. Be interactive.
   - Do not write the full plan in one shot.
   - Get buy-in at each major step.
   - Allow course corrections.
   - Work collaboratively.
3. Be thorough.
   - Read all context files completely before planning.
   - Research actual code patterns using parallel sub-tasks.
   - Include specific file paths and line numbers.
   - Write measurable success criteria with clear automated versus manual distinction.
   - Prefer `make`-based automated steps whenever possible.
4. Be practical.
   - Focus on incremental, testable changes.
   - Consider migration and rollback.
   - Think about edge cases.
   - Include what is not being done.
5. Track progress.
   - Use the available todo or plan-tracking tool when present.
   - Update todos as research completes.
   - Mark planning tasks complete when done.
6. Do not leave open questions in the final plan.
   - If open questions appear during planning, stop.
   - Research or ask for clarification immediately.
   - Do not write the plan with unresolved questions.
   - The final plan must be complete and actionable.
   - Every decision must be made before finalizing the plan.

## Success Criteria Guidelines

Always separate success criteria into two categories:

1. Automated Verification
   - Commands that can be run, such as `make test` or `npm run lint`
   - Specific files that should exist
   - Code compilation and type checking
   - Automated test suites
2. Manual Verification
   - UI or UX functionality
   - Performance under real conditions
   - Edge cases that are hard to automate
   - User acceptance criteria

Format example:

```markdown
### Success Criteria:

#### Automated Verification:
- [ ] Database migration runs successfully: `make migrate`
- [ ] All unit tests pass: `go test ./...`
- [ ] No linting errors: `golangci-lint run`
- [ ] API endpoint returns 200: `curl localhost:8080/api/new-endpoint`

#### Manual Verification:
- [ ] New feature appears correctly in the UI
- [ ] Performance is acceptable with 1000+ items
- [ ] Error messages are user-friendly
- [ ] Feature works correctly on mobile devices
```

## Common Patterns

### For Database Changes

- Start with schema or migration changes.
- Add store methods.
- Update business logic.
- Expose changes via API.
- Update clients.

### For New Features

- Research existing patterns first.
- Start with the data model.
- Build backend logic.
- Add API endpoints.
- Implement UI last.

### For Refactoring

- Document current behavior.
- Plan incremental changes.
- Maintain backwards compatibility.
- Include a migration strategy.

## Sub-Task Spawning Best Practices

When spawning research sub-tasks:

1. Spawn multiple tasks in parallel for efficiency.
2. Keep each task focused on a specific area.
3. Provide detailed instructions including:
   - exactly what to search for
   - which directories to focus on
   - what information to extract
   - the expected output format
4. Be extremely specific about directories.
   - If the ticket mentions WUI, specify `humanlayer-wui/`.
   - If it mentions daemon, specify `hld/`.
   - Never use generic terms like UI when WUI is intended.
   - Include the full path context in prompts.
5. Prefer read-only tools for research when possible.
6. Request specific `file:line` references in responses.
7. Wait for all tasks to complete before synthesizing.
8. Verify sub-task results.
   - If a sub-task returns unexpected results, spawn follow-up tasks.
   - Cross-check findings against the actual codebase.
   - Do not accept results that seem incorrect.

Example:

```python
# Spawn these tasks concurrently:
tasks = [
    Task("Research database schema", db_research_prompt),
    Task("Find API patterns", api_research_prompt),
    Task("Investigate UI components", ui_research_prompt),
    Task("Check test patterns", test_research_prompt),
]
```

Treat `Task(...)` as pseudocode. Use the current environment's subagent or parallel work primitives to achieve the same result.

## Example Interaction Flow

```text
User: $create-plan
Assistant: I'll help you create a detailed implementation plan...

User: We need to add parent-child tracking for Claude sub-tasks. See thoughts/allison/tickets/eng_1478.md
Assistant: Let me read that ticket file completely first...

[Reads file fully]

Based on the ticket, I understand we need to track parent-child relationships for Claude sub-task events in the hld daemon. Before I start planning, I have some questions...

[Interactive process continues...]
```
