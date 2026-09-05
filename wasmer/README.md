# Twenty / Wasmer compatibility experiment

Base: `twenty/v2.37.0` (`6da524b8903ec16a3eeea4b2e4a5fb63dbfc1c58`).
Branch: `wasmer/compatibility`.

## Patch

- Password and application OAuth-secret hashing use a shared adapter backed by `hash-wasm@4.12.0`, retaining the existing cost and native bcrypt's 72-byte UTF-8 truncation. Empty/NUL-containing inputs use `bcryptjs@3.0.3` to retain native hash behavior. This fallback is substantially slower on QuickJS; it needs concurrency and request-budget evaluation before production use.
- The native Sentry profiler is loaded only if Sentry is enabled and the profiling sample rate is greater than zero. Set `SENTRY_PROFILES_SAMPLE_RATE=0` on Wasmer. Native deployments retain their existing default behavior.
- No queue, database, worker, or encryption algorithm is replaced.

The adapter covers Twenty's two string-based hash/compare call sites. It is not a complete implementation of the native bcrypt package API. Tests cover native hash fixtures, Unicode/NUL/empty inputs, wrong passwords, fresh salts, requested work factors, and malformed/unsupported hashes.

## Local server build

With Node 24, Python 3, and the repository's Yarn version:

```sh
node .yarn/releases/yarn-4.13.0.cjs workspaces focus twenty twenty-server twenty-emails twenty-shared twenty-client-sdk
python3 wasmer/build-server.py
node node_modules/jest/bin/jest.js --config packages/twenty-server/jest.config.mjs --runInBand --runTestsByPath packages/twenty-server/src/engine/core-modules/auth/utils/bcrypt-compat.util.spec.ts
```

The helper executes the upstream server-workspace build commands explicitly, avoiding unrelated UI tasks inferred by Nx from the complete monorepo. Build outputs and logs are local. Lingui extraction/compilation can regenerate tracked translation catalogs; review those separately from the compatibility patch. This helper builds the backend and its runtime workspaces; build/copy the frontend separately before a browser trial.

## Validation and limits

On 2026-09-05: the full native server build passed, all 32 adapter Jest tests passed, and the actual adapter passed fixture/concurrency tests on Node and Edge.js QuickJS 0.2.0 with Wasmer 7.4.0. Compiled instrumentation loaded on Edge.js with profiling disabled; native profiling still loaded at its default rate. Native Postgres initialization/migrations and HTTP health passed using disposable local Postgres 16 and Valkey 8. The full HTTP server also reached healthy status under Edge.js, and the migration command successfully reran there against the already-initialized database.

Wasmer cloud deployment, managed Postgres compatibility, external Redis quotas, the frontend/onboarding trial, and persistent worker operation are not yet validated. This branch is experimental; successful component tests do not imply production readiness.

## Frontend and standalone package

The frontend is unchanged by this fork. To reuse the matching official release build:

```sh
python3 wasmer/copy-release-frontend.py
python3 wasmer/package-runtime.py
```

The first helper verifies `APP_VERSION` and extracts static files from the immutable official `v2.37.0` ARM64 image; the image is never executed. The second assembles `.wasmer/package/` from compiled workspaces and a focused production dependency install. It excludes host native addons and emits a Wasmer manifest plus a minimal app descriptor. It refuses to overwrite an existing generated package.

The manifest pins Edge.js QuickJS 0.2.0 and Bash 1.0.25 and exposes `server`, `initialize`, `migrate`, `upgrade`, and `precompile` commands. It does not register a continuous worker. The `server` command does not initialize or migrate the database. The release commands are individual building blocks, not an automatically retried deployment pipeline.

Before deployment, configure the Wasmer account/app placement and supply `PG_DATABASE_URL`, `REDIS_URL`, `APP_SECRET`, `ENCRYPTION_KEY`, `SERVER_URL`, and the platform's listening-port settings securely. Validate managed database capabilities and release failure/recovery behavior. Keep automatic migration retries disabled until the complete release sequence has been tested on that platform.

Fresh database initialization and migrations have now also passed entirely under Edge.js against disposable local Postgres/Valkey. Hosted networking, TLS/service quotas, onboarding, and the persistent worker remain separate gates.
