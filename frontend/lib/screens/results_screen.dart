import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/app_strings.dart';
import '../core/constants.dart';
import '../main.dart';
import '../models/scan_result.dart';
import '../widgets/score_gauge.dart';
import '../widgets/vulnerability_card.dart';

class ResultsScreen extends StatefulWidget {
  const ResultsScreen({super.key});

  @override
  State<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen> {
  ScanSession? _session;
  bool _loading = true;
  String? _error;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    if (_loading) {
      _loadResults();
    }
  }

  Future<void> _loadResults() async {
    final sessionId = ModalRoute.of(context)?.settings.arguments as String?;
    if (sessionId == null) {
      setState(() {
        _error = 'No session ID provided';
        _loading = false;
      });
      return;
    }

    try {
      final appState = context.read<AppState>();
      final result = await appState.apiClient.getScanResults(sessionId);
      setState(() {
        _session = ScanSession.fromJson(result);
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  String _tr(String key) {
    final appState = context.read<AppState>();
    final isEn = appState.languageCode == 'en';

    const strings = {
      'results': {'en': 'Results', 'tr': 'Sonuçlar'},
      'securityScore': {'en': 'Security Score', 'tr': 'Güvenlik Skoru'},
      'riskLevel': {'en': 'Risk Level', 'tr': 'Risk Seviyesi'},
      'vulnerabilities': {'en': 'Vulnerabilities', 'tr': 'Güvenlik Açıkları'},
      'noVulnerabilities': {
        'en': 'No vulnerabilities found',
        'tr': 'Güvenlik açığı bulunamadı'
      },
      'downloadReport': {'en': 'Download Report', 'tr': 'Raporu İndir'},
      'scanNewTarget': {'en': 'Scan New Target', 'tr': 'Yeni Hedef Tara'},
      'remediation': {'en': 'Remediation', 'tr': 'Düzeltme'},
      'evidence': {'en': 'Evidence', 'tr': 'Kanıt'},
      'payload': {'en': 'Payload', 'tr': 'Payload'},
      'parameter': {'en': 'Parameter', 'tr': 'Parametre'},
      'url': {'en': 'URL', 'tr': 'URL'},
      'targetInfo': {'en': 'Target Information', 'tr': 'Hedef Bilgisi'},
      'totalFindings': {'en': 'Total Findings', 'tr': 'Toplam Bulgu'},
      'aiAnalysisTitle': {'en': 'AI Analysis', 'tr': 'AI Analizi'},
    };

    return strings[key]?[isEn ? 'en' : 'tr'] ?? key;
  }

  Future<void> _downloadPdf() async {
    if (_session == null) return;

    try {
      final appState = context.read<AppState>();
      final pdfBytes = await appState.apiClient.downloadPdfReport(
        _session!.id,
        language: appState.languageCode,
      );

      var downloadsDir = Directory('/storage/emulated/0/Download');
      if (!await downloadsDir.exists()) {
        downloadsDir = Directory.current;
      }
      final file = File(
        '${downloadsDir.path}/webscan_report_${_session!.id.substring(0, 8)}.pdf',
      );
      await file.writeAsBytes(pdfBytes);

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Report saved to ${file.path}'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to download report: $e'),
            backgroundColor: const Color(AppConstants.accentRed),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return Scaffold(
        appBar: AppBar(title: Text(AppStrings.get(context, 'results_title'))),
        body: const Center(
          child: CircularProgressIndicator(
            color: Color(AppConstants.accentBlue),
          ),
        ),
      );
    }

    if (_error != null) {
      return Scaffold(
        appBar: AppBar(title: Text(AppStrings.get(context, 'results_title'))),
        body: Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline,
                  size: 64, color: Color(AppConstants.severityCritical)),
              const SizedBox(height: 16),
              Text(
                '${_tr('results')}: $_error',
                style: const TextStyle(color: Color(AppConstants.textPrimary)),
              ),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => Navigator.pop(context),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(AppConstants.accentBlue),
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                child: Text(_tr('scanNewTarget')),
              ),
            ],
          ),
        ),
      );
    }

    if (_session == null) {
      return Scaffold(
        appBar: AppBar(title: Text(AppStrings.get(context, 'results_title'))),
        body: Center(
          child: Text(
            _tr('noVulnerabilities'),
            style: const TextStyle(color: Color(AppConstants.textSecondary)),
          ),
        ),
      );
    }

    final session = _session!;
    final score = session.securityScore ?? 0;
    final riskLevel = session.riskLevel ?? 'info';
    final vulns = session.vulnerabilities;
    final riskColor = _getSeverityColor(riskLevel);

    return Scaffold(
      appBar: AppBar(
        title: Text(AppStrings.get(context, 'results_title')),
        actions: [
          IconButton(
            icon: const Icon(Icons.picture_as_pdf),
            color: const Color(AppConstants.textSecondary),
            tooltip: _tr('downloadReport'),
            onPressed: _downloadPdf,
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Center(
                child: SizedBox(
                  width: 280,
                  height: 280,
                  child: ScoreGauge(
                    score: score.toInt(),
                    riskLevel: riskLevel,
                    size: 200,
                  ),
                ),
              ),
              const SizedBox(height: 12),
              Center(
                child: Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 6),
                  decoration: BoxDecoration(
                    color: riskColor.withOpacity(0.15),
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: riskColor, width: 1),
                  ),
                  child: Text(
                    '${_tr('riskLevel')}: ${riskLevel.toUpperCase()}',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: riskColor,
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 24),
              if (session.aiSummary != null) ...[
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1a1a2e),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: const Color(AppConstants.borderSubtle),
                      width: 1,
                    ),
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _tr('aiAnalysisTitle'),
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 14,
                          color: Color(AppConstants.accentCyan),
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        session.aiSummary!,
                        style: const TextStyle(
                          color: Color(AppConstants.textSecondary),
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 16),
              ],
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: const Color(0xFF1a1a2e),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: const Color(AppConstants.borderSubtle),
                    width: 1,
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      _tr('targetInfo'),
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 14,
                        color: Color(AppConstants.accentCyan),
                      ),
                    ),
                    const SizedBox(height: 8),
                    _buildInfoRow(_tr('url'), session.targetUrl),
                    _buildInfoRow(_tr('totalFindings'), '${vulns.length}'),
                    _buildInfoRow(_tr('securityScore'),
                        '${score.toStringAsFixed(1)}/100'),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              Text(
                '${_tr('vulnerabilities')} (${vulns.length})',
                style: const TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 16,
                  color: Color(AppConstants.textPrimary),
                ),
              ),
              const SizedBox(height: 12),
              if (vulns.isEmpty)
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(32),
                  decoration: BoxDecoration(
                    color: const Color(0xFF1a1a2e),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: const Color(AppConstants.borderSubtle),
                      width: 1,
                    ),
                  ),
                  child: Column(
                    children: [
                      const Icon(Icons.check_circle_outline,
                          size: 48, color: Color(AppConstants.severityLow)),
                      const SizedBox(height: 12),
                      Text(
                        _tr('noVulnerabilities'),
                        style: const TextStyle(
                          color: Color(AppConstants.textPrimary),
                        ),
                      ),
                    ],
                  ),
                )
              else
                ...vulns.map(
                  (vuln) => Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: VulnerabilityCard(
                      vulnerability: vuln,
                      onTap: () => _showVulnDetails(vuln),
                    ),
                  ),
                ),
              const SizedBox(height: 24),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton.icon(
                  onPressed: () =>
                      Navigator.pushReplacementNamed(context, '/scan'),
                  icon: const Icon(Icons.refresh),
                  label: Text(_tr('scanNewTarget')),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(AppConstants.accentBlue),
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                  ),
                ),
              ),
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: const TextStyle(
                fontWeight: FontWeight.w500,
                fontSize: 12,
                color: Color(AppConstants.textSecondary),
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: const TextStyle(
                fontSize: 12,
                color: Color(AppConstants.textPrimary),
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showVulnDetails(Vulnerability vuln) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF1a1a2e),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.6,
        maxChildSize: 0.9,
        minChildSize: 0.3,
        expand: false,
        builder: (context, scrollController) {
          return SingleChildScrollView(
            controller: scrollController,
            padding: const EdgeInsets.all(24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Center(
                  child: Container(
                    width: 40,
                    height: 4,
                    decoration: BoxDecoration(
                      color: const Color(AppConstants.textDisabled)
                          .withOpacity(0.3),
                      borderRadius: BorderRadius.circular(2),
                    ),
                  ),
                ),
                const SizedBox(height: 20),
                Row(
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color:
                            _getSeverityColor(vuln.severity).withOpacity(0.2),
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(
                          color:
                              _getSeverityColor(vuln.severity).withOpacity(0.5),
                        ),
                      ),
                      child: Text(
                        vuln.severity.toUpperCase(),
                        style: TextStyle(
                          color: _getSeverityColor(vuln.severity),
                          fontWeight: FontWeight.w600,
                          fontSize: 12,
                        ),
                      ),
                    ),
                    const Spacer(),
                    if (vuln.cvssScore != null)
                      Text(
                        'CVSS ${vuln.cvssScore}',
                        style: TextStyle(
                          color: _getSeverityColor(vuln.severity),
                          fontWeight: FontWeight.bold,
                          fontSize: 13,
                        ),
                      ),
                  ],
                ),
                const SizedBox(height: 12),
                Text(
                  vuln.type.toUpperCase(),
                  style: const TextStyle(
                    color: Color(AppConstants.textSecondary),
                    fontSize: 11,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  vuln.title,
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                    color: Color(AppConstants.textPrimary),
                  ),
                ),
                if (vuln.description != null) ...[
                  const SizedBox(height: 12),
                  Text(
                    vuln.description!,
                    style: const TextStyle(
                      color: Color(AppConstants.textSecondary),
                    ),
                  ),
                ],
                const SizedBox(height: 16),
                if (vuln.url != null) _buildDetailRow(_tr('url'), vuln.url!),
                if (vuln.parameter != null)
                  _buildDetailRow(_tr('parameter'), vuln.parameter!),
                if (vuln.payload != null)
                  _buildDetailRow(_tr('payload'), vuln.payload!),
                if (vuln.evidence != null)
                  _buildDetailRow(_tr('evidence'), vuln.evidence!),
                if (vuln.remediation != null) ...[
                  const SizedBox(height: 16),
                  Text(
                    _tr('remediation'),
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                      color: Color(AppConstants.accentCyan),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    vuln.remediation!,
                    style: const TextStyle(
                      color: Color(AppConstants.textSecondary),
                    ),
                  ),
                ],
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 90,
            child: Text(
              label,
              style: const TextStyle(
                fontWeight: FontWeight.w500,
                fontSize: 12,
                color: Color(AppConstants.textSecondary),
              ),
            ),
          ),
          Expanded(
            child: SelectableText(
              value,
              style: const TextStyle(
                fontSize: 12,
                color: Color(AppConstants.textPrimary),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Color _getSeverityColor(String severity) {
    switch (severity.toLowerCase()) {
      case 'critical':
        return const Color(AppConstants.severityCritical);
      case 'high':
        return const Color(AppConstants.severityHigh);
      case 'medium':
        return const Color(AppConstants.severityMedium);
      case 'low':
        return const Color(AppConstants.severityLow);
      default:
        return const Color(AppConstants.severityInfo);
    }
  }
}
