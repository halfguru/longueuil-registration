# Longueuil-Aweille Expansion Plan

## Goal
Add two new commands (`browse`, `verify`) and pause & confirm feature to `register`.

---

## Phase 1: Browse Command ✅

- [x] Create `src/longueuil_aweille/browse.py`
  - [x] `ActivityScraper` class with pagination handling
  - [x] `Activity` dataclass (name, age_range, schedule, location, spots, status)
  - [x] Filter logic (available, age, day, location)
  - [x] Rich table output

- [x] Update `__main__.py`
  - [x] Add `browse` subcommand with filter options
  - [x] Wire up to `ActivityScraper`

- [x] Test browse command manually on live site

## Review - Phase 1

- Created `browse.py` with `ActivityScraper` class
- Added `browse` subcommand with options: `--domain`, `--available`, `--name`, `--location`, `--day`, `--age`
- Scraper navigates to Disponibilités tab and selects appropriate radio button
- Pagination handled to scrape all pages (38 pages, 390 activities)
- Filters work for domain, available, and name

---

## Phase 2: Pause & Confirm

- [ ] Update `config.py`
  - [ ] Add `require_confirm: bool = True`
  - [ ] Add `confirm_timeout: int = 300`

- [ ] Update `registration.py`
  - [ ] After SUCCESS, pause instead of closing browser
  - [ ] Add async input with timeout (`asyncio.wait_for`)
  - [ ] Handle 'C' key → click cancel button, return CANCELLED status
  - [ ] Handle Enter/timeout → close browser, return SUCCESS
  - [ ] Disable pause in headless mode (auto-confirm)

- [ ] Find cancel button selector on confirmation page
  - [ ] Investigate site flow or ask user for selector

- [ ] Update `cli.py`
  - [ ] Pass confirm options to bot
  - [ ] Display clear prompt message

- [ ] Test pause & confirm flow manually

---

## Phase 3: Verify Command ✅

- [x] Create `src/longueuil_aweille/verify.py`
  - [x] Hit `https://validationcarteacces.longueuil.quebec/`
  - [x] Submit carte_acces + telephone
  - [x] Return valid/invalid status

- [x] Update `__main__.py`
  - [x] Add `verify` subcommand

- [x] Test with valid and invalid credentials

- [x] Integrate verification into `register` command
  - [x] Add `--verify/--no-verify` flag (default: verify)
  - [x] Verify all participants before registration

## Review - Phase 3

- Created `verify.py` with `VerificationBot` class
- Added `verify` subcommand with `--carte` and `--tel` options
- Refactored CLI: `register` is now a proper subcommand instead of callback
- Fixed `uv sync` issue by pinning Python 3.12 in `.python-version`
- Renamed fields: `dossier` → `carte_acces`, `nip` → `telephone`
- Updated README.md and AGENTS.md with correct commands
- Tested: valid credentials return VALID, invalid return INVALID
- Integrated credential verification into `register` command
- Running `uv run aweille register` now verifies credentials by default

---

## Phase 4: Polish ✅

- [x] Update README.md with new commands
- [x] Add professional tone to README and CLI messages
- [x] Add pre-commit hook with ruff format and check
- [x] Add `.gitattributes` for consistent line endings
- [x] Add tests for new functionality
  - [x] `test_config.py` - Participant and Settings tests
  - [x] `test_cli.py` - CLI command tests (register, verify, browse)
- [x] Run typecheck: `uv run mypy src`

---

## Recent Updates

### Added Participant Age Field
- Added `age` field to `Participant` model for validation
- Updated `config.toml` example in README
- Added participant options table to documentation

### Added CLI Tests
- Created `tests/test_cli.py` with 12 tests covering:
  - Version flag
  - Register command (missing config, no participants, success, timeout, CLI options)
  - Verify command (valid, invalid, missing args)
  - Browse command (no activities, with activities, domain not found)
- Used `AsyncMock` for async bot methods
- Total: 16 tests passing

---

## Open Questions

1. Cancel button selector - need to find on site
2. Browse output - table only, or also JSON/CSV option?
3. Any additional browse filters?
