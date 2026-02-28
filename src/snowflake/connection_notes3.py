#     def crl_download_max_size(self) -> int | None:
"""
@property
def crl_download_max_size(self) -> int | None:
    "Maximum CRL file size in bytes."
    if not self._crl_config:
        return self._crl_download_max_size
    return self._crl_config.crl_download_max_size

This is a tool which returns the maximum allowed size in bytes 
for a downloaded CRL file 

* CRLs are downloaded from remote servers and without a size cap;
a malicious sever could return a huge file which can lead to memory
or disk exhuastion and you would be at risk of denial of service 
attacks
* This settings protects against oversized CRL downloads
"""

#    def skip_file_permissions_check(self) -> bool | None:
"""
@property
def skip_file_permissions_check(self) -> bool | None:
    "Whether to skip file permission checks for CRL cache files."
    if not self._crl_config:
        return self._skip_file_permissions_check
    return self._crl_config.skip_file_permissions_check

    
What this does:
    - It returns a decider of whether the connector should skip 
permission validation on CRL cache files.

The reason this exists is because when writing CRLs to disk, the 
connector may check:
    - File mode (e.g., not world-writeable)
    - Owner permissions 
    - Security constraits

What skipping permission checks would mean:
    - It is useful for restricted envrionments 
    - May be needed on certain filesystems 
    - Reduced security guarantees

* This is a tradeoff between strict security and envrionment 
flexibility
"""

#     def session_id(self) -> int:
"""
@property
def session_id(self) -> int:
    return self._session_id

This returns the Snowflake session ID assignmed by the server after 
authentication. 

No legacy fallback; no structured config and just exposes a private 
attribute 

session_id represents a unique identifier for the authenticated 
session which is used internally for query tracking, logging,
telemetry and server side correlation

* Note: after connect() runs successfully: self._session_id is populated
via the server response

"""

"""
| Property                      | Purpose                                      |
| ----------------------------- | -------------------------------------------- |
| `crl_download_max_size`       | Prevent oversized CRL downloads              |
| `skip_file_permissions_check` | Control CRL cache file security validation   |
| `session_id`                  | Expose server-assigned connection session ID |

"""

#       def user(self) -> str: 
"""
    @property
    def user(self) -> str:
        return self._user

It returns the authenticated username associated with the connection
    - _user is set during connect() -> inside __config() when kwards
    are processed
    - This is read-only
    - Exposes connection metadata safely
    
"""

#     def host(self) -> str:
"""
    @property
    def host(self) -> str:
        return self._host

This returns the Snowflake hostnmae being currently used;

Example:

abc123.us-east-1.snowflakecomputing.com
    1. where * _host is computed during connection setup.
    2. Exposed read-only \Used for degguing 

    
ESENOTE:
"""