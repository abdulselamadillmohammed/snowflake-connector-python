"""
we are still inside the authentication strategy selection block.

At this stage the connector is choosing among many exterprise 
authentication methods beyond the basic ones. 

I'll go through each section in order and explan what Snowflake is
doing internally. 
"""

# Ventral hippocampal inputs to the nucleus accumbens regulate anxiety-related behavior.
"""
elif self._authenticator == OAUTH_CLIENT_CREDENTIALS:

This is the OAuth2 Client Credentials Grant.

Unlike the OAuth2 Authorization code flow, this one is machine
to machine authentication

TYpical scenatio:
    backend service -> snowflake

    No user interaftion. 

Eaxmple identify flow:
    Service -> Identity provider
            -> receives access_token
            -> uses token to authenticate to Snowflake 

Inject Role into Oauth scope:
if self._role and (self._oauth_scop == "")
If the user configured a role but did not specify an OAuth scope,
the connector automatically constructs one. 

scope = session:role:<ROLE_NAME>

self._oauth_scope = _OAUTH_DEFAULT_SCOPE.format(role=self._role)

Example result:
session:role:ANALYST

That tells Snowflake which role the token should activate 

Create Oauth Credentials Authenticator 
self._oauth_scope = _OAUTH_DEFAULT_SCOPE.format(role=self._role)
This class performs the Oauth client credential token request.

Key parameters: application
application=self.application

used for telemetry and cleint identification. 

OAuth client credentials
    client_id = self._oauth_client_id
    client_secret=self._oauth_client_secret

These identify the application to the identity provider. 

Example:
    client_id = "snowflake-python-app"
    client_secret = "abc123"

Token endpoint:

    token_request_url=self._oauth_token_request_url.format(
    host=self.host, port=self.port
    )

This is where the connector sends:
    POST /oauth/token        
Example request:
    grant_type=client_credentials
    client_id=...
    client_secret=...
    scope=...

credentials_in_body
    credentials_in_body=self._oauth_credentials_in_body
Some OAuth providers expect:
    client_id + client_secret
In the HTTP body instead of the authorization header
This flag controls that behavior.

Connection reference:
    connection=self

The authenticator sometimes needs access to connection configuration. 

2. Username/Password + MFA Authentication

elif self._authenticator == USR_PWD_MFA_AUTHENTICATOR:

The method supports:
    username + password + MFA

Example:
    password login
    → push notification
    → OTP code

Enable MFA Token Caching
self._session_parameters[PARAMETER_CLIENT_REQUEST_MFA_TOKEN] = (
    self._client_request_mfa_token if IS_LINUX else True
)

This enables MFA token caching

Meaning:
    after successful MFA login
    token saved locally

So future logins can skip the MFA prompt

Behavior:
    Linux → configurable
    Mac/Windows → always enabled

Try loading cached MFA token
    auth.read_temporary_credentials(
        self.host,
        self.user,
        self._session_parameters,
    )
If an MFA token already exists locally:
    skip MFA challange
Otherwise the user must complete MFA.

Create MFA Authenticator

self.auth_class = AuthByUsrPwdMfa(
    password=self._password,
    mfa_token=self.rest.mfa_token,
    timeout=self.login_timeout,
    backoff_generator=self._backoff_generator,
)

Login flow:
username + password
        ↓
Snowflake triggers MFA challenge
        ↓
user approves
        ↓
session tokens issued

if a cached MFA token exists:
challenge skipped

3. Programmatic Access Token (PAT)

elif self._authenticator == PROGRAMMATIC_ACCESS_TOKEN:

A programmatic access token is similar to:  
    GitHub personal access tokens
* It is a pre-issued token used for authentication

Create PAT Authenticator 
    self.auth_class = AuthByPAT(self._token)
Login flow:
    client sends PAT
    Snowflake validates token
    session tokens returned

Used mainly for:
    automation
    API integrations
    scripts

4. PAT with External Session (Spark Integration)
elif self._authenticator == PAT_WITH_EXTERNAL_SESSION:
This is a special integeration mode used by systems like:
    Apache Spark
The key idea:
    Snowflake session already exists
So the connector does not perform normal login

Skip Authentication
    self.auth_class = AuthNoAuth()
This authenticator does nothing

Register PAT + External Session
self._rest.set_pat_and_external_session(
    self._token, self._external_session_id
)
Snowflake Identifies sessions using:
    (PAT, external_session_id)

So the first time this pair appaears:
    Snowflake creates a new Session

After that:
Same pair - > same session

This avoids repeated login requests


5. Workload identify authentication
    elif self._authenticator == WORKLOAD_IDENTITY_AUTHENTICATOR:
    
This is cloud workload identity federation.

Instead of passwords or keys, the connection authenticates using
cloud provider identity tokens. 

Supported providers include:
    AWS
    GCP
    Azure (Entra)

Example scenario:
    AWS Lambda -> Snowflake

No credentials stored in the code,

Convert Provider String to Enum

if isinstance(self._workload_identity_provider, str):

This user may pass:
"aws"
"gcp"

The connector converts it to an internal enum:
    AttestationProvider.from_string(...)

Validate Provider:  
    if not self._workload_identity_provider:

If no provider was configured, raise an error.
Error message:
    
    workload_identity_provider must be set to one of ...


Validate Impersonation Path:
if (
    self._workload_identity_impersonation_path
    and self._workload_identity_provider
    not in (
        AttestationProvider.GCP,
        AttestationProvider.AWS,
    )
)

Impersonation is only supported on:
    AWS
    GCP
    And not Azure

So if someone tries:
Azure + impersonation
The connector throws an error.

Create workload identify Authenticator:
    self.auth_class = AuthByWorkloadIdentity(..)

Parameters include:
    provider: provider=self._workload_identity_provider

    Example:
        AWS
        GCP

Token:
    token=self._token
Blaod identity token is provided by the workload.

entra_resource:
    entra_resource=self._workload_identity_entra_resource
Used for Azure Extra identity federation. 

Impersonation_path
    impersonation_path=self._workload_identity_impersonation_path

Allows impersonating another identity

Example: AWS role chain

6. Default Case -> OKTA Authentication

Okta is a cloud-based Identity and Access Management (IAM) service 
that securely connects users to applications, acting as a 
centralized, secure login portal. It enables Single Sign-On (SSO) 
and Multi-Factor Authentication (MFA), allowing employees to access 
all necessary apps with one set of credentials from any device 
while protecting data. 

Else:
if the authenticator value didn't match any earlier type, the connector
assumes: Okta Authentication


Create Okta authenticator

self.auth_class = AuthByOkta(

Parameters: 

application=self.application
timeout=self.login_timeout
backoff_generator=self._backoff_generator

This supports Okta SAML authentication. Flow: 
client → Okta login page
       → user authentication
       → Okta returns SAML assertion
       → Snowflake converts to session token

This section implements a huge authentication decision tree:

Supported methods include:

password login
browser SSO
cached SSO tokens
RSA key authentication
OAuth token authentication
OAuth authorization code flow
OAuth client credentials flow
username/password + MFA
programmatic access tokens
PAT with external sessions
workload identity federation
Okta SAML authentication

Alll of these ultimately produce an Auth strategy object:
AuthByDefault
AuthByWebBrowser
AuthByIdToken
AuthByKeyPair
AuthByOAuth
AuthByOauthCode
AuthByOauthCredentials
AuthByUsrPwdMfa
AuthByPAT
AuthByWorkloadIdentity
AuthByOkta

Later the connector simply executes: 
auth.authenticate(self.auth_class)
without caring which mechansim was used. 

"""

# Execute Authentication:
"""
self.authenticate_with_retry(self.auth_class)

This is the key moment
Everything before this was just:
    choosing strategy
This line actually does:    
    send login request to Snowflake 

What authenticate_with_retry conceptually does:
    This of it like:

try:
    auth.authenticate()
except transient error:
    retry with backoff

So internally:
   AuthByX.authenticate()
        ↓
build request payload
        ↓
POST /session/v1/login-request
        ↓
receive:
    session_token
    master_token

Why with retry?
Because login can fail due to:  
    - Network hiccups 
    - DNS issues
    - Temporary Snowflake outages

So instead of failing immediately:
    retry with exponential backoff

Clear Sensitive Data:   
self._password = None  # ensure password won't persist

Why this matters:
After authentication:
    Password is no longer needed

Keeping it in memory would be a security risk.
So they explicitly wipe it.

Real world implication:
    prevents:   
        - Accidental logging 
        - Memory dumps exposing credentials
        - Debugging leaks

4. Reset Auth secrets. 

self.auth_class.reset_secrets()

Each authenticator may store senitive data like:
    - passwords
    - private keys
    - OAuth tokens 
    - MFA tokens

This call tells the auth object:
    wipe any sensitive internal state.

So now:
    connection is authenticated
    no secrets remain in memory

5. Initalize query context cache
self.initialize_query_context_cache()

What this is:
    Snowflake uses a query context cache to store metadata about queries
Think:  
    query -> metadata -> cached locally 

Examples of cached info:
    query IDs
    result metadata
    execution context
    session state

Why this exists
    - improves perfromance for: 
        - repeated queries
        - result reuse 
        - metadat lookups 

Conceptually:
    connection starts
            ↓
    create empty cache structure
            ↓
    future queries populate it

6. Enable heartbeat (Keep Session Alive)
    if self.client_session_keep_alive:

If earlier you enabled 
    client_session_keep_alive = True

then:

Start heartbeat mechansim:
    self._add_heartbeat()

What this does

Starts a background process/thread that:    
    Peroidically calls:
        /session/heartbeat


Why?
    without heartbeat:  
        idle session -> expires

    With heartbeat:  
        idle session -> stays alive



Important detail from comment:
# heartbeat frequency has already been decided earlier

So there its just: activate the mechanism

Transision point:
✔ authenticated
✔ session tokens acquired
✔ secrets cleared
✔ cache initialized
✔ optional heartbeat running

The connection is now fully extablished and ready to execute queires. 

"""

# 7. Enter __config Method
"""
Now we move into:
    def __config(self, **kwargs):

This is configuration parsing + validation

# 8. Debug Log
logger.debug("__config")

Just logs that config is being processsed. 


9. Special Case Handling:
    a) Sequence Counter

    if "sequence_counter" in kwargs:
        self.sequence_counter = kwargs["sequence_counter"]

    Used internally for:
        request ordering
        retry tracking


b) Application Name validation:

    if "application" in kwargs

1. validate format:
    if not APPLICATION_RE.match(value):

This enforces: application name follows allowed pattern
Example calid: 
"MyApp"
"SnowflakeConnector"
Invalid:
"My App!!!"

Raise error if invalid:
    raise ProgrammingError(msg=msg, errno=0)

Otherwise store it:
    self._application = value

c) Validate Default Parameters Flag
    if "validate_default_parameters" in kwargs:
Just stores the flag you saw earlier

10. Skip List
skip_list = ["validate_default_parameters", "sequence_counter", "application"]
These were already handled manually, so skip them in the generic loop. 

11. Process Remaining Parametrs
for name, value in filter(...):

This loops over all other conneciton paaramters.

Example:
user
password
account
warehouse
timeout
...

12. Paramter Validation (if enabled)
if self.validate_default_parameters:
    If validation is ON, do two checks. 

a) Unknown Parameter Detection 
    if name not in DEFAULT_CONFIGURATION.keys():
        If user passes
    connect(userr="abc")  # typo

    suggest correction
    get_close_matches(...)

    Example:    
        'userr' -> did you mean 'user'?

Emit warning:   
    warnings.warn(...)

Important:
    does NOT crash
only warns 

b) Type Checking
elif not isinstance(value, DEFAULT_CONFIGURATION[name][1]):

Each paramter has an expected type:
    Example:    
        "user" -> str
        "port" -> int 

If wrong type:
    connect(port="not_a_number")

You get:
    warning: expected int but got str 

13. Store Patameter
setattr(self, "_" + name, value)

This is important

It converts:
    user="abc"
into:
    self._user = "abc"

Why prepend _?

Because:
_public API → properties
_internal storage → _variables

This ties back to the earlier quesiton about @property

Big picture; this section does two major things:

1. Finalize Authentication
    auth strategy chosen
            ↓
    authenticate_with_retry()
            ↓
    session tokens obtained
            ↓
    secrets wiped
            ↓
    connection fully established

2. Configure Connection Object 
    parse kwargs
        ↓
    validate parameters
            ↓
    warn on mistakes
            ↓
    store as internal attributes


Key insight: The design here is very clean:

Phase 1: Configuration:
    __config()
Phase 2: Authentication Strategy Selection
    if authenticator == ...
Phase 3: Authentication Execution
    authenticate_with_retry()
Phase 4: Post-Auth Setup
    heartbeat
    cache
    cleanup
"""

# if self._numpy:
"""
if self._numpy:
    try: 
        import numpy 
    except ModuleNotFoundError:
        Error.errorhandler_wrapper(...)

This means: 
    If the user aksed Snowflake to return results in NumPy form, 
    make sure NumPy is actually installed. 
So if someone configured the connection in a way that expcets NumPy-
backend fetching, but the package is missing, the connector raises a 
Snowflake-style error instead of later failing unpredictbly

The purpose is basically:
    requested feature -> check dependency now

instead of:
    connect sucessfully -> crash much later when fetching results 

2. Paramstyle defaulting and validation
if self._paramstyle is None:
    import snowflake.connector
    self._paramstyle = snowflake.connector.paramstyle
elif self._paramstyle not in SUPPORTED_PARAMSTYLES:
    raise ProgrammingError(...)

This is about how SQL parameter placeholders are written. 

Exammples from Python DB APIs are things like: 
    - qmark -> ?
    - format -> %s
    - pyformat -> %(name)s

What this block does is:

If the user did not specify one:
    use the connector's default global paramstyle.
If user did specify one:    
    make sure it is one Snowflake supports. 

So this protects against something like:
    paramstyle = "weirdstyle"
which would break query binding later. 

3. Validate custom auth class type:
    if self._auth_class and not isinstance(self._auth_class, AuthByPlug)
        raise TypeError("auth class must subclass AuthByPlugin")

This says:  
    if the user supplied a custom authenticator object, it must belong
    to Snowflake's authentication plugin system. 

So they are enforcing a contract here. The connector expects the auth 
object to have a certain interface and behavior. If you pass some random
object, it stops immediately rather than breaking later during login. 

4. Build host from account if needed. 

if "account" in kwargs:
    if "host" not in kwargs:
        self._host = construct_hostname(kwargs.get("region"), self._account)

This is important.
    If the user gives an account name but not explicit hostname, the
    connector derives the hostname automatically. 

Conceptually:   
    account + region -> Snowflake host
For example, instead of requiring the user to provide:
    xy12345.us-east-1.snowflakecomputing.com    

They can often just provide the account/region info, and the connector 
constructs the host itself. 
"""

# 5. Log which Snowflake domain is being used
"""
loggger.info(
    f"Connecting to {_DOMAIN_NAME_MAP.get(...)} Snowflake domain"
)

This is just informational logging, but it is useful in debugging. 

It tells you what top-level snowflake domain the computed host 
belongs to, such as global or some other deployment domain. 
So this is mostly:
    debug visibiloty for connection target:
    rather than functional logic. 

6. If custom auth class exists, derive authenticator from it

if self._auth_class:
    self._authenticator = self._auth_class.type_.value

This means: 
    When a custom auth object is supplied, let that object define
    what authenticator type the connection should consider itself
    to be using. 

So instead of trusting a seperate string like:  
    authenticator="externalbrowser"

The connector says:
    the auth plugin itself is the source of the truth. 

That avoids mismatch between:
    - The actual auth object
    - The string authenticator name

7. Otherwise validate the authenticator string 
elif self._authenticator:
    auth_tmp = self._authenticator.upper()

if there is no custom auth class, but there is an authenticator string, 
normalize it to uppercase first.

Why? Because user may pass:
    oauth
    OAuth
    OAUTH
and the connector wants consistent interna comparison
"""

# 8. Accept only known built-in authenticators
"""
if auth_tmp in [
    DEFAULT_AUTHENTICATOR,
    EXTERNAL_BROWSER_AUTHENTICATOR,
    KEY_PAIR_AUTHENTICATOR,
    ...
]:
    self._authenticator = auth_tmp

This is the official whitelist of recognized authenticator modes. 

So this block is essentially saying:
    Only these known authentication modes are legal. 

This prevents typos and unsupported values from silently slipping 
through.
"""

# 9. Special case: Okta URL
"""
elif auth_tmp.startswith("HTTPS://"):
    # okta authenticator link
    pass
    
This is a nice detail. 

Most authenticators are symbolic constants like:
OAUTH
EXTERNALBROWSER
SNOWFLAKE_JWT

but Okta can be provided as an actual URL, like:
    https://mycompany.okta.com/
if it starts with HTTPS://, they treat it as valid Okta authenticator 
and leave it alone


So this branch means:
    not a named mode
    but still valid because it is an Okta URL
"""


# 10. reject unknown authenticator values
"""
else:
    raise ProgrammingError(
        msg=f"Unknown authenticator: {self._authenticator}",
        errno=ER_INVALID_VALUE,
    )

If the authenticator is neither:    
    - one of the recognized constants 
    - nor an Okta HTTPS URL

then it is invalid. 
This is just hard validation to catch bad config early. 
"""

# 11. Read OAuth token from file is requested
"""
token_file_path = kwargs.get("token_file_path")
if token_file_path:
    with open(token_file_path) as f:
        self._token = f.read()

This lets the user provide the OAuth token indirectly through
a file instead of embedding it directly in code. 

So instead of:  
    token="abc..."
They can do:    
    token_file_path="/path/to/token.txt"

Purpose:
    - cleaner secret handling
    - easier automation
    - avoids hardcoding token in source code
"""

# 12. Define which authenticators allow empty user
"""
empty_user_allowed_authenticators = {
    OAUTH_AUTHENTICATOR,
    NO_AUTH_AUTHENTICATOR,
    WORKLOAD_IDENTITY_AUTHENTICATOR,
    ...
}

This set answers the question:
    Are there auth models where a username is optional or unnecessary?
And the answer is yes. 

For example, some token-based or workload-based mechanims identify the
caller through the token itself, not through a separate username field. 
"""

# 13. Only run these checks if we are not already reusing session/
#master tokens 
"""
if not (self._master_token and self._session_token):

If both tokens already exist, the connector may be reusing an 
authentication session, so some normal login requrements can be skipped. 

If not, then it must validate the credentials needed for a fresh 
authentication. 
"""

# 14. Enforce username when required
"""
if (
    not self.user
    and self._authenticator not in empty_user_allowed_authenticators
):
    Error.errorhandler_wrapper(...)

This says:
    If no user was supplied, and the chosen auth mode is not 
    one of the exceptuons, then that is an error. 

So tradional methods like password-based auth still require a 
username. Token-based methods may not. 
"""

# 15. Auto-switch to key pait auth if a private key was supplied 
"""
if self._private_key or self._private_key_file:
    self._authenticator = KEY_PAIR_AUTHENTICATOR

This is an important convenience behavior. 

If the user supplies private key material, the connector automatically 
infers:
    you want key pair authentication
even if they did not explicitly set the authenticator string. 

So the presence of key material overrides and selects the correct mode. 
"""

# 16. Workload identity dependent options must only be used with workload
# identity auth
"""
workload_identity_dependent_options = [
    "workload_identity_provider",
    "workload_identity_entra_resource",
    "workload_identity_impersonation_path",
]
These options are only meaningful for workload identiy federation.
so they then loop through and check:

if option is set and authenticator != WORKLOAD_IDENTITY_AUTHENTICATOR:
    error

This prevents nonsensical configs like:
    authenticator = OAUTH
    workload_identity_provider = AWS

    
That would miz unrelated auth systems. 

So the purpose is strict config consistency. 

17. Require password when the chosen aith flow still needs one

if (
    self.auth_class is None
    and self._authenticator
    not in (
        EXTERNAL_BROWSER_AUTHENTICATOR,
        OAUTH_AUTHENTICATOR,
        OAUTH_AUTHORIZATION_CODE,
        OAUTH_CLIENT_CREDENTIALS,
        KEY_PAIR_AUTHENTICATOR,
        PROGRAMMATIC_ACCESS_TOKEN,
        WORKLOAD_IDENTITY_AUTHENTICATOR,
        PAT_WITH_EXTERNAL_SESSION,
    )
    and not self._password
):
    Error.errorhandler_wrapper(...)

This big condition is basicaly:
    if there is no custom auth class, and the chosen auth mode 
    is not one of the methods that can operate wihout a password, 
    then password must be present. 

So for a normal password-based login, this protects against:
connect(user="alice", account="x", password=None)
and raises "Password is empty" 
"""

# 18 Require account unless using AuthNoAuth
"""
if not self._account and not isinstance(self.auth_class, AuthNoAuth):
    Error.errorhandler_wrapper(...)

Snowflake generally needs an account identifier to know where to 
connect. 

The one special exception is AuthNoAuth, because that mode bypasses
normal login/session setup behaviour

So this means:
    almost every real conneciton requires account

"""

# 19. Normalize dotted account identifiers
"""
if self._account and "." in self._account:
    self._account = parse_account(self._account)

If the account string contains dots, Snowflake normalizes/parses it. 

This is usually for account identifiers that include extra domain-
style or region-style pieces. The connector trims/parses it into the 
canonical account form it expects internally. 
"""

# Big picture:
"""
This block is doing four major jobs:

1. Feature/dependency valuidation
    Example: NumPy support

2. Authentication normalization 
    It figures out what authenticator is really being used and validates
    that it is legal

3. Credential requirement checks
    It decides whether user, password, token, private key, account, 
    or workload identiy settings are required for the chosen auth 
    mode. 

4. Canonicalization
    It normalizes things like host, authenticator casing, token loading, 
    and account format. 

So structurally this is the connector saying:
    before I attempt login,
    I want the configuration to be internally consistent,
    complete,
    and normalized.    

That is why this section matters so much. 

"""