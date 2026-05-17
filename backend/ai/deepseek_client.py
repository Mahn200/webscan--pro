"""
DeepSeek AI integration for vulnerability analysis.
Uses AsyncOpenAI client with DeepSeek base URL.
"""

import json
import logging
from typing import Dict, List, Optional

from openai import AsyncOpenAI

from config import settings

logger = logging.getLogger("webscanpro.deepseek")

# Language-specific system prompts
SYSTEM_PROMPTS = {
    "en": (
        "You are a senior cybersecurity analyst AI. Analyze the following vulnerability "
        "scan results and provide a professional security assessment. "
        "Respond ONLY with a valid JSON object (no markdown, no code blocks). "
        "The JSON must have this exact structure:\n"
        "{\n"
        '  "security_score": float (0-100),\n'
        '  "risk_level": "critical" | "high" | "medium" | "low" | "info",\n'
        '  "summary": "string - 2-3 sentence executive summary in English",\n'
        '  "vulnerabilities": [\n'
        "    {\n"
        '      "type": "string",\n'
        '      "severity": "critical" | "high" | "medium" | "low",\n'
        '      "title": "string in English",\n'
        '      "recommendation": "string - specific fix guidance",\n'
        '      "priority": 1-5 (1=most critical)\n'
        "    }\n"
        "  ],\n"
        '  "top_remediation_steps": ["string array - top 3-5 actions"]\n'
        "}"
    ),
    "tr": (
        "Sen kıdemli bir siber güvenlik analisti Yapay Zekasın. Aşağıdaki tarama "
        "sonuçlarını analiz ederek profesyonel bir güvenlik değerlendirmesi yap. "
        "SADECE geçerli bir JSON objesi ile yanıt ver (işaretleme veya kod bloğu yok). "
        "JSON tam olarak şu yapıda olmalı:\n"
        "{\n"
        '  "security_score": float (0-100),\n'
        '  "risk_level": "critical" | "high" | "medium" | "low" | "info",\n'
        '  "summary": "string - 2-3 cümlelik yönetici özeti Türkçe",\n'
        '  "vulnerabilities": [\n'
        "    {\n"
        '      "type": "string",\n'
        '      "severity": "critical" | "high" | "medium" | "low",\n'
        '      "title": "string Türkçe",\n'
        '      "recommendation": "string - özel düzeltme talimatı",\n'
        '      "priority": 1-5 (1=en kritik)\n'
        "    }\n"
        "  ],\n"
        '  "top_remediation_steps": ["string dizisi - en önemli 3-5 eylem"]\n'
        "}"
    ),
}


def _calculate_fallback_score(vulnerabilities: List[Dict]) -> float:
    """Calculate a security score based on vulnerability severity as fallback."""
    severity_weights = {
        "critical": 30,
        "high": 15,
        "medium": 5,
        "low": 2,
        "info": 0,
    }

    total_deduction = 0
    for vuln in vulnerabilities:
        severity = vuln.get("severity", "info")
        total_deduction += severity_weights.get(severity, 0)

    score = max(100 - total_deduction, 0)
    return score


def _calculate_risk_level(score: float) -> str:
    """Determine risk level from score."""
    if score <= 20:
        return "critical"
    elif score <= 40:
        return "high"
    elif score <= 60:
        return "medium"
    elif score <= 80:
        return "low"
    else:
        return "info"


class DeepSeekClient:
    """Client for interacting with the DeepSeek API for vulnerability analysis."""

    def __init__(self):
        self.api_key = settings.deepseek_api_key
        self.model = settings.deepseek_model
        self.base_url = settings.deepseek_base_url
        self._client: Optional[AsyncOpenAI] = None

    def reconfigure(self, api_key: Optional[str] = None, model: Optional[str] = None):
        """Update runtime settings and reset the client so the new values take effect."""
        if api_key is not None:
            self.api_key = api_key
        if model is not None:
            self.model = model
        # Force re-creation of the AsyncOpenAI client with the new credentials
        self._client = None

    def _get_client(self) -> AsyncOpenAI:
        """Get or create the AsyncOpenAI client."""
        if self._client is None:
            self._client = AsyncOpenAI(
                api_key=self.api_key,
                base_url=self.base_url,
            )
        return self._client

    async def analyze_vulnerabilities(
        self,
        vulnerabilities: List[Dict],
        target_url: str,
        language: str = "en",
    ) -> Dict:
        """
        Analyze scan results using DeepSeek AI.

        Args:
            vulnerabilities: List of vulnerability dicts from scanners.
            target_url: The scanned target URL.
            language: 'en' for English, 'tr' for Turkish.

        Returns:
            Dict with security_score, risk_level, summary, and recommendations.
        """
        # Check if API key is configured
        if not self.api_key or self.api_key == "your_deepseek_api_key_here":
            logger.warning("DeepSeek API key not configured. Using fallback scoring.")
            return self._fallback_analysis(vulnerabilities, target_url, language)

        # Prepare the scan results for analysis
        vuln_summary = self._prepare_vulnerability_summary(vulnerabilities)

        system_prompt = SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["en"])

        user_prompt = (
            f"Target URL: {target_url}\n"
            f"Total Vulnerabilities Found: {len(vulnerabilities)}\n"
            f"Vulnerability Details:\n{vuln_summary}\n\n"
            "Please analyze these results and provide your assessment in JSON format."
        )

        try:
            client = self._get_client()
            response = await client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=2000,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("Empty response from DeepSeek API")

            # Parse the JSON response
            result = json.loads(content)

            # Validate required fields
            required_fields = ["security_score", "risk_level", "summary"]
            for field in required_fields:
                if field not in result:
                    logger.warning(f"DeepSeek response missing field: {field}")
                    return self._fallback_analysis(
                        vulnerabilities, target_url, language
                    )

            logger.info(
                f"DeepSeek analysis complete. Score: {result.get('security_score')}, "
                f"Risk: {result.get('risk_level')}"
            )
            return result

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse DeepSeek response as JSON: {e}")
            return self._fallback_analysis(vulnerabilities, target_url, language)
        except Exception as e:
            logger.error(f"DeepSeek API error: {e}")
            return self._fallback_analysis(vulnerabilities, target_url, language)

    def _prepare_vulnerability_summary(self, vulnerabilities: List[Dict]) -> str:
        """Format vulnerabilities for the AI prompt."""
        lines = []
        for i, vuln in enumerate(vulnerabilities, 1):
            lines.append(
                f"{i}. Type: {vuln.get('type', 'unknown')} | "
                f"Severity: {vuln.get('severity', 'info')} | "
                f"Title: {vuln.get('title', 'N/A')} | "
                f"Description: {vuln.get('description', 'N/A')[:100]}"
            )
        return "\n".join(lines)

    def _fallback_analysis(
        self,
        vulnerabilities: List[Dict],
        target_url: str,
        language: str = "en",
    ) -> Dict:
        """
        Fallback analysis when DeepSeek API is unavailable.
        Provides a basic scoring based on vulnerability severity.
        """
        logger.info("Using fallback analysis (no AI).")

        score = _calculate_fallback_score(vulnerabilities)
        risk_level = _calculate_risk_level(score)

        severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0, "info": 0}
        vuln_types = {}

        for vuln in vulnerabilities:
            sev = vuln.get("severity", "info")
            severity_counts[sev] = severity_counts.get(sev, 0) + 1

            vtype = vuln.get("type", "unknown")
            vuln_types[vtype] = vuln_types.get(vtype, 0) + 1

        summary_en = (
            f"Scan of {target_url} found {len(vulnerabilities)} vulnerabilities. "
            f"Critical: {severity_counts['critical']}, "
            f"High: {severity_counts['high']}, "
            f"Medium: {severity_counts['medium']}, "
            f"Low: {severity_counts['low']}. "
            f"Security Score: {score:.0f}/100. "
            f"Risk Level: {risk_level.upper()}."
        )

        summary_tr = (
            f"{target_url} taramasında {len(vulnerabilities)} güvenlik açığı bulundu. "
            f"Kritik: {severity_counts['critical']}, "
            f"Yüksek: {severity_counts['high']}, "
            f"Orta: {severity_counts['medium']}, "
            f"Düşük: {severity_counts['low']}. "
            f"Güvenlik Skoru: {score:.0f}/100. "
            f"Risk Seviyesi: {risk_level.upper()}."
        )

        summary = summary_tr if language == "tr" else summary_en

        return {
            "security_score": round(score, 1),
            "risk_level": risk_level,
            "summary": summary,
            "vulnerabilities": [
                {
                    "type": vtype,
                    "severity": "medium",
                    "title": f"{count} {vtype} vulnerabilities found",
                    "recommendation": "Review and fix identified vulnerabilities.",
                    "priority": 3,
                }
                for vtype, count in sorted(
                    vuln_types.items(),
                    key=lambda x: x[1],
                    reverse=True,
                )
            ],
            "top_remediation_steps": [
                "Fix all critical and high severity vulnerabilities immediately.",
                "Implement proper input validation and sanitization.",
                "Configure security headers (HSTS, CSP, X-Frame-Options).",
                "Ensure secure cookie configuration (Secure + HttpOnly flags).",
                "Keep software and dependencies updated.",
            ],
        }


# Singleton instance
deepseek_client = DeepSeekClient()
