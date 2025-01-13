"""
Base class for API wrappers.

This module provides a base class `BaseAPIWrapper` for interacting with APIs that require
authentication using client credentials. It handles loading environment variables,
authenticating, and obtaining an access token.

Classes:
    BaseAPIWrapper: A base class for API wrappers that handles authentication and token management.
"""

import requests


class BaseAPIWrapper:
    def __init__(self, client_id, client_secret, token_url, base_url):

        self.client_id = client_id
        self.client_secret = client_secret
        self.token_url = token_url
        self.base_url = base_url
        self.timeout = 30
        self.token = self._get_token()

    def _get_token(self):
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
        return response_data.get("access_token")
