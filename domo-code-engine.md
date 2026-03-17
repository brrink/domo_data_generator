# Rule: Domo App Platform Code Engine (Toolkit-First)

This rule is **toolkit-first**. Use `CodeEngineClient` for function execution from apps.

> Legacy endpoint-first guidance has been archived to `archive/legacy-rules/domo-code-engine.md`.

## Canonical Client

```bash
yarn add @domoinc/toolkit
```

```typescript
import { CodeEngineClient } from '@domoinc/toolkit';

const response = await CodeEngineClient.execute(
  'calculateTax',
  { amount: 1000, state: 'CA' }
);
const result = response.body.output;
```

## Manifest Requirements

Code Engine functions still require `packageMapping` in `manifest.json`.

```json
{
  "packageMapping": [
    {
      "alias": "calculateTax",
      "parameters": [
        { "alias": "amount", "type": "number", "nullable": false, "isList": false, "children": null },
        { "alias": "state", "type": "string", "nullable": false, "isList": false, "children": null }
      ],
      "output": { "alias": "result", "type": "object", "children": null }
    }
  ]
}
```

## Error Handling Pattern

```typescript
async function executeFunction(alias: string, payload: Record<string, unknown>) {
  try {
    const response = await CodeEngineClient.execute(alias, payload);
    return response.body;
  } catch (error) {
    console.error(`CodeEngineClient.execute failed for ${alias}`, error);
    throw error;
  }
}
```

## Canonical Rules References

- Toolkit patterns: `.cursor/rules/04-toolkit.mdc`
- Manifest mapping details: `.cursor/rules/06-manifest.mdc`
- Operational gotchas: `.cursor/rules/09-gotchas.mdc`

## Checklist
- [ ] Function alias defined in `packageMapping`
- [ ] Calls use `CodeEngineClient.execute()` (not raw `domo.post` by default)
- [ ] Output parsing uses `response.body`
- [ ] Errors handled and surfaced to UI or logs
