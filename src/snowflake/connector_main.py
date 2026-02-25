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

