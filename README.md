# SQL MCP Server

An MCP (Model Context Protocol) server for SQL operations that integrates with VS Code.

## Features

- **SQL Tools**: Execute queries, list tables, get schema information
- **MCP Compliant**: Works seamlessly with VS Code's Copilot and MCP integrations
- **Async/Await**: Full async implementation for non-blocking operations

## Setup

1. Install dependencies:
```bash
pip install -e .
```

2. Run the server:
```bash
python server.py
```

## Available Tools

- **execute_query**: Execute a SQL query and return results
- **list_tables**: List all available tables in the database
- **get_schema**: Get the schema information for a specific table

## VS Code Integration

Configure in your VS Code settings or `claude_desktop_config.json`:

```json
{
  "mcp-servers": {
    "sql": {
      "command": "python",
      "args": ["c:\\dev\\sql-mcp\\server.py"]
    }
  }
}
```

## Architecture

- **server.py**: MCP server implementation with tool handlers
- **pyproject.toml**: Project configuration and dependencies
