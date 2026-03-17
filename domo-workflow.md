# Rule: Domo App Platform Workflows (Toolkit-First)

This rule is **toolkit-first**. Use `WorkflowClient` for workflow operations in apps.

> Legacy endpoint-first guidance has been archived to `archive/legacy-rules/domo-workflow.md`.

## Canonical Client

```bash
yarn add @domoinc/toolkit
```

```typescript
import { WorkflowClient } from '@domoinc/toolkit';

const startResponse = await WorkflowClient.start('model-uuid', {
  inputVar: 'value',
  anotherVar: 123
});
const instance = startResponse.body;
```

Check status:
```typescript
const statusResponse = await WorkflowClient.getInstance(instance.id);
const status = statusResponse.body.status;
```

## Manifest Requirements

Workflows still require `workflowMapping` entries in `manifest.json`.

```json
{
  "workflowMapping": [
    {
      "alias": "sendReport",
      "parameters": [
        { "aliasedName": "reportType", "type": "string", "list": false, "children": null },
        { "aliasedName": "recipients", "type": "string", "list": true, "children": null }
      ]
    }
  ]
}
```

## Error Handling Pattern

```typescript
async function runWorkflow(modelId: string, payload: Record<string, unknown>) {
  try {
    const response = await WorkflowClient.start(modelId, payload);
    return response.body;
  } catch (error) {
    console.error(`WorkflowClient.start failed for ${modelId}`, error);
    throw error;
  }
}
```

## Canonical Rules References

- Toolkit workflow methods: `.cursor/rules/04-toolkit.mdc`
- Workflow mapping requirements: `.cursor/rules/06-manifest.mdc`
- Runtime caveats: `.cursor/rules/09-gotchas.mdc`

## Checklist
- [ ] `workflowMapping` is configured
- [ ] Calls use `WorkflowClient` (`start`, `getInstance`, etc.)
- [ ] Response parsing uses `response.body`
- [ ] Long-running workflow UX includes status checks or async user feedback
