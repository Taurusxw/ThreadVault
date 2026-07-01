# Deep Research Report Appendices

This file tracks MathForge implementation appendices that reference the ThreadVault research principles during active Codex development.

## MathForge Round 22 - Formula Model Rerun Queue Framework

Date: 2026-07-01

Applied principle: build an auditable local fact layer before automating destructive or expensive model behavior.

Implementation notes:

- Added a durable `formula_rerun` task boundary for Pix2Text/Qwen-VL local formula review.
- The task payload records question id, target section, line number, original line text, source page, engine, and priority.
- The backend revalidates the target line before doing any model work, preventing stale suggestions from silently applying to edited Markdown.
- The runner reuses the existing OCR engine health registry and installation facts instead of guessing model availability in the UI.
- Current behavior intentionally fails when dependencies are missing or when the real adapter is still a placeholder.
- React exposes task creation and task-status review, but does not auto-overwrite question Markdown or claim real OCR inference.

Remaining research-linked boundary:

- Real Pix2Text/Qwen-VL runners must be added with explicit fixtures, page/region crop inputs, output parsing, and human-reviewable results before any automatic revision workflow is considered.

## MathForge Round 23 - PDF OCR Cache Cleanup And Real Upload Recovery E2E

Date: 2026-07-01

Applied principle: maintenance should be inspectable before destructive action, and recovery claims should be proven against real local state.

Implementation notes:

- Added dry-run/apply cleanup for `work/pdf_ocr_search_index/pdfocr_*`.
- The cleanup report records index id, path, manifest path, byte size, age, source name, task id, status, reason, and active-task protection.
- Queued/running conversion tasks referenced by an OCR index manifest are never deleted by cache cleanup.
- Non-index directories under the cache root are reported as invalid and preserved.
- React exposes cache inventory and cleanup from the PDF parse page without starting OCR during search or maintenance.
- Added a real-backend Playwright test where the first chunk reaches FastAPI, the second chunk is interrupted, the tab reloads, and reselecting the same PDF resumes the upload from persisted backend state.

Remaining research-linked boundary:

- More abnormal upload matrices, page-level OCR refinement, and real optional model runners remain separate work; this round intentionally avoids guessing recovery from arbitrary residue or pretending model inference exists.

## MathForge Round 24 - Real Backend Double-Corrupt Upload Recovery

Date: 2026-07-01

Applied principle: damaged local state should produce explicit, test-backed recovery guidance rather than guessed reconstruction.

Implementation notes:

- Added a real-backend Playwright test for the browser path where both chunk upload manifest files are corrupt.
- The test creates a real pending upload through React and FastAPI, then writes invalid JSON into `manifest.json` and `manifest.json.bak` under the isolated `work/e2e_real_backend` root.
- The browser reload path keeps only resumable metadata in localStorage and still requires the user to reselect the same local PDF.
- Retrying the upload surfaces the backend's cancel/restart guidance instead of rebuilding a manifest from residue.
- Clicking `取消上传` uses the existing `DELETE` route, deletes the corrupt session directory, clears browser pending state, and allows a clean upload restart.
- No production upload code change was needed; the round strengthened evidence and documentation around the existing contract.

Remaining research-linked boundary:

- More long-tail upload failures, such as multi-file mixed missing chunks, merge-time disk failures, and task-creation failures, remain future test scenarios.
- Real Pix2Text/Qwen-VL and optional PDF-to-Markdown runners still require separate model fixtures and human-reviewable result contracts.

## MathForge Round 25 - Real Backend Missing Chunk Retry

Date: 2026-07-01

Applied principle: durable local facts should be re-read at recovery boundaries instead of trusting stale browser state.

Implementation notes:

- Added a real-backend Playwright test for the path where a chunk file disappears before `complete`.
- The browser uploads a real 9MB PDF through FastAPI, then the test deletes `000001.part` in the isolated chunk session before allowing `complete` to run.
- The UI displays the backend's missing-chunk guidance and keeps the pending upload session available.
- A second upload attempt reuses the same `resume_key`; FastAPI recomputes uploaded chunks from disk and the browser uploads only the missing part.
- The retry completes by creating a normal conversion task, proving the route chain is recoverable without a new upload protocol.
- No production upload code change was required; the round documents and tests the existing manifest-plus-files fact layer.

Remaining research-linked boundary:

- Merge-time disk write failures, task creation failures after chunk assembly, and richer multi-file abnormal matrices remain separate validation work.

## MathForge Round 26 - Real Backend Complete Response Loss Retry

Date: 2026-07-01

Applied principle: idempotent local facts should prevent duplicate work after a lost response.

Implementation notes:

- Added a real-backend Playwright test for the path where `complete` succeeds on the server but the browser never receives the response.
- The test uses `route.fetch()` to let FastAPI merge chunks, create the conversion task, and write `task_id` into the chunk manifest, then aborts the browser route.
- The UI sees the same recovery wrapper it would see for a network failure and keeps the pending upload session.
- A retry returns the same manifest-backed task id rather than creating duplicate OCR work.
- The round explicitly avoided using Pix2Text as a fake synchronous task-creation failure after code inspection showed optional engines fail inside the subprocess task.

Remaining research-linked boundary:

- Future upload-matrix work should cover true pre-task validation failures and merge-time disk write failures with similarly precise evidence.

