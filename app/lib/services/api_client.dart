import 'dart:convert';
import 'dart:io' show Platform;

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;

import '../models/question.dart';

/// Kiwimath backend API client.
///
/// Base URL resolution:
/// - Web debug: http://localhost:8000
/// - Android emulator: http://10.0.2.2:8000  (Android maps host's localhost to this)
/// - iOS simulator / real device: override via --dart-define=KIWIMATH_API=http://<your-mac-ip>:8000
class ApiClient {
  static String get baseUrl {
    const override = String.fromEnvironment('KIWIMATH_API', defaultValue: '');
    if (override.isNotEmpty) return override;

    if (kIsWeb) return 'http://localhost:8000';
    if (Platform.isAndroid) return 'http://10.0.2.2:8000';
    return 'http://localhost:8000';
  }

  Future<Map<String, dynamic>> health() async {
    final uri = Uri.parse('$baseUrl/health');
    final res = await http.get(uri).timeout(const Duration(seconds: 5));
    if (res.statusCode != 200) {
      throw ApiException('health check failed: ${res.statusCode} ${res.body}');
    }
    return jsonDecode(res.body) as Map<String, dynamic>;
  }

  /// Fetch a random parent question for the given locale.
  Future<KiwiQuestion> nextQuestion({
    String locale = 'global',
    String? topic,
    int? seed,
  }) async {
    final params = <String, String>{'locale': locale};
    if (topic != null) params['topic'] = topic;
    if (seed != null) params['seed'] = seed.toString();
    final uri = Uri.parse('$baseUrl/questions/next').replace(queryParameters: params);

    final res = await http.get(uri).timeout(const Duration(seconds: 10));
    if (res.statusCode != 200) {
      throw ApiException('GET /questions/next failed: ${res.statusCode} ${res.body}');
    }
    return KiwiQuestion.fromJson(jsonDecode(res.body) as Map<String, dynamic>);
  }

  /// Fetch a specific question by ID, optionally passing inherited params for step-downs.
  Future<KiwiQuestion> questionById(
    String id, {
    String locale = 'global',
    Map<String, dynamic>? inheritedParams,
    int? seed,
  }) async {
    final params = <String, String>{'locale': locale};
    if (inheritedParams != null && inheritedParams.isNotEmpty) {
      params['inherit'] = inheritedParams.entries
          .map((e) => '${e.key}=${e.value}')
          .join(',');
    }
    if (seed != null) params['seed'] = seed.toString();
    final uri = Uri.parse('$baseUrl/questions/$id').replace(queryParameters: params);

    final res = await http.get(uri).timeout(const Duration(seconds: 10));
    if (res.statusCode != 200) {
      throw ApiException('GET /questions/$id failed: ${res.statusCode} ${res.body}');
    }
    return KiwiQuestion.fromJson(jsonDecode(res.body) as Map<String, dynamic>);
  }
}

class ApiException implements Exception {
  final String message;
  ApiException(this.message);
  @override
  String toString() => 'ApiException: $message';
}
