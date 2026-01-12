import argparse
import struct
import os
import pyodbc
import logging
from dotenv import load_dotenv
from azure.identity import DefaultAzureCredential
from mcp.server.fastmcp import FastMCP

# Load environment variables from .env
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# SQL token attribute constant
SQL_COPT_SS_ACCESS_TOKEN = 1256
SCOPE = "https://database.windows.net/.default"

# Initialize FastMCP server with streamable HTTP
mcp = FastMCP(name="sql-mcp", json_response=True, stateless_http=True)

# Database connection configuration from environment variables
DB_CONFIG = {
    "server": os.getenv("DB_SERVER", "localhost"),
    "database": os.getenv("DB_DATABASE", "master"),
    "driver": os.getenv("DB_DRIVER", "{ODBC Driver 18 for SQL Server}")
}

# Global connection object
conn = None

# Read-only validation
ALLOWED_KEYWORDS = ['SELECT', 'WITH', 'DECLARE']
FORBIDDEN_KEYWORDS = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'TRUNCATE', 'EXEC']


def is_readonly_query(query: str) -> tuple[bool, str]:
    """Validate that query is read-only (SELECT only)"""
    query_upper = query.strip().upper()
    
    # Remove comments and leading whitespace
    lines = [line.split('--')[0].strip() for line in query_upper.split('\n')]
    query_clean = ' '.join(lines).strip()
    
    if not query_clean:
        return False, "Empty query"
    
    # Check if starts with allowed keyword
    starts_with_allowed = any(query_clean.startswith(k) for k in ALLOWED_KEYWORDS)
    if not starts_with_allowed:
        return False, f"Query must start with one of: {', '.join(ALLOWED_KEYWORDS)}"
    
    # Check for forbidden keywords
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in query_upper:
            return False, f"Query contains forbidden operation: {keyword}"
    
    return True, "OK"


def get_connection():
    """Get or create database connection using Azure token"""
    try:
        logger.info(f"Connecting to {DB_CONFIG['server']}/{DB_CONFIG['database']} with token")
        
        # Build connection string
        conn_str = (
            f"Driver={DB_CONFIG['driver']};"
            f"Server=tcp:{DB_CONFIG['server']},1433;"
            f"Database={DB_CONFIG['database']};"
            "Encrypt=yes;"
            "TrustServerCertificate=no;"
            "Connection Timeout=30;"
        )
        
        # Get token from DefaultAzureCredential (uses az login cache + other auth methods)
        credential = DefaultAzureCredential(exclude_interactive_browser_credential=False)
        token = credential.get_token(SCOPE).token
        logger.info(f"Token acquired (length: {len(token)})")
        
        # Convert token to the format ODBC expects
        token_bytes = token.encode("utf-16-le")
        token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
        
        # Connect with token attribute
        conn = pyodbc.connect(conn_str, attrs_before={SQL_COPT_SS_ACCESS_TOKEN: token_struct})
        logger.info("Connected successfully with token")
        return conn
    except Exception as e:
        logger.error(f"Connection error: {str(e)}", exc_info=True)
        raise Exception(f"Connection error: {str(e)}")


def execute_sql(query: str) -> str:
    """Execute SQL query and return results"""
    try:
        logger.info(f"Executing query: {query[:100]}...")
        db = get_connection()
        cursor = db.cursor()
        cursor.execute(query)
        
        # Fetch results
        rows = cursor.fetchall()
        logger.info(f"Query returned {len(rows)} rows")
        
        if not rows:
            return "Query executed. No results returned."
        
        # Format results
        result = []
        # Add column names
        column_names = [desc[0] for desc in cursor.description]
        result.append(" | ".join(column_names))
        result.append("-" * 50)
        
        # Add rows
        for row in rows:
            result.append(" | ".join(str(val) for val in row))
        
        cursor.close()
        return "\n".join(result)
    
    except Exception as e:
        logger.error(f"Query execution error: {str(e)}", exc_info=True)
        return f"Error: {str(e)}"


@mcp.tool()
async def execute_query(query: str) -> str:
    """Execute a READ-ONLY SQL query (SELECT only).
    
    Args:
        query: The SQL query to execute (must be SELECT)
    """
    # Validate query is read-only
    is_valid, message = is_readonly_query(query)
    if not is_valid:
        return f"Error: {message}"
    
    return execute_sql(query)


@mcp.tool()
async def list_tables() -> str:
    """List all tables in the current database."""
    query = """
    SELECT TABLE_NAME 
    FROM INFORMATION_SCHEMA.TABLES 
    WHERE TABLE_TYPE = 'BASE TABLE'
    """
    return execute_sql(query)


@mcp.tool()
async def get_schema(table_name: str) -> str:
    """Get column information for a specific table.
    
    Args:
        table_name: Name of the table
    """
    query = f"""
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = '{table_name}'
    """
    return execute_sql(query)


if __name__ == "__main__":
    import uvicorn
    
    parser = argparse.ArgumentParser(description="Run SQL MCP Streamable HTTP server")
    parser.add_argument("--port", type=int, default=8000, help="Localhost port to listen on")
    args = parser.parse_args()
    
    print("SQL MCP Server with Streamable HTTP transport")
    print(f"Running on http://0.0.0.0:{args.port}")
    print(f"Database: {DB_CONFIG['server']}/{DB_CONFIG['database']}")
    
    # Start the server with Streamable HTTP transport
    uvicorn.run(mcp.streamable_http_app, host="0.0.0.0", port=args.port)
