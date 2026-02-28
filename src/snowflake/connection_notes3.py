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