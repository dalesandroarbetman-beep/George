# Errors

Command failures and integration errors.

---

## [ERR-20260917-001] skill-creator-validation-encoding

**Logged**: 2026-09-17T08:09:08.2249379Z
**Priority**: low
**Status**: resolved
**Area**: config

### Summary
`quick_validate.py` failed on Windows when reading a Skill with Chinese path/content under the default local encoding.

### Error
```text
UnicodeDecodeError: 'gbk' codec can't decode byte 0x8b
```

### Context
- Operation attempted: validate the new `video-multiplatform-publishing` skill.
- Environment: Windows PowerShell, Python 3.11, Chinese project path and Markdown content.

### Suggested Fix
Run the validator with UTF-8 mode enabled, for example by setting `PYTHONUTF8=1` for the command.

### Metadata
- Reproducible: yes
- Related Files: video-multiplatform-publishing/SKILL.md

### Resolution
- **Resolved**: 2026-09-17T08:09:08.2249379Z
- **Notes**: Re-ran `quick_validate.py` with `PYTHONUTF8=1`; validation passed.

---
