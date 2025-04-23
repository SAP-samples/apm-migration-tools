"""
Base class for API wrappers.

This module provides a base class `BaseAPIWrapper` for interacting with APIs that require
authentication using client credentials. It handles loading environment variables,
authenticating, and obtaining an access token.

Classes:
    BaseAPIWrapper: A base class for API wrappers that handles authentication and token management.
"""

import requests
import time


class BaseAPIWrapper:
    def __init__(
        self, client_id, client_secret, token_url, base_url, timeout: int = 30
    ):

        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.base_url = base_url
        self.timeout = timeout
        # self.token = self._get_token()
        self.token = None
        self.token_expiry = 0

    def _get_token(self):

        if self.token_expiry is None or time.time() >= self.token_expiry:
            # Authenticate and get the token
            response = requests.post(
                self.token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            response_data = response.json()
            self.token = response_data.get("access_token")
            expires_in = response_data.get("expires_in")
            self.token_expiry = time.time() + expires_in
        return self.token
