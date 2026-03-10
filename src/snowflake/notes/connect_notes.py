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

# `The single sentence summary
"""
connect() orchestrates configuration, security validation, HTTP session
creation, and authentication to establish a connection to Snowflake, 
REST session and registers the connection globally
"""