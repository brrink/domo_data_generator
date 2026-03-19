# Domo Sample Data Generator

Generate realistic sample data from multiple business sources and upload it to Domo. Datasets replicate what real connectors look like — Salesforce, Google Analytics, QuickBooks, NetSuite, Google Ads, Facebook Ads, and HubSpot — complete with connector icons and cross-source referential integrity.

## Features

- **10 pre-built datasets** across 4 source categories (Salesforce, Google Analytics, Financial/ERP, Marketing/Ads)
- **YAML-driven catalog** — add or modify datasets by editing simple YAML files
- **Shared entity pool** — companies, people, products, and sales reps are consistent across all datasets
- **Date rolling** — shift all date columns forward to keep data looking current without regenerating
- **Domo integration** — create datasets, upload data (full replace), and set connector type/icon via the API
- **Cron-friendly** — designed for scheduled runs to keep your Domo instance fresh

## Quick Start

### 1. Install dependencies

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure Domo credentials

```bash
cp .env.example .env
```

Edit `.env` with your Domo client credentials (developer token is required for internal API call to update dataset type and icon):

```
DOMO_CLIENT_ID=your_client_id
DOMO_CLIENT_SECRET=your_client_secret
DOMO_DEVELOPER_TOKEN=your_developer_token
DOMO_API_HOST=api.domo.com
DOMO_INSTANCE=your_instance_name
DOMO_SET_CONNECTOR_TYPE=false
```

To get client credentials, go to **Domo > Admin > Authentication > Client Credentials** and create a new client with the `data` and `dashboard` scopes.

### 3. Generate the entity pool

```bash
python -m datagen pool regenerate
```

This creates a shared pool of fake companies, people, products, sales reps, and campaigns in `data/entity_pool.json`. All datasets reference this pool for cross-source consistency.

### 4. Generate data

```bash
# Generate all datasets
python -m datagen generate --all

# Generate a single dataset
python -m datagen generate salesforce_opportunities
```

Generated CSV files are saved to `data/`.

### 5. Create datasets in Domo

```bash
# Create all datasets (skips any that already have a domo_id)
python -m datagen create-dataset --all --skip-existing

# Create a single dataset
python -m datagen create-dataset salesforce_opportunities
```

This creates the datasets in Domo and writes the `domo_id` back into each YAML catalog file.

### 6. Upload data to Domo

```bash
# Upload all datasets (full replace)
python -m datagen upload --all

# Upload a single dataset
python -m datagen upload salesforce_opportunities
```

## CLI Reference

```
python -m datagen [OPTIONS] COMMAND [ARGS]

Commands:
  generate        Generate sample data for one or all datasets
  upload          Upload generated data to Domo (full replace)
  create-dataset  Create dataset(s) in Domo from catalog definitions
  roll-dates      Shift all rolling date columns to stay current
  list            List all dataset definitions in the catalog
  status          Show generation status for all datasets
  pool            Manage the shared entity pool

Global Options:
  --verbose / -v  Enable verbose logging
```

### generate

```bash
python -m datagen generate --all              # Generate all datasets
python -m datagen generate <name>             # Generate one dataset
python -m datagen generate --all --seed 42    # Reproducible generation
python -m datagen generate --all --dry-run    # Preview without writing
```

### upload

```bash
python -m datagen upload --all                # Upload all to Domo
python -m datagen upload <name>               # Upload one dataset
```

### create-dataset

```bash
python -m datagen create-dataset --all --skip-existing
python -m datagen create-dataset <name>
```

### roll-dates

```bash
python -m datagen roll-dates                          # Roll to today
python -m datagen roll-dates --anchor-date 2026-04-01 # Roll to specific date
```

### list / status

```bash
python -m datagen list              # Show catalog summary
python -m datagen list --verbose    # Show column details for each dataset
python -m datagen status            # Show generation state and CSV row counts
```

### pool

```bash
python -m datagen pool regenerate                     # Default sizes
python -m datagen pool regenerate --seed 99           # Custom seed
python -m datagen pool regenerate --company-count 500 # Custom pool sizes
python -m datagen pool show                           # Show pool summary
```

## Keeping Data Fresh

Date rolling shifts all date columns marked `rolling: true` forward so the data always looks current. This avoids full regeneration — the same rows keep their relationships, only dates move.

**Daily cron example:**

```bash
# Add to crontab: run daily at 6am
0 6 * * * cd /path/to/data_generator && .venv/bin/python -m datagen roll-dates && .venv/bin/python -m datagen upload --all
```

## Included Datasets

| Dataset | Source Type | Default Rows |
|---------|-----------|-------------|
| Salesforce - Accounts | salesforce | 500 |
| Salesforce - Contacts | salesforce | 1,500 |
| Salesforce - Opportunities | salesforce | 2,500 |
| Google Analytics - Sessions | google_analytics | 5,000 |
| Google Analytics - Page Views | google_analytics | 10,000 |
| QuickBooks - Invoices | quickbooks | 3,000 |
| NetSuite - General Ledger | netsuite | 5,000 |
| Google Ads - Campaign Performance | google_ads | 3,000 |
| Facebook Ads - Campaign Performance | facebook_ads | 2,500 |
| HubSpot - Contacts | hubspot | 2,000 |

## Adding a New Dataset

Create a new YAML file in `catalog/`. Here's a minimal example:

```yaml
dataset:
  name: "Jira - Issues"
  domo_id: null
  source_type: jira
  description: "Sample Jira issue tracking data"
  row_count: 1000

schema:
  - name: IssueKey
    type: STRING
    generator: sequence
    template: "PROJ-{i}"
    min: 1

  - name: Summary
    type: STRING
    generator: faker
    faker_method: sentence

  - name: Assignee
    type: STRING
    generator: entity_ref
    entity: person
    field: full_name

  - name: Status
    type: STRING
    generator: weighted_choice
    choices:
      To Do: 0.20
      In Progress: 0.30
      In Review: 0.15
      Done: 0.35

  - name: CreatedDate
    type: DATETIME
    generator: date_range
    start_days_ago: 180
    end_days_ahead: 0
    rolling: true
```

Then run:

```bash
python -m datagen generate jira_issues
python -m datagen create-dataset jira_issues
python -m datagen upload jira_issues
```

### Available Generators

| Generator | Description | Key Parameters |
|-----------|------------|----------------|
| `uuid4` | Random UUID | — |
| `random_choice` | Pick from a list | `choices` (list) |
| `weighted_choice` | Pick with weights | `choices` (dict of value: weight) |
| `random_int` | Random integer | `min`, `max` |
| `random_decimal` | Random float | `min`, `max`, `precision` |
| `date_range` | Random date in range | `start_days_ago`, `end_days_ahead`, `rolling` |
| `entity_ref` | Reference shared pool | `entity`, `field` |
| `compound` | Template string | `template`, `refs` |
| `sequence` | Sequential IDs | `template`, `min` |
| `derived_from_date` | Derive from date column | `source_column`, `format` |
| `stage_derived` | Map from another column | `source_column`, `mapping` |
| `faker` | Any Faker method | `faker_method`, `faker_args` |
| `constant` | Fixed value | `choices` (single value) |

**Source-specific generators:** `sf_id`, `sf_opportunity_name`, `sf_case_subject`, `sf_lead_rating`, `ga_session_id`, `ga_source`, `ga_medium`, `ga_page_path`, `ga_browser`, `ga_device_category`, `ga_country`, `ga_bounce_rate`, `ga_session_duration`, `ga_pageviews`, `ga_landing_page`, `gl_account_code`, `gl_account_name`, `invoice_number`, `payment_terms`, `payment_method`, `invoice_status`, `journal_type`, `department`, `fiscal_period`, `debit_credit`, `ad_platform`, `campaign_objective`, `ad_format`, `ad_headline`, `ad_keyword`, `targeting_type`, `impressions`, `clicks_from_impressions`, `ctr`, `cost_per_click`, `ad_spend`, `conversions_from_clicks`, `hubspot_lifecycle`, `hubspot_lead_status`, `ad_group_id`

### Entity Pool Types

The shared entity pool contains these entity types that can be referenced via `entity_ref`:

| Entity Type | Fields |
|-------------|--------|
| `company` | `id`, `account_id`, `name`, `domain`, `industry`, `size`, `city`, `state`, `annual_revenue`, `employee_count` |
| `person` | `id`, `contact_id`, `first_name`, `last_name`, `full_name`, `email`, `company_id`, `company_name`, `title`, `phone` |
| `product` | `id`, `name`, `category`, `unit_price`, `sku` |
| `sales_rep` | `id`, `rep_id`, `first_name`, `last_name`, `full_name`, `email`, `region` |
| `campaign` | `id`, `name`, `channel`, `budget`, `status` |

## Dataset Type / Connector Icon

By default, datasets created via the API show a generic "API" icon in Domo. Setting `DOMO_SET_CONNECTOR_TYPE=true` in `.env` enables an attempt to set the connector type (e.g., Salesforce icon) using an undocumented Domo internal API. This requires `DOMO_INSTANCE` to be set and may not work in all environments. If it fails, it logs a warning and falls back gracefully.

## Project Structure

```
data_generator/
  .env                    # Domo credentials (not committed)
  requirements.txt        # Python dependencies
  catalog/                # YAML dataset definitions
  data/                   # Generated CSVs and entity pool (gitignored)
  datagen/
    cli.py                # Typer CLI with all commands
    config.py             # Environment and path configuration
    models.py             # Pydantic models for catalog schema
    catalog_loader.py     # YAML parsing and validation
    entity_pool.py        # Shared entity generation and persistence
    domo_client.py        # Domo API wrapper (pydomo + type setting)
    uploader.py           # Generation and upload orchestration
    date_roller.py        # Date shifting logic
    generators/
      base.py             # Generator registry and built-in generators
      salesforce.py       # Salesforce-specific generators
      google_analytics.py # GA-specific generators
      financial.py        # QuickBooks/NetSuite generators
      marketing.py        # Google Ads/Facebook Ads/HubSpot generators
```
