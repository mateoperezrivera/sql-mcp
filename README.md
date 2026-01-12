# SQL MCP Server

An MCP (Model Context Protocol) server for SQL operations with **Streamable HTTP** transport. Connects to Azure SQL using token-based authentication with `az login` credentials.

## Features

- 🌐 **Streamable HTTP Transport**: Uses FastMCP with SSE for real streaming
- 🔐 **Azure Authentication**: Uses `DefaultAzureCredential` (respects `az login` cache)
- 🔄 **Stateless**: Each request is independent for better scalability
- 📊 **SQL Tools**: Execute queries, list tables, inspect schemas
- ⚡ **Async/Await**: Full async implementation

## Quick Start

### 1. Setup

```bash
# Install dependencies
uv sync

# Configure your database
cp .env.example .env  # Or create your own
# Edit .env with your Azure SQL details
```

### 2. Environment Variables

Create a `.env` file:
```env
DB_SERVER=yourserver.database.windows.net
DB_DATABASE=yourdatabase
DB_DRIVER={ODBC Driver 18 for SQL Server}
```

### 3. Azure Authentication

Make sure you're logged in:
```bash
az login
```

The server will use your cached Azure credentials automatically.

### 4. Run the Server

```bash
python server.py --port 8000
```

The server will start on `http://localhost:8000`

## VS Code Configuration

Configure in your VS Code settings (`mcp.json` or Claude Desktop config):

```json
{
  "servers": {
    "sql-mcp": {
      "url": "http://localhost:8000",
      "type": "http"
    }
  }
}
```

### With Authentication (Optional)

If you add API key or Bearer token auth to the server:

```json
{
  "servers": {
    "sql-mcp": {
      "url": "http://localhost:8000",
      "type": "http",
      "headers": {
        "Authorization": "Bearer YOUR_TOKEN_HERE",
        "X-API-Key": "your-api-key"
      }
    }
  }
}
```

Or use environment variables:

```json
{
  "servers": {
    "sql-mcp": {
      "url": "http://localhost:8000",
      "type": "http",
      "env": {
        "API_KEY": "${API_KEY}"
      }
    }
  }
}
```

## Available Tools

### 1. `list_tables`
List all tables in the current database
- **Input**: None
- **Output**: Table names

### 2. `get_schema`
Get column information for a specific table
- **Input**: `table_name` (string)
- **Output**: Column names, data types, nullable info

### 3. `execute_query`
Execute a SQL query and return results
- **Input**: `query` (string) - SQL query
- **Output**: Query results formatted as text

## Examples

```sql
-- List tables with schema
SELECT TABLE_SCHEMA, TABLE_NAME FROM INFORMATION_SCHEMA.TABLES

-- Get customer data
SELECT TOP 5 CustomerID, FirstName, LastName FROM SalesLT.Customer

-- Get schema for a table
SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME = 'Customer'
```

## Project Structure

```
sql-mcp/
├── server.py          # MCP server with FastMCP
├── pyproject.toml     # Dependencies and project config
├── .env               # Environment variables (git ignored)
├── .env.example       # Example env file
├── .gitignore         # Git ignore rules
└── README.md          # This file
```

## Authentication Details

The server uses **token-based authentication** with Azure SQL:

1. Gets token from `DefaultAzureCredential` (uses `az login` cache)
2. Converts token to ODBC format using `struct`
3. Passes token via `SQL_COPT_SS_ACCESS_TOKEN` attribute
4. Respects Azure firewall rules

## Prerequisites

- Python 3.9+
- `uv` package manager
- Azure CLI (`az login` configured)
- ODBC Driver 18 for SQL Server
- Access to an Azure SQL Server database

