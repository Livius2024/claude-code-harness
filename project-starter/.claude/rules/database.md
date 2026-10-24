---
paths:
  - "**/schema*"
  - "**/migrations/**"
  - "drizzle/**"
  - "prisma/**"
  - "**/models.py"
  - "alembic/**"
---

# Database

- Every schema change: edit the schema, generate a migration, read the generated SQL, apply it locally, commit both.
- Never push a schema straight to a database (`drizzle-kit push`, `prisma db push`). Never edit a migration that is already committed; add a new one.
- A migration that drops or rewrites columns with data needs the owner's OK, with a note on how to roll back.
- Never run migrations or queries against production; the owner does that.
