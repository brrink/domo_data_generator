# Rule: Domo App Platform AppDB (Toolkit-First)

This rule is **toolkit-first**. Use `AppDBClient` instead of raw `domo.get/post/put/delete` endpoints.

> Legacy endpoint-first guidance has been archived to `archive/legacy-rules/domo-appdb.md`.

## Canonical Client

```bash
yarn add @domoinc/toolkit
```

```typescript
import { AppDBClient } from '@domoinc/toolkit';

type Task = {
  title: string;
  status: 'active' | 'completed';
  priority: 'Low' | 'High' | 'Urgent';
};

const tasksClient = new AppDBClient.DocumentsClient<Task>('TasksCollection');
```

## Core Operations

### Create
```typescript
const created = await tasksClient.create({
  title: 'New Task',
  status: 'active',
  priority: 'High'
});
const task = created.body;
```

### Read / query
```typescript
const all = await tasksClient.get();
const active = await tasksClient.get({ status: { $eq: 'active' } });
const highOpen = await tasksClient.get({
  $and: [{ status: { $ne: 'completed' } }, { priority: { $in: ['High', 'Urgent'] } }]
});
```

### Update
```typescript
await tasksClient.update({
  id: 'document-uuid',
  content: { title: 'Updated', status: 'completed', priority: 'Low' }
});

await tasksClient.partialUpdate(
  { status: { $eq: 'active' } },
  { $set: { status: 'archived' } }
);
```

### Delete
```typescript
await tasksClient.delete('document-uuid');
await tasksClient.delete(['uuid-1', 'uuid-2']);
```

## Manifest Requirements

Collections still must exist in `manifest.json` under `collections`.

```json
{
  "collections": [
    {
      "name": "TasksCollection",
      "schema": {
        "columns": [
          { "name": "title", "type": "STRING" },
          { "name": "status", "type": "STRING" }
        ]
      }
    }
  ]
}
```

## Canonical Rules References

- Toolkit AppDB patterns: `.cursor/rules/04-toolkit.mdc`
- AppDB gotchas and sync caveats: `.cursor/rules/09-gotchas.mdc`

## Checklist
- [ ] `collections` mapping exists in manifest
- [ ] `AppDBClient.DocumentsClient` used for CRUD
- [ ] Query/update operators (`$eq`, `$in`, `$set`, `$inc`, etc.) used correctly
- [ ] Error handling and loading states included in UI flows
