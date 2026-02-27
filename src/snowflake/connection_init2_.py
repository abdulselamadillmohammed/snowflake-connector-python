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