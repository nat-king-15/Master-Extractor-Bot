"""
APPX Token and API authentication module.
Reconstructed from appx_token.so (database/appx_token.py).
Provides APPX API authentication headers used by Appx extractor modules.

The APPX API uses static API key authentication (Auth-Key header),
not JWT bearer tokens. This is consistent across all workspace projects.
"""

# APPX API static authentication key
# Used in headers as: {"Auth-Key": "appxapi", "Client-Service": "Appx"}
# Found in: freeappx.py, appex_v4.py, check.py, getappxotp.py, mix.py
APPX_AUTH_KEY = "appxapi"
APPX_CLIENT_SERVICE = "Appx"

# Default APPX API headers used by all Appx extractors
APPX_HEADERS = {
    "Auth-Key": APPX_AUTH_KEY,
    "Client-Service": APPX_CLIENT_SERVICE,
    "Content-Type": "application/x-www-form-urlencoded",
    "User-Agent": "okhttp/3.12.1"
}

# Legacy APPX token variable (for backward compatibility with .so imports)
APPX = ""
