<!---
---
title: SAMPLE  Project Rules & Standards
created: 2025-06-11T12:00:00
modified: 2025-06-11T12:00:00
author: Lil Claudy Flossy
tags: [rules, standards, fastmcp, cloudclusters, mcp-server, guidelines]
project: fastmcp-cloudclusters
format: hybrid
---
{
  "title": "SAMPLE  Project Rules & Standards",
  "project": "fastmcp-cloudclusters",
  "created": "2025-06-11T12:00:00",
  "modified": "2025-06-11T12:00:00",
  "author": "Lil Claudy Flossy",
  "tags": ["rules", "standards", "fastmcp", "cloudclusters", "mcp-server", "guidelines"],
  "related_files": ["../README.md", "../docs/TOOL_REFERENCE.md", "../MANIFEST.md"]
}
Activity Log:
- 2025-06-11T12:00:00: Created comprehensive project rules integrating global claude_rules standards
- 2025-06-11T12:00:00: Defined MCP server specific guidelines and tool usage patterns
-->

# Project Rules & Standards

## 1. Project Overview


## 2. Core Principles

- **Security First**: No database credentials or API keys in code or metadata
- **Self-Containment**: Server must run independently with its own virtual environment
- **Documentation as Code**: Every tool, function, and workflow must be documented
- **Test Before Done**: All changes must be tested 
- **Memory Persistence**: Knowledge graph and cached data must survive server restarts

## 3. Documentation Standards

### 3.1 Metadata Requirements

All new files MUST begin with the hybrid metadata block:

```markdown
<!---
---
title: <Document Title>
created: <YYYY-MM-DDTHH:MM:SS>
modified: <YYYY-MM-DDTHH:MM:SS>
author: Lil Claudy Flossy
tags: [relevant, tags, here]
project: fastmcp-cloudclusters
format: hybrid
---
{
  "title": "<Document Title>",
  "project": "fastmcp-cloudclusters",
  "created": "<YYYY-MM-DDTHH:MM:SS>",
  "modified": "<YYYY-MM-DDTHH:MM:SS>",
  "author": "Lil Claudy Flossy",
  "tags": ["relevant", "tags", "here"],
  "related_files": ["path/to/related.py"]
}
Activity Log:
- <YYYY-MM-DDTHH:MM:SS>: Created/Updated with description
-->
```

### 3.2 Documentation Files

- `README.md` - Main project documentation
- `MANIFEST.md` - Complete file inventory
- `AUTOSTART_GUIDE.md` - Systemd service setup
- `SETUP_WALKTHROUGH.md` - Detailed setup instructions
- `docs/TOOL_REFERENCE.md` - Complete 23-tool reference
- `.claude/README.md` - Claude Code configuration
- `.claude/RULES.md` - This file


## 5. Code Standards

### 5.1 Python Code

1. **File Headers**: All Python files must start with:
```python
"""
Module: <module_name>
Description: <what this module does>
Author: Lil Claudy Flossy
Created: <YYYY-MM-DD>
Modified: <YYYY-MM-DD>
"""
```

2. **Import Organization**:
```python
# Standard library imports
import os
import sys

# Third-party imports
from sqlalchemy import create_engine
import networkx as nx

# Local imports
from .database import ConnectionManager
from .memory import KnowledgeGraph
```

3. **Error Handling**:
   - Use try-except blocks for all database operations
   - Return consistent error format: `{"success": false, "error": "message"}`
   - Log errors to system logger


- Always use `venv/` for isolation
- Update `requirements.txt` when adding dependencies

### 6.2 Configuration

- Use `.env` for all sensitive configuration
- Never commit `.env` file
- Keep `.env.example` updated
- Use absolute paths in configuration

## 7. Version Control

### 7.1 Branch Strategy

- Main branch: `main`
- Feature branches: `feature/descriptive-name`
- Bugfix branches: `bugfix/issue-description`
- Always create PRs for review

### 7.2 Commit Standards

```
ALWAYS ADD ROBUST COMMIT MESSAGES


🤖 Generated with [Claudie Flo$sie]

Co-Authored-By: Claudie Flo$sie <noreply@ClaudieFlo$sie.com>
```


## 10. Security Guidelines

1. **Never Store**:
   - Database passwords
   - API keys (Intercom, etc.)
   - Connection strings with credentials
   - User personal data

2. **Always Use**:
   - Environment variables from `.env`
   - Parameterized queries
   - Connection pooling
   - Secure file permissions

## 11. Continuous Improvement

- Update this document when patterns emerge
- Document new tool discoveries
- Add examples from real usage
- Review and refactor regularly

## 12. References

- [MCP Protocol Documentation](https://modelcontextprotocol.io)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [NetworkX Documentation](https://networkx.org/)
- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code)

---

Last Updated: 2025-06-24T15:58:00 by Claudie Flo$sie