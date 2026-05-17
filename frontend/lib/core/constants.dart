class AppConstants {
  AppConstants._();

  static const String appName = 'WebScan Pro';
  static const String appVersion = '2.0.0';
  static const String apiBaseUrl = 'http://127.0.0.1:8000';
  static const Duration scanPollInterval = Duration(seconds: 2);
  static const int maxHistoryItems = 100;

  static const int severityCritical = 0xFFEF4444;
  static const int severityHigh = 0xFFF59E0B;
  static const int severityMedium = 0xFF3B82F6;
  static const int severityLow = 0xFF22C55E;
  static const int severityInfo = 0xFF6B7280;

  static const int riskCritical = 0xFFEF4444;
  static const int riskHigh = 0xFFF59E0B;
  static const int riskMedium = 0xFF3B82F6;
  static const int riskLow = 0xFF22C55E;
  static const int riskInfo = 0xFF6B7280;

  static const int appBg = 0xFF121620;
  static const int cardBg = 0xFF1A2130;
  static const int accentBlue = 0xFF3B82F6;
  static const int accentCyan = 0xFF00D4FF;
  static const int textPrimary = 0xFFF0F6FC;
  static const int textSecondary = 0xFF94A3B8;
  static const int textDisabled = 0xFF4B5563;
  static const int borderSubtle = 0xFF21262D;
  static const int dividerColor = 0xFF21262D;

  static const int primaryDark = 0xFF121620;
  static const int surfaceDark = 0xFF1A2130;
  static const int cardDark = 0xFF1A2130;
  static const int accentGreen = 0xFF22C55E;
  static const int accentOrange = 0xFFF59E0B;
  static const int accentRed = 0xFFEF4444;
  static const int borderColor = 0xFF21262D;
}
