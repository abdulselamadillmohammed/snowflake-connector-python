"""
The following three methods are part of the DB-API interface layer
of the Snowflake connection. They expose the standard database 
operations (commit, rollback, cursor) thay Python database drivers
are expected to support
"""

#     def commit(self) -> None:
"""
def commit(self) -> None:
    "Commits the current transaction."
    self.cursor().execute("COMMIT")

What it does: 
    This commits the current transaction. 

Instead of implementing commit logic locally, the connector
simply sends SQL to Snowflake

Execution flow:
    commit()
    ↓
    create cursor
    ↓
    execute SQL: COMMIT
    ↓
    Snowflake commits transaction

So this method is basically a wrapper around a SQL statement

Important detail:
    if autocommit = True, transactions are commited automatically
    after each statement so calling commit has no effect
"""

#     def rollback(self) -> None:
"""
    def rollback(self) -> None:
        "Rolls back the current transaction."
        self.cursor().execute("ROLLBACK")

This is the exact same pattern as commit().

rollback()
  ↓
create cursor
  ↓
execute SQL: ROLLBACK
  ↓
Snowflake discards current transaction

Again the connector simply sends the SQL command to the server
"""

# 3. Cursor

"""
def cursor(self, cursor_class: type[CursorCls] = SnowflakeCursor) -> CursorCls:

The purpose of this function is to create a cursor object which is 
responsible for executing SQL statements. 

In python database APIs, the hierarchy usually looks like:

Connection
   ↓
Cursor
   ↓
Execute SQL
   ↓
Fetch results

The connection manages the session while cursors execute queries 

* logger.debug("cursor")
If debug logging is enabled, this recods that a new cursor is 
being created. 
    - Useful for debugging query execution. 

"""

# 5. Connection state check
"""
if not self.rest:
* This checks if the connection is closed. 
ie we already should have had it set to None. So if the 
REST client does not exist, the connection cannot communi
cate with Snowflake

In that case, the driver rasises a databse error using:
    Error.errorhandler_wrapper(...)
    which includes:

    msg: "Connection is closed"
    errno: ER_CONNECTION_IS_CLOSED
    sqlstate: SQLSTATE_CONNECTION_NOT_EXISTS

This follows the Python DB-API error conventions
    
"""

# 6. Cursor creation
"""
return cursor_class(self)

This constructs a cursor object and passes the connection instance into it. 

So internally it does something like:   
    - Cursor = SnowflakeCursor(connection=self)

* The cursor then stores a reference to the connection so it can:
    - Send queries through the REST client 
    - Access session configuration
    - Track query IDs and results
"""

# 7. Why cursor_class is a parameter
"""
The method signature allows specifying a differnt cursor implementation:
    cursor_class: type[CursorCls] = SnowflakeCursor

    Example usage:  
    conn.cursor(MyCustomCursor)

This enables:   
    - Custom cursor behaviour. 
    - Alternative result handling
    - Specialized query processing

* But normally the defualt SnowflakeCursor is used.

"""

# 8. Why a new cursor per statement
"""
The docstring says:
    Each statement wil be executed ina new cursor object. 

This is intentional.
* Many database drivers treat cursors as a single query objects 
that hold:
    - Query metadata
    - Result buffers
    - Fetch state
    - Error information

Creating a new cursor prevents state conflicts between queries. 
"""

# 9. How these methods work together

"""
Typical usage:

conn = connect()

cur = conn.cursor()
cur.execute("SELECT * FROM table")

conn.commit()

This internally becomes:
cursor() → SnowflakeCursor(connection)
execute() → REST API call to Snowflake
commit() → SQL COMMIT command

"""

# 10. One design pattern you mught notice
"""
The conncetor avoids implementing complex logic locally and 
instead relies on SQL commands sent to the server. 

Examples:

commit() → COMMIT
rollback() → ROLLBACK
autocommit() → ALTER SESSION SET autocommit

So the driver acts mostly as a client wrapper around Snowflake's 
SQL interface. 
"""

# Summary
"""
commit() → COMMIT
rollback() → ROLLBACK
autocommit() → ALTER SESSION SET autocommit

The cursor holds the execution state, while the connection manages
the session.
"""

"""
Snowflake engineers get the structure for these wrappers primarily 
from PEP 249 (Python DB-API 2.0), which standardizes how Python 
database drivers must behave. The connector then maps those standard 
methods to Snowflake SQL commands and REST API calls.
"""