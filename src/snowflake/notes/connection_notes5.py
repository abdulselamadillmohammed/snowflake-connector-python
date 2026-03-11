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

# The following three functions show three differnt patterns used in the
# Snowflake connector:

"""
1. Convenience wrapper methods (execute_string)
2. Streaming execution logic (execute_stream)
3. Dynamic method injection (__set_error_attributes)
"""

# 1. execute_string
"""
def execute_string(
    self,
    sql_text: str,
    remove_comments: bool = False,
    return_cursors: bool = True,
    cursor_class: SnowflakeCursor = SnowflakeCursor,
    **kwargs,
) -> Iterable[SnowflakeCursor]:

The purpose of this to execute multiple SQL statements contained in 
a string. 

Example input: 
    CREATE TABLE t(a int);
    INSERT INTO t VALUES(1);
    SELECT * FROM t;

Normal cursor.execute() runs one statement only

* This helper method allows:
conn.execute_string(sql_script)


// Step 1 - Convert string into a stream

stream = StringIO(sql_text)
StringIO turns the string into a file-like object

So instead of reading SQL from a file:
    file.sql
They simulate a file stream in memory

This allows reuse of the same logic used for file execution. 

---

# Step 2 - delegate to execute_stream 

stream_generator = self.execute_stream(
    stream,
    remove_comments=remove_comments,
    cursor_class=cursor_class,
    **kwargs
)

Instead of implementing logic twice, the function delegates to the 
straming executor.

This is a common desing pattern:

execute_string
        ↓
execute_stream
        ↓
cursor.execute

---

Step 3 - force execution
ret = list(stream_generator)

execute_stream returns a generator
* generators are lazy so you use list to for 
execution of every statement

---

Step 4 - Optionally return cursors

    ret = list(stream_generator)
    return ret if return_cursors else list()

if return_cursors=True, return the cursor objects used to execute 
each query. 

Example:
    [cursor1, cursor2, cursor3]
Each cursor contains metadata about the query results 

If false, the queries run but nothing is returned. 

"""

# 2. execute_stream
"""
This is the core implementation and it returns a generator 
of type snowflakeCursor

    def execute_stream(
        self,
        stream: StringIO,
        remove_comments: bool = False,
        cursor_class: SnowflakeCursor = SnowflakeCursor,
        **kwargs,
    ) -> Generator[SnowflakeCursor]:

This method executes SQL statemets coming from a stram. 
Example sources:
    - SQL files
    - pipeliens
    - in-memory text streams

1. Step 1 - split SQL statements

    split_statements_list = split_statements(
        stream, remove_comments=remove_comments
    )
    The function split_statements() parses SQL and separates 
    statements 

    Example input:
        SELECT 1;
        SELECT 2;

    Becomes:
        [
            ("SELECT 1", False),
            ("SELECT 2", False)
        ]
    Each entry is:
        (sql_statement, is_put_or_get)

2. Step 2 - filter empty statements
non_empty_statements = [e for e in split_statements_list is e[0]]

Removes blank entries. 

Example: 
";;;" would produce empty statements

Those get filtered out.

3. Step 3 - execute each SQL statement 
    for sql, is_put_or_get in non_empty_statements:
Loop over all SQL commands 

4. Step 4 - create a new cursor 
cur = self.cursor(cursor_class=cursor_class)
Each statement gets its own cursor object. 

This prevents result sets from interfering. 

5. Step 5 - execute query

cur.execute(sql, _is_put_get=is_put_or_get, **kwargs)
This sends the query to Snowflake 
_is_put_get indicates special commands:
    PUT
    GET

These are Snowflake-specific file transfer commands. 
The driver needs to treat them differently. 

6. Step 6 - yield the cursor
yield cur

This makes the function a generator 

meaning results are produced incrementally

Example usage:
for cursor in conn.execute_stream(stream):
    print(cursor.fetchall())

this avoids loading everything into memory

------

Key architecture idea:

execute_string
        ↓
execute_stream
        ↓
cursor.execute
        ↓
Snowflake REST API

Each layer adds a convenience abstractuib
"""

# 3. __set_error_attributes
"""
This is a different method that's purpose of to attach error-handling
methods dynamically to the connection object. 

Step 1 - itertate over error modules. 

for m in [
    method for method in dir(errors) if callable(getattr(errors, method))
]:

    this finds every callable function insdie the errors module:

    errors.DatabaseError
    errors.ProgrammingError
    errors.InterfaceError


2. Step 2 - clean up private names:


name = m if not m.startswith("_") else m[1:]

If a function starts with an "_", underscore is remvoed

Example:
_errors → errors

This is mostly cosmetic 
    
_errors → errors

Step 3 - attach to connection object:
setattr(self, name, getattr(errors, m))

this dynamically adds attributes to the connection

Equivilant to writing:
self.DatabaseError = errors.DatabaseError
self.ProgrammingError = errors.ProgrammingError
self.InterfaceError = errors.InterfaceError

So instead of manually writing them all, it generates them 
automatically

"""

"""
Why do this?

Because DB-API requires drivers to expose error classes.

Instead of manually duplicating definitions, the connector 
imports them dynamically.

This reduces boilerplate and keeps error handling centralized.

Summary:
"""

"""
Step 3 — attach to connection object
setattr(self, name, getattr(errors, m))

This dynamically adds attributes to the connection.

Equivalent to writing:

self.DatabaseError = errors.DatabaseError
self.ProgrammingError = errors.ProgrammingError
self.InterfaceError = errors.InterfaceError

But instead of manually writing them all, it generates them automatically.

Why do this?

Because DB-API requires drivers to expose error classes.

Instead of manually duplicating definitions, the connector imports them dynamically.

This reduces boilerplate and keeps error handling centralized.

Summary of the three methods
execute_string

Convenience method to run multiple SQL statements in a single string.

execute_stream

Core generator that parses and executes SQL statements one by one.

__set_error_attributes

Dynamically attaches error classes from the errors module to the connection object.

"""

# One deeper design insight
"""
high-level convenience methods
        ↓
generic streaming executor
        ↓
cursor execution
        ↓
REST API request

Each later reduces complexity for the user.
"""

# Preparing the networking layer
"""
This section is where the connector actually prepares the networking
layer and session configuration before authenticating with snowflake.

Two important things happen here:
    1. OCSP configuration for PrivateLink environments
    2. Creation of the REST client that will communicate with Snowflake
"""

# 1. setup_oscp_privatelink

"""
@staticmethod
def setup_ocsp_privatelink(app, hostname) -> None:

This function configures OCSP certificate validation when using Snowflake
PrivateLink

What OCSP is:
    - OCSP = Online Certificate Status Protocol 

When a TLS certificate is used, the client must verify that the 
certificate has not been revoked.

Normally this requires contacting the certificate authority.
Snowflake instead provides an OCSP response cache server. 

1. Normalize hostname
hostname = hostname.lower()
    - Ensures consistent hostname formatting. 

2. Acquire lock
SnowflakeConnection.OCSP_ENV_LOCK.acquire()

This lock protects access to environemnt variables

Why?
    - Because environment variables are global to the Python process, 
    and multiple connections could modify them simultaneously. 
The lock prevents race conditions. 

3. Construct OCSP cache URL
ocsp_cache_server = f"http://ocsp.{hostname}/ocsp_response_cache.json"

Example:
    hostname = abc123.privatelink.snowflakecomputing.com
    http://ocsp.abc123.privatelink.snowflakecomputing.com/ocsp_response_cache.json

This is where Snowflake stores cached OCSP responses. 

Step 4 - set environment variable
os.environ["SF_OCSP_RESPONSE_CACHE_SERVER_URL"] = ocsp_cache_server
Use this OCSP cache server for certificate validation instead of 
contacting public certificate authorities

Step 5 - logging 
logger.debug("OCSP Cache Server is updated: %s", ocsp_cache_server)
    Records the new OCSP server location. 

Step 6 - release lock
SnowflakeConnection.OCSP_ENV_LOCK.release() // this unlocks 
the environment variable modification.

"""

#     def __open_connection(self):
"""
This function intializes everything needed for the connection
before authentication occurs. 

The high-level responsibilites are: 
    - initialize converters
    - create REST client 
    - configure OCSP
    - Configure session parameters

3. Creation of the converter
    self.converter = self._converter_class(
        use_numpy=self._numpy,
        support_negative_year=self._support_negative_year
    ) 

This converter handles data type conversions between Snowflake and 
Python; Example:
| Snowflake | Python        |
| --------- | ------------- |
| NUMBER    | int / decimal |
| TIMESTAMP | datetime      |
| ARRAY     | list          |
| VARIANT   | dict          |

Options : 
use_numpy=True
* Means numeric columns can be returned as NumPy arrays.
"""

# 4. Create REST client 
"""
self._rest = SnowflakeRestful(

This object is the core networking component of the connector. 

It is responsible for:
    sending SQL queries;
    authentication;
    handling retries;
    handling HTTP sessions;
    receiving results

Parameters:
    host=self.host
    port=self.port
    protocol=self._protocol

Example:
    https://abc123.snowflakecomputing.com:443

Important parameter
session_manager = self._session_manager

Earlier in connect() we saw:
    SessionManagerFactory.get_manager(...)

This object manages:
    HTTP connection pooling
    session reuse
    retry logic
    
So multiple Snowflake requests share the same HTTP infrasture. 

Logging:
    logger.debug("REST API object was created: %s:%s", self.host, self.port)
Confirms the REST layer is ready. 

5. Check custom OCSP cache
if "SF_OCSP_RESPONSE_CACHE_SERVER_URL" in os.environ:
    this is just a chekc is the user has manually set a custom 
    OCSP cache server, the connector logs it. 
    This allows advanced users to override default certificate 
    validation behaviour. 

6. Detect PrivateLink environment 
if ".privatelink.snowflakecomputing." in self.host.lower():

* PrivateLink is Snowflake's private AWS netowkring option. 

Instead of public internet:
    client → internet → snowflake
traffic flows through private AWS endpoints

If PrivateLink is detected, the connector runs:
    setup_oscp_privatelink(...)
So certificate validation happens within the private network

    if "SF_OCSP_RESPONSE_CACHE_SERVER_URL" in os.environ:
        logger.debug(
            "Custom OCSP Cache Server URL found in environment - %s",
            os.environ["SF_OCSP_RESPONSE_CACHE_SERVER_URL"],
        )

"""

# Continuation: ...

"""

7. Remove custom OCSP is not PrivateLink
else:
    if "SF_OCSP_RESPONSE_CACHE_SERVER_URL" in os.environ:
        del os.environ["SF_OCSP_RESPONSE_CACHE_SERVER_URL"]

If not using PrivateLink, the connector removes the custom OCSP
setting. 

This ensures the driver falls back to normal certificate validation
behaviour.

---

8. Initialize session parameters
if self._session_parameters is None:
    self._session_parameters = {}

This dictionary holds Snowflake session configuration settings. 

    AUTOCOMMIT
    TIMEZONE
    QUERY_TAG
    CLIENT_SESSION_KEEP_ALIVE

---

9. Configure autocommit
if self._autocommit is not None:
    self._session_parameters[PARAMETER_AUTOCOMMIT] = self._autocommit

if autocommit was specified in the connection settings:
    connect(autocommit=False)
    The connector adds it to session parameters.
    Later during authentication these parameters are sent to Snowflake

---

10. Configure timezone
if self._autocommit is not None:
    self._session_parameters[PARAMETER_AUTOCOMMIT] = self._autocommit

Example:
    connect(timezone="America/Toronto")

The connector stores the setting so Snowflake can apply it to the 
session. 

---

High-level architecture of this section
__open_connection()
    ↓
create data converter
    ↓
create REST client
    ↓
configure OCSP validation
    ↓
configure session parameters
    ↓
authenticate with Snowflake (happens later)

Key takeaway:
    The snowflake connector does not open a socket or authenticate 
    immediatelt here. Instead this function prepares the networking
    and session environment so the authentication step can run 
    safely afterward. 

"""

## Stopped at line 1406 or something
#         if self._validate_default_parameters:
