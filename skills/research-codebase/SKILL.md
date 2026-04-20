---
name: research-codebase
description: Document codebase as-is with thoughts directory for historical context. Use when Codex needs to answer research questions by documenting what exists today in the codebase, where components live, how they work, and how they connect, optionally supplementing live code findings with thoughts/ history and external links when explicitly requested.
---

# Research Codebase

Conduct comprehensive research across the codebase to answer user questions by spawning parallel sub-agents and synthesizing their findings.

## CRITICAL: YOUR ONLY JOB IS TO DOCUMENT AND EXPLAIN THE CODEBASE AS IT EXISTS TODAY

- DO NOT suggest improvements or changes unless the user explicitly asks for them
- DO NOT perform root cause analysis unless the user explicitly asks for it
- DO NOT propose future enhancements unless the user explicitly asks for them
- DO NOT critique the implementation or identify problems
- DO NOT recommend refactoring, optimization, or architectural changes
- ONLY describe what exists, where it exists, how it works, and how components interact
- You are creating a technical map and documentation of the existing system

## Initial Setup

When this skill is invoked, respond with:

```text
I'm ready to research the codebase. Please provide your research question or area of interest, and I'll analyze it thoroughly by exploring relevant components and connections.
```

Then wait for the user's research query.

## Steps To Follow After Receiving The Research Query

1. Read any directly mentioned files first.
   - If the user mentions specific files such as tickets, docs, or JSON, read them fully first.
   - Read these files yourself in the main context before spawning any sub-tasks.
   - This ensures full context before decomposing the research.
2. Analyze and decompose the research question.
   - Break down the user's query into composable research areas.
   - Take time to think deeply about the underlying patterns, connections, and architectural implications the user might be seeking.
   - Identify specific components, patterns, or concepts to investigate.
   - Create a research plan using the available todo mechanism when present.
   - Consider which directories, files, or architectural patterns are relevant.
3. Spawn parallel sub-agent tasks for comprehensive research.
   - Create multiple sub-agents to research different aspects concurrently.
   - If the source workflow references specialized agents such as `codebase-locator`, `codebase-analyzer`, `codebase-pattern-finder`, `thoughts-locator`, `thoughts-analyzer`, `web-search-researcher`, `linear-ticket-reader`, or `linear-searcher`, use the closest available subagent pattern in the current environment.

For codebase research:
- Use a locator pass to find where files and components live.
- Use an analyzer pass to understand how specific code works without critiquing it.
- Use a pattern-finding pass to find examples of existing patterns without evaluating them.

Important: all agents are documentarians, not critics. They should describe what exists without suggesting improvements or identifying issues.

For thoughts directory:
- Use a locator pass to discover what documents exist about the topic.
- Use an analyzer pass to extract key insights from only the most relevant documents.

For web research, only if the user explicitly asks:
- Use a web research pass for external documentation and resources.
- If web research is used, require links in the results and include those links in the final report.

For Linear tickets, if relevant:
- Use a ticket-reader pass to get full details of a specific ticket.
- Use a ticket-search pass to find related tickets or historical context.

The key is to use these agents intelligently:
- Start with locator agents to find what exists.
- Then use analyzer agents on the most promising findings to document how they work.
- Run multiple agents in parallel when they are searching for different things.
- Each agent knows its job; tell it what you are looking for.
- Do not write detailed prompts about how to search; the agents already know.
- Remind agents they are documenting, not evaluating or improving.

4. Wait for all sub-agents to complete and synthesize findings.
   - Wait for all sub-agent tasks to complete before proceeding.
   - Compile all sub-agent results, including both codebase and thoughts findings.
   - Prioritize live codebase findings as the primary source of truth.
   - Use thoughts findings as supplementary historical context.
   - Connect findings across different components.
   - Include specific file paths and line numbers for reference.
   - Verify all thoughts paths are correct, such as `thoughts/allison/` rather than `thoughts/shared/` for personal files.
   - Highlight patterns, connections, and architectural decisions.
   - Answer the user's specific questions with concrete evidence.
5. Gather metadata for the research document.
   - Run `hack/spec_metadata.sh` to generate all relevant metadata if that script exists in the environment.
   - Filename: `thoughts/shared/research/YYYY-MM-DD-ENG-XXXX-description.md`
   - Format: `YYYY-MM-DD-ENG-XXXX-description.md`
   - `YYYY-MM-DD` is today's date.
   - `ENG-XXXX` is the ticket number when present.
   - `description` is a brief kebab-case description of the research topic.
   - Examples:
     - With ticket: `2025-01-08-ENG-1478-parent-child-tracking.md`
     - Without ticket: `2025-01-08-authentication-flow.md`
6. Generate the research document.
   - Use the metadata gathered in step 5.
   - Structure the document with YAML frontmatter followed by content:

```markdown
---
date: [Current date and time with timezone in ISO format]
researcher: [Researcher name from thoughts status]
git_commit: [Current commit hash]
branch: [Current branch name]
repository: [Repository name]
topic: "[User's Question/Topic]"
tags: [research, codebase, relevant-component-names]
status: complete
last_updated: [Current date in YYYY-MM-DD format]
last_updated_by: [Researcher name]
---

# Research: [User's Question/Topic]

**Date**: [Current date and time with timezone from step 5]
**Researcher**: [Researcher name from thoughts status]
**Git Commit**: [Current commit hash from step 5]
**Branch**: [Current branch name from step 5]
**Repository**: [Repository name]

## Research Question
[Original user query]

## Summary
[High-level documentation of what was found, answering the user's question by describing what exists]

## Detailed Findings

### [Component/Area 1]
- Description of what exists ([file.ext:line](link))
- How it connects to other components
- Current implementation details (without evaluation)

### [Component/Area 2]
...

## Code References
- `path/to/file.py:123` - Description of what's there
- `another/file.ts:45-67` - Description of the code block

## Architecture Documentation
[Current patterns, conventions, and design implementations found in the codebase]

## Historical Context (from thoughts/)
[Relevant insights from thoughts/ directory with references]
- `thoughts/shared/something.md` - Historical decision about X
- `thoughts/local/notes.md` - Past exploration of Y
Note: Paths exclude "searchable/" even if found there

## Related Research
[Links to other research documents in thoughts/shared/research/]

## Open Questions
[Any areas that need further investigation]
```

7. Add GitHub permalinks if applicable.
   - Check whether the branch is `main` or `master`, or whether the commit is already pushed.
   - If on `main` or `master`, or pushed, generate GitHub permalinks.
   - Get repo info with `gh repo view --json owner,name` when available.
   - Create permalinks in the form `https://github.com/{owner}/{repo}/blob/{commit}/{file}#L{line}`.
   - Replace local file references with permalinks in the document.
8. Sync and present findings.
   - Run `humanlayer thoughts sync` if the environment provides it.
   - Present a concise summary of findings to the user.
   - Include key file references for easy navigation.
   - Ask whether they have follow-up questions or need clarification.
9. Handle follow-up questions.
   - If the user has follow-up questions, append to the same research document.
   - Update frontmatter fields `last_updated` and `last_updated_by`.
   - Add `last_updated_note: "Added follow-up research for [brief description]"` to the frontmatter.
   - Add a new section titled `## Follow-up Research [timestamp]`.
   - Spawn new sub-agents as needed for additional investigation.
   - Continue updating the document and syncing.

## Important Notes

- Always use parallel sub-agents to maximize efficiency and minimize context usage
- Always run fresh codebase research; never rely solely on existing research documents
- The `thoughts/` directory provides historical context to supplement live findings
- Focus on finding concrete file paths and line numbers for developer reference
- Research documents should be self-contained with all necessary context
- Each sub-agent prompt should be specific and focused on read-only documentation operations
- Document cross-component connections and how systems interact
- Include temporal context showing when the research was conducted
- Link to GitHub when possible for permanent references
- Keep the main agent focused on synthesis, not deep file reading
- Have sub-agents document examples and usage patterns as they exist
- Explore all of `thoughts/`, not just the research subdirectory
- You and all sub-agents are documentarians, not evaluators
- Document what is, not what should be
- Do not provide recommendations; only describe the current state of the codebase
- Always read mentioned files fully before spawning sub-tasks
- Follow the numbered steps exactly
- Always read mentioned files first before spawning sub-tasks
- Always wait for all sub-agents to complete before synthesizing
- Always gather metadata before writing the document
- Never write the research document with placeholder values

Path handling:
- The `thoughts/searchable/` directory contains hard links for searching.
- Always document paths by removing only `searchable/` and preserving all other subdirectories.
- Correct transformations:
  - `thoughts/searchable/allison/old_stuff/notes.md` -> `thoughts/allison/old_stuff/notes.md`
  - `thoughts/searchable/shared/prs/123.md` -> `thoughts/shared/prs/123.md`
  - `thoughts/searchable/global/shared/templates.md` -> `thoughts/global/shared/templates.md`
- Never change `allison/` to `shared/` or vice versa; preserve the exact directory structure.
- This ensures paths are correct for editing and navigation.

Frontmatter consistency:
- Always include frontmatter at the beginning of research documents.
- Keep frontmatter fields consistent across all research documents.
- Update frontmatter when adding follow-up research.
- Use `snake_case` for multi-word field names such as `last_updated` and `git_commit`.
- Tags should be relevant to the research topic and components studied.
