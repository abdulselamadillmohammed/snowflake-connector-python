# connector_main,py

"""
How to run this file:
PYTHONPATH=. python -m snowflake.connector_main

"""

from .connector.connection import SnowflakeConnection
from .connector.connection import DEFAULT_CONFIGURATION
import pathlib


# The init function relies on connection-level configuration and 
# state attributes

# Passed on object instation 

'''
Some are passed once when you create the Connection object
Others are stored as internal state and are used automatically

Some are translated into session parameters and sent during 
authentication

Some of them affect how the HTTP requests are built 

Some are purely local cleint behavior settings
'''


# Note the connection object takes in more than two parameters
'''
-- The real configuration happens through **kwargs 
def __init__(
    self,
    connection_name: str | None = None,
    connections_file_path: pathlib.Path | None = None,
    **kwargs,
) -> None:
'''

# What is passed into as **kwards: DEFAULT_CONFIGURATION 

# Sample declaration of a connection instance



conn = SnowflakeConnection(

    # The following act as kwargs
    user="MY_USER",
    password="MY_PASSWORD",
    account="MY_ACCOUNT",
    warehouse="MY_WH",
    database="MY_DB",
    schema="PUBLIC",
    role="SYSADMIN",
)

# The main component:  self.connect(**kwargs)
'''
__init__'s function signature:
    def __init__(
        self,
        connection_name: str | None = None,
        connections_file_path: pathlib.Path | None = None,
        **kwargs,
    ) -> None:
'''

# connection_name: Loads in a predefined connection configuration
# connections_file_path: Override the default location of the TOML config file.

# from a TOML file
'''
"A TOML file is a configuration file using the Tom's Obvious, Minimal 
Language format, designed to be easily readable by humans and 
unambiguously parseable into data structures (like hash tables or 
dictionaries) in various programming languages."
'''

''' 
The purpose of the two variables being that instead of creating
kwargs by yourself each time, you predefine your kwargs and just
link to them via file path
'''

''' 
SAMPLE TOML FILE:
[connections.dev]
user = "abdul"
password = "devpass"
account = "dev-account"
'''

# Once you have it defined
conn = SnowflakeConnection(connection_name="dev")

# CONFIG_MANAGER then does -> 
# connections = CONFIG_MANAGER["connections"]
# kwargs = {**connections[connection_name], **kwargs}


# NOTE: if you don't define a connection path, the default 
# is assumed

# Overriding behaviour built in

conn = SnowflakeConnection(connection_name="dev", user="override_user")

# First the dev profile is loaded then it is overriden by the kwargs

# adding custom path:
 
SnowflakeConnection(
    connection_name="dev",
    connections_file_path=pathlib.Path("/custom/path/connections.toml")
)

# OCSP_ENV_LOCK = Lock()
# This implements a named lock on the OCSP environment variable
# so that only one thread at a time can modify it

# Uses OCSP_ENV_LOCK to protect global TLS/OCSP environment modifications.

# OCSP is a protocol used to revoke digital certificates such as SSL/TLS
# The Online Certificate Status Protocol (OCSP) is an internet protocol 
# used to determine the revocation status of digital certificates 
# (SSL/TLS) in real-time.

# CRL = Certification revocation list

# Passing only the file path: default in config_manager will get
# triggered by the not kwargs check


''' 
"If overwriting values from the default connection is desirable, 
supply the name explicitly."

[connections]
default = "prod"

[connections.prod]
user = "admin"
warehouse = "WH1"
---

SnowflakeConnection(
    connection_name="prod",
    warehouse="WH2"
)

'''

# logging is performed by a seperate libary called logging->getLogger
"""
logger = getLogger(__name__)
"""

"""
PARAMETER breakdown:

self._unsafe_skip_file_permissions_check = kwargs.get(
    "unsafe_skip_file_permissions_check", False
)

-- Since kwargs is a dict, you call get on it on the 

"""
# The following just checks if it is set to some value, if so, 
# use that value, else use false

""" 
USECASE: 

easy_logging = EasyLoggingConfigPython(
    skip_config_file_permissions_check=self._unsafe_skip_file_permissions_check
)

AND 

if connections_file_path is not None:
    # Change config file path and force update cache
    for i, s in enumerate(CONFIG_MANAGER._slices):
        if s.section == "connections":
            CONFIG_MANAGER._slices[i] = s._replace(path=connections_file_path)
            CONFIG_MANAGER.read_config(
                skip_file_permissions_check=self._unsafe_skip_file_permissions_check
            )
            break
        
"""

# The entire purpose of that parameter is to tell snowflake 
# to either skip or not skip file permission checks
# By default you do perform file permission checks

# Usecase 1: .log_configuration brings in EasyLoggingConfigPython 
# which relies on _unsafe_skip_file_permission_check

# Usecase 2: CONFIG_MANAGER.read_config from .config_manager relies on 
# that as well

# Class level logging: easy_logging = ...
"""
easy_logging = EasyLoggingConfigPython(
    skip_config_file_permissions_check=self._unsafe_skip_file_permissions_check
)
easy_logging.create_log()
"""

# The two lines above create an easy logging configuration object 
# which I believe latches on to the logging instance created above in
# this file and creates configurations based on it

# The two lines are different types of loggers compared to 
"""
logger = getLogger(__name__)
"""

# ...which is just used for logging general things like 

"""
logger.debug("connecting...")
logger.warning("OCSP disabled")
logger.info("Session closed")
"""

# Locking and error handling 
'''
self._lock_sequence_counter = Lock()
self.sequence_counter = 0
self._errorhandler = Error.default_errorhandler
self._lock_converter = Lock()
'''

# Lock sequence counter
"""
This is a lock to modify the sequence counter so that
only 1 thing can modify the counter at once
"""

# self._lock_sequence_counter - is connected to - self.sequence_counter

"""
These two go together and the connector maintains 
a per-connection sequence counter 

- These two fields are used to track the request order that is being 
sent because they require for their system that the requests are in 
monotonically increasing sequence ID. 
This is used for: 
 - Request tracking 
 - Retry logic 
 - Idempotency guarantees eg SET x = 5 and running that command 5 times
 - Matching responses to requests 

In the connection object they track sequence_counter
and every time a request is made, something like the
    def _next_sequence_counter(self) -> int:

is triggered and it causes the incrementation with a lock

The reason for the lock: 
A snowflake connection onject can be used by multiple threads 
so both may attempt to send requests simultaneously, without a lock
the both may send requests at the same time and then set the 
sequnce id to the same value

Therefore the sequence couunter is a shared mutable state 
and _lock_sequence_counter protects it 

* This is per-connection because each connection has its own
independent request stream 
    
"""


#         self._errorhandler = Error.default_errorhandler

"""
Imported from .errors which is a custom build tool which allows them to
specify what error detials you'll be using.
- Basically acts a switch for later which will follow the required details 
for your custom error handling needs

    @property
    def errorhandler(self) -> Callable:  # TODO: callable args
        return self._errorhandler

    @errorhandler.setter
    # Note: Callable doesn't implement operator|
    def errorhandler(self, value: Callable | None) -> None:
        if value is None:
            raise ProgrammingError("None errorhandler is specified")
        self._errorhandler = value

- Notice you have a function which returns the property that you're 
looking for and hinted as a callable

- Basically, instead of always raising exceptions directly, it can
transform, collect or delay errors or apply DB-API compliant behaviour
to them. 

By storing the error handler on the connection instance, they allow: 
connection.errorhandler = custom_handler

! The key detail with this is that this allows connection specific 
errors 
"""

# self._lock_converter = Lock()
"""
Basically the conventer relies on shared state, 
ie it is a single object or class which connection requests 
rely on, and when you're multithreading, you would be modifying
state at the same time. Hence why you would need a lock

    "converter_class": (DefaultConverterClass(), SnowflakeConverter),

    from .converter import SnowflakeConverter


conn = SnowflakeConnection(...)

Thread A:
    cursor1.fetchall()

Thread B:
    cursor2.fetchall()    

"""

# self.messages = []

"""
This is a simple list which is attached to the connection object.
It is used for storing non-fata messages returned from snowflake
which are typically Warnings, Information messages and 
notices from the servers. 

Notice del self.messages[:] in def close(...)

It follows DB-API conventions and some drivers expose .messages 
on connections or cursors

* Not for async tracking but just serves as metadata from the backend


"""

#         self._async_sfqids: dict[str, None] = {}

"""
The key for the dictionary are snowflake query ids
[Snowflake Query ID (UUID string)]

They set it to none likley for future extension to 
allow the storing of metadata regarding querys 

Example:
{
   "01a1234b-....": None,
   "01c5678d-....": None
}

- It represents queries that were started by this connection that 
are currently executing asynchronously

Usecase:

def _cache_query_status(self, sf_qid: str, status_ret: QueryStatus) -> None:
    if sf_qid in self._async_sfqids and not self.is_still_running(status_ret):
        self._async_sfqids.pop(sf_qid, None)
        self._done_async_sfqids[sf_qid] = None

Chain of command:
_async_sfqids -> Running async queries -> finished -> Moved to _done_async_sfqids

if not self._server_session_keep_alive:
    if self._all_async_queries_finished():
        logger.debug(
            "No async queries seem to be running, deleting session"
        )
        self.rest.delete_session(retry=retry)
    else:
        logger.debug(
            "There are {} async queries still running, not deleting session".format(
                len(self._async_sfqids)
            )

- Notice you check the length to show that some async queries are running        
"""

#         self._done_async_sfqids: dict[str, None] = {}

"""
This stores: 
    Async queries started by this connection have finished

* It's basically a completion cache. 
Why store finished ones?

Because:
    - Multiple may check status and don't want to repeatedly treat a 
    finished query as active
    - This avoids race conditions when popping

* You only need to append to on sucessful async query completions

messages stores connection-level server notices.

_async_sfqids tracks currently running async query IDs.

_done_async_sfqids It provides a terminal state record, but is not actively used in this file for safety guarantees.

"""

#These two dicts are the connection-level async lifecycle manager.
# Ie per connection session

# _client_param_telemetry_enabled
"""
- A boolean check of if client telemetry is enabled
which can be innfluenced by: Connection parameters,
Environment variables, Config file, Default behavior in the connector
* Holy moly: Might genuinlt trick you into force enabling telemetry
! PARAMETER_CLIENT_TELEMETRY_ENABLED

Auth success → session created
Session created → server sends policy flags
One of those flags = telemetry allowed or not

Basically client is for the single connection instance
ie 

conn1 = SnowflakeConnection(client = True)
conn1 = SnowflakeConnection(client = False)

... HTTP request (auth) -> params{server = True}
-> 
conn1 = SnowflakeConnection(server = True)

"""

# _session_parameters
"""
self._session_parameters: dict[str, str | int | bool] = {}

What this is:
    This is a dictionary that stores session-level parameters 
    returned by the Snowflake server.

Params like ={AUTOCOMMIT, TIMEZONE, CLIENT_SESSION_KEEP_ALIVE
,QUERY_CONTEXT_CACHE_SIZE, etc.}
*  _session_parameters is the in-memory representation of the current session state.
"""


#  logger.info(...)

"""
logger = getLogger(__name__)

    logger.info(
        "Snowflake Connector for Python Version: %s, "
        "Python Version: %s, Platform: %s",
        SNOWFLAKE_CONNECTOR_VERSION,
        PYTHON_VERSION,
        PLATFORM,
    )

Example of what it looks like:
    Snowflake Connector for Python Version: 3.7.2, Python Version: 3.11.5, Platform: Darwin-23.3.0-x86_64

"""

# These are request attributes
"""
__http_config - Holds low-level HTTP transport settings such as proxy
configuration, pooling behavior, and network adapter setup used for 
backend communiction. 

_crl_config - Stores cetificate revocation list (CRL) 
validation settings that control how TLS certificate revocation 
is checked during secure connections 

_session_manager - Manages the lifecycle and reuse of HTTP sessions
(connection pooling, adapters, retries) for all network requests 
made by the connection

_rest - The Snowflake REST client responsible for sending authenticated 
API requests (login, queries, heartbeats, session deletion) to the snow-
flake backend. 

"""

#         self._http_config: HttpConfig | None = None

"""
Defined as HttpConfig type, this is a set of configuration settings
which controls how HTTP requests are made

It controls things such as Timeouts, Proxy settings, SSL/TLS 
verification options, retry behavior, and adapter configuration

Why it exists: 
- Snowflake communicates over HTTPS. Every REST call needs 
consistent low-level network settings 

* Basically it acts as a blueprint for how outbound HTTPS traffic 
behaves
Without it, you wouldn't know how long to wait, whether to 
verify certificates, whether to use a proxy, and how retries
are handled 
"""

#         self._crl_config: CRLConfig | None = None


# --- QUESTIONS --- 
"""
1. Why do you have multithreading on a single connection instead of 
creating multiple connection objects then you avoid having to 
create locks?

2. What does this decorator do?:     @errorhandler.setter

3. What does the type hinting of Callable mean? aren't all functions
callable?

4. 
"""