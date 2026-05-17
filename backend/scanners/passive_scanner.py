"""
Passive Scanner for WebScan Pro.
Analyzes SSL/TLS, HTTP headers, cookies, and information disclosure
without sending malicious payloads.
"""

import logging
import re
import socket
import ssl
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

import httpx

from utils.stealth import StealthSession, get_realistic_headers

logger = logging.getLogger("webscanpro.passive_scanner")


class PassiveScanner:
    """
    Performs passive security analysis on a target URL.
    Checks: SSL/TLS configuration, HTTP security headers, cookies, info disclosure.
    """

    def __init__(self, target_url: str, language: str = "en"):
        self.target_url = target_url.rstrip("/")
        self.language = language
        self.parsed = urlparse(self.target_url)
        self.hostname = self.parsed.hostname or ""
        self.base_url = f"{self.parsed.scheme}://{self.parsed.netloc}"
        self.vulnerabilities: List[Dict] = []

    async def run(self) -> List[Dict]:
        """
        Execute all passive checks and return findings.
        """
        logger.info(f"Starting passive scan for {self.target_url}")

        # Run SSL check
        ssl_result = await self._check_ssl()
        if ssl_result:
            self.vulnerabilities.append(ssl_result)

        # Run HTTP headers check
        headers_result = await self._analyze_headers()
        self.vulnerabilities.extend(headers_result)

        # Run cookie analysis
        cookie_results = await self._analyze_cookies()
        self.vulnerabilities.extend(cookie_results)

        # Info disclosure check
        info_result = await self._check_info_disclosure()
        if info_result:
            self.vulnerabilities.extend(info_result)

        logger.info(
            f"Passive scan complete for {self.target_url}: "
            f"{len(self.vulnerabilities)} findings"
        )
        return self.vulnerabilities

    async def _check_ssl(self) -> Optional[Dict]:
        """Check SSL/TLS certificate validity and configuration."""
        if self.parsed.scheme != "https":
            return None

        try:
            context = ssl.create_default_context()
            context.check_hostname = True
            context.verify_mode = ssl.CERT_REQUIRED

            with socket.create_connection(
                (self.hostname, self.parsed.port or 443), timeout=10
            ) as sock:
                with context.wrap_socket(sock, server_hostname=self.hostname) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    ssl_version = ssock.version()

            # Check certificate expiration
            if cert and "notAfter" in cert:
                expiry_str = str(cert["notAfter"])
                expiry_date = datetime.strptime(
                    expiry_str, "%b %d %H:%M:%S %Y %Z"
                ).replace(tzinfo=timezone.utc)
                days_remaining = (expiry_date - datetime.now(timezone.utc)).days

                if days_remaining < 0:
                    severity = "high"
                    title_en = "SSL Certificate Expired"
                    title_tr = "SSL Sertifikası Süresi Dolmuş"
                    desc_en = f"SSL certificate expired {abs(days_remaining)} days ago."
                    desc_tr = f"SSL sertifikasının süresi {abs(days_remaining)} gün önce dolmuş."
                elif days_remaining < 30:
                    severity = "medium"
                    title_en = "SSL Certificate Expiring Soon"
                    title_tr = "SSL Sertifikası Yakında Süresi Dolacak"
                    desc_en = f"SSL certificate expires in {days_remaining} days."
                    desc_tr = f"SSL sertifikasının süresi {days_remaining} gün içinde dolacak."
                else:
                    severity = "info"
                    title_en = "SSL Certificate Valid"
                    title_tr = "SSL Sertifikası Geçerli"
                    desc_en = f"SSL certificate is valid and expires in {days_remaining} days."
                    desc_tr = f"SSL sertifikası geçerli ve {days_remaining} gün içinde süresi dolacak."

                title = title_tr if self.language == "tr" else title_en
                description = desc_tr if self.language == "tr" else desc_en

                # Weak cipher check
                cipher_strength = "weak"
                if cipher and cipher[0]:
                    cipher_name = cipher[0]
                    if any(
                        weak in cipher_name.upper() for weak in ["RC4", "DES", "MD5"]
                    ):
                        cipher_strength = "weak"
                        if severity != "high":
                            severity = "high"
                        description += " " + (
                            f"Weak cipher detected: {cipher_name}"
                            if self.language == "en"
                            else f"Zayıf şifreleme tespit edildi: {cipher_name}"
                        )
                    else:
                        cipher_strength = "strong"

                evidence = (
                    f"SSL Version: {ssl_version}, Cipher: {cipher[0] if cipher else 'Unknown'}, "
                    f"Expires: {expiry_str}"
                )

                return {
                    "type": "ssl",
                    "severity": severity,
                    "title": title,
                    "description": description,
                    "url": self.target_url,
                    "evidence": evidence,
                    "remediation": (
                        "Renew the SSL certificate before expiry and disable weak ciphers."
                        if self.language == "en"
                        else "SSL sertifikasını süresi dolmadan yenileyin ve zayıf şifrelemeleri devre dışı bırakın."
                    ),
                    "cvss_score": (
                        7.5
                        if severity == "high"
                        else 5.0 if severity == "medium" else 0.0
                    ),
                }

        except ssl.SSLError as e:
            return {
                "type": "ssl",
                "severity": "high",
                "title": (
                    "SSL Certificate Error"
                    if self.language == "en"
                    else "SSL Sertifika Hatası"
                ),
                "description": str(e),
                "url": self.target_url,
                "evidence": f"SSL Error: {e}",
                "remediation": (
                    "Fix SSL certificate configuration on the server."
                    if self.language == "en"
                    else "Sunucuda SSL sertifika yapılandırmasını düzeltin."
                ),
                "cvss_score": 7.5,
            }
        except Exception as e:
            logger.debug(f"SSL check failed for {self.target_url}: {e}")
            return None

    async def _analyze_headers(self) -> List[Dict]:
        """Analyze HTTP security headers."""
        findings = []
        headers: Dict[str, str] = {}

        try:
            async with httpx.AsyncClient(
                verify=True, timeout=httpx.Timeout(20.0), follow_redirects=True
            ) as client:
                response = await client.get(
                    self.target_url, headers=get_realistic_headers()
                )
                headers = dict(response.headers)
        except Exception as e:
            logger.warning(
                f"Failed to fetch headers for {self.target_url}: {type(e).__name__}: {e}"
            )
            return findings

        # Security header checks
        checks = [
            {
                "header": "strict-transport-security",
                "name": "HSTS",
                "severity": "medium",
                "title_en": "Missing HSTS Header",
                "title_tr": "HSTS Başlığı Eksik",
                "desc_en": "HTTP Strict Transport Security header is missing.",
                "desc_tr": "HTTP Strict Transport Security başlığı eksik.",
                "remediation_en": "Add 'Strict-Transport-Security: max-age=31536000; includeSubDomains' header.",
                "remediation_tr": "'Strict-Transport-Security: max-age=31536000; includeSubDomains' başlığını ekleyin.",
                "cvss": 5.0,
            },
            {
                "header": "x-frame-options",
                "name": "Clickjacking Protection",
                "severity": "medium",
                "title_en": "Missing X-Frame-Options Header",
                "title_tr": "X-Frame-Options Başlığı Eksik",
                "desc_en": "X-Frame-Options header is missing, making the site vulnerable to clickjacking.",
                "desc_tr": "X-Frame-Options başlığı eksik, site tıklama hırsızlığına açık.",
                "remediation_en": "Add 'X-Frame-Options: DENY' or 'SAMEORIGIN' header.",
                "remediation_tr": "'X-Frame-Options: DENY' veya 'SAMEORIGIN' başlığını ekleyin.",
                "cvss": 4.3,
            },
            {
                "header": "x-content-type-options",
                "name": "MIME Sniffing Protection",
                "severity": "low",
                "title_en": "Missing X-Content-Type-Options Header",
                "title_tr": "X-Content-Type-Options Başlığı Eksik",
                "desc_en": "X-Content-Type-Options header is missing.",
                "desc_tr": "X-Content-Type-Options başlığı eksik.",
                "remediation_en": "Add 'X-Content-Type-Options: nosniff' header.",
                "remediation_tr": "'X-Content-Type-Options: nosniff' başlığını ekleyin.",
                "cvss": 3.0,
            },
            {
                "header": "content-security-policy",
                "name": "CSP",
                "severity": "medium",
                "title_en": "Missing Content-Security-Policy Header",
                "title_tr": "Content-Security-Policy Başlığı Eksik",
                "desc_en": "Content-Security-Policy header is missing.",
                "desc_tr": "Content-Security-Policy başlığı eksik.",
                "remediation_en": "Implement a Content-Security-Policy header.",
                "remediation_tr": "Content-Security-Policy başlığı uygulayın.",
                "cvss": 5.0,
            },
            {
                "header": "x-xss-protection",
                "name": "XSS Protection",
                "severity": "low",
                "title_en": "Missing X-XSS-Protection Header",
                "title_tr": "X-XSS-Protection Başlığı Eksik",
                "desc_en": "X-XSS-Protection header is missing.",
                "desc_tr": "X-XSS-Protection başlığı eksik.",
                "remediation_en": "Add 'X-XSS-Protection: 1; mode=block' header.",
                "remediation_tr": "'X-XSS-Protection: 1; mode=block' başlığını ekleyin.",
                "cvss": 3.0,
            },
            {
                "header": "referrer-policy",
                "name": "Referrer Policy",
                "severity": "low",
                "title_en": "Missing Referrer-Policy Header",
                "title_tr": "Referrer-Policy Başlığı Eksik",
                "desc_en": "Referrer-Policy header is missing.",
                "desc_tr": "Referrer-Policy başlığı eksik.",
                "remediation_en": "Add 'Referrer-Policy: strict-origin-when-cross-origin' header.",
                "remediation_tr": "'Referrer-Policy: strict-origin-when-cross-origin' başlığını ekleyin.",
                "cvss": 2.0,
            },
            {
                "header": "permissions-policy",
                "name": "Permissions Policy",
                "severity": "low",
                "title_en": "Missing Permissions-Policy Header",
                "title_tr": "Permissions-Policy Başlığı Eksik",
                "desc_en": "Permissions-Policy header is missing.",
                "desc_tr": "Permissions-Policy başlığı eksik.",
                "remediation_en": "Add a Permissions-Policy header to restrict feature access.",
                "remediation_tr": "Özellik erişimini kısıtlamak için Permissions-Policy başlığı ekleyin.",
                "cvss": 2.0,
            },
        ]

        for check in checks:
            header_key = check["header"]
            if header_key not in headers and header_key not in {
                k.lower() for k in headers
            }:
                findings.append(
                    {
                        "type": "headers",
                        "severity": check["severity"],
                        "title": (
                            check["title_tr"]
                            if self.language == "tr"
                            else check["title_en"]
                        ),
                        "description": (
                            check["desc_tr"]
                            if self.language == "tr"
                            else check["desc_en"]
                        ),
                        "url": self.target_url,
                        "evidence": f"Missing header: {check['header']}",
                        "remediation": (
                            check["remediation_tr"]
                            if self.language == "tr"
                            else check["remediation_en"]
                        ),
                        "cvss_score": check["cvss"],
                    }
                )

        # Check for server information disclosure
        server_header = headers.get("server", "")
        if server_header and not any(
            generic in server_header.lower()
            for generic in ["cloudflare", "nginx", "apache"]
        ):
            findings.append(
                {
                    "type": "info_disclosure",
                    "severity": "low",
                    "title": (
                        "Server Information Disclosure"
                        if self.language == "en"
                        else "Sunucu Bilgisi Sızıntısı"
                    ),
                    "description": (
                        f"Server header reveals: {server_header}"
                        if self.language == "en"
                        else f"Sunucu başlığı bilgi veriyor: {server_header}"
                    ),
                    "url": self.target_url,
                    "evidence": f"Server: {server_header}",
                    "remediation": (
                        "Remove or obfuscate the Server header."
                        if self.language == "en"
                        else "Sunucu başlığını kaldırın veya gizleyin."
                    ),
                    "cvss_score": 1.0,
                }
            )

        # Check for X-Powered-By disclosure
        xpb = headers.get("x-powered-by", "")
        if xpb:
            findings.append(
                {
                    "type": "info_disclosure",
                    "severity": "low",
                    "title": (
                        "Technology Disclosure"
                        if self.language == "en"
                        else "Teknoloji Bilgisi Sızıntısı"
                    ),
                    "description": (
                        f"X-Powered-By header reveals: {xpb}"
                        if self.language == "en"
                        else f"X-Powered-By başlığı bilgi veriyor: {xpb}"
                    ),
                    "url": self.target_url,
                    "evidence": f"X-Powered-By: {xpb}",
                    "remediation": (
                        "Remove the X-Powered-By header."
                        if self.language == "en"
                        else "X-Powered-By başlığını kaldırın."
                    ),
                    "cvss_score": 1.0,
                }
            )

        return findings

    async def _analyze_cookies(self) -> List[Dict]:
        """Analyze cookies for security issues."""
        findings: List[Dict] = []
        response = None
        cookies: List[Any] = []

        try:
            async with httpx.AsyncClient(
                verify=True, timeout=httpx.Timeout(20.0), follow_redirects=True
            ) as client:
                response = await client.get(
                    self.target_url, headers=get_realistic_headers()
                )
        except Exception as e:
            logger.debug(f"Cookie analysis failed: {e}")
            return findings

        # Use .items() to get (name, value) string tuples from httpx cookie jar
        for cookie_name, _ in response.cookies.items():
            cookie_attrs = {}

            # httpx may not expose all cookie attributes, check from headers
            for header_val in response.headers.get_list("set-cookie"):
                if cookie_name in header_val:
                    cookie_attrs["secure"] = "Secure" in header_val
                    cookie_attrs["httponly"] = "HttpOnly" in header_val
                    cookie_attrs["samesite"] = re.search(
                        r"SameSite=(\w+)", header_val, re.IGNORECASE
                    )
                    cookie_attrs["domain"] = re.search(
                        r"Domain=([^;]+)", header_val, re.IGNORECASE
                    )

            if not cookie_attrs.get("secure"):
                findings.append(
                    {
                        "type": "cookies",
                        "severity": "medium",
                        "title": (
                            f"Cookie '{cookie_name}' Missing Secure Flag"
                            if self.language == "en"
                            else f"'{cookie_name}' Çerezi Güvenli Bayrağı Eksik"
                        ),
                        "description": (
                            f"Cookie '{cookie_name}' does not have the Secure flag set."
                            if self.language == "en"
                            else f"'{cookie_name}' çerezi Güvenli (Secure) bayrağına sahip değil."
                        ),
                        "url": self.target_url,
                        "evidence": f"Cookie: {cookie_name} (no Secure flag)",
                        "remediation": (
                            "Add the 'Secure' flag to the cookie."
                            if self.language == "en"
                            else "Çereze 'Secure' bayrağını ekleyin."
                        ),
                        "cvss_score": 4.0,
                    }
                )

            if not cookie_attrs.get("httponly"):
                findings.append(
                    {
                        "type": "cookies",
                        "severity": "medium",
                        "title": (
                            f"Cookie '{cookie_name}' Missing HttpOnly Flag"
                            if self.language == "en"
                            else f"'{cookie_name}' Çerezi HttpOnly Bayrağı Eksik"
                        ),
                        "description": (
                            f"Cookie '{cookie_name}' does not have the HttpOnly flag set, "
                            "making it accessible to JavaScript."
                            if self.language == "en"
                            else f"'{cookie_name}' çerezi HttpOnly bayrağına sahip değil, "
                            "JavaScript tarafından erişilebilir."
                        ),
                        "url": self.target_url,
                        "evidence": f"Cookie: {cookie_name} (no HttpOnly flag)",
                        "remediation": (
                            "Add the 'HttpOnly' flag to the cookie."
                            if self.language == "en"
                            else "Çereze 'HttpOnly' bayrağını ekleyin."
                        ),
                        "cvss_score": 4.0,
                    }
                )

        return findings

    async def _check_info_disclosure(self) -> Optional[List[Dict]]:
        """Check for information disclosure through common sensitive paths."""
        sensitive_paths = [
            "/.env",
            "/.git/config",
            "/.git/HEAD",
            "/admin",
            "/backup",
            "/config",
            "/debug",
            "/robots.txt",
            "/sitemap.xml",
            "/wp-admin",
            "/phpinfo.php",
            "/.htaccess",
            "/server-status",
            "/info.php",
            "/test.php",
        ]

        findings = []

        async with StealthSession(self.target_url) as session:
            for path in sensitive_paths:
                try:
                    test_url = f"{self.base_url}{path}"
                    response = await session.get(test_url)

                    if response.status_code == 200 and len(response.text) > 0:
                        body_lower = response.text.lower()
                        is_sensitive = False

                        # Check if response contains sensitive data
                        sensitive_patterns = [
                            "DB_",
                            "PASSWORD",
                            "SECRET",
                            "API_KEY",
                            "wp_",
                            "<?php",
                            "refs/heads",
                        ]

                        for pattern in sensitive_patterns:
                            if pattern.lower() in body_lower:
                                is_sensitive = True
                                break

                        if is_sensitive or path in [
                            "/.env",
                            "/.git/config",
                            "/.git/HEAD",
                            "/phpinfo.php",
                            "/info.php",
                        ]:
                            findings.append(
                                {
                                    "type": "info_disclosure",
                                    "severity": "high",
                                    "title": (
                                        f"Sensitive Path Exposed: {path}"
                                        if self.language == "en"
                                        else f"Hassas Yol Açıkta: {path}"
                                    ),
                                    "description": (
                                        f"The path '{path}' is publicly accessible and "
                                        "may expose sensitive information."
                                        if self.language == "en"
                                        else f"'{path}' yolu herkese açık ve hassas bilgiler sızdırabilir."
                                    ),
                                    "url": test_url,
                                    "evidence": f"HTTP {response.status_code} - Path: {path}",
                                    "remediation": (
                                        f"Restrict access to '{path}' or remove the file."
                                        if self.language == "en"
                                        else f"'{path}' yoluna erişimi kısıtlayın veya dosyayı kaldırın."
                                    ),
                                    "cvss_score": 7.5,
                                }
                            )

                except Exception as e:
                    logger.debug(f"Info disclosure check failed for {path}: {e}")
                    continue

        return findings if findings else None
