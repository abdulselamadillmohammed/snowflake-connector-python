#        self.__set_error_attributes()

"""
They segment out the error attributes and then they set it 
with a single call


    def __set_error_attributes(self) -> None:
        for m in [
            method for method in dir(errors) if callable(getattr(errors, method))
        ]:
            # If name starts with _ then ignore that
            name = m if not m.startswith("_") else m[1:]
            setattr(self, name, getattr(errors, m))

It dynamically attaches error classes/functions from the errors
module directly into the conneection instance. 

So after it runs, these properties are present:
    conn.ProgrammingError
    conn.DatabaseError
    conn.Error

instead of:
    from snowflake.connector.errors import ProgrammingError

"""

#        self.connect(**kwargs)
"""
This is where the real connection is established

inside the connect function you perform several operations: 
    - Calls self.__config(**kwargs) -> sets all _account, _user, _warehouse, etc. 
    - Builds HTTP config
    - Creates SessionManager 
    - Creates Snowflake restful
    - Authenticates (password, OAuth, keypair, etc.)
    - Establishes session
    - Initializes query context cache 
    - Possibily start heartbeat

** After this finishes sucessfully, self._rest
allows a live REST client that is connected to Snowflake
"""
#        self._telemetry = TelemetryClient(self._rest)

"""
Now that _rest exists, they can now intialize telemetry 
via the telemetry cleint because TelemetryClient requires 
_rest

This batches telemetery events and sends them to Snowflake via 
REST using the session tokens 

Important ordering detail: 
    - Telemetry is created after successful connection
      because it depends on _rest. If connection fails, 
      telemetry is never created.

"""

#        self.expired = False
"""
This is a simple state flag. It tracks whether the session has 
expired. Later in the lifecycle:
    - If tokens expire
    - If reauthentication is needed
    - If server signals expirtion 

This flag can be flipped. 
    
Post intialization, this is set to false since at the nanosecond level
the session will not be experired. 

"""

# Order of operations
"""
Attach error types
->
Establish connection + authentication
->
Create telemetry (needs REST session)
->
Mark connection as active
"""

# The telemetry abuse :) :

#        self._log_telemetry_imported_packages()

"""
This basically inspects sys.modules which is a dictionary that 
contains all currently imported python modules. 
It likely checks whether certain optional packages are present, 
logs that information via telemetry and sends that to Snowflake
for analytics. 

Why?: Because Snowflake wants to know if users are importing 
pandas, pyarrow, or sqlalchemy or Other ecosystem integrations

It helps them: measure feature usage, detect compatibility issues
and prioritize development. 


"""
#        self._log_nanoarrow_import()

"""
This is likely a simple check, since Nanoarrow is a compiled 
C-extension that is used for fast Arrow data conversion. 
This function likely checks:
"nanoarrow_arrow_iterator" in sys.modules or something similar

If nanoarrow loaded sucessfully:
    - Log that optimized Arrow path is being used
If not:
    - Log fallback behavior. 

Why? 
    - Performance diagnostics.

They want to know:
    - Is the fast path being used? Is the compiled module missing?
    Are users running pure Python fallback?   
"""

#        self._log_minicore_import()
"""
This is the same idea as a nanocore check, minicore is another 
optional compiled component used internally (for performance-critical 
logic). 

This logs whether it was sucessfully imported for Observability, 
Deployment diagnostics and Feature adoption tracking 

"""

#        atexit.register(self._close_at_exit)
"""

    def _close_at_exit(self):
        with suppress(Exception):
            self.close(retry=False)

The atexit is a Python standard library module.
When you call it, it ensures that when the interpreter 
exits normally call the function passed in


    def _close_at_exit(self):
        with suppress(Exception):
            self.close(retry=False)

What _close_at_exit probably does:
Closes open sessions
Flushes telemetry
Cleans up REST resources
Stops heartbeats
Prevents dangling threads

This prevents:
Zombie sessions
Token leaks
Server-side abandoned connections

"""


# -- File operations --

"""
The problem they are solving: Snowflake supports 

PUT file://local.csv @mystage
GET @mystage/file.csv file://.

Those are not normal SQL queries.
They trigger:
    - Uploads to S3 / Azure / GCS
    - Parallel downloads
    - Compression
    - Encryption
    - Chunking 
    - Retry logic  

* These operations require extra client-side logic 
"""
# self._file_operation_parser = FileOperationParser(self)
"""
This is a parser which takes in the self and parses SQL statements
to detect file operations

cursor.execute("PUT file://data.csv @stage")

The parser: 
    - Detects it is a PUT commands
    - Extracts
        - Local file path
        - Target stage
        - Compression flags
        - Parallelism settings 
    - Converts SQL text -> structured file operation instruction

It likely answers:
    - Is this a PUT?
    - Is this a GET?
    - What options are present?

- Without this parser, the connector would treat PUT/GET like normal
SQL
"""

# self._stream_downloader = StreamDownloader(self)

"""
This is used for downloading result sets and staged files

Ie when downloading larg efiles or result sets, it 
streams HTTP chunks, handles decompression,
handles chunk reassembly and supports parallel 
downloads and writes to disk or buffers

Instead of : requests.get(...).content

which would load everything into memory:
it instead reafs reponse iteratively and handles
retries. It alos handles network interruptions and verifies
checksums. 

"""

# Why are they attached to the connection?

"""
They are static functions which use the self which gives access to 
self._rest (authenticated session)
and also allows them to have access to Credentials
Config flags, retry policies, Logging and Telemetry

* They are helpers bound to the connection state. 

"""

# What @ property does
"""
@property turns a method into a read-only attribute.

Instead of calling:
conn.insecure_mode()

you can do:
conn.insecure_mode

Why not just do:

self.disable_ocsp_checks

Because:
The internal variable is named _disable_ocsp_checks
The leading underscore means "internal implementation detail"

They may want to:

1. Validate later
2. Add logging
3. Change behavior
4. Deprecate names cleanly

Properties allow them to expose a stable public interface while 
keeping internal flexibility.
"""

#  NOTE: "ocsp_fail_open": (True, bool),  # fail open on ocsp issues, default true

#    def _ocsp_mode(self) -> OCSPMode:

"""
def _ocsp_mode(self) -> OCSPMode:

    'OCSP mode. DISABLE_OCSP_CHECKS, FAIL_OPEN or FAIL_CLOSED'

    if self.disable_ocsp_checks:
        return OCSPMode.DISABLE_OCSP_CHECKS

    elif self.ocsp_fail_open:
        return OCSPMode.FAIL_OPEN

    else:
        return OCSPMode.FAIL_CLOSED


* This decides that the OSCPMode is (although they don't seem to be 
using it); at least anywhere in this file

What it does: 
    - It converts two booleans into a single enum that represents the 
    effective OSCP policy. 

Inputs:
    - disable_oscp_checks
    - oscp_fail_open


OCSPMode is an object which is defined as a constant 

The output of this is to return the modified object 

What the three modes classify:
    1. DISABLE_OCSP_CHECKS
    - Do not check certificate revocation at all. 
    - Although this is tecnically fast, it is the least secure. 

    2. FAIL_OPEN
    Check revocation via OCSP.
    If OCSP server fails or is unreachable → allow connection anyway.

    3. FAIL_CLOSED
    Check revocation.
    If OCSP check fails → block connection.

    Strictest; most secure 
"""

#    def cert_revocation_check_mode(self) -> str | None:

"""
@property
def cert_revocation_check_mode(self) -> str | None:
    if not self._crl_config:
        return self._cert_revocation_check_mode
    return self._crl_config.cert_revocation_check_mode.value

This is a setter for determining the check mode for the revocation
list. This is related to CRL

* Unlike OCSP which is a real time check, CRL uses downlaoded revocation
lists. 


* It determines the effective CRL mode. 

There are two possibilites. 

Case 1: _crl_config is None
Use legacy internal value:
    self._cert_revocation_check_mode

Case 2: _crl_config exists

In this case, use a structured CRL configuration object:
    self._crl_config.cert_revocation_check_mode.value

* This version supports richer CRL configuration via _crl_config


Possible values
    Docstring says:
        "DISABLED"
        "ENABLED"
        "ADVISORY"

    Meaning:
        DISABLED → no CRL checking
        ENABLED → strict CRL validation
        ADVISORY → check but don't fail hard
"""

#    def allow_certificates_without_crl_url(self) -> bool | None:

"""

* This is just a wrapper to support both legacy and newer versions

@property
def allow_certificates_without_crl_url(self) -> bool | None:
    if not self._crl_config:
        return self._allow_certificates_without_crl_url
    return self._crl_config.allow_certificates_without_crl_url

What this controls:
    Some certificates contain a CRL distribution URL. 
    Some do not. 
    This setting answers:
        If a certificate has no CRL URL, should we reject it

If True:
    Allow certificate even if no CRL URL exists.

If False:

    Reject certificate if CRL URL missing.
    Same design pattern as previous property

    If structured CRL config exists → use it.
        Else → fall back to legacy attribute.

"""

#     def crl_connection_timeout_ms(self) -> int | None:
"""
@property
def crl_connection_timeout_ms(self) -> int | None:
    "Connection timeout for CRL downloads in milliseconds."
    if not self._crl_config:
        return self._crl_connection_timeout_ms
    return self._crl_config.connection_timeout_ms

This controls how long to wait when establishing the TCP connection
to downlaod a CLR life. 

This is: DNS lookup, TCP handshake and TLS handskake to CRL host
which is measured in milliseconds. 

* Note: if for example, _crl_connection_timeout_ms is set to 3000, 
the connector waits 3 seconds to connect to the CRL server before 
failing
"""

#     def crl_read_timeout_ms(self) -> int | None:
"""
@property
def crl_read_timeout_ms(self) -> int | None:
    "Read timeout for CRL downloads in milliseconds."
    if not self._crl_config:
        return self._crl_read_timeout_ms
    return self._crl_config.read_timeout_ms

* basically same thing as before but now they choose to allow
a newer version with a better struct, ie now reach within
_crl_config which is set in I believe .connect()

This controls how long to wait while reading data after 
connection is established. 

Difference from connection timeout:

Type	            Covers
Connection timeout	Time to establish connection
Read timeout	    Time to receive response data

Example:    
    * Connection succeeds in 100ms 
    * Server stalls during download 
    * Read timeout determines how long to wait before aborting 

"""
#     def crl_cache_validity_hours(self) -> float | None:

"""
@property
def crl_cache_validity_hours(self) -> float | None:
    "CRL cache validity time in hours."
    if not self._crl_config:
        return self._crl_cache_validity_hours
    // Doesn't python run into division issues if seconds is too large?
    return self._crl_config.cache_validity_time.total_seconds() / 3600

This controls how long a downloaded CRL is considered valid in 
cache. 
Instead of downloading the CRL every time:
    - Download once 
    - Cache locally
    - reuse for X hours

If set to 24, CRL is valid for 24 hours before re-fetching
"""

# Why this pattern exists 
"""
if not self._crl_config:
    return legacy_value
else:
    return structured_config_value

This means:
    Older versions stored individual attributes
    Newer versions use _crl_config object
    They're maintaining backward compatibility

----------------------------------------------------

CRL flow works like this:
    - Server certificate contains CRL distribution URL
    - Connector downloads CRL file
    - Checks if certificate serial is revoked
    - Uses cache to avoid repeated downloads

These properties tune:
    - How long to wait for CRL servers
    - How long to trust cached CRLs

"""

#     def enable_crl_cache(self) -> bool | None:
"""
@property
def enable_crl_cache(self) -> bool | None:
    "Whether CRL caching is enabled."
    if not self._crl_config:
        return self._enable_crl_cache
    return self._crl_config.enable_crl_cache

This controls whether CRLs are cached at all. 
If this is false, every certificate validation may re-download the CRL
which will lead to slower and more network usafe however you 
techanically ensure that every CRL is fresh

If true:
    - You only have to download it once and then reuse the same CRL
    until crl_cache_validity_hours expires
* This is in-mempory caching control. 

"""

#     def enable_crl_file_cache(self) -> bool | None:
"""
@property
def enable_crl_file_cache(self) -> bool | None:
    "Whether file-based CRL cache is enabled."
    if not self._crl_config:
        return self._enable_crl_file_cache
    return self._crl_config.enable_crl_file_cache

What it controls: Whether CRLs are cached to disk. 

| Layer        | Purpose                         |
| ------------ | ------------------------------- |
| Memory cache | Per-process reuse               |
| File cache   | Persist across process restarts |

This is done so that the CRLs are written to disk which would
allow future sessions to reuse them and avoid repeated downloads 
across runs 

* If this is disabled, you only cache in memory so when the program
exists, you can't reuse crl
"""

#     def crl_cache_dir(self) -> str | None:
"""
@property
def crl_cache_dir(self) -> str | None:
    "Directory for CRL file cache."
    if not self._crl_config:
        return self._crl_cache_dir

    if not self._crl_config.crl_cache_dir:
        return None

    return str(self._crl_config.crl_cache_dir)

It controls where CRLs are stored if file caching is enabled 
Example:
    crl_cache_dir = "~/.snowflake/crl_cache"

If None:
    either file cache is disabled or use the default located that is used 
    internally

    1. CRL downloaded
    2. Stored in memory
    3. Written to /tmp/crl
    4. Reused until expiration
    5. Available across restarts 
    
"""

#     def crl_cache_removal_delay_days(self) -> int | None:
"""
@property
def crl_cache_removal_delay_days(self) -> int | None:
    "Days to keep expired CRL files before removal."
    if not self._crl_config:
        return self._crl_cache_removal_delay_days
    return self._crl_config.crl_cache_removal_delay_days

This returns how many days expired CRL files should remain on 
disk before being deleted. 

Even after a CRL is expired (no longer valid for certificate 
checking), the file can remain on disk for X days before cleanup 
removes it.

This is a retention buffer. 
"""
#    def crl_cache_cleanup_interval_hours(self) -> int | None:
"""
@property
def crl_cache_cleanup_interval_hours(self) -> int | None:
    "CRL cache cleanup interval in hours."
    if not self._crl_config:
        return self._crl_cache_cleanup_interval_hours
    return self._crl_config.crl_cache_cleanup_interval_hours

Retuns how often in hours the connector should run a cleanup pass
over the CRL cache directory.

* Controls the frequency the frequency of scanning the CRL
cache directory and removinf old expired files which is based
on removal delay.

Example:
    if set to 12 -> cleanup runs every 12 hours. 
"""

#    def crl_cache_start_cleanup(self) -> bool | None:
"""
@property
def crl_cache_start_cleanup(self) -> bool | None:
    "Whether to start CRL cache cleanup immediately."
    if not self._crl_config:
        return self._crl_cache_start_cleanup
    return self._crl_config.crl_cache_start_cleanup

What is does:
    - Returns whether cleanup should begin immediately when 
    the connection initalizes. 

Two cases:
    - No _crl_config -> use legacy flag
    - _crl_config exists -> use structrued config 

Meaning:
    if True:
        - Cleanup scheduler starts immediately after connection setup
    if False:
        - Cleanup may wait until first interval tick.
        - Or only run lazily when triggered.

These three control the lifecycle of CRL files on disk, not 
certificate validation itself.

They define:
    - How long expired CRLs are retained
    - How often cleanup runs
    - Whether cleanup starts immediately
Same transitional design pattern as before:
    - Legacy attribute fallback
    - Structured _crl_config preferred
"""

"""
Questions:

1. When would you ever need to cache CRLs in disk

def enable_crl_file_cache(self) -> bool | None:
    "Whether file-based CRL cache is enabled."
    if not self._crl_config:
        return self._enable_crl_file_cache
    return self._crl_config.enable_crl_file_cache


    
"""