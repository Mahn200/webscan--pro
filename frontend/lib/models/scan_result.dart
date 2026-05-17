library;

class ScanSession {
  final String id;
  final String targetUrl;
  final String status;
  final String scanType;
  final double? securityScore;
  final String? riskLevel;
  final String? aiSummary;
  final List<Vulnerability> vulnerabilities;
  final DateTime createdAt;
  final String language;

  ScanSession({
    required this.id,
    required this.targetUrl,
    required this.status,
    required this.scanType,
    this.securityScore,
    this.riskLevel,
    this.aiSummary,
    this.vulnerabilities = const [],
    required this.createdAt,
    this.language = 'en',
  });

  factory ScanSession.fromJson(Map<String, dynamic> json) {
    return ScanSession(
      id: json['id'] ?? '',
      targetUrl: json['target_url'] ?? '',
      status: json['status'] ?? 'unknown',
      scanType: json['scan_type'] ?? 'full',
      securityScore: (json['security_score'] as num?)?.toDouble(),
      riskLevel: json['risk_level'],
      aiSummary: json['ai_summary'],
      vulnerabilities: (json['vulnerabilities'] as List<dynamic>?)
              ?.map((v) => Vulnerability.fromJson(v))
              .toList() ??
          [],
      createdAt: DateTime.tryParse(json['created_at'] ?? '') ?? DateTime.now(),
      language: json['language'] ?? 'en',
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'target_url': targetUrl,
        'status': status,
        'scan_type': scanType,
        'security_score': securityScore,
        'risk_level': riskLevel,
        'ai_summary': aiSummary,
        'vulnerabilities': vulnerabilities.map((v) => v.toJson()).toList(),
        'created_at': createdAt.toIso8601String(),
        'language': language,
      };
}

class ScanHistoryItem {
  final String id;
  final String targetUrl;
  final String status;
  final double? securityScore;
  final String? riskLevel;
  final int vulnerabilityCount;
  final DateTime createdAt;

  ScanHistoryItem({
    required this.id,
    required this.targetUrl,
    required this.status,
    this.securityScore,
    this.riskLevel,
    this.vulnerabilityCount = 0,
    required this.createdAt,
  });

  factory ScanHistoryItem.fromJson(Map<String, dynamic> json) {
    return ScanHistoryItem(
      id: json['id'] ?? '',
      targetUrl: json['target_url'] ?? '',
      status: json['status'] ?? 'unknown',
      securityScore: (json['security_score'] as num?)?.toDouble(),
      riskLevel: json['risk_level'],
      vulnerabilityCount: json['vulnerability_count'] ?? 0,
      createdAt: DateTime.tryParse(json['created_at'] ?? '') ?? DateTime.now(),
    );
  }
}

class Vulnerability {
  final String id;
  final String type;
  final String severity;
  final String title;
  final String? description;
  final String? url;
  final String? parameter;
  final String? payload;
  final String? evidence;
  final String? remediation;
  final double? cvssScore;

  Vulnerability({
    required this.id,
    required this.type,
    required this.severity,
    required this.title,
    this.description,
    this.url,
    this.parameter,
    this.payload,
    this.evidence,
    this.remediation,
    this.cvssScore,
  });

  factory Vulnerability.fromJson(Map<String, dynamic> json) {
    return Vulnerability(
      id: json['id'] ?? '',
      type: json['type'] ?? 'unknown',
      severity: json['severity'] ?? 'info',
      title: json['title'] ?? '',
      description: json['description'],
      url: json['url'],
      parameter: json['parameter'],
      payload: json['payload'],
      evidence: json['evidence'],
      remediation: json['remediation'],
      cvssScore: (json['cvss_score'] as num?)?.toDouble(),
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'type': type,
        'severity': severity,
        'title': title,
        'description': description,
        'url': url,
        'parameter': parameter,
        'payload': payload,
        'evidence': evidence,
        'remediation': remediation,
        'cvss_score': cvssScore,
      };
}
