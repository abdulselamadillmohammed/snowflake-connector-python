# Connection-Centered Change Backlog

This document lists concrete code changes starting from `src/snowflake/connector/connection.py` and moving outward into the modules it directly depends on.

Scope note: this intentionally excludes `src/snowflake/notes/**`, which is your local notes area and not part of the original codebase.

In each entry:
- `Previous version` means the current state of the repository today.
- `Future version` means the proposed state after the change.

## Recommended First Commits

If you want the safest first commit candidates from this list, start with one of these:

1. `02` - Add an explicit `bool` type to `consent_cache_id_token`.
2. `03` - Simplify and harden `setup_ocsp_privatelink`.
3. `05` - Remove the no-op `self.auth_class = self.auth_class` assignment.
4. `06` - Fix the stale async `auth_class` setter error message.
5. `10` - Add targeted unit tests around connection-adjacent validation paths.

## Proposed Updates

### 01. Introduce a Shared `ErrorHandler` Type Alias
- Scope: `src/snowflake/connector/connection.py:979`, `src/snowflake/connector/cursor.py:379`, `src/snowflake/connector/cursor.py:549`, `src/snowflake/connector/errors.py:210`.
- Effort: Small.
- Previous version: the connection and cursor expose raw `Callable` types, while `errors.py` already assumes one concrete handler shape: `(connection, cursor, error_class, error_value) -> None`.
- Future version: define one shared alias or `Protocol` for the error-handler signature and reuse it across the backing fields, public properties, and helper wrappers.
- Reasoning: this removes type drift, makes refactors safer, and documents the real extension point more clearly.

### 02. Add an Explicit `bool` Return Type to `consent_cache_id_token`
- Scope: `src/snowflake/connector/connection.py:1002`, `src/snowflake/connector/connection.py:2001`.
- Effort: Trivial.
- Previous version: `consent_cache_id_token` has no return annotation even though the backing value is populated with `getattr(..., True)`, which makes it effectively boolean.
- Future version: annotate the property and backing attribute as `bool`.
- Reasoning: this is a low-risk, first-commit-friendly typing cleanup that improves editor support immediately.

### 03. Simplify and Harden `setup_ocsp_privatelink`
- Scope: `src/snowflake/connector/connection.py:1360`, `src/snowflake/connector/aio/_connection.py:237`.
- Effort: Small.
- Previous version: `setup_ocsp_privatelink` takes an unused `app` parameter and manually acquires/releases the lock.
- Future version: remove the unused argument from the method and both call sites, and switch to a safer lock-handling pattern such as `with` or `try/finally`.
- Reasoning: this reduces API noise and closes off the risk of a leaked lock if the function changes later.

### 04. Normalize `AuthByWebBrowser` Port Typing and Origin Validation
- Scope: `src/snowflake/connector/auth/webbrowser.py:59`, `src/snowflake/connector/auth/webbrowser.py:323`, `src/snowflake/connector/connection.py:1482`, `src/snowflake/connector/aio/_connection.py:325`.
- Effort: Small.
- Previous version: `AuthByWebBrowser` stores `port` as `str | None`, but the sync and async callers pass `self.port`, which is an `int`; `_validate_origin` then compares parsed string ports to the stored value.
- Future version: normalize ports to a single type at construction time, ideally `int`, or compare normalized string values on both sides.
- Reasoning: this prevents false-negative origin validation when the browser sends an explicit port.

### 05. Remove the No-Op `self.auth_class = self.auth_class` Assignment
- Scope: `src/snowflake/connector/connection.py:1452`, `src/snowflake/connector/aio/_connection.py:299`.
- Effort: Trivial.
- Previous version: both sync and async custom-auth branches reassign `self.auth_class` to itself after validation.
- Future version: delete the self-assignment or replace it with a real normalization step if one is actually needed.
- Reasoning: this is dead-looking code in a sensitive area, so removing it makes the auth flow easier to read without changing behavior.

### 06. Fix the Stale Async `auth_class` Setter Error Message
- Scope: `src/snowflake/connector/aio/_connection.py:826`.
- Effort: Trivial.
- Previous version: the async setter checks `isinstance(value, AuthByPlugin)` but raises `TypeError("auth_class must subclass AuthByPluginAsync")`.
- Future version: align the error message with the real expected type.
- Reasoning: the current message is misleading during debugging and implies a type that is not what the code is actually checking.

### 07. Fix Duplicate Errno Formatting in `Error.__init__`
- Scope: `src/snowflake/connector/errors.py:69`.
- Effort: Small.
- Previous version: in the non-SQLSTATE path at info/debug log levels, the message is formatted as `000123: 123: message`, which repeats the error number.
- Future version: format the number once, or include a different field there if the duplicate value was not intended.
- Reasoning: error messages are user-facing; repeated codes make them look broken and harder to scan.

### 08. Replace the Unsafe Async Telemetry Logging Path
- Scope: `src/snowflake/connector/errors.py:165`.
- Effort: Small.
- Previous version: `send_exception_telemetry` calls `asyncio.get_running_loop().run_until_complete(result)` when it sees an awaitable, which is invalid once a loop is already running and falls into a debug-only failure path.
- Future version: if a loop is running, schedule work with `create_task`; if not, use an explicit sync bridge or separate sync/async implementations.
- Reasoning: the current code looks like it supports async telemetry but effectively drops that path under real async execution.

### 09. Make Heartbeat and Prefetch Validation Helpers Pure and Typed
- Scope: `src/snowflake/connector/connection.py:2288`.
- Effort: Small.
- Previous version: `_validate_client_session_keep_alive_heartbeat_frequency` and `_validate_client_prefetch_threads` mutate connection state while validating, and the heartbeat helper casts to `int` before its own `None` fallback branch.
- Future version: extract pure clamp/normalize helpers that return a value, then assign that value in the caller.
- Reasoning: pure helpers are easier to test, easier to share with async code, and harder to misuse.

### 10. Add Targeted Unit Tests for Connection-Adjacent Validation Paths
- Scope: `src/snowflake/connector/connection.py:1667`, `src/snowflake/connector/auth/webbrowser.py:323`, `src/snowflake/connector/errors.py:69`.
- Effort: Small.
- Previous version: several important but local branches rely on behavior rather than explicit unit coverage, especially connection kwarg warnings, origin validation, and error formatting.
- Future version: add focused tests for unknown-parameter warnings and typo suggestions in `__config`, explicit-port origin checks in `AuthByWebBrowser`, and formatted error strings in `Error`.
- Reasoning: these are cheap tests that make later refactors around `connection.py` much safer.

### 11. Extract a Shared Session-Parameter Builder from Sync and Async `__open_connection`
- Scope: `src/snowflake/connector/connection.py:1397`, `src/snowflake/connector/aio/_connection.py:245`.
- Effort: Medium.
- Previous version: sync and async both build `_session_parameters` with nearly identical code for autocommit, timezone, validation flags, keep-alive, heartbeat frequency, and prefetch threads.
- Future version: move this into a shared helper on the base connection class or a small mixin.
- Reasoning: this is high-value deduplication because session-parameter drift can create subtle sync/async behavior mismatches.

### 12. Extract an Authenticator Factory from Sync and Async `__open_connection`
- Scope: `src/snowflake/connector/connection.py:1452`, `src/snowflake/connector/aio/_connection.py:299`.
- Effort: Medium to Large.
- Previous version: both sync and async hold large `if/elif` authenticator ladders with mostly parallel logic.
- Future version: move authenticator selection into shared helpers or a registry keyed by the authenticator constant.
- Reasoning: this is the biggest structural duplication around `connection.py`, and it makes auth changes costlier than they need to be.

### 13. Extract a Shared OAuth Default-Scope Helper
- Scope: `src/snowflake/connector/connection.py:1524`, `src/snowflake/connector/connection.py:1552`, `src/snowflake/connector/aio/_connection.py:366`, `src/snowflake/connector/aio/_connection.py:395`.
- Effort: Small.
- Previous version: sync and async duplicate the same `if self._role and (self._oauth_scope == "")` block in both OAuth flows.
- Future version: add a small helper such as `_ensure_default_oauth_scope()` and call it from both branches.
- Reasoning: this is a clean, low-risk dedupe that improves readability right away.

### 14. Extract a Shared Temporary-Credential Preload Helper
- Scope: `src/snowflake/connector/connection.py:1469`, `src/snowflake/connector/connection.py:1567`, `src/snowflake/connector/aio/_connection.py:313`, `src/snowflake/connector/aio/_connection.py:417`.
- Effort: Medium.
- Previous version: browser and MFA branches in sync and async each set session flags and manually call `auth.read_temporary_credentials`.
- Future version: introduce one helper that prepares cached-ID-token and cached-MFA-token state based on auth mode.
- Reasoning: repeated auth side effects are hard to audit; centralizing them makes behavior easier to test and review.

### 15. Replace Dynamic Error Attribute Injection with Explicit Delegation
- Scope: `src/snowflake/connector/connection.py:1352`, `src/snowflake/connector/aio/_connection.py:705`.
- Effort: Medium.
- Previous version: `__set_error_attributes` copies callables from the `errors` module onto the connection object at runtime.
- Future version: replace the dynamic copy with explicit wrapper methods, explicit imports, or a small curated adapter layer.
- Reasoning: runtime monkey-patching obscures the real public API and makes the connection object harder to reason about.

### 16. Route OAuth Token and Refresh Requests Through Fresh Non-Pooled `SessionManager` Sessions
- Scope: `src/snowflake/connector/auth/_oauth_base.py:328`, `src/snowflake/connector/auth/_oauth_base.py:379`, `src/snowflake/connector/auth/_oauth_base.py:452`.
- Effort: Medium.
- Previous version: `_oauth_base.py` manually creates `urllib3.PoolManager` and `ProxyManager` clients, even though the codebase already has a `SessionManager` abstraction and TODO comments pointing at it.
- Future version: create short-lived `SessionManager` instances with `use_pooling=False` for OAuth token exchange and refresh operations.
- Reasoning: this aligns auth HTTP behavior with the rest of the connector and removes duplicated transport logic.

### 17. Consolidate Proxy Resolution Under `SessionManager`
- Scope: `src/snowflake/connector/auth/_oauth_base.py:452`, `src/snowflake/connector/session_manager.py:128`, `src/snowflake/connector/session_manager.py:500`.
- Effort: Medium.
- Previous version: OAuth code resolves proxies itself using explicit config plus environment helpers, while the session layer has its own proxy model.
- Future version: put proxy-selection policy in the HTTP/session layer and let auth code request a ready-to-use session.
- Reasoning: proxy behavior should have one source of truth; duplicated logic is a long-term maintenance trap.

### 18. Replace Raw Qmark Binding Dicts with a Typed Binding Model
- Scope: `src/snowflake/connector/connection.py:2121`.
- Effort: Medium.
- Previous version: `_process_params_qmarks` returns nested dicts keyed by string positions, for example `{"1": {"type": ..., "value": ...}}`.
- Future version: introduce a small typed structure for the in-memory representation, then serialize to the existing wire format at the edge.
- Reasoning: typed local data is easier to validate, easier to refactor, and much easier to unit test.

### 19. Tighten the `_process_params_pyformat` Input Contract
- Scope: `src/snowflake/connector/connection.py:2156`.
- Effort: Small to Medium.
- Previous version: any non-list, non-tuple scalar is silently wrapped into a one-item list even though the function signature already advertises tuple, list, dict, or `None`.
- Future version: reject invalid scalar input directly or move the compatibility shim into a separate adapter layer.
- Reasoning: silently rewriting input shape makes the API harder to understand and hides caller mistakes.

### 20. Unify Duplicated Pyformat Error Paths
- Scope: `src/snowflake/connector/connection.py:2181`, `src/snowflake/connector/connection.py:2197`.
- Effort: Small.
- Previous version: `_process_params_pyformat` and `_process_params_dict` both catch `Exception` and construct nearly identical `ProgrammingError` payloads.
- Future version: use one helper to wrap parameter-processing failures and build a consistent error message.
- Reasoning: this reduces duplication and avoids small wording drift between the two branches.

### 21. Harden Sync and Async `_get_query_status`
- Scope: `src/snowflake/connector/connection.py:2374`, `src/snowflake/connector/aio/_connection.py:727`.
- Effort: Medium.
- Previous version: both implementations assume `status_resp["data"]` exists and that `QueryStatus[status]` will always succeed.
- Future version: guard missing keys, handle unknown statuses explicitly, and preserve the raw payload in the failure path.
- Reasoning: monitoring endpoints can evolve; these methods should fail predictably instead of surfacing low-level `KeyError` behavior.

### 22. Protect Async-Query Tracking Maps with Locking
- Scope: `src/snowflake/connector/connection.py:623`, `src/snowflake/connector/connection.py:2405`, `src/snowflake/connector/aio/_connection.py:634`, `src/snowflake/connector/aio/_connection.py:507`.
- Effort: Medium.
- Previous version: `_async_sfqids` and `_done_async_sfqids` are mutated from multiple flows without one dedicated synchronization helper.
- Future version: wrap all mutation in a small set of helper methods protected by the appropriate sync or async lock.
- Reasoning: query-status tracking is concurrency-sensitive, so it should not rely on informal discipline.

### 23. Consolidate Query-Context-Cache Helpers
- Scope: `src/snowflake/connector/connection.py:675`, `src/snowflake/connector/connection.py:1104`, `src/snowflake/connector/connection.py:2482`, `src/snowflake/connector/aio/_connection.py:683`.
- Effort: Medium.
- Previous version: cache initialization, access, mutation, and close-time cleanup are spread across several methods with repeated guard checks.
- Future version: create a small internal helper layer that handles disabled-cache and `None` cases in one place.
- Reasoning: this reduces repeated conditionals and makes query-context behavior easier to change later.

### 24. Avoid `asyncio.run` Inside AIO Close-at-Exit
- Scope: `src/snowflake/connector/aio/_connection.py:723`.
- Effort: Small to Medium.
- Previous version: `_close_at_exit` calls `asyncio.run(self.close(retry=False))`.
- Future version: detect whether a loop is already running and either schedule cleanup safely or fall back to a best-effort synchronous path.
- Reasoning: `asyncio.run` cannot be nested inside an active event loop, which makes this brittle in notebook, service, and test environments.

### 25. Prevent `SessionPool.return_session()` from Re-Adding Unknown Sessions
- Scope: `src/snowflake/connector/session_manager.py:205`.
- Effort: Small.
- Previous version: if a session is not found in `_active_sessions`, the method logs the issue but still appends that session to `_idle_sessions`.
- Future version: only append sessions that were actually checked out from the active pool, and ignore or close foreign/duplicate sessions.
- Reasoning: session pools should not silently accept unknown objects; doing so can create duplicate idle entries and confusing reuse behavior.
