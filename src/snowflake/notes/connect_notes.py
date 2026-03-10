#    def connect(self, **kwargs) -> None:
 
"""
The purpose of this function is to establish a connection to Snowflake.

It is reponsisble for accepting parameters,
Configuring the connection object,
Building HTTP networking infrastructure,
Configuring certificate revocation checks, 
Optionally running connectivity diagnostics,
Establishing the authenticated REST session,
Registering the connection globally 

* This is basically sets up everything before SQL queries can be sent

---

logger.debug("connect")

If logging is enabled at the DEBUG level, this will record that
the connection process has begun.
    - Useful during connection failure debugging

    
---
Check performed if kwargs is has parameters or it doesn't
* Notation seems to be that if the length is quantifiable 
then you will check it 

if len(kwargs) > 0:
    self.__config(**kwargs)

connect(
    user="bob",
    password="secret",
    account="abc123",
    warehouse="COMPUTE_WH"
)

The __config is a function within the object so im not sure why 
they're calling self instead of calling __config:

    def __config(self, **kwargs):


* The role of the config function is to validate 
the kwargs, store them in internal attirbutes, 
perform typechecking, resolve hostname from account,
sets authentication mode, loads OAuth tokens or 
keypair files if needed.

kwargs["user"] → self._user
kwargs["account"] → self._account


NOTE: The reason you have to call it with self ie 
self.__config is because it is not a function who's 
role is just to output a computation but instead
is responsible for the instance of the class

Yes. In normal Python class code, if you want to call another 
instance method from inside a method, you should call it as:

self.method(...)

because Python does not automatically search the object for 
attributes when resolving names inside a function. It only 
searches local variables, enclosing scopes, globals, and 
builtins. Using self.method performs attribute lookup on the 
instance, which finds the method on the class and binds it 
to the object.
-------

self._crl_config: CRLConfig = CRLConfig.from_connection(self)

CRL = Certificate Revocation List

TLS certificates can be revoked if compromised. This configuration
dertermines: 
    1. Whether revocation checking is enabled 
    2. How CRL files are cached 
    3. Timeouts for CLR downloads 
    4. Cleanup of CRL cache files

* Note it is intially set to None but only intialize it when you
establish a connection at which point you rely on the 
module it comes from 

CRLConfig.from_connection(self) reads connectiin parameters such as:
    cert_revocation_check_mode
    crl_cache_dir 
    enable_crl_cache 

and constructs a security configuration object 

So now the connection knows how to validate 
TLS certificates securely. 

"""

# Normalizing no_proxy

"""
    no_proxy_csv_str = (
        ",".join(str(x) for x in self.no_proxy)
        if (
            self.no_proxy is not None
            and isinstance(self.no_proxy, Iterable)
            and not isinstance(self.no_proxy, (str, bytes))
        )
        else self.no_proxy
    )

The problem at hand: 
    
no_proxy can be given as: 
    ["localhost", "127.0.0.1"]

    or:

    "localhost,127.0.0.1"

BUT! the HTTP library expects a comma seperated string

So the code converts:
    ["a","b","c"]

into:
"a,b,c" 


* And of course leaves the existing strings unchanges.
This normalization ensures consistent proxy configuration.
"""

# 6. Build HTTP configuration:
"""

self._http_config = HttpConfig(
    adapter_factory=ProxySupportAdapterFactory(),
    use_pooling=(not self.disable_request_pooling),
    proxy_host=self.proxy_host,
    proxy_port=self.proxy_port,
    proxy_user=self.proxy_user,
    proxy_password=self.proxy_password,
    no_proxy=no_proxy_csv_str,
)

This section is responsible for constructing the network layer
configuration which is used by Snowflake REST client. 

Key parts:

ProxySupportAdapterFactory()

- It creates HTTP adapters that understand:
    - Corporate proxies
    - proxy authentication
    - TLS handling

use_pooling 
    - This performs connection pooling which improves performance by 
    reusing TCP connections instead of reconnecting for every request.

    use_pooling = True 
    means that HTTP requests reuse sockets

The following parameters come from connection parameters and 
are used to configure the proxy settings for the HTTP client:

proxy_host
proxy_port
proxy_user
proxy_password

So after this step we now have a fully 
configured HTTP networking layer.

"""

# Session manager

"""
 self._session_manager = SessionManagerFactory.get_manager(self._http_config)

 The session manager is responsible for 
    managing HTTP sessions
    maintaing connection pools
    Thread safety and 
    retries 

* Instead of creating raw request.Session objects everywhere, the 
connector uses a central session manager abstraction

So this line creates the object responsoible for making all HTTP 
requests to snowflake, and it is configured with the HTTP 
settings we just built.

"""

# 8. Connection diagnostic mode 

"""
Now we reach a special debugging feature:

    if self.enable_connection_diag:

* This is a feature which essentially acts as Snowflake's 
connectivity debugging tool. 

It runs diagnostic tests to identify issues like:
    - firewall blocking 
    - DNS failures 
    - Proxy issues 
    - TLS problems
    - Network routing problems     

"""

# Connection diagnostics
"""
First you create and exceptions dict: 

exceptions_dict = {}

from .connection_diagnostic import ConnectionDiagnostic


connection_diag = ConnectionDiagnostic(
    account=self.account,
    host=self.host,
    connection_diag_log_path=self.connection_diag_log_path,
    connection_diag_allowlist_path=(
        self.connection_diag_allowlist_path
        if self.connection_diag_allowlist_path is not None
        else self.connection_diag_whitelist_path
    ),
    proxy_host=self.proxy_host,
    proxy_port=self.proxy_port,
    proxy_user=self.proxy_user,
    proxy_password=self.proxy_password,
    session_manager=self._session_manager.clone(use_pooling=False),
)

* This object runs tests against the network configuration. 

Notice:
    session_manager.clone(use_pooling=False)

* Pooling is disabled because diagnostics should run clean 
isolated network requests

"""

# The key operation being performed:

"""
10. The first phase requires that you ran a test phase:
connection_diag.run_test()
    - The idea is that since the connection_diag is a 
    diagnostic object you're able to take advantage of that
    - It runs a series of tests to check connectivity to Snowflake

    It checks for :
    - DNS resolution
    - HTTPS reachability
    - Proxy routing
    - certificate validation

__open_connection()

"""

# 11. Attempt real connection
"""
self.__open_connection()

This performs the actual connection to Snowflake ie the login process.

inside it, you create a REST client, set session parameters
select authenticator, send login requests, and obtain session tokens. 

This is where authentication happens. 
"""

# 12. Create cursor for testing 
"""

connection_diag.cursor = self.cursor()
The diagnostic object gets a cursor so it can test queries 

For example: 
SELECT 1
to confirm query execution works. 

"""

# 12. Capture connection test errors
"""
except Exception:
    eceptions_dict["connection_diag"] = traceback.format_exc()

If any exceptions occur during diagnostics, they are captured and 
stored in the exceptions_dict for later analysis.
This allows the diagnostic report to show detailed error 
information about what went wrong during connection testing.
"""

# 14. Run post-connection tests
"""
connection_diag.run_post_tests()

This is likely responsible for running tests like:
    - Query execution
    - Session validation
    - Stage access
    - Credential caching 

"""

# 15. Always generate report 
"""
connection_diag.generate_report()

This creates a diagnostic report summarizing the 
results of all tests, which contiains:
    - Connection results
    - Failures
    - Stack traces
    - Environment configuration

If any tests failed:
    - raise Exception(str(exceptions_dict))

And as such the connection fails with diagnostic information

"""

# 16. Normal connection path

"""
If diagnostics are disabled:
    else:
        self.__open_connection()

The connector simply performs the login handshake which is 
typically the normal path used by almost all users...

because enable_connection_diag is false by default:
    "enable_connection_diag": (False, bool),  

"""

# 17. Register connection globally
"""
_connections_registry.add_connection(self)
* This adds the connection to a global registry of active connections

The registry tracks open connections using a Weakset. 
The reason being that the connector wants to:
    1. detect when all connections are closed
    2. Stop CRL background cleanup threads
    3. Manage global resources

Example internal structure:
_connections = WeakSet([
   conn1,
   conn2,
   conn3
])  
When a connection closes, it is removed from the registry.

if the set becomes empty:
    CRLCacheFactory.stop_periodic_cleanup() will be triggered

This prevents background threads from lingering.


"""

# Conceptual architecture of connect()

"""
connect()
│
├── 1. Parameter configuration
│       __config()
│
├── 2. Security configuration
│       CRLConfig.from_connection()
│
├── 3. Networking setup
│       HttpConfig
│       SessionManager
│
├── 4. Connection establishment
│       __open_connection()
│
└── 5. Global registration
        _connections_registry.add_connection()

"""

# The critical call chain
"""
connect()
    │
    ├─ __config()
    │
    ├─ CRLConfig.from_connection()
    │
    ├─ HttpConfig(...)
    │
    ├─ SessionManagerFactory.get_manager()
    │
    ├─ __open_connection()
    │        │
    │        ├─ create REST client
    │        ├─ configure session parameters
    │        ├─ choose authenticator
    │        ├─ authenticate_with_retry()
    │        └─ start heartbeat thread
    │
    └─ register connection globally
"""

# The single sentence summary
"""
connect() orchestrates configuration, security validation, HTTP session
creation, and authentication to establish a connection to Snowflake, 
REST session and registers the connection globally
"""

# close(self, mode: bool) -> None:

"""
The closse() method is basically the shutdown procedure for the
Snowflake connection object. It carefully tears down everything 
associated with the connection: background threads, telemetry, 
sessions on the server, caches and the internal state. 

Walkthough:

1. Function signature:
    def close(self, retry: bool = True) -> None:

    purpose:    
        Gracefully terminate the Snowflake session and clean up
        client resources

* The retry parameter controls whether network operations (like 
deleting the session) should retry if they fail. 
"""

# 2. Remove the atexit hook

"""
atext.unregister(self._close_at_exit)

earlier in the connection lifecycle this was registered:

atext.register(self._close_at_exit)

meaning that if the python program exits without explciity closing
the connection, the connector autoatically runs _close at exit()

Now the close() is being called manually, the code unregisters
that handler so it doesn't run twice. 

So this prevents duplciate cleanup when the interpreter shuts down. 

"""

# 3. Remove the connection from the global registry
"""
_connections_registry.remove_connection(self)

* Earlier we saw that the connection was added here when connecting.

The registry tracks all active Snowflake connections.

Removing it means:
    - this connection is no longer considered active

* This also helps with things like stopping global CRL cache 
clean up threads when no connections remain. 

"""

# 4. Check if REST client still exists
"""
    if not self.rest:
        logger.debug("Rest object has been destroyed, cannot close session")
        return
    
    self.rest is the HTTP client used to communicate with Snowflake.

    If it is already None or destroyed, there is nothing to close. 

    So the function simply exits. 

"""

# 5. Cancel the heartbeat thread
"""
self._cancel_heartbeat()

Snowflake connections may run a heartbeat thread. 

The purpose of heartbear is to keep alive the session by 
peroidically pinging the server. 

Without canceling the heartbeat, the program mught hang during 
shutdown because the thread is still running and trying to access
resources that are being cleaned up.

So this step stops the background thread
"""

# 6. Close telemetry first
"""
if self._telemetry_enabled:
    self._telemetry.close(retry=retry)

Telemetry collects usage data such as:  
    - Performance metrics
    - Feature usage
    - Errors

It sends this data back to Snowflake.
The imporant detail is the comment: 
    # Close telemetry first, since it needs rest to send remaining data

Telemetry relies on the REST client to send its final data.
If we closed the REST client first, telemetry would lose the ability to
send its final data.

"""

# 7. Decide whether to delete the Snowflake session
"""
if not self._server_session_keep_alive:

* This parameter determines whether the session should persist on the
server 

Two possible behaviors:

Case 1 - Normal behaviour (default):
    if self._all_async_queries_finished():
    logger.debug(
        "No async queries seem to be running, deleting session"
    )
    self.rest.delete_session(retry=retry)

    This logs the client out and releases resources. 

Case 2 - Async querires still running:
    If async queiries exist:        
       "There are X async queries still running, not deleting session"
    
    Why? 
        - Because deleting the session would kill the running 
        queries. So the connector leaves the session alive until 
        those queries finsih. 

Case 3 - sever_session_keep_alive == True

else:
    logger.info(...)

If this flag is enabled, the connector never deletes the session.
The session continues running on Snowflake even after the client 
disconnects. The warning explains:  
    - Queries may continue running and consume Snowflake credits
    - Users must canvel them manually

"""

# 8. Close the REST client 
"""
self.rest.close()
self._rest = None

This shuts down the HTTP layer. 

Likely effects:
    - Close HTTP connections
    - Release connection pool resources
    - Stop background networking tasks

Setting _rest = None ensures that the connection object cannot 
accidentally reuse the closed REST client after this point.
"""

# 9. Clear the query context cache
"""
if self._query_context_cache:
    self._query_context_cache.clear_cache()

Snowflake caches query context information for permance
This clears that cached data to free memory

"""

# 10. Clear stored messages 
"""
del self._messages[:]

messages is typicaly a list of warning or status messages collected
during the connection lifetime. 

This line clears the list in-place. 

Equivalent to:
    self._messages.clear()

But using slice deletion.
    
"""

# 11 and 12: Final message message and Error handling
"""
logger.debug("Session is closed")

-   Indicates that shutdown finished successfully.

Error handling
    except Exception as e:
        logger.debug(
            "Exception encountered in closing connection. ignoring...: %s", e
        )

    The connector intentionally supresses errors during shutdown.
    Reason:
        Failing during clean up should not crash the user's program. 
    So errors are logged but ignored. 

"""

# Execution flow summary
"""
close()
│
├─ unregister atexit cleanup
├─ remove connection from registry
├─ cancel heartbeat thread
├─ flush telemetry
├─ optionally delete server session
├─ close REST client
├─ clear caches
├─ clear messages
└─ finish
"""

# Key desing ideas
"""
The function protects against several real-world issues:

Thread leaks:   
    - Heartbeat threads must be stopped. 

Session leaks:
    - Sessions must be deleted to avoid unused Snowflake sessions. 

Credit consumption:
    - Async queries might still be running. 

Telemetry loss:
    - Telemetry must be flushed before closing REST client.

Shutdown crahes:    
    - Errors during cleanup should not crash the program. 

"""

# One sentence summary
"""
close() safely shuts down the Snowflake connection by stopping background threads, 
flushing telemetry, optionally deleting the server session, closing the REST client, 
and cleaning up internal state while suppressing errors during shutdown.

"""

#     def is_closed(self) -> bool:
"""
    def is_closed(self) -> bool:
        "Checks whether the connection has been closed."
        return self.rest is None

What it does:
    This function acts a boolean check if the connection 
    is closed

The connector uses a simple rule:
    connection is closed ⇔ REST client does not exist

Recall from close() earlier:
    self.rest.close()
    self._rest = None  

So after closing the REST client pointer becomes None. 

| State             | `self.rest` | `is_closed()` |
| ----------------- | ----------- | ------------- |
| connection open   | REST object | False         |
| connection closed | None        | True          |

* The REST client is the communication channel to Snowflake. 
If it does not exist, the connector literally connot send 
queries. 

So the connector uses that as the canonical indicator of connection
state

"""

# 2. autocommit()
"""
def autocommit(self, mode) -> None:

Purpose: Set whether every SQL statement commits automatically. 


| Mode             | Behavior                       |
| ---------------- | ------------------------------ |
| autocommit=True  | each query commits immediately |
| autocommit=False | user must call `commit()`      |

Snowflake defaults to autocommit=True. 

"""

# 3. First check - connection must exist
"""
if not self.rest:

Equivalent to:
    if connection is closed

at which point it will call an error:
    Error.errorhandler_wrapper(...)

This constructs a database error. 

Error details passed:
    msg: "Connection is closed"
    errno: ER_CONNECTION_IS_CLOSED
    sqlstate: SQLSTATE_CONNECTION_NOT_EXISTS

This is part of the DB-API 2.0 error system.

Meaning:
    You attempted an operation on a closed connection.
"""

# Second check - parameter validation
"""
if not isinstance(mode, bool):
    Error.errorhandler_wrapper(
        self,
        None,
        ProgrammingError,
        {
            "msg": f"Invalid parameter: {mode}",
            "errno": ER_INVALID_VALUE,
        },
    )

The function only accepts a boolean:
True
False

If you pass something like:
"true"
1
None

The connector throws a ProgrammingError. 

Error payload:
    msg: "Invalid parameter"
    errno: ER_INVALID_VALUE

* So this is stirct type validation
    
"""

# Actually changing the autocommit mode
"""
self.cursor().execute(f"ALTER SESSION SET autocommit={mode}")

Important design detail:
    - The connector does not change a local variable 

instead it sends SQL to Snowflake

ALTER SESSION SET autocommit=True

or

ALTER SESSION SET autocommit=False

So autocommit is controlled sever-side in the session configuration. 

Flow:
    create cursor
    → execute SQL command
    → Snowflake updates session parameter
"""

# 6. Why a cursor is created
"""

self.cursor()

Because SQL must be executed through a cursor object. 

Typical DB-API pattern: 
    connection → cursor → execute SQL
So this internally does something like:
    cursor = SnowflakeCursor(self)
    cursor.execute(...)
"""

# 7. Error handling
"""
except Error as e:

If snowflake rejects the command, the connector checks: 

    if e.sqlstate == SQLSTATE_FEATURE_NOT_SUPPORTED

Meaning:
    The server does not support the atuocommit feature
    In that case, the connector does not crash but instead
    logs a debug message:

    - Autocommit feature is not enabled for this connection
    And simply ignores the request

"""