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