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