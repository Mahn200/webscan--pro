import 'package:flutter/material.dart';
import '../core/constants.dart';

class AppTheme {
  AppTheme._();

  static ThemeData get light => ThemeData(
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
      );

  static ThemeData get dark => ThemeData(
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
            borderSide:
                BorderSide(color: Color(AppConstants.borderSubtle), width: 1),
          ),
          enabledBorder: OutlineInputBorder(
            borderRadius: BorderRadius.all(Radius.circular(12)),
            borderSide:
                BorderSide(color: Color(AppConstants.borderSubtle), width: 1),
          ),
          focusedBorder: OutlineInputBorder(
            borderRadius: BorderRadius.all(Radius.circular(12)),
            borderSide:
                BorderSide(color: Color(AppConstants.accentBlue), width: 2),
          ),
        ),
      );
}
