import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/app_strings.dart';
import '../core/constants.dart';
import '../main.dart';

class ScanScreen extends StatefulWidget {
  final bool showAppBar;

  const ScanScreen({super.key, this.showAppBar = true});

  @override
  State<ScanScreen> createState() => _ScanScreenState();
}

class _ScanScreenState extends State<ScanScreen> {
  final _urlController = TextEditingController();
  String _scanType = 'full';
  bool _isScanning = false;
  String? _sessionId;
  Timer? _pollTimer;
  int _elapsedSeconds = 0;

  @override
  void dispose() {
    _urlController.dispose();
    _pollTimer?.cancel();
    super.dispose();
  }

  String _tr(String key) {
    final appState = context.read<AppState>();
    final isEn = appState.languageCode == 'en';

    const strings = {
      'enterUrl': {'en': 'Enter target URL...', 'tr': 'Hedef URL girin...'},
      'startScan': {'en': 'Start Scan', 'tr': 'Taramayı Başlat'},
      'fullScan': {'en': 'Full Scan', 'tr': 'Tam Tarama'},
      'passiveScan': {'en': 'Passive Only', 'tr': 'Sadece Pasif'},
      'activeScan': {'en': 'Active Only', 'tr': 'Sadece Aktif'},
      'scanning': {'en': 'Scanning...', 'tr': 'Taranıyor...'},
      'scanInProgress': {
        'en': 'Scan in progress...',
        'tr': 'Tarama devam ediyor...'
      },
      'passiveCheck': {'en': 'Passive Check', 'tr': 'Pasif Kontrol'},
      'activeCheck': {'en': 'Active Check', 'tr': 'Aktif Kontrol'},
      'aiAnalysis': {'en': 'AI Analysis', 'tr': 'AI Analizi'},
      'viewResults': {'en': 'View Results', 'tr': 'Sonuçları Gör'},
      'errorNoUrl': {
        'en': 'Please enter a valid URL',
        'tr': 'Lütfen geçerli bir URL girin'
      },
      'errorHttp': {
        'en': 'URL must start with http:// or https://',
        'tr': 'URL http:// veya https:// ile başlamalıdır'
      },
      'errorNetwork': {
        'en': 'Network error. Please check your connection.',
        'tr': 'Ağ hatası. Bağlantınızı kontrol edin.'
      },
      'retry': {'en': 'Retry', 'tr': 'Tekrar Dene'},
      'targetUrl': {'en': 'Target URL', 'tr': 'Hedef URL'},
      'scanTimedOut': {
        'en': 'Scan timed out. Please try again.',
        'tr': 'Tarama zaman aşımına uğradı. Lütfen tekrar deneyin.'
      },
      'passiveSubtitle': {
        'en': 'SSL, Headers, Cookies, Info Disclosure',
        'tr': 'SSL, Başlıklar, Çerezler, Bilgi Sızıntısı'
      },
      'activeSubtitle': {
        'en': 'SQL Injection, XSS, Directory Traversal',
        'tr': 'SQL Enjeksiyonu, XSS, Dizin Gezinme'
      },
      'fullSubtitle': {
        'en': 'SQLi, XSS, Headers, SSL, Traversal + AI',
        'tr': 'SQLi, XSS, Başlıklar, SSL, Gezinme + AI'
      },
    };

    return strings[key]?[isEn ? 'en' : 'tr'] ?? key;
  }

  Future<void> _startScan() async {
    final url = _urlController.text.trim();

    if (url.isEmpty) {
      _showError(_tr('errorNoUrl'));
      return;
    }

    if (!url.startsWith('http://') && !url.startsWith('https://')) {
      _showError(_tr('errorHttp'));
      return;
    }

    setState(() => _isScanning = true);

    try {
      final appState = context.read<AppState>();
      final result = await appState.apiClient.startScan(
        targetUrl: url,
        scanType: _scanType,
        language: appState.languageCode,
      );

      setState(() => _sessionId = result['id']);

      _elapsedSeconds = 0;
      _pollTimer = Timer.periodic(AppConstants.scanPollInterval, (_) async {
        _elapsedSeconds += AppConstants.scanPollInterval.inSeconds;
        if (_elapsedSeconds >= 300) {
          _pollTimer?.cancel();
          if (mounted) {
            setState(() {
              _isScanning = false;
            });
            _showError(_tr('scanTimedOut'));
          }
          return;
        }
        try {
          final status = await appState.apiClient.getScanStatus(_sessionId!);
          if (status['status'] == 'completed' || status['status'] == 'failed') {
            _pollTimer?.cancel();
            if (mounted) {
              setState(() => _isScanning = false);
              if (status['status'] == 'completed') {
                _navigateToResults();
              } else {
                _showError(_tr('errorNetwork'));
              }
            }
          }
        } catch (e) {
          _pollTimer?.cancel();
          if (mounted) {
            setState(() => _isScanning = false);
          }
        }
      });
    } catch (e) {
      if (mounted) {
        setState(() => _isScanning = false);
        _showError(_tr('errorNetwork'));
      }
    }
  }

  void _navigateToResults() {
    Navigator.pushNamed(context, '/results', arguments: _sessionId);
  }

  void _showError(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: const Color(AppConstants.accentRed),
        behavior: SnackBarBehavior.floating,
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: widget.showAppBar
          ? AppBar(
              title: Text(AppStrings.get(context, 'start_scan')),
            )
          : null,
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                _tr('targetUrl'),
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                  color: Theme.of(context).textTheme.bodyMedium!.color,
                ),
              ),
              const SizedBox(height: 8),
              TextField(
                controller: _urlController,
                enabled: !_isScanning,
                decoration: InputDecoration(
                  hintText: _tr('enterUrl'),
                  prefixIcon: Icon(Icons.language,
                      color: Theme.of(context).textTheme.bodyMedium!.color),
                ),
                style: TextStyle(
                    color: Theme.of(context).textTheme.bodyLarge!.color),
                keyboardType: TextInputType.url,
                textInputAction: TextInputAction.go,
                onSubmitted: (_) => _startScan(),
              ),
              const SizedBox(height: 24),
              Text(
                _tr('fullScan'),
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                  color: Theme.of(context).textTheme.bodyMedium!.color,
                ),
              ),
              const SizedBox(height: 12),
              _buildScanTypeOption(
                value: 'full',
                icon: Icons.shield,
                title: _tr('fullScan'),
                subtitle: _tr('fullSubtitle'),
              ),
              const SizedBox(height: 8),
              _buildScanTypeOption(
                value: 'passive',
                icon: Icons.remove_red_eye_outlined,
                title: _tr('passiveScan'),
                subtitle: _tr('passiveSubtitle'),
              ),
              const SizedBox(height: 8),
              _buildScanTypeOption(
                value: 'active',
                icon: Icons.flash_on,
                title: _tr('activeScan'),
                subtitle: _tr('activeSubtitle'),
              ),
              const SizedBox(height: 32),
              SizedBox(
                width: double.infinity,
                height: 56,
                child: ElevatedButton.icon(
                  onPressed: _isScanning ? null : _startScan,
                  icon: _isScanning
                      ? const SizedBox(
                          width: 20,
                          height: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Colors.white,
                          ),
                        )
                      : const Icon(Icons.play_arrow_rounded),
                  label: Text(
                    _isScanning ? _tr('scanning') : _tr('startScan'),
                    style: const TextStyle(
                        fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: const Color(AppConstants.accentBlue),
                    foregroundColor: Colors.white,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(12),
                    ),
                    disabledBackgroundColor:
                        const Color(AppConstants.accentBlue).withOpacity(0.5),
                  ),
                ),
              ),
              if (_isScanning) ...[
                const SizedBox(height: 32),
                _buildScanProgress(),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildScanTypeOption({
    required String value,
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
    final selected = _scanType == value;

    return InkWell(
      onTap: _isScanning ? null : () => setState(() => _scanType = value),
      borderRadius: BorderRadius.circular(12),
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: selected
                ? const Color(AppConstants.accentBlue)
                : Theme.of(context).dividerColor,
            width: selected ? 2 : 1,
          ),
          color: selected
              ? (Theme.of(context).brightness == Brightness.dark
                  ? const Color(0xFF1F3A6E)
                  : const Color(0xFFE8F0FE))
              : Theme.of(context).cardColor,
        ),
        child: Row(
          children: [
            Icon(
              icon,
              color: selected
                  ? const Color(AppConstants.accentBlue)
                  : Theme.of(context).textTheme.bodyMedium!.color,
            ),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontWeight:
                          selected ? FontWeight.w600 : FontWeight.normal,
                      color: selected
                          ? Theme.of(context).textTheme.bodyLarge!.color
                          : Theme.of(context).textTheme.bodyLarge!.color,
                    ),
                  ),
                  Text(
                    subtitle,
                    style: TextStyle(
                      fontSize: 12,
                      color: Theme.of(context).textTheme.bodyMedium!.color,
                    ),
                  ),
                ],
              ),
            ),
            if (selected)
              const Icon(
                Icons.check_circle,
                color: Color(AppConstants.accentBlue),
                size: 20,
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildScanProgress() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: Theme.of(context).dividerColor,
          width: 1,
        ),
      ),
      child: Column(
        children: [
          LinearProgressIndicator(
            backgroundColor: const Color(AppConstants.borderSubtle),
            valueColor: const AlwaysStoppedAnimation<Color>(
              Color(AppConstants.accentBlue),
            ),
          ),
          const SizedBox(height: 16),
          Text(
            _tr('scanInProgress'),
            style: TextStyle(
              color: Theme.of(context).textTheme.bodyLarge!.color,
            ),
          ),
          const SizedBox(height: 12),
          _buildProgressStep(Icons.search, _tr('passiveCheck'), true),
          const SizedBox(height: 8),
          _buildProgressStep(
              Icons.flash_on, _tr('activeCheck'), _scanType != 'passive'),
          const SizedBox(height: 8),
          _buildProgressStep(Icons.psychology, _tr('aiAnalysis'), true),
        ],
      ),
    );
  }

  Widget _buildProgressStep(IconData icon, String label, bool isActive) {
    return Row(
      children: [
        Icon(
          icon,
          size: 18,
          color: isActive
              ? const Color(AppConstants.accentBlue)
              : const Color(AppConstants.textDisabled),
        ),
        const SizedBox(width: 8),
        Text(
          label,
          style: TextStyle(
            color: isActive
                ? Theme.of(context).textTheme.bodyLarge!.color
                : const Color(AppConstants.textDisabled),
          ),
        ),
      ],
    );
  }
}
