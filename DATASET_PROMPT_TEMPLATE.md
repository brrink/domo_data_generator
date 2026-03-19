# New Dataset Request Template

Use this template to request a new sample dataset for the Domo data generator. Fill in the sections below, then provide this entire document (including the reference sections) to Claude or another AI assistant.

---

## YOUR REQUEST (fill this in)

### 1. Data Source
**What system does this data come from?**
<!-- e.g., Zendesk, Stripe, Jira, Snowflake, ServiceNow, Workday -->

Source name:

### 2. Dataset Identity
**What should this dataset be called in Domo?**
<!-- Follow the pattern: "Source - Object" (e.g., "Zendesk - Tickets", "Stripe - Payments") -->

Dataset name:
Description:
Row count: <!-- 100-10000; more rows = more realistic distributions -->

### 3. Domo Connector Type (for icon)
**What connector icon should this dataset show in Domo?**
<!-- Run `datagen discover-types <search>` to find the provider key, or write "look up later" -->

Provider key:

### 4. Columns
**List every column this dataset should have.** For each column, provide:
- Column name
- What it represents / what values it should contain
- Whether values should follow a realistic distribution (e.g., "mostly Closed Won, few Closed Lost") or be uniform
- Whether it's a date that should stay current over time (rolling)
- Whether it depends on another column (e.g., "clicks = impressions * CTR")

| Column Name | Description | Notes |
|-------------|-------------|-------|
| | | |
| | | |

### 5. Entity Pool Relationships
**Should any columns pull from the shared entity pool?** This ensures the same companies, people, products, etc. appear across multiple datasets.

<!-- e.g., "CustomerName should use company names from the pool" or "AssignedTo should use sales rep names" -->

### 6. Column Dependencies
**Do any columns derive from other columns?**
<!-- e.g., "TotalAmount = Quantity * UnitPrice", "FiscalQuarter derived from InvoiceDate", "Status determines Priority via mapping" -->

### 7. Custom Generator Needs
**Do you need any behavior that doesn't match the existing generators below?**
<!-- e.g., "Ticket IDs should look like ZD-123456", "Amounts should follow a log-normal distribution", "Status should transition realistically" -->

---

## REFERENCE: Project Architecture

This project generates sample data for Domo datasets. Key concepts:

- **Catalog files** (`catalog/*.yaml`): Each YAML file defines one dataset -- its metadata and column schema
- **Generators**: Functions that produce realistic data for each column type
- **Entity pool**: Shared set of companies, people, products, sales reps, and campaigns used across all datasets for referential integrity
- **Source type map**: Maps each dataset's source to a Domo connector provider key for the correct icon

### File to create
The output should be a YAML file at `catalog/{dataset_name}.yaml` where `{dataset_name}` is a snake_case identifier (e.g., `zendesk_tickets.yaml`).

If new generators are needed, create or update the appropriate file in `datagen/generators/` and register them with the `@register_generator` decorator. Also add a new import line in `datagen/uploader.py` if creating a new generator module.

If the source_type is new, add the provider key mapping to `SOURCE_TYPE_MAP` in `datagen/domo_client.py`.

---

## REFERENCE: YAML Catalog Schema

```yaml
dataset:
  name: "Source - Object"           # Display name in Domo
  domo_id: null                     # Leave null; auto-populated on first upload
  source_type: salesforce           # Maps to Domo connector icon (see Source Type Map below)
  description: "What this dataset represents"
  row_count: 2500                   # Number of rows to generate
  tags:                             # Optional
    - tag1
    - tag2

schema:
  - name: ColumnName                # Column name (no spaces)
    type: STRING                    # Domo type (see Column Types below)
    generator: generator_name       # Which generator to use (see Available Generators below)
    rolling: true                   # (dates only) Set true to auto-shift dates to stay current
    # ... additional generator-specific params (see generator table)
```

---

## REFERENCE: Column Types

| Type | Use for |
|------|---------|
| `STRING` | Text, IDs, names, categories |
| `LONG` | Whole numbers (counts, quantities) |
| `DECIMAL` | Numbers with decimals (money, rates, percentages) |
| `DOUBLE` | Large floating-point numbers |
| `DATE` | Date only (YYYY-MM-DD) |
| `DATETIME` | Date + time (YYYY-MM-DD HH:MM:SS) |

---

## REFERENCE: Available Generators

### Generic Generators (always available)

| Generator | Required Params | Optional Params | Description |
|-----------|----------------|-----------------|-------------|
| `uuid4` | — | — | Random UUID string |
| `random_choice` | `choices: [list]` | — | Uniform random pick from a list |
| `weighted_choice` | `choices: {val: weight, ...}` | — | Weighted random pick; weights should sum to ~1.0 |
| `random_int` | `min`, `max` | — | Random integer in range [min, max] |
| `random_decimal` | `min`, `max` | `precision` (default 2) | Random float in range, rounded to precision |
| `date_range` | `start_days_ago`, `end_days_ahead` | `rolling: true` | Random date/datetime in range relative to today |
| `entity_ref` | `entity`, `field` | — | Random value from the shared entity pool |
| `compound` | `template`, `refs: [entity_types]` | — | Template string filled with entity pool values |
| `sequence` | `template` | `min` (start number) | Sequential IDs like `"INV-{i:06d}"` |
| `constant` | `choices: value` | — | Same value for every row |
| `derived_from_date` | `source_column`, `format` | — | Derive string from a date column |
| `stage_derived` | `source_column`, `mapping: {val: result}` | — | Map one column's values to another |
| `faker` | `faker_method` | `faker_args: {kwarg: val}` | Any [Faker](https://faker.readthedocs.io/) method |

### Salesforce Generators

| Generator | Params | Description |
|-----------|--------|-------------|
| `sf_id` | `template` (3-char prefix) | 18-char Salesforce-style ID. Prefixes: `001`=Account, `003`=Contact, `006`=Opportunity |
| `sf_opportunity_name` | — | "Company - Product" format using entity pool |
| `sf_case_subject` | — | Realistic support case subjects |
| `sf_lead_rating` | — | Hot (20%), Warm (35%), Cold (45%) |

### Google Analytics Generators

| Generator | Params | Description |
|-----------|--------|-------------|
| `ga_session_id` | — | `"digits.digits"` format session ID |
| `ga_page_path` | — | Random from common website paths |
| `ga_source` | — | Traffic sources (google 35%, direct 25%, facebook 10%, ...) |
| `ga_medium` | — | Mediums (organic 35%, cpc 20%, social 12%, ...) |
| `ga_campaign` | — | Campaign names (brand, non-brand, retargeting, ...) |
| `ga_browser` | — | Browsers (Chrome 55%, Safari 20%, Firefox 10%, ...) |
| `ga_device_category` | — | desktop 55%, mobile 35%, tablet 10% |
| `ga_country` | — | Countries (US 45%, UK 10%, Canada 8%, ...) |
| `ga_bounce_rate` | — | Gaussian distribution centered at 55%, range 0-1 |
| `ga_session_duration` | — | Seconds; 30% bounce (0-10s), rest 10-900s |
| `ga_pageviews` | — | Exponential distribution, min 1 |
| `ga_landing_page` | — | Weighted common landing pages |

### Financial Generators

| Generator | Params | Description |
|-----------|--------|-------------|
| `gl_account_code` | — | Random GL account code (1000-9000) |
| `gl_account_name` | `source_column` | Derives account name from account code column |
| `invoice_number` | `template` (prefix), `min` (start) | Sequential invoice IDs like `"INV-10001"` |
| `payment_terms` | — | Net 15/30/45/60, Due on Receipt |
| `payment_method` | — | ACH, Wire, Check, Credit Card, PayPal |
| `invoice_status` | — | Paid 45%, Open 25%, Overdue 15%, Partial 10%, Void 5% |
| `journal_type` | — | Standard 60%, Adjusting 20%, Closing 10%, Reversing 10% |
| `department` | — | Sales, Marketing, Engineering, Operations, Finance, HR, Support |
| `fiscal_period` | `source_column` | `"FY{year}-{month}"` derived from a date column |
| `debit_credit` | — | Random Debit or Credit |

### Marketing / Ads Generators

| Generator | Params | Description |
|-----------|--------|-------------|
| `ad_platform` | — | Google Ads 35%, Facebook 30%, LinkedIn 15%, Instagram 12%, Twitter 8% |
| `campaign_objective` | — | Conversions, Traffic, Brand Awareness, Lead Gen, App Installs, Video Views |
| `ad_format` | — | Search, Display, Video, Carousel, Single Image, Collection, Stories |
| `ad_headline` | — | Marketing copy headlines |
| `ad_keyword` | — | Marketing/BI-related keywords |
| `targeting_type` | — | Keywords, Interest, Lookalike, Retargeting, Custom Audience, Demographic |
| `impressions` | `min`, `max` | Log-normal distribution of impression counts |
| `clicks_from_impressions` | `source_column` | Derives clicks from impressions (0.5-8% CTR) |
| `ctr` | `refs: [ClicksCol, ImpressionsCol]` | Calculates CTR percentage from two columns |
| `cost_per_click` | `min`, `max` | Random CPC in range |
| `ad_spend` | `refs: [ClicksCol, CPCCol]` | Calculates spend = clicks * CPC |
| `conversions_from_clicks` | `source_column` | Derives conversions from clicks (2-15% rate) |
| `hubspot_lifecycle` | — | Subscriber, Lead, MQL, SQL, Opportunity, Customer, Evangelist |
| `hubspot_lead_status` | — | New, Open, In Progress, Attempted to Contact, Connected, Qualified, Unqualified |
| `ad_group_id` | — | 12-digit random numeric string |

---

## REFERENCE: Entity Pool

These shared entities ensure cross-dataset referential integrity. Use `entity_ref` generator with `entity` and `field` params.

### company (200 entities)
| Field | Example |
|-------|---------|
| `id` | UUID |
| `account_id` | `"ACC-0001"` |
| `name` | `"Meridian Systems"` |
| `domain` | `"meridiansystems.com"` |
| `industry` | Technology, Healthcare, Finance, Manufacturing, Retail, Education, ... (18 industries) |
| `size` | SMB, Mid-Market, Enterprise |
| `city` | Major US city |
| `state` | US state code |
| `annual_revenue` | 500K - 50M |
| `employee_count` | 10 - 10000 |

### person (500 entities)
| Field | Example |
|-------|---------|
| `id` | UUID |
| `contact_id` | `"CON-0001"` |
| `first_name` | `"Sarah"` |
| `last_name` | `"Chen"` |
| `full_name` | `"Sarah Chen"` |
| `email` | `"sarah.chen@meridiansystems.com"` |
| `company_id` | UUID (linked to a company) |
| `company_name` | `"Meridian Systems"` |
| `title` | CEO, CTO, VP Sales, Product Manager, ... (15 titles) |
| `phone` | `"(555) 123-4567"` |

### product (50 entities)
| Field | Example |
|-------|---------|
| `id` | UUID |
| `name` | `"CloudSync Pro"` |
| `category` | SaaS, Hardware, Services, Support, Training, Consulting |
| `unit_price` | 49.99 - 9999.99 |
| `sku` | `"SKU-PRD-001"` |

### sales_rep (20 entities)
| Field | Example |
|-------|---------|
| `id` | UUID |
| `rep_id` | `"REP-001"` |
| `first_name` | `"Mike"` |
| `last_name` | `"Johnson"` |
| `full_name` | `"Mike Johnson"` |
| `email` | `"mike.johnson@company.com"` |
| `region` | West, East, Central, South, Northeast, Southeast, International |

### campaign (30 entities)
| Field | Example |
|-------|---------|
| `id` | UUID |
| `name` | `"Spring Launch"` |
| `channel` | Email, Social, PPC, Display, Content, Events, Webinar, Direct Mail |
| `budget` | 5000 - 100000 |
| `status` | Active, Completed, Planned, Paused |

---

## REFERENCE: Source Type Map

Current mappings from `source_type` to Domo provider key (controls the connector icon):

| source_type | Domo Provider Key |
|-------------|-------------------|
| `salesforce` | `salesforce` |
| `google_analytics` | `google-analytics` |
| `quickbooks` | `quickbooks` |
| `netsuite` | `netsuite` |
| `google_ads` | `google-adwords` |
| `facebook_ads` | `facebook` |
| `hubspot` | `hubspot` |
| `linkedin_ads` | `linkedin` |

To add a new source type, run `datagen discover-types <search>` to find the provider key, then add it to `SOURCE_TYPE_MAP` in `datagen/domo_client.py`.

---

## REFERENCE: Complete Example

This is a real catalog file (`catalog/marketing_google_ads.yaml`) showing the full pattern:

```yaml
dataset:
  name: Google Ads - Campaign Performance
  domo_id: null
  source_type: google_ads
  description: Sample Google Ads campaign performance data
  row_count: 3000
schema:
- name: Date
  type: DATE
  generator: date_range
  start_days_ago: 90
  end_days_ahead: 0
  rolling: true
- name: CampaignName
  type: STRING
  generator: entity_ref
  entity: campaign
  field: name
- name: AdGroupId
  type: STRING
  generator: ad_group_id
- name: Keyword
  type: STRING
  generator: ad_keyword
- name: AdHeadline
  type: STRING
  generator: ad_headline
- name: Impressions
  type: LONG
  generator: impressions
  min: 100
  max: 50000
- name: Clicks
  type: LONG
  generator: clicks_from_impressions
  source_column: Impressions
- name: CostPerClick
  type: DECIMAL
  generator: cost_per_click
  min: 0.5
  max: 12.0
- name: Spend
  type: DECIMAL
  generator: ad_spend
  refs:
  - Clicks
  - CostPerClick
- name: Conversions
  type: LONG
  generator: conversions_from_clicks
  source_column: Clicks
- name: ConversionValue
  type: DECIMAL
  generator: random_decimal
  min: 0
  max: 5000
  precision: 2
- name: QualityScore
  type: LONG
  generator: random_int
  min: 1
  max: 10
- name: AdFormat
  type: STRING
  generator: weighted_choice
  choices:
    Search: 0.5
    Display: 0.25
    Video: 0.15
    Shopping: 0.1
- name: TargetingType
  type: STRING
  generator: targeting_type
```

### Key patterns shown:
- **Rolling dates**: `Date` column with `rolling: true` keeps data current
- **Entity references**: `CampaignName` pulls from the shared campaign pool
- **Dependent columns**: `Clicks` derives from `Impressions` via `source_column`
- **Multi-column dependencies**: `Spend` derives from both `Clicks` and `CostPerClick` via `refs`
- **Weighted choices**: `AdFormat` with realistic distribution weights
- **Bounded ranges**: `Impressions` with `min`/`max`, `CostPerClick` with `min`/`max`

---

## After Implementation

Once the YAML and any new generators are created:

```bash
# Generate the CSV
datagen generate <dataset_name>

# Create the dataset in Domo (first time only)
datagen create-dataset <dataset_name>

# Upload data
datagen upload <dataset_name>

# Set the connector icon
datagen set-type <dataset_name>
```
