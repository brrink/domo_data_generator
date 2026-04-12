# Domo Sample Data Generator

Generate realistic sample data from multiple business sources and upload it to Domo. Datasets replicate what real connectors look like -- Salesforce, Google Analytics, QuickBooks, NetSuite, Google Ads, Facebook Ads, HubSpot, and more -- complete with connector icons and cross-source referential integrity.

## Features

- **18 pre-built datasets** across 6 source categories (Salesforce, Google Analytics, Financial/ERP, Marketing/Ads, Health, AdPoint)
- **YAML-driven catalog** -- add or modify datasets by editing simple YAML files
- **Shared entity pool** -- companies, people, products, and sales reps are consistent across all datasets
- **Date rolling** -- shift date columns forward to keep data looking current without regenerating
- **Domo integration** -- create datasets, upload data (full replace), and set connector type/icon
- **Structured output** -- JSON (default), table, or YAML output for easy parsing by AI agents and scripts
- **pipx installable** -- install globally and run from any directory

## Install

```bash
# Recommended: install globally with pipx
pipx install git+https://github.com/brrink/domo_data_generator.git

# Or install with pip
pip install git+https://github.com/brrink/domo_data_generator.git
```

## Quick Start

### 1. Initialize a working directory

```bash
mkdir my-domo-data && cd my-domo-data
datagen init
```

This copies the built-in catalog definitions, a `.env` template, and creates a `data/` directory.

### 2. Configure credentials

Edit `.env`:

```
DOMO_INSTANCE=your_instance_name
DOMO_DEVELOPER_TOKEN=your_developer_token

# Required for data upload and dataset creation
DOMO_CLIENT_ID=your_client_id
DOMO_CLIENT_SECRET=your_client_secret
```

| Variable | Purpose | Required for |
|----------|---------|-------------|
| `DOMO_INSTANCE` | Your Domo instance name | All Domo operations |
| `DOMO_DEVELOPER_TOKEN` | Developer token from Domo Admin | Connector icons, listing |
| `DOMO_CLIENT_ID` | OAuth client ID | Dataset creation, data upload |
| `DOMO_CLIENT_SECRET` | OAuth client secret | Dataset creation, data upload |

To create OAuth credentials: **Domo > Admin > Authentication > Client credentials** -- create a client with `data` and `dashboard` scopes.

To create a developer token: **Domo > Admin > Authentication > Access tokens**.

### 3. Generate and upload

```bash
datagen pool regenerate          # Create shared entity pool
datagen generate --all           # Generate all datasets as CSV
datagen create-dataset --all     # Create datasets in Domo
datagen upload --all             # Upload data (full replace)
datagen set-type-all             # Set connector icons
```

## CLI Reference

```
datagen [OPTIONS] COMMAND [ARGS]

Options:
  --verbose / -v        Enable verbose logging
  --output / -o TEXT    Output format: json, table, yaml (default: json)
  --yes / -y            Skip confirmation prompts
```

### Core Commands

```bash
datagen init                               # Initialize working directory
datagen generate --all                     # Generate all datasets
datagen generate <name>                    # Generate one dataset
datagen generate --all --seed 42           # Reproducible generation
datagen generate --all --dry-run           # Preview without writing
datagen upload --all                       # Upload all to Domo
datagen upload <name>                      # Upload one dataset
datagen create-dataset --all --skip-existing  # Create datasets in Domo
datagen create-dataset <name>              # Create one dataset
datagen roll-dates                         # Roll dates to today
datagen roll-dates --anchor-date 2026-04-01   # Roll to specific date
```

### Informational Commands

```bash
datagen list                    # List all catalog definitions
datagen list --verbose          # Include column/schema details
datagen status                  # Show generation state and CSV row counts
datagen discover-types salesforce   # Search Domo provider types
```

### Entity Pool Commands

```bash
datagen pool regenerate                     # Default sizes
datagen pool regenerate --seed 99           # Custom seed
datagen pool regenerate --company-count 500 # Custom pool sizes
datagen pool show                           # Show pool summary
```

### Connector Icon Commands

```bash
datagen set-type <name>                    # Set icon on one dataset
datagen set-type <name> --provider-key X   # Override provider key
datagen set-type-all                       # Set icons on all datasets
```

## Output Formats

All commands emit structured data. The default is JSON for easy machine parsing:

```bash
datagen list                      # JSON (default)
datagen --output table list       # Rich table for humans
datagen --output yaml list        # YAML
```

## Keeping Data Fresh

Date rolling shifts columns marked `rolling: true` forward so data always looks current, without regenerating.

```bash
# Daily cron: roll dates and re-upload at 6am
0 6 * * * cd /path/to/project && datagen roll-dates && datagen upload --all
```

## Included Datasets

| Dataset | Source Type | Rows |
|---------|-----------|------|
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
| Marketing - Market Leads | marketo | 2,500 |
| Marketo - Leads | marketo | 3,000 |
| Health Portal - Demographics | health | 15 |
| Health Portal - Lab Results | health | 1,470 |
| Health Portal - Vitals | health | 5,250 |
| AdPoint - Orders | custom | 150 |
| AdPoint - Line Items | custom | 500 |
| AdPoint - Flights | custom | 2,000 |

## Adding a New Dataset

Create a YAML file in your local `catalog/` directory:

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

Then generate and upload:

```bash
datagen generate jira_issues
datagen create-dataset jira_issues
datagen upload jira_issues
```

### Available Generators

| Generator | Description | Key Parameters |
|-----------|------------|----------------|
| `uuid4` | Random UUID | -- |
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

| Entity Type | Fields |
|-------------|--------|
| `company` | `id`, `account_id`, `name`, `domain`, `industry`, `size`, `city`, `state`, `annual_revenue`, `employee_count` |
| `person` | `id`, `contact_id`, `first_name`, `last_name`, `full_name`, `email`, `company_id`, `company_name`, `title`, `phone` |
| `product` | `id`, `name`, `category`, `unit_price`, `sku` |
| `sales_rep` | `id`, `rep_id`, `first_name`, `last_name`, `full_name`, `email`, `region` |
| `campaign` | `id`, `name`, `channel`, `budget`, `status` |

## Authentication

The CLI uses two auth mechanisms:

- **Developer token** -- for the Domo instance API (connector icons, provider discovery). Set `DOMO_DEVELOPER_TOKEN`.
- **OAuth client credentials** -- for the Domo public API (dataset creation, data upload). Set `DOMO_CLIENT_ID` and `DOMO_CLIENT_SECRET`.

Offline commands (`generate`, `list`, `status`, `pool`, `roll-dates`, `init`) require no credentials.

## Project Structure

```
domo_data_generator/
  pyproject.toml          # Package metadata and dependencies
  .env.example            # Credential template
  datagen/
    __init__.py           # Package version
    __main__.py           # python -m datagen entry point
    cli.py                # Typer CLI with all commands
    config.py             # Environment and path configuration
    models.py             # Pydantic models for catalog schema
    catalog_loader.py     # YAML parsing and domo_id state management
    entity_pool.py        # Shared entity generation and persistence
    domo_client.py        # Domo API client (httpx, dev token + OAuth)
    uploader.py           # Generation and upload orchestration
    date_roller.py        # Date shifting logic
    output.py             # Structured output formatting (json/table/yaml)
    state.py              # CLI application state
    .env.example          # Bundled credential template (for init)
    catalog/              # Bundled YAML dataset definitions
    generators/
      base.py             # Generator registry and built-in generators
      salesforce.py       # Salesforce-specific generators
      google_analytics.py # GA-specific generators
      financial.py        # QuickBooks/NetSuite generators
      marketing.py        # Google Ads/Facebook Ads/HubSpot generators
      health.py           # Health portal generators
```
