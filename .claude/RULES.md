<!---
---
title: Dolla-Bucks Project Rules & Standards
created: 2025-06-11T12:00:00
modified: 2025-06-11T12:00:00
author: Lil Claudy Flossy
tags: [rules, standards, fastmcp, cloudclusters, mcp-server, guidelines]
project: Dolla-Bucks
format: hybrid
---
{
  "title": "Dolla-Bucks Project Rules & Standards",
  "project": "Dolla-Bucks",
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

# Dolla-Bucks Project Rules & Standards

## 1. Project Overview

Dolla-Bucks is a self-contained project. This document defines the rules, standards, and best practices specific to this project.

## 2. Core Principles

- **Security First**: No database credentials or API keys in code or metadata
- **Self-Containment**: Server must run independently with its own virtual environment
- **Documentation as Code**: Every tool, function, and workflow must be documented
- **Test Before Done**: All changes must be tested with `test_list_databases.py` and `test_mcp_tools.py`
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
project: Dolla-Bucks
format: hybrid
---
{
  "title": "<Document Title>",
  "project": "Dolla-Bucks",
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

## 4. MCP Server Rules

### 4.1 Tool Development

1. **Tool Naming**: Use descriptive snake_case names (e.g., `list_databases`, `execute_query`)
2. **Tool Documentation**: Every tool must have:
   - Clear description
   - Parameter definitions with types
   - Return value examples
   - Usage examples in TOOL_REFERENCE.md

3. **Tool Categories**:
   - Database Operations (11 tools)
   - Memory & Knowledge Graph (9 tools)
   - Model Generation (3 tools)

### 4.2 Database Connection Rules

1. **Connection Management**:
   - All 9 databases must be configured in `.env`
   - Use connection pooling via SQLAlchemy
   - Test connections on startup
   - Handle connection failures gracefully

2. **Query Execution**:
   - Always use parameterized queries
   - Implement query result caching (1 hour expiry)
   - Log all queries to memory system
   - Use LIMIT clauses for exploratory queries

3. **Schema Caching**:
   - Cache schema information for 24 hours
   - Invalidate cache on DDL operations
   - Store schemas in knowledge graph

### 4.3 Memory System Rules

1. **Knowledge Graph**:
   - Use NetworkX for graph structure
   - Persist to `~/.fastmcp/memory/`
   - Support entity types: database, table, query, workflow, model
   - Maintain relationships between entities

2. **Memory Tools Usage**:
   - `remember_query` - Store frequently used queries
   - `remember_workflow` - Document multi-step processes
   - `remember_schema` - Automatically cache table schemas
   - `search_memories` - Enable knowledge retrieval

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

### 5.2 Testing Requirements

1. **Before Marking Complete**:
   - Run `./venv/bin/python test_list_databases.py`
   - Run `./venv/bin/python test_mcp_tools.py`
   - Verify all 9 databases show correct table counts
   - Test at least 3 different tool categories

2. **Test Documentation**:
   - Document test results in commit messages
   - Update test scripts when adding new tools
   - Include example outputs in documentation

## 6. Deployment Standards

### 6.1 Virtual Environment

- Always use `venv/` for isolation
- Update `requirements.txt` when adding dependencies
- Test fresh installs with `./setup.sh`

### 6.2 Configuration

- Use `.env` for all sensitive configuration
- Never commit `.env` file
- Keep `.env.example` updated
- Use absolute paths in configuration

### 6.3 Service Management

- Systemd service: `Dolla-Bucks.service`
- Docker support via `docker-compose.yml`
- Always test both deployment methods

## 7. Version Control

### 7.1 Branch Strategy

- Main branch: `main`
- Feature branches: `feature/descriptive-name`
- Bugfix branches: `bugfix/issue-description`
- Always create PRs for review

### 7.2 Commit Standards

```
feat: Add new memory search capabilities

- Implemented fuzzy search for memory retrieval
- Added search_memories tool with pattern matching
- Updated documentation with usage examples
- Tested with all 9 databases

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
```

## 8. Tool Usage Patterns

### 8.1 Database Exploration

```python
# 1. List all databases
databases = await list_databases()

# 2. Get tables for a database
tables = await list_tables({"database": "spider_sync"})

# 3. Describe table schema
schema = await describe_table({
    "database": "spider_sync",
    "table": "customers"
})

# 4. Execute query with caching
result = await execute_query({
    "database": "spider_sync",
    "query": "SELECT * FROM customers LIMIT 10"
})
```

### 8.2 Memory Workflow

```python
# 1. Create workflow entity
await create_entity({
    "name": "customer_analysis",
    "entity_type": "workflow",
    "observations": ["Analyzes customer data"]
})

# 2. Remember useful query
await remember_query({
    "name": "active_customers",
    "database": "spider_sync",
    "query": "SELECT * FROM customers WHERE active = 1",
    "tags": ["customers", "active"]
})

# 3. Search memories
results = await search_memories({
    "pattern": "customer",
    "memory_type": "query"
})
```

## 9. Monitoring & Logging

### 9.1 Log Format

```text
[2025-01-11 12:00:00] [INFO] [tool:execute_query] Query executed successfully
Database: spider_sync
Query: SELECT COUNT(*) FROM customers
Result: 1234 rows
Cache: HIT
Duration: 0.05s
```

### 9.2 Health Checks

- Monitor all 9 database connections
- Check memory system disk usage
- Verify cache performance
- Log tool usage statistics

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

Last Updated: 2025-06-11T12:00:00 by Lil Claudy Flossy