import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';

Future<void> syncSettingsToBackend() async {
  final prefs = await SharedPreferences.getInstance();

  final timeoutVal = prefs.get("scan_timeout");
  final retriesVal = prefs.get("max_retries");

  final settingsPayload = {
    "deepseek_api_key": prefs.getString("deepseek_api_key") ?? "",
    "deepseek_model": prefs.getString("deepseek_model") ?? "deepseek-chat",
    "scan_timeout": timeoutVal is num ? timeoutVal.toInt() : 15,
    "max_retries": retriesVal is num ? retriesVal.toInt() : 3,
    "waf_evasion": prefs.getBool("waf_evasion") ?? true,
    "stealth_mode": prefs.getBool("stealth_mode") ?? true,
  };

  try {
    await http.post(
      Uri.parse("http://127.0.0.1:8000/settings/update"),
      headers: {"Content-Type": "application/json"},
      body: jsonEncode(settingsPayload),
    );
    debugPrint("[Settings] Successfully synced to backend.");
  } catch (e) {
    debugPrint("[Settings] Failed to sync to backend: $e");
  }
}
