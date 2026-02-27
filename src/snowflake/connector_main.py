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
"""
CRL = Certificate Revocation List

What it controls:
    - Whether revoked certificates are checked 
    - How CRL caching works
    - OCSP/CRL validation behavior 

Why it exists: Snowflake enforces strong TLS validation. Enterprises 
require: revokation checking, proper certificate hygine, compliance 
guarantees

This object configures that security layer 
Think of it as: Extra TLS  integrity beyond basic HTTPS
"""

# NOTE: HttpConfig and CRLConfig are general configurations for 
# settings up networking layer

#         self._session_manager: SessionManager | None = None
"""
Note: the session_manager controls the HttpConfig and SessionManager
and the .crl file ie crl.py controls CRLConfig

_session_manager manages the session token lifecyle, keep-alive 
heartbeats, reauthentication, possibilty connection reuse 
and session expiration handling. 

After login, Snowflake gives you a session token which is 
at some point going to expire.
    - It also needs refreshing and must be attached to every
    request
"""

#         self._rest: SnowflakeRestful | None = None

"""
.network implements the restful client. This client implementation
is what is responsible for talking directly with snowflake. 

It: 
    - Sends HTTPS requests 
    - Attaches auth tokens
    - Serializes JSON payloads
    - Handles retry logic
    - Processes server responses 
    - Detects reauthentication triggers 

For example: 
    cursor.execute("SELECT 1")

Eventually it flows into _rest.
* Think of it as:
    - The engine that actually communicates with Snowflake's backend.    
"""

"""

SnowflakeConnection
    ↓
_http_config → defines HTTP behavior
_crl_config → defines TLS validation rules
_session_manager → manages auth/session state
_rest → sends actual REST API calls

---

Application
   ↓
SnowflakeConnection
   ↓
SessionManager
   ↓
SnowflakeRestful
   ↓
HTTPS
   ↓
Snowflake backend

"""

#  setattr(self, f"_{name}", value)
"""
All you're doing is iterating through all DEFAULT_CONFIGURATION's 
items and setting an attribute in default configuration to 
the value that is present in the default config

    for name, (value, _) in DEFAULT_CONFIGURATION.items():
        setattr(self, f"_{name}", value)

"""

#       self.heartbeat_thread = None
"""
The purpose of this attribute is to reserve a slot for a background
thread that will later send periodic heartbeats to Snowflake

You need this because snowflake sessions can expire if idle.

In order to prevent that, the counter may:

    - Start a background tread
    - Periodically ping the server 
    - Keep the session alive 

It is currently none because the connection has not been 
established and has not started yet. 

Later, if CLIENT_SESSION_KEEP_ALIVE is enabled, they'll do something
like: 

    self.heartbeat_thread = HeartBeatTimer(...)
    self.heartbeat_thread.start()

So this line just initializes the attribute.
"""
#       is_kwargs_empty = not kwargs

"""
This is just a checker to see if kwargs is empty and is used later on
it is; i think it is verbose so I added it as a possible patch note 

"""

# application check from the DEFAULT_CONFIGURATION
"""
    if "application" not in kwargs:
        app = self._detect_application()
        if app:
            kwargs["application"] = app

The main purpose of this is if the user did not explity pass in 
application in the kwargs
- This is an eleborate case where the user for some reason chose to 
define things except "application" so you have to watch out for this

Hence why you might want to auto detect what environment the code 
is running in. If something is detected, inject it into kwargs

So it's:
    - "If the user didn't specify the application name, try to infer it"

* Snowflake tracks a connection attribute called application. 
This is used for: 
    - Query history attribution
    - Monitoring dashboards 
    - Usage analytics
    - Support debugging 
    - Possibly telemetry tagging

"""

# For example, Snowflake can show:
"""
Application: streamlit
Application: jupyter_notebook
Application: my_custom_app

* This helps identify traffic source

"""

# What is done if the application is in fact not in kwargs
"""

# This is the static method called  _detect_application()

    @staticmethod
    def _detect_application() -> None | str:
        if ENV_VAR_PARTNER in os.environ.keys():
            return os.environ[ENV_VAR_PARTNER]

        if "streamlit" in sys.modules:
            return "streamlit"

        if all(
            (jpmod in sys.modules)
            for jpmod in ("ipykernel", "jupyter_core", "jupyter_client")
        ):

            return "jupyter_notebook"

        if "snowbooks" in sys.modules:
            return "snowflake_notebook"

Case 1. It is defined as an environment variable

if ENV_VAR_PARTNER in os.environ.keys():
    return os.environ[ENV_VAR_PARTNER]

This is implemented in .constants so im assuming it performs an 
internal fetch
* This allows for snowflake partners, embedded integrations
and SaaS wrappers to brand their applcaiton

Example: 
export SNOWFLAKE_PARTNER="my_enterprise_tool"
* Assuming the SaaS runs as a wrapper over snowflake, 
then the SaaS will explort the VAR

export SF_PARTNER="my_enterprise_tool"

// cause in .constants: ENV_VAR_PARTNER = "SF_PARTNER"

Then connections will report:
    application = my_enterprise_tool

"""

# Case 2: Streamlit detection
"""

if "streamlit" in sys.modules:
    return "streamlit"

If the module streamlit has been imported, you're probably running inside Streamlit.
"""

# Case 3: Jupyter has been detected 
"""
if all(
    (jpmod in sys.modules)
    for jpmod in ("ipykernel", "jupyter_core", "jupyter_client")
):
    return "jupyter_notebook"

If those modules are loaded, you're in a Jupyter 
notebook environment. 
"""
# Case 4: Snowflake Notebook

# The above only checks if the modules have been imported 
# and does linear scan 

#Otherwise → leave it unset


# insecure_mode checking 
# ** NOTE ** - This is deprecated

"""

if "insecure_mode" in kwargs:
    // Since this is deprecated, as in you will be encouraged to perform
    // the OSCP check, the system will warn the user
    // From what im seeing they created a new disable_ocsp_checks variable

    warn_message = "The 'insecure_mode' connection property is deprecated. Please use 'disable_ocsp_checks' instead"
    
    warnings.warn(
        warn_message,
        DeprecationWarning, // This is built in
        stacklevel=2,
    )

    // If for some reason the user doesn't have two neurons to rub
    // together and they declare contradicting both, help them out
    if (
        "disable_ocsp_checks" in kwargs
        and kwargs["disable_ocsp_checks"] != kwargs["insecure_mode"]
    ):
        logger.warning(
            "The values for 'disable_ocsp_checks' and 'insecure_mode' differ. "
            "Using the value of 'disable_ocsp_checks."
        )
   
    // Force hold your hand to declare the OSCP disable to the same as
    // the deprecated version.  
    else:
        self._disable_ocsp_checks = kwargs["insecure_mode"]
"""

"""

Seems like this is primarily a naming convention thing and is not
related to alteration of function 

    insecure_mode (deprecated): Whether or not the connection is in OCSP disabled mode. It means that the connection
        validates the TLS certificate but doesn't check revocation status with OCSP provider.

    disable_ocsp_checks: Whether or not the connection is in OCSP disabled mode. It means that the connection
        validates the TLS certificate but doesn't check revocation status with OCSP provider.


"""


#         self.converter = None
"""
Don't you already have a default attribute called converter_class?

This is what will later hold the SnowflakeConverter instance. 
The converter is responsible for:
    - Converting Snowflake datatypes into python native types

Just declaring but not yet initializing:
     self.converter = None

    
| Snowflake Type | Python Type   |
| -------------- | ------------- |
| NUMBER         | int / Decimal |
| FLOAT          | float         |
| TIMESTAMP      | datetime      |
| DATE           | datetime.date |
| VARIANT        | dict / JSON   |
| BINARY         | bytes         |

When you do:
    cursor.execute("SELECT 1")
    cursor.fetchall()

* What is recieved from the cursor is a raw JSON which is retrieved 
from the REST API which must be converted into Python objects.

That's what the converter handles. 
Why initialize as None? 

Because:
    - The converter depends on session parameters (timezone, numeric handling, etc.)
    - It gets initialized after connection is established 

So they reserve the slot early. 
     
"""
#        self.query_context_cache: QueryContextCache | None = None

"""
self.query_context_cache: QueryContextCache = None

* You type hint here maybe because it is an object 

- Snowflake supports a feature called Query Context Cache. 
* It likely stores metadata about previously executed queries 
possibly table metadata, query planning context and result-set
related state as well as Server-provided optimization hints 

The cache likely reduces round trips, repeated metadata fetches 
and repeated context reconstruction

In high-throughput systems, this improves performance
"""


#        self.query_context_cache_size = 5

"""
This sets the maximum number of cached query contexts. 
* This means that it keeps upto 5 recent query contexts and
evicts older ones
* It's a small LRU-style cache size. 

Why 5? 
    - The reason being to keep it small enough that it doesn't 
    abuse memeory but large enough to benefit interactive sessions 

"""

# -- LifeCycle -- 
# Query execution → response parsing → type conversion → caching context

"""
Application
  ↓
SnowflakeConnection
  ↓
SnowflakeRestful (network)
  ↓
Server JSON response
  ↓
SnowflakeConverter (type conversion)
  ↓
QueryContextCache (optimization)
  ↓
User receives Python objects
"""

# -- if connections_file_path is not None:

"""
if connections_file_path is not None:

    # Change config file path and force update cache

    for i, s in enumerate(CONFIG_MANAGER._slices):
    
        if s.section == "connections":
        
            CONFIG_MANAGER._slices[i] = s._replace(path=connections_file_path)

            CONFIG_MANAGER.read_config(skip_file_permissions_check=self._unsafe_skip_file_permissions_check)

            break
            

Understanding the code block:

By default; CONFIG_MANAGER reads :
    ~/.snowflake/config.toml
    ~/.snowflake/connections.toml   ← this is a “slice”

The parser inside CONFIG_MANAGER:
    ConfigSlice(CONNECTIONS_FILE, ..., "connections")

- All this is doing is if the user passes in a configuration file, 
replace the default parameters with the ones which the user would 
prefer.

- If the user explicitly passed a custom connections_file_path,
replace the default slice path with that new file and reload config.

"""

"""
Iterating one by one:

class ConfigSlice(NamedTuple):
    path: Path
    options: ConfigSliceOptions
    section: str

Each s is a ConfigSlice(path, options, section).
    
[
  {
    "path": "/Users/abdul/.snowflake/connections.toml",
    "options": {
      "check_permissions": true,
      "only_in_slice": false
    },
    "section": "connections"
  }
]

1. for i, s in enumerate(CONFIG_MANAGER._slices):
    - Each s is a ConfigSlice(path, options, section)

** You basically replace the old path into the connection path you've
now specificed since each attribute gets tied by path of ConfigSlice

"""

# Block2: if connection_name is not None:

"""
if connection_name is not None:
    connections = CONFIG_MANAGER["connections"]
    
    if connection_name not in connections:
        raise Error(
            f"Invalid connection_name '{connection_name}',"
            f" known ones are {list(connections.keys())}"
        )
    kwargs = {**connections[connection_name], **kwargs}


[connections.myprod]
account = "abc"
user = "abdul"
warehouse = "wh1"

[connections.dev]
account = "xyz"
user = "abdul_dev"
warehouse = "wh_dev"


--> Becomes:
{
    "myprod": { "account": "...", "user": "...", ... },
    "dev": { ... }
}

* Raise error if there is a mismatch

Kwargs merging:
    kwargs = {**connections[connection_name], **kwargs}

    You start with dictionary unpacking where you take the 
    params which are in the file then you continue with the ones
    which are most closely defined, therefore allow even faster 
    override
    

"""


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