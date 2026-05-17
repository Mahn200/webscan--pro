import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:path/path.dart' as p;

class BackendManager {
  static final BackendManager _instance = BackendManager._internal();
  factory BackendManager() => _instance;
  BackendManager._internal();

  Process? _backendProcess;

  Future<void> startBackend() async {
    try {
      if (!Platform.isWindows) return;

      final String currentPath = File(Platform.resolvedExecutable).parent.path;

      final String backendExePath = p.join(currentPath, 'WebScanBackend.exe');

      if (File(backendExePath).existsSync()) {
        debugPrint('WebScanBackend.exe found. Starting background process...');
        _backendProcess = await Process.start(
          backendExePath,
          [],
          workingDirectory:
              currentPath, // <-- THIS IS THE CRITICAL MANDATORY FIX
          mode: ProcessStartMode
              .detached, // Ensure it runs silently in the background
        );
        debugPrint(
            'Backend successfully started with PID: ${_backendProcess?.pid}');
      } else {
        debugPrint('WebScanBackend.exe not found. Running in dev mode.');
      }
    } catch (e) {
      debugPrint('Error starting backend: $e');
    }
  }

  void stopBackend() {
    if (_backendProcess != null) {
      debugPrint('Terminating backend process...');
      _backendProcess?.kill();
      _backendProcess = null;
    }
  }
}
