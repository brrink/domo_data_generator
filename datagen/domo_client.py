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
    DOMO_INSTANCE,
    DOMO_SET_CONNECTOR_TYPE,
)
from datagen.models import DatasetDefinition

logger = logging.getLogger(__name__)

# Mapping from our source_type to Domo's dataProviderType values
SOURCE_TYPE_MAP = {
    "salesforce": "salesforce",
    "google_analytics": "google-analytics",
    "quickbooks": "quickbooks",
    "netsuite": "netsuite",
    "google_ads": "google-adwords",
    "facebook_ads": "facebook",
    "hubspot": "hubspot",
    "linkedin_ads": "linkedin",
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
    ):
        self.client_id = client_id or DOMO_CLIENT_ID
        self.client_secret = client_secret or DOMO_CLIENT_SECRET
        self.api_host = api_host or DOMO_API_HOST
        self.instance = instance or DOMO_INSTANCE
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

    def set_dataset_type(self, dataset_id: str, source_type: str) -> bool:
        """Attempt to set the dataset connector type/icon via Domo's internal API.

        This uses an undocumented endpoint and may not work in all environments.
        Returns True if successful, False otherwise.
        """
        provider_type = SOURCE_TYPE_MAP.get(source_type)
        if not provider_type:
            logger.warning(f"No provider type mapping for source_type '{source_type}'")
            return False

        if not self.instance:
            logger.warning(
                "DOMO_INSTANCE not set. Cannot set dataset type. "
                "Set DOMO_INSTANCE in .env to your Domo instance name."
            )
            return False

        try:
            # Get an access token from pydomo's transport
            token = self.domo.transport.access_token
            url = f"https://{self.instance}.domo.com/api/data/v3/datasources/{dataset_id}"
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            }
            payload = {"dataProviderType": provider_type}
            resp = requests.put(url, json=payload, headers=headers, timeout=30)
            if resp.ok:
                logger.info(
                    f"Set dataset {dataset_id} type to '{provider_type}'"
                )
                return True
            else:
                logger.warning(
                    f"Failed to set dataset type (HTTP {resp.status_code}): {resp.text}"
                )
                return False
        except Exception as e:
            logger.warning(f"Failed to set dataset type: {e}")
            return False
