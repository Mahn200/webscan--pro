import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../main.dart';

class LanguageSelector extends StatelessWidget {
  const LanguageSelector({super.key});

  @override
  Widget build(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, _) {
        final currentLang = appState.languageCode;
        return PopupMenuButton<String>(
          tooltip: 'Language',
          icon: const Icon(
            Icons.language,
            size: 16,
            color: Color(0xFF8B949E),
          ),
          onSelected: (lang) async {
            final prefs = await SharedPreferences.getInstance();
            await prefs.setString('language', lang);

            appState.setLanguage(lang);
          },
          itemBuilder: (_) => [
            PopupMenuItem(
              value: 'en',
              child: Row(
                children: [
                  Icon(
                    Icons.check,
                    size: 16,
                    color: currentLang == 'en'
                        ? const Color(0xFF3B82F6)
                        : Colors.transparent,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'English',
                    style: TextStyle(
                      fontSize: 13,
                      color: Theme.of(context).colorScheme.onSurface,
                    ),
                  ),
                ],
              ),
            ),
            PopupMenuItem(
              value: 'tr',
              child: Row(
                children: [
                  Icon(
                    Icons.check,
                    size: 16,
                    color: currentLang == 'tr'
                        ? const Color(0xFF3B82F6)
                        : Colors.transparent,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    'Türkçe',
                    style: TextStyle(
                      fontSize: 13,
                      color: Theme.of(context).colorScheme.onSurface,
                    ),
                  ),
                ],
              ),
            ),
          ],
        );
      },
    );
  }
}
