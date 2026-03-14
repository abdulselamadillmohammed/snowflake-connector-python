# previously

"""

We checked if existing tokens existed and if they are still valid; 
if so we can continue the session which would have been useful for 
connection pooling and continuing sessions from the previous time.

That is to say, the session can continue without logging in again

"""

# 2. No existing tokens -> Start authentication setup
"""
    Since we arived at the else case, we know that there are 
    not existing tokens or they are no valid so we start the 
    authentication processess.

else:

    This else corresponds to:

        if self._session_token and self._master_token:

        So this path runs when:

    No session token exists

    OR

    No master token exists

    Meaning:

        We must perform a new login

"""

# 3. If a custom authentication class was provided

"""
# The first check if a wide cast of possiblitliy capturing in that 
if the auth class is not None we can perform the step;

that is to say if the auth class was provided previously, we can just 
set it to that. 

if self.auth_class is not None:
    if type(
        self.auth_class
    ) not in FIRST_PARTY_AUTHENTICATORS and not issubclass(
        type(self.auth_class), AuthByKeyPair
    ):
        raise TypeError("auth_class must be a child class of AuthByKeyPair")
        # TODO: add telemetry for custom auth
    self.auth_class = self.auth_class
# match authentivator - validation happens in __config

If the user passed in thier auth authenticator, the driver 
will perform a check if it valid and if not; it will raise 
an error

Allowed cases:

1. A Snowflake built-in authenticator
2. A subclass of AuthByKeyPair

The reason being:
    Because key-pair authentication 
    is the only officially supported custom extension point.

error handing:
    raise TypeError("auth_class must be a child class of AuthByKeyPair")

telemetry:
    Snowflake engineers want to add telemetry to track when 
    people use custom authentication plugins.


* self.auth_class = self.auth_class
    - This triggers the setter for the auth class

    @auth_class.setter
    def auth_class(self, value: AuthByPlugin) -> None:
        if isinstance(value, AuthByPlugin):
            self._auth_class = value
        else:
            raise TypeError("auth_class must subclass AuthByPlugin")

"""

# next check
"""
You check if the authenticator the user has is the default 
authenticator:

    elif self._authenticator == DEFAULT_AUTHENTICATOR:
        self.auth_class = AuthByDefault(
            password=self._password,
            timeout=self.login_timeout,
            backoff_generator=self._backoff_generator,
        )

The backoff generator controls the retry pattern
1s
2s
4s
8s
* This protects against transient failures.
"""

# 10. External Browser Authentication (SSO)
"""
    elif self._authenticator == EXTERNAL_BROWSER_AUTHENTICATOR:

SSO: single sign on

Example login:
    Okta
    Azure AD
    SAML
    OAuth

Instead of password login, Snowflake opens a browser

11. Enable Credential Caching
    self._session_parameters[
        PARAMETER_CLIENT_STORE_TEMPORARY_CREDENTIAL
    ] = (self._client_store_temporary_credential if IS_LINUX else True)

This allows the connector to store temporary SSO tokens locally.

Why?
So the user doesn't need to re-login every time.

Behavior:
    Linux → configurable
    Mac/Windows → always enabled

This is because Linux environments are often servers where credential 
caching might be undesirable.

"""

# 12. Attempt to Load Cached Credentials
"""
auth.read_temporary_credentials(
    self.host, 
    self.user, 
    self._session_parameters,
)
This checks if a cached SSO token already exists

Possible storage locations include:
    ~/.snowsql/
    system keychain
    OS credential store

if found: 
    no browser login needed
"""

# 13. Check Whether an ID Token Exists
"""
if self._rest.id_token is None:

Meaning:
    No cached SSO token available

So the user must authenticate interactively

"""

# 14. Browser-based login
"""
self.auth_class = AuthByWebBrowser(
    application=self.application,
    protocol=self._protocol,
    host=self.host,
    port=self.port,
    timeout=self.login_timeout,
    backoff_generator=self._backoff_generator,
)

The flow works as:

    Connector opens browser
        ↓
    User logs into SSO provider
        ↓
    Provider returns SAML/OAuth token
        ↓
    Snowflake converts it to session tokens

On the other hand! If the token in cached!

else:
    self.auth_class = AuthByIdToken(

This happens when:

SSO token already cached

So instead of browser login:

reuse existing identity token
"""

# 16. ID Token Authentication
"""
    else:
        self.auth_class = AuthByIdToken(
            id_token=self._rest.id_token,
            application=self.application,
            protocol=self._protocol,
            host=self.host,
            port=self.port,
            timeout=self.login_timeout,
            backoff_generator=self._backoff_generator,
        )

The authenticator:
   sends the ID token directly to Snowflake

Flow:
    cached SSO token
        ↓
    send to Snowflake login endpoint
        ↓
    receive session_token + master_token

No browser required. 

"""

# The big picture
"""
existing tokens?
        │
        ├─ yes → validate tokens
        │
        └─ no → determine authentication method
                    │
                    ├─ custom authenticator
                    │
                    ├─ username/password
                    │
                    └─ SSO browser login
                          │
                          ├─ cached token → AuthByIdToken
                          └─ no token → AuthByWebBrowser
"""

# Continuing with the descion tree
"""
At this point, the connector is selecting which authentication 
mechansim to use based on the value of:
    self._authenticator

Earlier you saw:
    - Password login, 
    - Browser SSO
    - Cached SSO tokens 

Now we move into programmatic authentication methods.
"""

# 1. Key pair authentication (RSA authentication)
"""
elif self._authenticator == KEY_PAIR_AUTHENTICATOR:

* This authentication type uses public/private key crypotography instead
of passwords.

Typical Snowflake configuration:        
    ALTER USER myuser SET RSA_PUBLIC_KEY='MIIBIjANBgkqh...'
Then the client authenticates using the matching private key
"""

# 2, Load private key from memory
"""
private_key = self._private_key
private_key_passphrase = self._private_key_passphrase

The connector supports two ways tto supply the key:
    1. direclty as a key object
    2. via a private key file

Here it starts with the in-memory key if provided
"""

# 3. Load Private key from file (if specified)
"""
if self._private_key_file:
    private_key = _get_private_bytes_from_file(
        self._private_key_file,
        self._private_key_file_pwd,
    )

if the user passed:
    private_key_file="/path/to/key.pem"
* the connector reads it from disk

The helper function _get_private_bytes_from_file(..)
does things like read the PEM file, decrypt it if
encrypted and return the raw key bytes

Example key file:
-----BEGIN PRIVATE KEY-----
MIIEvQIBADANBgkqhki...
-----END PRIVATE KEY-----

"""

# 4. Create Key Pair Authenticator
"""
self.auth_class = AuthByKeyPair(
    private_key=private_key,
    private_key_passphrase=private_key_passphrase,
    timeout=self.login_timeout,
    backoff_generator=self._backoff_generator,
)

The authentication method works like this:
    client signs login request with RSA private key
            ↓
    Snowflake verifies signature using stored public key
            ↓
    if valid → issue session tokens

Benefits:
    no passwords
    common for automated services
    widely used in CI/CD pipelines
"""

# 5. OAuth Token authentication
"""
elif self._authenticator == OAUTH_AUTHENTICATOR:
This is a token-based OAuth login; instead of username/password 
or SSO:

client already has an OAuth token

Example usage:
connect(authenticator="oauth", token="eyJhbGciOi...")
"""

# 6. Create OAuth Authenticator
"""
self.auth_class = AuthByOAuth(
    oauth_token=self._token,
    timeout=self.login_timeout,
    backoff_generator=self._backoff_generator,
)

This is the simplest OAuth flow.

Process:
    client obtains OAuth token elsewhere
            ↓
    connector sends token to Snowflake
            ↓
    Snowflake validates token with IdP
            ↓
    session tokens issued

This is common when integrating with:
    Okta
    Azure AD
    enterprise identity providers
"""

# 7. OAuth Authorization Code flow
"""
elif self._authenticator == OAUTH_AUTHORIZATION_CODE:

This is a full OAuth2 autherization code flow

Used when the connector itself must perform the OAuth process.

TYpical OAuth flow:

client → authorization server
        ↓
user login
        ↓
authorization code returned
        ↓
exchange for access token
"""

# 8. Inject Role into OAuth scope
"""
    if self._role and (self._oauth_scope == ""):
        # if role is known then let's inject it into scope
        self._oauth_scope = _OAUTH_DEFAULT_SCOPE.format(role=self._role)

    If the user specified a Snowflake role but no OAuth scope:
role = "ANALYST"
scope = ""
    The connector automatically generates a scope
"""

# 9. Generate Default OAuth Scope
"""
self._oauth_scope = _OAUTH_DEFAULT_SCOPE.format(role=self._role)
Example result:

scope = "session:role:ANALYST"

This tells Snowflake:

issue token with this role activated
"""

# 10. Create OAuth Code Authenticator
"""
self.auth_class = AuthByOauthCode(
This authenticor performs the full OAuth autherization code exchange

Parameters:

client_id=self._oauth_client_id
client_secret=self._oauth_client_secret

These idenitfy the application to the OAuth provider

Eaxmple:
client_id = "snowflake-python-app"
client_secret = "abc123"


authentication_url=self._oauth_authorization_url.format(
    host=self.host, port=self.port
)
This is where the user is sent to autherize the app. 

Example:
https://login.microsoftonline.com/.../authorize
User sees login page

token exchange url:
token_request_url=self._oauth_token_request_url.format(
    host=self.host, port=self.port
)

After receiving an authorization code:
POST /token
to exchange it for:
access_token
refresh_token

Redirect URI
redirect_uri=self._oauth_redirect_uri

OAuth requires a callback URL

Example:
    http://localhost:3037/callback
After login:
    OAuth server redirects browser here

Local Socket Listener:
uri=self._oauth_socket_uri
The connector often starts a temporary local sever to receive
the OAuth callback. 

Example:
    http://127.0.0.1:3037
This is how the authorization code is captured. 

---

OAuth Scope:
    scope=self._oauth_scope

Defines what permissions the token grants. 

Example:    
    session:role:ANALYST

PKCE Secuirity
pkce_enabled=not self._oauth_disable_pkce

PKCE = Proof Key for Code Exchange

Adds extra protection against interception attacks. 

Flow:
    client creates code_verifier
            ↓
    hash sent in authorization request
            ↓
    verifier sent during token exchange

This prevents attackers from stealing the authorization code. 


Token cache:
token_cache=(
    auth.get_token_cache()
    if self._client_store_temporary_credential
    else None
)

If enabled:
OAuth tokens stored locally 
So next login can reuse them 

Refresh token support:
    refresh_token_enabled=self._oauth_enable_refresh_tokens

    If true:
        connector can renew expired tokens automatically

Flow:
    access_token expires
            ↓
    connector uses refresh_token
            ↓
    new access_token issued

20. Browser Timeout
    external_browser_timeout=self._external_browser_timeout

Limits how long the connector waits for the OAuth login to 
complete. 

Example:
    timeout = 120 seconds. 

Single Use Refresh tokens:
enable_single_use_refresh_tokens=self._oauth_enable_single_use_refresh_tokens

Some identify providers issue refresh tokens that can only be used once. 
This flag tells the connector to support that behaviour. 

Big picture:

At this stage the driver supports multiple authentication systems:

password login
SSO browser login
cached SSO tokens
RSA key pair authentication
OAuth token authentication
OAuth authorization code flow

The code is basically building the correct Auth strategy object:

AuthByDefault
AuthByWebBrowser
AuthByIdToken
AuthByKeyPair
AuthByOAuth
AuthByOauthCode

Later the connector simply calls:
auth.authenticate(auth_class)

without caring which method is used.
"""