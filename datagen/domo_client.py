"""Domo API client wrapping pydomo with helpers for dataset type/icon."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd
import requests
from pydomo import Domo
from pydomo.datasets import DataSetRequest, Schema, Column, ColumnType

from datagen.config import (
    DOMO_API_HOST,
    DOMO_CLIENT_ID,
    DOMO_CLIENT_SECRET,
    DOMO_DEVELOPER_TOKEN,
    DOMO_INSTANCE,
    DOMO_SET_CONNECTOR_TYPE,
)
from datagen.models import DatasetDefinition

logger = logging.getLogger(__name__)

# Mapping from our source_type to Domo provider keys (from /api/data/v1/providers)
# Use 'datagen discover-types <search>' to find the correct key for new sources.
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
}

# Map our column types to pydomo ColumnType
COLUMN_TYPE_MAP = {
    "STRING": ColumnType.STRING,
    "DECIMAL": ColumnType.DECIMAL,
    "LONG": ColumnType.LONG,
    "DOUBLE": ColumnType.DOUBLE,
    "DATE": ColumnType.DATE,
    "DATETIME": ColumnType.DATETIME,
}


class DomoClient:
    """Wrapper around pydomo for dataset operations."""

    def __init__(
        self,
        client_id: str | None = None,
        client_secret: str | None = None,
        api_host: str | None = None,
        instance: str | None = None,
        developer_token: str | None = None,
    ):
        self.client_id = client_id or DOMO_CLIENT_ID
        self.client_secret = client_secret or DOMO_CLIENT_SECRET
        self.api_host = api_host or DOMO_API_HOST
        self.instance = instance or DOMO_INSTANCE
        self.developer_token = developer_token or DOMO_DEVELOPER_TOKEN
        self._domo: Domo | None = None

    @property
    def domo(self) -> Domo:
        if self._domo is None:
            if not self.client_id or not self.client_secret:
                raise ValueError(
                    "Domo credentials not configured. Set DOMO_CLIENT_ID and "
                    "DOMO_CLIENT_SECRET in your .env file."
                )
            self._domo = Domo(self.client_id, self.client_secret, api_host=self.api_host)
        return self._domo

    def _instance_headers(self) -> dict[str, str]:
        """Get auth headers for Domo instance internal API calls.

        Uses DOMO_DEVELOPER_TOKEN (access token from Domo Admin) for internal
        instance API calls, since the OAuth client credentials token from pydomo
        is not accepted by the instance endpoints.
        """
        token = self.developer_token
        if not token:
            raise ValueError(
                "DOMO_DEVELOPER_TOKEN is required for instance API calls "
                "(set-type, discover-types). Generate one in Domo > Admin > "
                "Authentication > Access tokens and add it to your .env file."
            )
        return {
            "X-DOMO-Developer-Token": token,
            "Content-Type": "application/json",
        }

    def _instance_url(self, path: str) -> str:
        """Build a URL for the Domo instance internal API."""
        return f"https://{self.instance}.domo.com{path}"

    def create_dataset(self, definition: DatasetDefinition) -> str:
        """Create a new dataset in Domo from a catalog definition. Returns the dataset ID."""
        dsr = DataSetRequest()
        dsr.name = definition.dataset.name
        dsr.description = definition.dataset.description
        dsr.schema = Schema([
            Column(
                COLUMN_TYPE_MAP.get(col.type.upper(), ColumnType.STRING),
                col.name,
            )
            for col in definition.schema_
        ])
        result = self.domo.datasets.create(dsr)
        dataset_id = result["id"]
        logger.info(f"Created dataset '{definition.dataset.name}' with ID: {dataset_id}")

        # Attempt to set the connector type/icon
        if DOMO_SET_CONNECTOR_TYPE:
            self.set_dataset_type(dataset_id, definition.dataset.source_type)

        return dataset_id

    def replace_data(self, dataset_id: str, df: pd.DataFrame) -> None:
        """Replace all data in a Domo dataset with the given DataFrame."""
        csv_data = df.to_csv(index=False, header=False)
        self.domo.datasets.data_import(dataset_id, csv_data)
        logger.info(f"Replaced data in dataset {dataset_id} ({len(df)} rows)")

    def get_dataset(self, dataset_id: str) -> dict[str, Any]:
        """Get dataset metadata from Domo."""
        return self.domo.datasets.get(dataset_id)

    def list_datasets(self, limit: int = 50, offset: int = 0) -> list[dict]:
        """List datasets in Domo."""
        return self.domo.datasets.list(limit=limit, offset=offset)

    def update_dataset_meta(self, dataset_id: str, definition: DatasetDefinition) -> None:
        """Update dataset name and description."""
        update = DataSetRequest()
        update.name = definition.dataset.name
        update.description = definition.dataset.description
        self.domo.datasets.update(dataset_id, update)
        logger.info(f"Updated metadata for dataset {dataset_id}")

    def list_providers(self, search: str | None = None) -> list[dict]:
        """Fetch the list of available data providers/connector types from Domo.

        Returns a list of dicts with 'key' and 'name' fields.
        """
        if not self.instance:
            raise ValueError("DOMO_INSTANCE must be set to list providers")

        url = self._instance_url(
            "/api/data/v1/providers?displayType=cs&fields=key,name&iconPickerOnly=true"
        )
        resp = requests.get(url, headers=self._instance_headers(), timeout=30)
        resp.raise_for_status()
        providers = resp.json()

        if search:
            search_lower = search.lower()
            providers = [
                p for p in providers
                if search_lower in p.get("key", "").lower()
                or search_lower in p.get("name", "").lower()
            ]

        return [{"key": p["key"], "name": p["name"]} for p in providers]

    def get_datasource(self, dataset_id: str) -> dict:
        """Get the full internal datasource object for a dataset."""
        if not self.instance:
            raise ValueError("DOMO_INSTANCE must be set")

        url = self._instance_url(f"/api/data/v3/datasources/{dataset_id}")
        resp = requests.get(url, headers=self._instance_headers(), timeout=30)
        resp.raise_for_status()
        return resp.json()

    def set_dataset_type(
        self, dataset_id: str, source_type: str, provider_key_override: str | None = None
    ) -> bool:
        """Set the dataset connector type/icon via Domo's internal API.

        Uses the /api/data/v1/datasources endpoint with the provider key
        from the providers list (/api/data/v1/providers).

        Args:
            dataset_id: The Domo dataset ID.
            source_type: The source_type from the catalog (used to look up SOURCE_TYPE_MAP).
            provider_key_override: If set, use this key directly instead of looking up.

        Returns True if successful, False otherwise.
        """
        provider_key = provider_key_override or SOURCE_TYPE_MAP.get(source_type)
        if not provider_key:
            logger.warning(
                f"No provider key mapping for source_type '{source_type}'. "
                f"Run 'datagen discover-types {source_type}' to find the correct key."
            )
            return False

        if not self.instance:
            logger.warning(
                "DOMO_INSTANCE not set. Cannot set dataset type. "
                "Set DOMO_INSTANCE in .env to your Domo instance name."
            )
            return False

        try:
            # Use the /properties sub-endpoint on v3 with userDefinedType
            url = self._instance_url(
                f"/api/data/v3/datasources/{dataset_id}/properties"
            )
            headers = self._instance_headers()

            # First GET current datasource to get name/description
            get_url = self._instance_url(f"/api/data/v3/datasources/{dataset_id}")
            get_resp = requests.get(get_url, headers=headers, timeout=30)
            if not get_resp.ok:
                logger.warning(
                    f"Failed to get datasource {dataset_id} (HTTP {get_resp.status_code}): "
                    f"{get_resp.text}"
                )
                return False

            ds = get_resp.json()

            payload = {
                "dataSourceName": ds.get("name", ""),
                "dataSourceDescription": ds.get("description", ""),
                "userDefinedType": provider_key,
            }

            put_resp = requests.put(url, json=payload, headers=headers, timeout=30)
            if put_resp.ok:
                logger.info(
                    f"Set dataset {dataset_id} type to '{provider_key}' ({source_type})"
                )
                return True
            else:
                logger.warning(
                    f"Failed to set dataset type (HTTP {put_resp.status_code}): {put_resp.text}"
                )
                return False
        except Exception as e:
            logger.warning(f"Failed to set dataset type: {e}")
            return False
