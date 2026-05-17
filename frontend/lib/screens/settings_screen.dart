import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:provider/provider.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../core/app_strings.dart';
import '../core/settings_sync.dart';
import '../core/constants.dart';
import '../main.dart';
import '../widgets/language_selector.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final _apiKeyController = TextEditingController();
  bool _obscureApiKey = true;
  String _aiModel = 'deepseek-chat';

  double _timeout = 15;
  int _maxRetries = 3;
  bool _wafEvasion = true;
  bool _stealthMode = true;

  bool _backendOnline = false;
  bool _backendChecking = true;

  @override
  void initState() {
    super.initState();
    _loadSettings();
    _checkBackendHealth();
  }

  @override
  void dispose() {
    _apiKeyController.dispose();
    super.dispose();
  }

  Future<void> _loadSettings() async {
    final prefs = await SharedPreferences.getInstance();
    setState(() {
      _apiKeyController.text = prefs.getString('deepseek_api_key') ?? '';
      _aiModel = prefs.getString('deepseek_model') ?? 'deepseek-chat';
      _timeout = prefs.getDouble('scan_timeout') ?? 15;
      _maxRetries = prefs.getInt('max_retries') ?? 3;
      _wafEvasion = prefs.getBool('waf_evasion') ?? true;
      _stealthMode = prefs.getBool('stealth_mode') ?? true;
    });
  }

  Future<void> _checkBackendHealth() async {
    try {
      final response = await http
          .get(Uri.parse('http://127.0.0.1:8000/health'))
          .timeout(const Duration(seconds: 5));
      if (mounted) {
        setState(() {
          _backendOnline = response.statusCode == 200;
          _backendChecking = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _backendOnline = false;
          _backendChecking = false;
        });
      }
    }
  }

  Future<void> _saveApiKey(String value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('deepseek_api_key', value);
    await syncSettingsToBackend();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('API key saved'),
          backgroundColor: const Color(AppConstants.severityLow),
          behavior: SnackBarBehavior.floating,
          duration: const Duration(seconds: 2),
        ),
      );
    }
  }

  Future<void> _saveAiModel(String value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('deepseek_model', value);
    await syncSettingsToBackend();
  }

  Future<void> _saveTimeout(double value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setDouble('scan_timeout', value);
    await syncSettingsToBackend();
  }

  Future<void> _saveMaxRetries(int value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setInt('max_retries', value);
    await syncSettingsToBackend();
  }

  Future<void> _saveWafEvasion(bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('waf_evasion', value);
    await syncSettingsToBackend();
  }

  Future<void> _saveStealthMode(bool value) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool('stealth_mode', value);
    await syncSettingsToBackend();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              AppStrings.get(context, 'settings'),
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.bold,
                color: Theme.of(context).textTheme.bodyLarge!.color,
              ),
            ),
            const SizedBox(height: 24),
            _buildSection(
              context,
              title: AppStrings.get(context, 'aiConfiguration'),
              child: Column(
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: TextField(
                          controller: _apiKeyController,
                          obscureText: _obscureApiKey,
                          decoration: InputDecoration(
                            labelText:
                                AppStrings.get(context, 'deepseekApiKey'),
                            hintText: 'sk-...',
                            suffixIcon: IconButton(
                              icon: Icon(
                                _obscureApiKey
                                    ? Icons.visibility_off
                                    : Icons.visibility,
                                size: 18,
                                color: Theme.of(context)
                                    .textTheme
                                    .bodyMedium!
                                    .color,
                              ),
                              onPressed: () {
                                setState(() {
                                  _obscureApiKey = !_obscureApiKey;
                                });
                              },
                            ),
                          ),
                          style: TextStyle(
                            color: Theme.of(context).textTheme.bodyLarge!.color,
                          ),
                        ),
                      ),
                      const SizedBox(width: 8),
                      ElevatedButton(
                        onPressed: () => _saveApiKey(_apiKeyController.text),
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(AppConstants.accentBlue),
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(8),
                          ),
                        ),
                        child: Text(AppStrings.get(context, 'save')),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  DropdownButtonFormField<String>(
                    value: _aiModel,
                    decoration: InputDecoration(
                      labelText: AppStrings.get(context, 'aiModel'),
                    ),
                    dropdownColor: Theme.of(context).cardColor,
                    style: TextStyle(
                      color: Theme.of(context).textTheme.bodyLarge!.color,
                    ),
                    items: const [
                      DropdownMenuItem(
                        value: 'deepseek-chat',
                        child: Text('deepseek-chat'),
                      ),
                      DropdownMenuItem(
                        value: 'deepseek-reasoner',
                        child: Text('deepseek-reasoner'),
                      ),
                    ],
                    onChanged: (value) {
                      if (value != null) {
                        setState(() => _aiModel = value);
                        _saveAiModel(value);
                      }
                    },
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            _buildSection(
              context,
              title: AppStrings.get(context, 'scanConfiguration'),
              child: Column(
                children: [
                  Row(
                    children: [
                      Text(
                        '${AppStrings.get(context, 'requestTimeout')}: ${_timeout.toInt()}s',
                        style: TextStyle(
                          fontSize: 13,
                          color: Theme.of(context).textTheme.bodyMedium!.color,
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Slider(
                          value: _timeout,
                          min: 5,
                          max: 30,
                          divisions: 25,
                          activeColor: const Color(AppConstants.accentBlue),
                          inactiveColor: Theme.of(context).dividerColor,
                          label: '${_timeout.toInt()}s',
                          onChanged: (value) {
                            setState(() => _timeout = value);
                            _saveTimeout(value);
                          },
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),
                  DropdownButtonFormField<int>(
                    value: _maxRetries,
                    decoration: InputDecoration(
                      labelText: AppStrings.get(context, 'maxRetries'),
                    ),
                    dropdownColor: Theme.of(context).cardColor,
                    style: TextStyle(
                      color: Theme.of(context).textTheme.bodyLarge!.color,
                    ),
                    items: const [
                      DropdownMenuItem(value: 1, child: Text('1')),
                      DropdownMenuItem(value: 2, child: Text('2')),
                      DropdownMenuItem(value: 3, child: Text('3')),
                      DropdownMenuItem(value: 5, child: Text('5')),
                    ],
                    onChanged: (value) {
                      if (value != null) {
                        setState(() => _maxRetries = value);
                        _saveMaxRetries(value);
                      }
                    },
                  ),
                  const SizedBox(height: 16),
                  SwitchListTile(
                    contentPadding: EdgeInsets.zero,
                    title: Text(
                      AppStrings.get(context, 'enableWafEvasion'),
                      style: TextStyle(
                        fontSize: 13,
                        color: Theme.of(context).textTheme.bodyLarge!.color,
                      ),
                    ),
                    value: _wafEvasion,
                    activeColor: const Color(AppConstants.accentBlue),
                    onChanged: (value) {
                      setState(() => _wafEvasion = value);
                      _saveWafEvasion(value);
                    },
                  ),
                  SwitchListTile(
                    contentPadding: EdgeInsets.zero,
                    title: Text(
                      AppStrings.get(context, 'enableStealthMode'),
                      style: TextStyle(
                        fontSize: 13,
                        color: Theme.of(context).textTheme.bodyLarge!.color,
                      ),
                    ),
                    value: _stealthMode,
                    activeColor: const Color(AppConstants.accentBlue),
                    onChanged: (value) {
                      setState(() => _stealthMode = value);
                      _saveStealthMode(value);
                    },
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
            _buildSection(
              context,
              title: AppStrings.get(context, 'appearance'),
              child: Consumer<AppState>(
                builder: (context, appState, _) {
                  return Column(
                    children: [
                      SwitchListTile(
                        contentPadding: EdgeInsets.zero,
                        title: Text(
                          AppStrings.get(context, 'darkMode'),
                          style: TextStyle(
                            fontSize: 13,
                            color: Theme.of(context).textTheme.bodyLarge!.color,
                          ),
                        ),
                        value: appState.isDarkMode,
                        activeColor: const Color(AppConstants.accentBlue),
                        onChanged: (_) {
                          appState.toggleDarkMode();
                        },
                      ),
                      ListTile(
                        contentPadding: EdgeInsets.zero,
                        title: Text(
                          AppStrings.get(context, 'language'),
                          style: TextStyle(
                            fontSize: 13,
                            color: Theme.of(context).textTheme.bodyLarge!.color,
                          ),
                        ),
                        trailing: const LanguageSelector(),
                      ),
                    ],
                  );
                },
              ),
            ),
            const SizedBox(height: 16),
            _buildSection(
              context,
              title: AppStrings.get(context, 'about'),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'WebScan Pro',
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.bold,
                      color: Theme.of(context).textTheme.bodyLarge!.color,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    'v2.0',
                    style: TextStyle(
                      fontSize: 13,
                      color: Theme.of(context).textTheme.bodyMedium!.color,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    AppStrings.get(context, 'appDescription'),
                    style: TextStyle(
                      fontSize: 13,
                      color: Theme.of(context).textTheme.bodyMedium!.color,
                    ),
                  ),
                  const SizedBox(height: 16),
                  Row(
                    children: [
                      Text(
                        '${AppStrings.get(context, 'backendStatus')}: ',
                        style: TextStyle(
                          fontSize: 13,
                          color: Theme.of(context).textTheme.bodyMedium!.color,
                        ),
                      ),
                      if (_backendChecking)
                        const SizedBox(
                          width: 14,
                          height: 14,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            color: Color(0xFF8B949E),
                          ),
                        )
                      else
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: _backendOnline
                                ? const Color(0xFF1A4731)
                                : const Color(0xFF3D1F1F),
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            _backendOnline
                                ? AppStrings.get(context, 'online')
                                : AppStrings.get(context, 'offline'),
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w500,
                              color: _backendOnline
                                  ? const Color(0xFF3FB950)
                                  : const Color(0xFFF85149),
                            ),
                          ),
                        ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSection(BuildContext context,
      {required String title, required Widget child}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: Theme.of(context).dividerColor,
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.bold,
              color: Color(AppConstants.accentCyan),
            ),
          ),
          const SizedBox(height: 16),
          child,
        ],
      ),
    );
  }
}
