# Rule: Domo App Platform AI (Toolkit-First)

This rule is **toolkit-first**. Use `AIClient` from `@domoinc/toolkit`.

> Legacy endpoint-first guidance has been archived to `archive/legacy-rules/domo-ai-endpoints.md`.

## Canonical Client

```bash
yarn add @domoinc/toolkit
```

```typescript
import { AIClient } from '@domoinc/toolkit';
```

## Text Generation

```typescript
const response = await AIClient.generate_text(
  'Explain this sales trend in simple terms',
  { template: 'You are a business analyst. ${input}' },
  { tone: 'professional' },
  undefined,
  { temperature: 0.7 }
);

const body = response.data || response.body || response;
const text = body.output || body.choices?.[0]?.output;
```

## Additional AI Methods

```typescript
const sqlResult = await AIClient.text_to_sql('Show total sales by region', [
  {
    dataSourceName: 'Sales',
    description: 'Sales transactions',
    columns: [{ name: 'region', type: 'string' }, { name: 'amount', type: 'number' }]
  }
]);

const beastModeResult = await AIClient.text_to_beastmode(
  'Calculate year over year growth percentage',
  { dataSourceName: 'Revenue', columns: [{ name: 'revenue', type: 'number' }, { name: 'date', type: 'date' }] }
);
```

## Response Handling Rule

`AIClient` responses are not always shaped like other toolkit clients:
- often uses `response.data`
- may include both `output` and `choices`

Always parse defensively:

```typescript
const body = response.data || response.body || response;
const output = body.output || body.choices?.[0]?.output;
```

## Canonical Rules References

- Toolkit AI methods and caveats: `.cursor/rules/04-toolkit.mdc`
- Naming/response gotchas: `.cursor/rules/09-gotchas.mdc`

## Checklist
- [ ] `AIClient` methods use snake_case (`generate_text`, `text_to_sql`, etc.)
- [ ] Responses parsed from `data`/`body` fallback
- [ ] Prefer `output`; fallback to `choices[0].output`
- [ ] Error handling and loading state in UI
