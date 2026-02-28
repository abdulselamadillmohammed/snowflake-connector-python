#     def crl_download_max_size(self) -> int | None:
"""
@property
def crl_download_max_size(self) -> int | None:
    "Maximum CRL file size in bytes."
    if not self._crl_config:
        return self._crl_download_max_size
    return self._crl_config.crl_download_max_size

This is a tool which returns the maximum allowed size in bytes 
for a downloaded CRL file 

* CRLs are downloaded from remote servers and without a size cap;
a malicious sever could return a huge file which can lead to memory
or disk exhuastion and you would be at risk of denial of service 
attacks
* This settings protects against oversized CRL downloads
"""

#    def skip_file_permissions_check(self) -> bool | None:
"""
@property
def skip_file_permissions_check(self) -> bool | None:
    "Whether to skip file permission checks for CRL cache files."
    if not self._crl_config:
        return self._skip_file_permissions_check
    return self._crl_config.skip_file_permissions_check

    
What this does:
    - It returns a decider of whether the connector should skip 
permission validation on CRL cache files.

The reason this exists is because when writing CRLs to disk, the 
connector may check:
    - File mode (e.g., not world-writeable)
    - Owner permissions 
    - Security constraits

What skipping permission checks would mean:
    - It is useful for restricted envrionments 
    - May be needed on certain filesystems 
    - Reduced security guarantees

* This is a tradeoff between strict security and envrionment 
flexibility
"""

#     def session_id(self) -> int:
"""
@property
def session_id(self) -> int:
    return self._session_id

This returns the Snowflake session ID assignmed by the server after 
authentication. 

No legacy fallback; no structured config and just exposes a private 
attribute 

session_id represents a unique identifier for the authenticated 
session which is used internally for query tracking, logging,
telemetry and server side correlation

* Note: after connect() runs successfully: self._session_id is populated
via the server response

"""

"""
| Property                      | Purpose                                      |
| ----------------------------- | -------------------------------------------- |
| `crl_download_max_size`       | Prevent oversized CRL downloads              |
| `skip_file_permissions_check` | Control CRL cache file security validation   |
| `session_id`                  | Expose server-assigned connection session ID |

"""

#       def user(self) -> str: 
"""
    @property
    def user(self) -> str:
        return self._user

It returns the authenticated username associated with the connection
    - _user is set during connect() -> inside __config() when kwards
    are processed
    - This is read-only
    - Exposes connection metadata safely
    
"""

#     def host(self) -> str:
"""
    @property
    def host(self) -> str:
        return self._host

This returns the Snowflake hostnmae being currently used;

Example:

abc123.us-east-1.snowflakecomputing.com
    1. where * _host is computed during connection setup.
    2. Exposed read-only \Used for degguing 

and it is used for debugging, logging and diagnostics
    
"""

#     def port(self) -> int:
"""

@property
def port(self) -> int:
    return int(self._port)

This returns the port number (integer)
* does a type conversion

"""

#     def region(self) -> str | None:
"""
@property
def region(self) -> str | None:
    warnings.warn(
        "Region has been deprecated and will be removed in the near future",
        PendingDeprecationWarning,
        # Raise warning from where this property was called from
        stacklevel=2,
    )
    return self._region

This is a depricated feature so they raise a warning but this
used to just return the region which is no longer needed cause 
it has fully quantified account identifiers like host:

abc123.us-east-1.snowflakecomputing.com

"""

"""
| Property | Purpose                             |
| -------- | ----------------------------------- |
| `user`   | Authenticated username              |
| `host`   | Snowflake hostname                  |
| `port`   | Connection port (normalized to int) |
| `region` | Deprecated legacy region accessor   |


"""

#    def proxy_host(self) -> str | None:
"""
This is used to route outbound HTTPS traffic through a corporate 
proxy server. 

If set:
    proxy_host = "proxy.company.com"
The connector will send all Snowflake HTTPS requests to:
    https://proxy.company.com:<proxy_port>

instead of directly to:
    https://<account>.snowflakecomputing.com

The reason they do this because it is required in enterprise networks
because it is behind firewalls and enables traffic inspecttion and
monitoring


"""

# Proxy port:

"""
proxy_port

The port of the proxy server.

Example:

proxy_port = "8080"

Snowflake will construct a proxy URL like:

http://proxy.company.com:8080

This is passed into the HTTP layer as part of the proxies configuration.
"""

# proxy_user
"""
Username for authenticating to the proxy.
Some enterprise proxies require authentication.

Used to build:
http://user:password@proxy.company.com:8080

Passed to the HTTP client.
"""

# proxy_password
"""
This is used for password for a proxy authentication. 
Used alongside proxy_user; these are consumed when building
the HTTP session inside _rest.

Internally, something like:
requests.Session().proxies = {
    "https": proxy_url
}
"""

# no_proxy

"""
This defines hosts that should bypass the proxy.

# Example:
    no_proxy = "localhost,127.0.0.1,.internal.company"

Meaning:
    - Requests to those domains go direct and all other go through the 
    proxy
    
"""

# account
"""
This is the core Snowflake account identifier 

account = "abc123.us-east-1"

It is used to build the actual snowflake endpoint:

https://abc123.us-east-1.snowflakecomputing.com

account → host → REST endpoint
"""

"""
During connect():
    _account is parsed
    _host is constructed from account
    _rest = SnowflakeRestful(...) is created

Inside REST setup:
    Proxy settings are injected into HTTP session
    TLS configuration applied
    OCSP / CRL logic configured
    Session established

So proxy_* parameters affect:
    Authentication requests
    Query execution requests
    Telemetry uploads
    File transfers
    OCSP / CRL downloads

Everything goes through the same HTTP layer.

"""

# database
"""
@property
def database(self) -> str | None:
    return self._database

This controls the default database for the session. In SQL terms
USE DATABASE my_db;

if set during connection:
    SnowflakeConnection(database="MY_DB")

Then after authentication, Snowflake initalizes the session with:
    - CURRENT_DATABASE = MY_DB

So when you run:
    SELECT * FROM my_table;

Snowflake resolves it as:
    SELECT * FROM MY_DB.<current_schema>.my_table;

If not set:
    - No default database
    - Fully quantified names required
"""

# schema: 
"""
@property
def schema(self) -> str | None:
    return self._schema

It controls the default schema inside the selected database

Equivalent to:
    USE SCHEMA my_schema;

Together with database:
    database + schema = namespace

If both are set:
    database="MY_DB"
    schema="PUBLIC"

Then:
    SELECT * FROM my_table;

Resolves to:
    SELECT * FROM MY_DB.PUBLIC.my_table;
"""

# warehouse
"""
@property
def warehouse(self) -> str | None:
    return self._warehouse

It controls the virtual warehouse that is used to execute queries. 
It determines the compute resources, cost, performance, concurrency. 

It is equivalent to:
    USE WAREHOUSE my_wh;

Without a warehouse:
    - Queries cannot execute
    - Snowflake raises error
* This is critical for actual query execution
"""

# role
"""
@property
def role(self) -> str | None:
    return self._role

It controls the security role used for permissions. It is the 
equivalent to USE ROLE analyst;

It determines what objects you can access; what priviledges you
have and what schemas/tables are visible. 

Even if authenticated sucessfully, wrong role -> access denied 
errors. 


During authentication:

    Connector sends login request.
    Server establishes session.
    Server applies:
        database
        schema
        warehouse
        role

These become session-level parameters.
They influence:
    Query resolution
    Authorization
    Execution routing
    Billing
"""

# login_timeout
"""
@property
def login_timeout(self) -> int | None:
    return int(self._login_timeout) if self._login_timeout is not None else None

* Purpose:
    Controls how long (in seconds) the connector waits during authentication. 

Covers:
    Initial REST login request
    Token exchange
    MFA / OAuth flows
    OCSP checks during login

If login exceeds this duration → authentication fails.
Why cast to int?
    Config values may come from:
    Environment variables (strings)
    TOML files (strings)
    kwargs (mixed types)
This guarantees a numeric value before passing to HTTP layer.
"""

# network_timeout
"""
@property
def network_timeout(self) -> int | None:
    return int(self._network_timeout) if self._network_timeout is not None else None

Purpose:
    Controls timeout for regular network operations after login

Applies to:
    Query execution requests
    Result fetch requests
    Metadata calls
    File transfers

* If a request takes longer than this → request fails.
* This is a higher-level request timeout.
"""

# socket_timeout
"""
@property
def socket_timeout(self) -> int | None:
    return int(self._socket_timeout) if self._socket_timeout is not None else None

Purpose:
    This controls low-level socket I/O timeout. 

More granular than network timeout. 
Applies to:
    - TCP read/write operations
    - Underlying HTTP client socket behavior

| Timeout Type    | Level                     |
| --------------- | ------------------------- |
| login_timeout   | Authentication phase      |
| network_timeout | Full request lifecycle    |
| socket_timeout  | Raw TCP socket operations |

Socket timeout is typically used by urllib3 or 
requests under the hood.
"""

#     def _backoff_generator(self) -> Iterator:
"""
@property
def _backoff_generator(self) -> Iterator:
    return self._backoff_policy()

Purpose:
    Returns an iterator that produces retry delays. 

for delay in conn._backoff_generator:
    try request
    if fails:
        sleep(delay)

_backoff_policy() likely implements:
    - Exponential backoff
    - Jitter
    - Max retry cap

It is used when:
    - Network request fails
    - Transient errors occur
    - Retrying login
    - Retrying queries
    - Retrying file transfers

* This is how Snowflake avoids hammering servers on failure.
"""

#     def client_session_keep_alive(self) -> bool | None:
"""
@property
def client_session_keep_alive(self) -> bool | None:
    return self._client_session_keep_alive

Purpose:
    Controls whether the connector sends heartbeat messages to 
    keep session alive.

* If True:
    - Background thread periodically pings sever.
    - Prevents session expiration due to inactviity.
* If False:
    - Session may expire after idle timeout. 

Why this matters:
    - Snowflake sessions expire automatically after inactivity 
    - Keep alive prevents re-authentocation overhead

| Property                  | What It Controls                    |
| ------------------------- | ----------------------------------- |
| login_timeout             | How long to wait for authentication |
| network_timeout           | How long to wait for API requests   |
| socket_timeout            | Low-level TCP timeout               |
| _backoff_generator        | Retry delay strategy                |
| client_session_keep_alive | Whether to send periodic heartbeats |
    
"""

