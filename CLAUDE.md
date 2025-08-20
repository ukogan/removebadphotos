# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Photo deduplication tool for macOS Photos library - identifies similar photos taken within seconds of each other and helps users select the best ones for keeping while marking others for deletion.

## Vibe Coding System Requirements

**Critical Process:**
1. I am the product manager - drive standards, audit work, set direction, prioritize features, review code
2. **NO CODE** written until architecture.md is agreed upon and documented
3. Architecture must list features, lock in language/tech stack, require explicit discussion for changes
4. Track architecture changes (counter) - alert at 5 changes for security audit
5. Create feature-level markdown for each feature with architectural choices, plain language descriptions, file references, inputs/outputs/APIs
6. Link feature markdowns in master README.md
7. Build incrementally - recommend minimum scope, create PRD.md with development stages and user stories
8. Maintain RISKS.md with skeptical assessment of project risks and derisking recommendations
9. Read architecture and .md docs at session start
10. Maintain data-schema document, consult before data work
11. Mark test/dummy data explicitly in frontend and feature docs

## Project Constraints

**Technical:**
- macOS Photos library only (no videos initially)
- Open source libraries only (no commercial tools)
- Photos grouped by: within 10 seconds, same camera, similar composition
- Max 4 photos per group

**User Flow:**
- Present photo sets side-by-side with metadata (timestamp, size)
- Pre-select best photo (highlighted border)
- User clicks to change/add selections
- Generate deletion list → confirm → tag photos "marked-for-deletion"
- Create smart album "marked for deletion on MMM-DD at HH:MM to save ### MB"
- User manually deletes in Photos app
- Export list for future Google Photos API deletion

## Development Commands

Use `python3` (not `python`) for all Python commands.

## Required Documentation Files

Before any coding:
- architecture.md (detailed, with features list, tech stack)
- PRD.md (development stages, user stories)
- RISKS.md (skeptical risk assessment, derisking)
- data-schema.md (data structures)
- Feature-specific .md files
- README.md (links to all features)

## Architecture Change Counter

Current count: 2
Alert at 5 changes for security audit.