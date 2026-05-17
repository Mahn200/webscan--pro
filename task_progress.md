# Task Progress Checklist
- [ ] Fix 1 — `utils/stealth.py`: Add httpx.Timeout(20.0), improve error logging in warm_up
- [ ] Fix 2 — `scanners/passive_scanner.py`: Add follow_redirects=True, httpx.Timeout(20.0), improve error logging
- [ ] Fix 3 — `main.py`: Add exc_info=True logging, pass error_message to update_scan_status
- [ ] Fix 4 — `database/models.py` + `database/crud.py`: Add error_message field and parameter
- [ ] Fix 5 — `frontend/lib/screens/scan_screen.dart`: Add 5-minute polling timeout safety net
