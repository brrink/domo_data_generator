"""Domo API client using httpx.

Auth:
- Instance API (create datasets, set types, list): developer token
- Public API (data upload): OAuth client credentials (DOMO_CLIENT_ID/SECRET)
- Ryuu session: if available, used for both APIs
"""

from __future__ import annotations

import base64
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx
import pandas as pd

from datagen.config import (
    DOMO_CLIENT_ID,
    DOMO_CLIENT_SECRET,
    DOMO_DEVELOPER_TOKEN,
    DOMO_INSTANCE,
)
from datagen.models import DatasetDefinition

logger = logging.getLogger(__name__)

# Mapping from our source_type to Domo provider keys (from /api/data/v1/providers)
SOURCE_TYPE_MAP = {
    "salesforce": "salesforce",
    "google_analytics": "google-analytics",
    "quickbooks": "quickbooks",
    "netsuite": "netsuite",
    "google_ads": "google-adwords",
    "facebook_ads": "facebook",
    "hubspot": "hubspot",
    "linkedin_ads": "linkedin",
    "jira": "jira",
    "marketo": "marketo",
}

COLUMN_TYPE_MAP = {
    "STRING": "STRING",
    "DECIMAL": "DECIMAL",
    "LONG": "LONG",
    "DOUBLE": "DOUBLE",
    "DATE": "DATE",
    "DATETIME": "DATETIME",
}

RYUU_CONFIG_DIR = Path.home() / ".config" / "configstore" / "ryuu"


def _load_ryuu_config(instance: str) -> dict | None:
    """Load ryuu session config for an instance."""
    path = RYUU_CONFIG_DIR / f"{instance}.domo.com.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


class DomoApiError(Exception):
    """Error from the Domo API."""

    def __init__(self, message: str, status_code: int | None = None, body: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.body = body


@dataclass
class DomoClient:
    """HTTP client for the Domo API.

    Auth:
    - Instance API: developer token (X-DOMO-Developer-Token) or ryuu SID
    - Public API (data upload): OAuth client credentials or ryuu access token
    """

    instance: str = ""
    developer_token: str = ""
    client_id: str = ""
    client_secret: str = ""
    _access_token: str = field(init=False, repr=False, default="")
    _sid: str = field(init=False, repr=False, default="")
    _instance_http: httpx.Client = field(init=False, repr=False, default=None)  # type: ignore[assignment]
    _public_http: httpx.Client = field(init=False, repr=False, default=None)  # type: ignore[assignment]

    def __post_init__(self) -> None:
        self.instance = self.instance or DOMO_INSTANCE
        if not self.instance:
            raise ValueError(
                "DOMO_INSTANCE is required. Set it in your .env file or as an "
                "environment variable (e.g., DOMO_INSTANCE=mycompany)."
            )

        # Resolve instance API auth: dev token > ryuu
        self.developer_token = self.developer_token or DOMO_DEVELOPER_TOKEN
        if not self.developer_token:
            ryuu = _load_ryuu_config(self.instance)
            if ryuu and ryuu.get("refreshToken"):
                if ryuu.get("devToken"):
                    self.developer_token = ryuu["refreshToken"]
                    logger.debug("Using developer token from ryuu config")
                else:
                    self._bootstrap_ryuu_session(ryuu["refreshToken"])
            else:
                raise ValueError(
                    "No Domo credentials found. Either:\n"
                    "  1. Set DOMO_DEVELOPER_TOKEN in .env or environment\n"
                    "  2. Run: npm install -g @domoinc/ryuu && domo login"
                )

        # Resolve public API auth: OAuth client credentials (for data upload)
        self.client_id = self.client_id or DOMO_CLIENT_ID
        self.client_secret = self.client_secret or DOMO_CLIENT_SECRET

    def _bootstrap_ryuu_session(self, refresh_token: str) -> None:
        """Exchange a ryuu refresh token for an access token and SID."""
        base = f"https://{self.instance}.domo.com"

        # Step 1: refresh token -> access token
        resp = httpx.post(
            f"{base}/api/oauth2/token",
            data={"grant_type": "refresh_token", "refresh_token": refresh_token},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=30.0,
        )
        if not resp.is_success:
            raise ValueError(
                f"Failed to exchange ryuu refresh token (HTTP {resp.status_code}). "
                "Your session may be expired. Run: domo login"
            )
        token_data = resp.json()
        self._access_token = token_data["access_token"]

        # Step 2: access token -> SID (for instance API)
        resp = httpx.post(
            f"{base}/api/oauth2/sid",
            headers={
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
            },
            timeout=30.0,
        )
        if not resp.is_success:
            raise ValueError(
                f"Failed to get session ID (HTTP {resp.status_code}). "
                "Your session may be expired. Run: domo login"
            )
        self._sid = resp.text.strip().strip('"')
        logger.debug("Ryuu session established (SID obtained)")

    def _get_oauth_token(self) -> str:
        """Exchange OAuth client credentials for a Bearer token."""
        creds = base64.b64encode(f"{self.client_id}:{self.client_secret}".encode()).decode()
        resp = httpx.post(
            "https://api.domo.com/oauth/token",
            params={"grant_type": "client_credentials"},
            headers={"Authorization": f"Basic {creds}"},
            timeout=30.0,
        )
        if not resp.is_success:
            raise ValueError(
                f"OAuth token exchange failed (HTTP {resp.status_code}). "
                "Check DOMO_CLIENT_ID and DOMO_CLIENT_SECRET in your .env."
            )
        return resp.json()["access_token"]

    @property
    def instance_http(self) -> httpx.Client:
        """HTTP client for the instance API ({instance}.domo.com)."""
        if self._instance_http is None:
            headers: dict[str, str] = {"Content-Type": "application/json"}
            if self.developer_token:
                headers["X-DOMO-Developer-Token"] = self.developer_token
            elif self._sid:
                headers["X-Domo-Authentication"] = self._sid
            self._instance_http = httpx.Client(
                base_url=f"https://{self.instance}.domo.com",
                headers=headers,
                timeout=60.0,
            )
        return self._instance_http

    @property
    def public_http(self) -> httpx.Client | None:
        """HTTP client for the public API (api.domo.com).

        Available with OAuth client credentials or ryuu access token.
        Returns None if neither is configured.
        """
        if self._public_http is None:
            token = self._access_token
            if not token and self.client_id and self.client_secret:
                token = self._get_oauth_token()
                self._access_token = token
            if token:
                self._public_http = httpx.Client(
                    base_url="https://api.domo.com",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                    },
                    timeout=60.0,
                )
            else:
                # No access token — can't use public API
                self._public_http = None  # type: ignore[assignment]
        return self._public_http

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: dict | list | None = None,
        content: str | bytes | None = None,
        content_type: str | None = None,
        params: dict[str, Any] | None = None,
        use_public_api: bool = False,
    ) -> Any:
        """Make an HTTP request to the Domo API."""
        headers = {}
        if content_type:
            headers["Content-Type"] = content_type

        kwargs: dict[str, Any] = {"params": params}
        if content is not None:
            kwargs["content"] = content
            kwargs["headers"] = headers
        elif json_body is not None:
            kwargs["json"] = json_body
        else:
            kwargs["headers"] = headers

        if use_public_api and self.public_http:
            client = self.public_http
        else:
            client = self.instance_http

        resp = client.request(method, path, **kwargs)

        if not resp.is_success:
            raise DomoApiError(
                f"Domo API error: {method} {path} -> {resp.status_code}",
                status_code=resp.status_code,
                body=resp.text,
            )

        if resp.status_code == 204 or not resp.text:
            return None
        return resp.json()

    # --- Dataset CRUD ---

    def create_dataset(self, definition: DatasetDefinition) -> str:
        """Create a new dataset in Domo. Returns the dataset ID.

        Uses the public API (OAuth) if available, falls back to instance API v2.
        """
        columns = [
            {
                "type": COLUMN_TYPE_MAP.get(col.type.upper(), "STRING"),
                "name": col.name,
            }
            for col in definition.schema_
        ]

        if self.public_http:
            body = {
                "name": definition.dataset.name,
                "description": definition.dataset.description,
                "schema": {"columns": columns},
            }
            result = self._request("POST", "/v1/datasets", json_body=body, use_public_api=True)
            dataset_id = result["id"]
        else:
            body = {
                "dataSourceName": definition.dataset.name,
                "dataSourceDescription": definition.dataset.description,
                "columns": columns,
            }
            result = self._request("POST", "/api/data/v2/datasources", json_body=body)
            dataset_id = result["dataSource"]["dataSourceId"]

        logger.info(f"Created dataset '{definition.dataset.name}' with ID: {dataset_id}")
        return dataset_id

    def replace_data(self, dataset_id: str, df: pd.DataFrame) -> None:
        """Replace all data in a Domo dataset via the public API.

        Requires OAuth client credentials (DOMO_CLIENT_ID/SECRET) or a
        ryuu session with a real refresh token (not a developer token).
        """
        if not self.public_http:
            raise ValueError(
                "Data upload requires OAuth credentials. Add to your .env:\n"
                "  DOMO_CLIENT_ID=your_client_id\n"
                "  DOMO_CLIENT_SECRET=your_client_secret\n"
                "Create these in Domo > Admin > Authentication > Client credentials."
            )

        csv_data = df.to_csv(index=False, header=False)
        self._request(
            "PUT",
            f"/v1/datasets/{dataset_id}/data",
            content=csv_data,
            content_type="text/csv",
            use_public_api=True,
        )
        logger.info(f"Replaced data in dataset {dataset_id} ({len(df)} rows)")

    def get_dataset(self, dataset_id: str) -> dict[str, Any]:
        """Get dataset metadata from Domo."""
        return self._request("GET", f"/api/data/v3/datasources/{dataset_id}")

    def list_datasets(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """List datasets in Domo."""
        return self._request(
            "GET", "/api/data/v3/datasources",
            params={"limit": limit, "offset": offset},
        )

    def update_dataset_meta(self, dataset_id: str, definition: DatasetDefinition) -> None:
        """Update dataset name and description."""
        body = {
            "name": definition.dataset.name,
            "description": definition.dataset.description,
        }
        self._request("PUT", f"/api/data/v3/datasources/{dataset_id}", json_body=body)
        logger.info(f"Updated metadata for dataset {dataset_id}")

    # --- Instance API (connector types/icons) ---

    def list_providers(self, search: str | None = None) -> list[dict]:
        """Fetch the list of available data providers/connector types."""
        result = self._request(
            "GET",
            "/api/data/v1/providers",
            params={"displayType": "cs", "fields": "key,name", "iconPickerOnly": "true"},
        )

        if search:
            search_lower = search.lower()
            result = [
                p for p in result
                if search_lower in p.get("key", "").lower()
                or search_lower in p.get("name", "").lower()
            ]

        return [{"key": p["key"], "name": p["name"]} for p in result]

    def get_datasource(self, dataset_id: str) -> dict:
        """Get the full internal datasource object for a dataset."""
        return self._request("GET", f"/api/data/v3/datasources/{dataset_id}")

    def set_dataset_type(
        self, dataset_id: str, source_type: str, provider_key_override: str | None = None
    ) -> bool:
        """Set the dataset connector type/icon.

        Returns True if successful, False otherwise.
        """
        provider_key = provider_key_override or SOURCE_TYPE_MAP.get(source_type)
        if not provider_key:
            logger.warning(
                f"No provider key mapping for source_type '{source_type}'. "
                f"Run 'datagen discover-types {source_type}' to find the correct key."
            )
            return False

        try:
            ds = self._request("GET", f"/api/data/v3/datasources/{dataset_id}")
            payload = {
                "dataSourceName": ds.get("name", ""),
                "dataSourceDescription": ds.get("description", ""),
                "userDefinedType": provider_key,
            }
            self._request(
                "PUT",
                f"/api/data/v3/datasources/{dataset_id}/properties",
                json_body=payload,
            )
            logger.info(f"Set dataset {dataset_id} type to '{provider_key}' ({source_type})")
            return True
        except DomoApiError as e:
            logger.warning(f"Failed to set dataset type (HTTP {e.status_code}): {e.body}")
            return False
        except Exception as e:
            logger.warning(f"Failed to set dataset type: {e}")
            return False
