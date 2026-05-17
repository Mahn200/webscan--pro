import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/constants.dart';
import '../main.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  bool _isConnected = false;
  bool _checking = true;

  @override
  void initState() {
    super.initState();
    _checkConnection();
  }

  Future<void> _checkConnection() async {
    setState(() => _checking = true);
    final appState = context.read<AppState>();
    try {
      final connected = await appState.apiClient.healthCheck();
      setState(() {
        _isConnected = connected;
        _checking = false;
      });
    } catch (e) {
      setState(() {
        _isConnected = false;
        _checking = false;
      });
    }
  }

  String _tr(String key) {
    final appState = context.read<AppState>();
    final isEn = appState.languageCode == 'en';

    const strings = {
      'appTitle': {'en': 'WebScan Pro', 'tr': 'WebScan Pro'},
      'appSubtitle': {
        'en': 'AI-Powered Security Scanner',
        'tr': 'AI Destekli Güvenlik Tarayıcısı'
      },
      'startScan': {'en': 'Start Scan', 'tr': 'Taramayı Başlat'},
      'scanHistory': {'en': 'Scan History', 'tr': 'Tarama Geçmişi'},
      'startScanSubtitle': {
        'en': 'SQLi, XSS, Headers, SSL & more',
        'tr': 'SQLi, XSS, Başlıklar, SSL ve daha fazlası'
      },
      'scanHistorySubtitle': {
        'en': 'View previous scan results',
        'tr': 'Önceki tarama sonuçlarını gör'
      },
      'about': {'en': 'About', 'tr': 'Hakkında'},
      'connected': {'en': 'Backend Connected', 'tr': 'Sunucu Bağlı'},
      'disconnected': {
        'en': 'Backend Disconnected',
        'tr': 'Sunucu Bağlı Değil'
      },
      'checking': {
        'en': 'Checking connection...',
        'tr': 'Bağlantı kontrol ediliyor...'
      },
      'version': {'en': 'Version 2.0', 'tr': 'Sürüm 2.0'},
      'poweredBy': {
        'en': 'Powered by DeepSeek AI',
        'tr': 'DeepSeek AI Destekli'
      },
    };

    return strings[key]?[isEn ? 'en' : 'tr'] ?? key;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(_tr('appTitle')),
        centerTitle: true,
        actions: [
          Consumer<AppState>(
            builder: (context, appState, _) {
              return PopupMenuButton<String>(
                icon: const Icon(Icons.language,
                    color: Color(AppConstants.textSecondary)),
                onSelected: (lang) => appState.setLanguage(lang),
                itemBuilder: (_) => [
                  PopupMenuItem(
                    value: 'en',
                    child: Row(
                      children: [
                        Icon(
                          Icons.check,
                          size: 18,
                          color: appState.languageCode == 'en'
                              ? const Color(AppConstants.accentBlue)
                              : Colors.transparent,
                        ),
                        const SizedBox(width: 8),
                        const Text('English'),
                      ],
                    ),
                  ),
                  PopupMenuItem(
                    value: 'tr',
                    child: Row(
                      children: [
                        Icon(
                          Icons.check,
                          size: 18,
                          color: appState.languageCode == 'tr'
                              ? const Color(AppConstants.accentBlue)
                              : Colors.transparent,
                        ),
                        const SizedBox(width: 8),
                        const Text('Türkçe'),
                      ],
                    ),
                  ),
                ],
              );
            },
          ),
          Consumer<AppState>(
            builder: (context, appState, _) {
              return IconButton(
                icon: Icon(
                  appState.isDarkMode ? Icons.light_mode : Icons.dark_mode,
                  color: const Color(AppConstants.textSecondary),
                ),
                onPressed: appState.toggleDarkMode,
              );
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Container(
                  width: 100,
                  height: 100,
                  decoration: BoxDecoration(
                    color:
                        const Color(AppConstants.accentBlue).withOpacity(0.1),
                    shape: BoxShape.circle,
                    border: Border.all(
                      color:
                          const Color(AppConstants.accentBlue).withOpacity(0.3),
                      width: 2,
                    ),
                  ),
                  child: const Icon(
                    Icons.security,
                    size: 48,
                    color: Color(AppConstants.accentBlue),
                  ),
                ),
                const SizedBox(height: 24),
                Text(
                  _tr('appTitle'),
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 28,
                    color: Color(AppConstants.textPrimary),
                  ),
                ),
                const SizedBox(height: 8),
                Text(
                  _tr('appSubtitle'),
                  style: const TextStyle(
                    fontSize: 14,
                    color: Color(AppConstants.textSecondary),
                  ),
                ),
                const SizedBox(height: 16),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  decoration: BoxDecoration(
                    color: _checking
                        ? const Color(0xFF1a1a2e)
                        : _isConnected
                            ? const Color(0xFF22C55E).withOpacity(0.15)
                            : const Color(0xFFEF4444).withOpacity(0.15),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: _checking
                          ? const Color(AppConstants.borderSubtle)
                          : _isConnected
                              ? const Color(0xFF22C55E).withOpacity(0.5)
                              : const Color(0xFFEF4444).withOpacity(0.5),
                    ),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      Container(
                        width: 8,
                        height: 8,
                        decoration: BoxDecoration(
                          color: _checking
                              ? const Color(AppConstants.textDisabled)
                              : _isConnected
                                  ? const Color(0xFF22C55E)
                                  : const Color(0xFFEF4444),
                          shape: BoxShape.circle,
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        _checking
                            ? _tr('checking')
                            : _isConnected
                                ? _tr('connected')
                                : _tr('disconnected'),
                        style: TextStyle(
                          fontSize: 12,
                          color: _checking
                              ? const Color(AppConstants.textDisabled)
                              : _isConnected
                                  ? const Color(0xFF22C55E)
                                  : const Color(0xFFEF4444),
                        ),
                      ),
                    ],
                  ),
                ),
                const SizedBox(height: 48),
                _buildActionButton(
                  icon: Icons.play_arrow_rounded,
                  label: _tr('startScan'),
                  subtitle: _tr('startScanSubtitle'),
                  color: const Color(AppConstants.accentBlue),
                  onTap: () => Navigator.pushNamed(context, '/scan'),
                ),
                const SizedBox(height: 16),
                _buildActionButton(
                  icon: Icons.history_rounded,
                  label: _tr('scanHistory'),
                  subtitle: _tr('scanHistorySubtitle'),
                  color: const Color(AppConstants.accentCyan),
                  onTap: () => Navigator.pushNamed(context, '/history'),
                ),
                const SizedBox(height: 48),
                Text(
                  _tr('poweredBy'),
                  style: const TextStyle(
                    fontSize: 11,
                    color: Color(AppConstants.textDisabled),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  _tr('version'),
                  style: const TextStyle(
                    fontSize: 11,
                    color: Color(AppConstants.textDisabled),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildActionButton({
    required IconData icon,
    required String label,
    required String subtitle,
    required Color color,
    required VoidCallback onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(16),
      child: Container(
        width: double.infinity,
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: const Color(0xFF1a1a2e),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: const Color(AppConstants.borderSubtle),
            width: 1,
          ),
        ),
        child: Row(
          children: [
            Container(
              width: 56,
              height: 56,
              decoration: BoxDecoration(
                color: color.withOpacity(0.15),
                borderRadius: BorderRadius.circular(14),
              ),
              child: Icon(icon, color: color, size: 28),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      fontSize: 16,
                      color: Color(AppConstants.textPrimary),
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    subtitle,
                    style: const TextStyle(
                      fontSize: 12,
                      color: Color(AppConstants.textSecondary),
                    ),
                  ),
                ],
              ),
            ),
            const Icon(
              Icons.chevron_right,
              color: Color(AppConstants.textSecondary),
            ),
          ],
        ),
      ),
    );
  }
}
