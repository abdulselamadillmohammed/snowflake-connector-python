#     def telemetry_enabled(self) -> bool:

"""
@property
def telemetry_enabled(self) -> bool:
    return bool(
        self._client_param_telemetry_enabled
        and self._server_param_telemetry_enabled
    )

@telemetry_enabled.setter
def telemetry_enabled(self, value) -> None:
    self._client_param_telemetry_enabled = True if value else False
    if (
        self._client_param_telemetry_enabled
        and not self._server_param_telemetry_enabled
    ):
        logger.info(
            "Telemetry has been disabled by the session parameter CLIENT_TELEMETRY_ENABLED."
            " Set session parameter CLIENT_TELEMETRY_ENABLED to true to enable telemetry."
        )

The getter returns the effective telemetry state which is only 
considered to be enabled when noth the client-side flag and 
server/session-side flag are true

The setter only updates the client side flag; ie forces the value
to a strict boolean

If the client tries to enable telemetry but the server-side flag is
false, it logs an infromational message. It does not override the 
server setting. 

What is CLIENT_TELEMETRY_ENABLED?

CLIENT_TELEMETRY_ENABLED is a Snowflake session parameter.
It is not a Python variable.
It lives on the Snowflake server side and controls whether the 
account/session allows clients to send telemetry data back 
to Snowflake.

Think of it as:
“Does this Snowflake session permit client telemetry?”
"""

#     def service_name(self) -> str | None:

"""

@property
def service_name(self) -> str | None:
    return self._service_name

@service_name.setter
def service_name(self, value) -> None:
    self._service_name = value

The two above functions expose _service_name as a readable and 
writable property without any addional validation of 
transformartion. 

service_name exists so Snowflake can know which logical application 
or service is using the connection, independent of the database 
username.

"""

# def log_max_query_length(self) -> int:
"""
@property
def log_max_query_length(self) -> int:
    return self._log_max_query_length

This exits in order to enforce a hard ceiling on how much SQL text
is emitted into logs and telemetry.

Snowflake connections can execute arbitrarily large queries and
without a cap:
    - Logs could explode in size
    - Sensitive SQL text could leak in full
    - Telemetry payloads could grow unbounded
    - Memory and network overhead increase

So this value is a defensive guardrail used by logging/telemetry code
to truncate SQL before emitting it.

It is read-only here because:
    - It is configuration, not runtime behavior.
    - It is meant to be set at intialization, mut mutated mid flight
* This is about log hygine and operational safety, not syntax. 
"""

#     def disable_request_pooling(self) -> bool:
"""
@property
def disable_request_pooling(self) -> bool:
    return self._disable_request_pooling

@disable_request_pooling.setter
def disable_request_pooling(self, value) -> None:
    self._disable_request_pooling = True if value else False

The pupose of this is that Snowflake uses HTTP under the hood. 
Request pooling means:
    - Reusing HTTP sessions/ connections
    - Possibly multiplexing requests 
    - Avoiding connection setup overhead
Pooling improves perfromance and reduces TLS handshakes. 
This flag exists as a kill switch for that optimizaiton. 

Why would you need it?
    - Debugging low-level networkign issues
    - Working around proxt/load balances incompatabilities
    - Diagnosing connection reuse bugs
    - Isolation in highly controlled envrionments
So this property is an operational escape hatch

- It is not about returning a boolena -- it is about turning off
a performance optimization layer when necessary
"""

#     def use_openssl_only(self) -> bool:
"""
@property
def use_openssl_only(self) -> bool:
    # Deprecated, kept for backwards compatibility
    return True

Purpose: at some point, the connector likely supported multiple SSL/
TLS backends. 
They standardized on OpenSSL but external code may still check. However,
external code may still check:

    if conn.use_openssl_only:

Removing the property would break external integrations. 
So this propertu now serves one purpose:
    - Perseve API compatibility without perserving old behaviour. 
It freezes the surface area while the internal implementation
changed. 
This is about API stability across versions.  
"""

#     def arrow_number_to_decimal(self):
"""
@property
def arrow_number_to_decimal(self):
    return self._arrow_number_to_decimal

Purpose: 
    Snowflake returns results via Arrow for performance. 
    Arrow numeric types can map to:
        - Python float (fast, but precision loss possible)
        - Python Decimal (slower, but exact)

    This flag determines which numeric fidelity policy to use. 

So this property exists to control:
    - Precision guarantees
    - Financial / scientific correctness
    - Tradeoff between speed and exactness. 

* It inffluneces the result conversion layer, not the connection itself. 
""" 


#     def enable_stage_s3_privatelink_for_us_east_1(self) -> bool:
"""
    @property
    def enable_stage_s3_privatelink_for_us_east_1(self) -> bool:
        return self._enable_stage_s3_privatelink_for_us_east_1

    @enable_stage_s3_privatelink_for_us_east_1.setter
    def enable_stage_s3_privatelink_for_us_east_1(self, value) -> None:
        self._enable_stage_s3_privatelink_for_us_east_1 = True if value else False

The purpose of this is that when snowflake stages data to S3, it can 
use public AWS endpoints or PrivateLink (private AWS networking)

PrivateLink is:
    - More secure
    - Internal network only
    - Required in certain enterprise setups

This flag contols routing behaviour specifically for us-east-1

Why region specific?
    - Because AWS networking and PrivateLink endpoitns vary by region. 

So this property exists to:
    - Control network path selection for staging. 
    - Satisfy enterprise networking constraints
    - Enable VPC-restricted envrionemnts. 
* This is about network topology control, not boolean getter. 
"""

#   def enable_connection_diag(self) -> bool:

"""
@property
def enable_connection_diag(self) -> bool:
    return self._enable_connection_diag

This functions prupose is to enable diagnostic mode, specifically
for connection establishment. It likely activates addtional logging, 
netwotking tracing, or envrionment inspection during login and 
handshake.

This exists for:
    - Debugging authentication failures
    - TLS/OSCP issues
    - Proxy / firewall problems
    - Enterprise support cases
It is an operational debugging switch, not normal runtime 
behavior. 
"""

# def connection_diag_log_path(self):
"""
@property
def connection_diag_log_path(self):
    return self._connection_diag_log_path

When connection diagnostsics are enabled, logs must be written 
somewhere. This propety provides the filesystem path where 
diagnostic output is stored. 

Purpose:
    - Allow support teams to collect artifacts
    - Persist handshake / networking trace logs 
    - Enable structured troubleshooting
This separates diagnostic logging from normal appication logs    
"""

# def connection_diag_whitelist_path(self):

"""
@property
def connection_diag_whitelist_path(self):

    Old version of ``connection_diag_allowlist_path``.
    This used to be the original name, but snowflake backend
    deprecated whitelist for allowlist. This name will be
    deprecated in the future.
    warnings.warn(
        "connection_diag_whitelist_path has been deprecated, use connection_diag_allowlist_path instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return self._connection_diag_whitelist_path

The purpose of this is to be a backward-compatibility bridge 
since snowflake renamed whitelist to allowlist. 
Although the backend changed terminology;
this property perserves old API usage, emits depricattion warning
and redirects to the same internal value
* It exists to avoid breaking external vode while migrating 
naming standards
"""

# def connection_diag_allowlist_path(self):
"""
@property
def connection_diag_allowlist_path(self):
    return self._connection_diag_allowlist_path

This is the new canocial property for defining a file that contains
an allowlist of endpoints or hosts relavant to connection diagnostics. 

Likely used to:
    - restrict diagnostic checks to specific domains
    - Control which endpoints are tested or logged
    - Avoid excessive scanning in enterprise networks
It is configuration for controlled network inspection.
"""

# def arrow_number_to_decimal_setter(self, value: bool) -> None:
"""
@arrow_number_to_decimal.setter
def arrow_number_to_decimal_setter(self, value: bool) -> None:
    self._arrow_number_to_decimal = value

This enables dynamic control over Arrow numeric conversion policy. 
Previously you saw the getter. This setter allows changing numeric 
fidelity behaviour after connection intialization. 
Why this matters:
    - Some workflows require exact decimal precision
    - Others prioritize speed
    - Testing envrionments may toggle behaviour. 
This impacts result conversion, not connection state.  
"""

# def auth_class(self) -> AuthByPlugin | None:
"""
@property
def auth_class(self) -> AuthByPlugin | None:
    return self._auth_class

@auth_class.setter
def auth_class(self, value: AuthByPlugin) -> None:
    if isinstance(value, AuthByPlugin):
        self._auth_class = value
    else:
        raise TypeError("auth_class must subclass AuthByPlugin")

The purpose of these methods is to enalble pluggable authentication
strategies. Ie., instead of hard coding authentication mechansims, 
the connection can accept an authentication plugin implementing 
AuthByPlugin. 

This supports:
    - Password authentication
    - Key pair authentication
    - OAuth 
    - SSO / external identify providers
    - Futur custom auth mechansims 
The type check enforces that only valid authentication strategy 
objects are injected.
"""

#    def is_query_context_cache_disabled(self) -> bool:
"""
@property
def is_query_context_cache_disabled(self) -> bool:
    return self._disable_query_context_cache

Snowflake likely caches query context (metadata, session parameters, 
etc.) to avoid repeated lookups.

This flag disables that optimization. 

Use cases:
    - Debugging caching bugs
    - Ensuring fresh metadata retrieval
    - Testing context invalidation
This is another operational override switch
"""

# def iobound_tpe_limit(self) -> int | None:
"""
@property
def iobound_tpe_limit(self) -> int | None:
    return self._iobound_tpe_limit

TPE likely refers to ThreadPoolExecutor. 
This property defines the maximum number of threads for IO-bound
tasks. 
Snowflake performs: 
    - Parallel result fetching
    - File transfer
    - Network operations
* It exists to prevent resource exhuastion, tine performance, 
and adapt to constrained envrionments. 
* It is a concurrency control parameter. 
"""

#   def unsafe_file_write(self) -> bool:
"""
@property
def unsafe_file_write(self) -> bool:
    return self._unsafe_file_write

@unsafe_file_write.setter
def unsafe_file_write(self, value: bool) -> None:
    self._unsafe_file_write = value

Thier own description:
            unsafe_file_write: When true, files downloaded by 
            GET will be saved with 644 permissions. Otherwise, 
            files will be saved with safe - owner-only 
            permissions: 600.
* Basically, the owner gets read and write permission while 
group and others only get read access if this is set to true
* False (default) → files saved with 600 permissions (owner-only)

Note: by defaulting to 600, they ensure that no accidental 
data exposure to other OS users. 
    This is especially useful where the envrionments require
    shared file access. 
"""

#     def check_arrow_conversion_error_on_every_column(self) -> bool:
"""
@property
def check_arrow_conversion_error_on_every_column(self) -> bool:
    return self._check_arrow_conversion_error_on_every_column

@check_arrow_conversion_error_on_every_column.setter
def check_arrow_conversion_error_on_every_column(self, value: bool) -> bool:
    self._check_arrow_conversion_error_on_every_column = value

This is a controller for data conversion since Snowflake returns 
results in Arrow format so they must be converted into python 
objects. 
    - This can lead to type mismacthes or conversion errors 
NOTE: Historically, there was a bug where type errors occuring
before the last column in a row could silently pass

This flag enforces a stricter validation pass:
    True → check every column for conversion errors
    False → previous (buggy) behavior
"""

#    def snowflake_version(self) -> str:
"""
@cached_property # NOTE: cached property, although im pretty sure 
# It will get sent to an l4 cache since unless you constantly reach
# for it for logging, there is not need for this 
def snowflake_version(self) -> str:
    # The result from SELECT CURRENT_VERSION() is `<version> <internal hash>`,
    # and we only need the first part
    return str(
        self.cursor().execute("SELECT CURRENT_VERSION()").fetchall()[0][0]
    ).split(" ")[0]

This runs the query SELECT CURRENT_VERSION() once, strips the ash, caches
the semantic version and keeps it for the lifetime fo the connection. 

The purpose it being that it gates features based on the server version, 
enables forward and backward compatbility then adjusts based on that..
Lastly: telemetry and logging

@cached_property ensures:
    - Only one network call; no repeated latency and stable value
    for the entire session

"""



"""
Questions:
1.     @cached_property
        def snowflake_version(self) -> str:
What is the under the hood implementation of this? When is it 
transported from L1->L2...->L4->MM
        

"""