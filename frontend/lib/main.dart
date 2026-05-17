import 'dart:async';
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'core/api_client.dart';
import 'core/backend_manager.dart';
import 'core/constants.dart';
import 'screens/scan_screen.dart';
import 'screens/results_screen.dart';
import 'screens/history_screen.dart';
import 'screens/main_dashboard.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  unawaited(BackendManager().startBackend());

  final prefs = await SharedPreferences.getInstance();
  final savedLang = prefs.getString('language') ?? 'en';

  runApp(
    ChangeNotifierProvider(
      create: (_) => AppState(initialLanguage: savedLang),
      child: const WebScanProApp(),
    ),
  );
}

class AppState extends ChangeNotifier {
  AppState({String initialLanguage = 'en'}) : _locale = Locale(initialLanguage);

  final ApiClient apiClient = ApiClient();
  Locale _locale = const Locale('en');
  bool _isDarkMode = true;

  Locale get locale => _locale;
  bool get isDarkMode => _isDarkMode;

  String get languageCode => _locale.languageCode;

  void setLanguage(String languageCode) {
    _locale = Locale(languageCode);
    notifyListeners();
  }

  void toggleDarkMode() {
    _isDarkMode = !_isDarkMode;
    notifyListeners();
  }
}

class WebScanProApp extends StatefulWidget {
  const WebScanProApp({super.key});

  @override
  State<WebScanProApp> createState() => _WebScanProAppState();
}

class _WebScanProAppState extends State<WebScanProApp> {
  @override
  void dispose() {
    BackendManager().stopBackend();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, _) {
        return MaterialApp(
          title: 'WebScan Pro',
          debugShowCheckedModeBanner: false,
          locale: appState.locale,
          supportedLocales: const [
            Locale('en'),
            Locale('tr'),
          ],
          localizationsDelegates: const [
            GlobalMaterialLocalizations.delegate,
            GlobalWidgetsLocalizations.delegate,
            GlobalCupertinoLocalizations.delegate,
          ],
          localeResolutionCallback: (locale, supportedLocales) {
            for (final supported in supportedLocales) {
              if (supported.languageCode == locale?.languageCode) {
                return supported;
              }
            }
            return const Locale('en');
          },
          theme: ThemeData(
            brightness: Brightness.light,
            primaryColor: const Color(0xFF1a1a2e),
            scaffoldBackgroundColor: Colors.white,
            appBarTheme: const AppBarTheme(
              backgroundColor: Color(0xFF1a1a2e),
              foregroundColor: Colors.white,
              elevation: 0,
            ),
            cardTheme: CardThemeData(
              color: Colors.white,
              elevation: 2,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            colorScheme: ColorScheme.fromSeed(
              seedColor: const Color(0xFF1a1a2e),
              brightness: Brightness.light,
            ),
          ),
          darkTheme: ThemeData(
            brightness: Brightness.dark,
            scaffoldBackgroundColor: Colors.black,
            primaryColor: const Color(AppConstants.accentBlue),
            appBarTheme: const AppBarTheme(
              backgroundColor: Colors.black,
              foregroundColor: Color(AppConstants.textPrimary),
              elevation: 0,
              centerTitle: true,
              titleTextStyle: TextStyle(
                color: Color(AppConstants.textPrimary),
                fontSize: 20,
                fontWeight: FontWeight.bold,
              ),
              iconTheme: IconThemeData(
                color: Color(AppConstants.textSecondary),
              ),
            ),
            cardTheme: CardThemeData(
              color: Color(0xFF1a1a2e),
              elevation: 12,
              shadowColor: Colors.black,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
                side: BorderSide(
                  color: Color(0xFF2A2A2A),
                  width: 1.5,
                ),
              ),
            ),
            colorScheme: ColorScheme.fromSeed(
              seedColor: const Color(AppConstants.accentBlue),
              brightness: Brightness.dark,
              surface: Color(0xFF1a1a2e),
            ),
            dividerColor: const Color(AppConstants.dividerColor),
            textTheme: const TextTheme(
              bodyLarge: TextStyle(color: Color(AppConstants.textPrimary)),
              bodyMedium: TextStyle(color: Color(AppConstants.textPrimary)),
              bodySmall: TextStyle(color: Color(AppConstants.textSecondary)),
              titleLarge: TextStyle(color: Color(AppConstants.textPrimary)),
              titleMedium: TextStyle(color: Color(AppConstants.textPrimary)),
              titleSmall: TextStyle(color: Color(AppConstants.textPrimary)),
              headlineLarge: TextStyle(color: Color(AppConstants.textPrimary)),
              headlineMedium: TextStyle(color: Color(AppConstants.textPrimary)),
              headlineSmall: TextStyle(color: Color(AppConstants.textPrimary)),
            ),
            inputDecorationTheme: const InputDecorationTheme(
              filled: true,
              fillColor: Color(0xFF1a1a2e),
              hintStyle: TextStyle(color: Color(AppConstants.textDisabled)),
              labelStyle: TextStyle(color: Color(AppConstants.textSecondary)),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.all(Radius.circular(12)),
                borderSide: BorderSide(
                    color: Color(AppConstants.borderSubtle), width: 1),
              ),
              enabledBorder: OutlineInputBorder(
                borderRadius: BorderRadius.all(Radius.circular(12)),
                borderSide: BorderSide(
                    color: Color(AppConstants.borderSubtle), width: 1),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.all(Radius.circular(12)),
                borderSide:
                    BorderSide(color: Color(AppConstants.accentBlue), width: 2),
              ),
            ),
          ),
          themeMode: appState.isDarkMode ? ThemeMode.dark : ThemeMode.light,
          home: const MainDashboard(),
          routes: {
            '/scan': (context) => const ScanScreen(),
            '/results': (context) => const ResultsScreen(),
            '/history': (context) => const HistoryScreen(),
          },
        );
      },
    );
  }
}
