# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Git Workflow Standards

**Branch Protection (Manual Enforcement):**
- NEVER push directly to main branch
- Always work on feature branches: `feature/description`, `fix/description`, `docs/description`
- Create PRs for all changes using `gh pr create`

**Required Pre-merge Checks:**
```bash
npm run lint           # Code style and quality
npm run typecheck      # Type validation (if applicable) 
npm test              # All tests must pass
npm run build         # Ensure build succeeds
```

**Commit Standards:**
- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`
- Keep commits atomic and descriptive
- Reference issues when applicable

**Security Requirements:**
- NEVER commit secrets or API keys
- Add sensitive files to .gitignore
- Review diffs before committing

## Development Commands

[Add project-specific commands here]

## Architecture Notes

[Add project-specific architecture details here]

- remember this testing guidance and apply it when i ask for e2e testing on this project