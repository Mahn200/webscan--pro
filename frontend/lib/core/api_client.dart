import 'dart:convert';
import 'dart:typed_data';
import 'package:http/http.dart' as http;
import 'constants.dart';

class ApiClient {
  final String baseUrl;
  final http.Client _client;

  ApiClient({String? baseUrl})
      : baseUrl = baseUrl ?? AppConstants.apiBaseUrl,
        _client = http.Client();

  Future<bool> healthCheck() async {
    try {
      final response = await _client
          .get(Uri.parse('$baseUrl/health'))
          .timeout(const Duration(seconds: 5));
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  Future<Map<String, dynamic>> startScan({
    required String targetUrl,
    String scanType = 'full',
    String language = 'en',
  }) async {
    try {
      final response = await _client.post(
        Uri.parse('$baseUrl/scan/start'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'target_url': targetUrl,
          'scan_type': scanType,
          'language': language,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw ApiException(
          statusCode: response.statusCode,
          message: jsonDecode(response.body)['detail'] ?? 'Unknown error',
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(statusCode: 0, message: 'Network error: $e');
    }
  }

  Future<Map<String, dynamic>> getScanStatus(String sessionId) async {
    try {
      final response =
          await _client.get(Uri.parse('$baseUrl/scan/status/$sessionId'));

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else if (response.statusCode == 404) {
        throw ApiException(statusCode: 404, message: 'Scan not found');
      } else {
        throw ApiException(
          statusCode: response.statusCode,
          message: 'Failed to get scan status',
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(statusCode: 0, message: 'Network error: $e');
    }
  }

  Future<Map<String, dynamic>> getScanResults(String sessionId) async {
    try {
      final response =
          await _client.get(Uri.parse('$baseUrl/scan/results/$sessionId'));

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        throw ApiException(
          statusCode: response.statusCode,
          message: jsonDecode(response.body)['detail'] ?? 'Unknown error',
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(statusCode: 0, message: 'Network error: $e');
    }
  }

  Future<List<Map<String, dynamic>>> getHistory({
    int limit = 20,
    int offset = 0,
  }) async {
    try {
      final response = await _client.get(
        Uri.parse('$baseUrl/history?limit=$limit&offset=$offset'),
      );

      if (response.statusCode == 200) {
        return List<Map<String, dynamic>>.from(jsonDecode(response.body));
      } else {
        throw ApiException(
          statusCode: response.statusCode,
          message: 'Failed to get scan history',
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(statusCode: 0, message: 'Network error: $e');
    }
  }

  Future<void> deleteScan(String sessionId) async {
    try {
      final response =
          await _client.delete(Uri.parse('$baseUrl/scan/$sessionId'));

      if (response.statusCode != 200) {
        throw ApiException(
          statusCode: response.statusCode,
          message: 'Failed to delete scan',
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(statusCode: 0, message: 'Network error: $e');
    }
  }

  Future<Uint8List> downloadPdfReport(
    String sessionId, {
    String language = 'en',
  }) async {
    try {
      final response = await _client.get(
        Uri.parse('$baseUrl/report/pdf/$sessionId?language=$language'),
      );

      if (response.statusCode == 200) {
        return response.bodyBytes;
      } else {
        throw ApiException(
          statusCode: response.statusCode,
          message: 'Failed to download report',
        );
      }
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException(statusCode: 0, message: 'Network error: $e');
    }
  }

  void dispose() {
    _client.close();
  }
}

class ApiException implements Exception {
  final int statusCode;
  final String message;

  ApiException({required this.statusCode, required this.message});

  @override
  String toString() => 'ApiException($statusCode): $message';
}
