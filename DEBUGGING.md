# Debugging Log

## HALT Protocol Guidelines

**Before ANY debugging session:**
1. Run diagnostics: `python3 -m pytest tests/diagnostics -v`
2. Create debug branch: `git checkout -b debug/[issue-name]` 
3. Document hypothesis in this file
4. Start 30-minute timer

**During debugging:**
- Test smallest unit first (never multiple layers simultaneously)
- One change at a time, commit working states
- Update this file every 10 minutes
- Binary search elimination of layers
- Pivot to workaround at 20 minutes

**Time Budget Per Layer:**
- Diagnostics: < 1 second
- Unit tests: < 5 seconds  
- Integration: < 30 seconds
- E2E: < 2 minutes
- **Total session: < 30 minutes (HARD LIMIT)**

---

## Active Debugging Sessions

### Template for New Sessions

```markdown
## [Date] [Issue Name]

### Hypothesis
What I think is wrong: [specific hypothesis]

### Test Results (Update every 10 min)
| Time | Test Level | Result | Learning |
|------|------------|--------|----------|  
| 0min | Diagnostics | ❓ | Starting diagnostics |
| 5min | Unit | ❓ | [Update] |
| 15min | Integration | ❓ | [Update] |
| 25min | PIVOT/STOP | - | [Decision made] |

### Resolution
- Root cause: [actual issue found]
- Fix applied: [specific code change]
- Time investment: [X] minutes  
- Status: [Resolved/Abandoned/Escalated]
- Prevention: [how to avoid this in future]
```

---

## Completed Debugging Sessions

*(Sessions will be moved here when completed)*

---

## Escalation Triggers

**Immediate PM/Architecture Review Required:**
- Same error recurring 3+ times
- Multiple services failing simultaneously  
- Memory usage >200MB consistently
- Architecture change counter reaching 5
- Any single session approaching 30 minutes

**Emergency Procedures:**
1. STOP all feature work
2. Run full diagnostic suite
3. Review last known working commit
4. Consider rollback to stable state
5. Document crisis in this file
6. Escalate to product management