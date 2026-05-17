import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/app_strings.dart';
import '../core/constants.dart';
import '../main.dart';
import '../models/scan_result.dart';

class HistoryScreen extends StatefulWidget {
  final bool showAppBar;

  const HistoryScreen({super.key, this.showAppBar = true});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  List<ScanHistoryItem> _history = [];
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    setState(() => _loading = true);
    try {
      final appState = context.read<AppState>();
      final data = await appState.apiClient.getHistory();
      setState(() {
        _history = data.map((json) => ScanHistoryItem.fromJson(json)).toList();
        _loading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  String _tr(String key) {
    final appState = context.read<AppState>();
    final isEn = appState.languageCode == 'en';

    const strings = {
      'scanHistory': {'en': 'Scan History', 'tr': 'Tarama Geçmişi'},
      'noHistory': {
        'en': 'No scan history yet',
        'tr': 'Henüz tarama geçmişi yok'
      },
      'scanNewTarget': {'en': 'Scan New Target', 'tr': 'Yeni Hedef Tara'},
      'completed': {'en': 'Completed', 'tr': 'Tamamlandı'},
      'running': {'en': 'Running', 'tr': 'Çalışıyor'},
      'pending': {'en': 'Pending', 'tr': 'Bekliyor'},
      'failed': {'en': 'Failed', 'tr': 'Başarısız'},
      'viewResults': {'en': 'Results', 'tr': 'Sonuçlar'},
      'delete': {'en': 'Delete', 'tr': 'Sil'},
      'confirmDelete': {'en': 'Delete this scan?', 'tr': 'Bu taramayı sil?'},
      'cancel': {'en': 'Cancel', 'tr': 'İptal'},
      'deleteScan': {'en': 'Delete', 'tr': 'Sil'},
      'retry': {'en': 'Retry', 'tr': 'Tekrar Dene'},
      'findings': {'en': 'findings', 'tr': 'bulgu'},
    };

    return strings[key]?[isEn ? 'en' : 'tr'] ?? key;
  }

  Future<void> _deleteScan(String sessionId) async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: Theme.of(context).cardColor,
        title: Text(
          _tr('confirmDelete'),
          style: TextStyle(color: Theme.of(context).textTheme.bodyLarge!.color),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: Text(
              _tr('cancel'),
              style: TextStyle(
                  color: Theme.of(context).textTheme.bodyMedium!.color),
            ),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            child: Text(
              _tr('deleteScan'),
              style:
                  const TextStyle(color: Color(AppConstants.severityCritical)),
            ),
          ),
        ],
      ),
    );

    if (confirmed == true) {
      try {
        final appState = context.read<AppState>();
        await appState.apiClient.deleteScan(sessionId);
        _loadHistory();
      } catch (e) {
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text('Failed to delete: $e'),
              backgroundColor: const Color(AppConstants.accentRed),
            ),
          );
        }
      }
    }
  }

  String _statusText(String status) {
    switch (status.toLowerCase()) {
      case 'completed':
        return _tr('completed');
      case 'running':
        return _tr('running');
      case 'pending':
        return _tr('pending');
      case 'failed':
        return _tr('failed');
      default:
        return status;
    }
  }

  Color _statusColor(String status) {
    switch (status.toLowerCase()) {
      case 'completed':
        return const Color(AppConstants.severityLow);
      case 'running':
        return const Color(AppConstants.accentBlue);
      case 'pending':
        return const Color(AppConstants.severityHigh);
      case 'failed':
        return const Color(AppConstants.severityCritical);
      default:
        return const Color(AppConstants.textDisabled);
    }
  }

  Color _getScoreColor(double? score) {
    if (score == null) return const Color(AppConstants.textDisabled);
    if (score >= 80) return const Color(AppConstants.severityLow);
    if (score >= 50) return const Color(AppConstants.severityMedium);
    if (score >= 25) return const Color(AppConstants.severityHigh);
    return const Color(AppConstants.severityCritical);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: widget.showAppBar
          ? AppBar(
              title: Text(AppStrings.get(context, 'history_title')),
              actions: [
                IconButton(
                  icon: const Icon(Icons.refresh,
                      color: Color(AppConstants.textSecondary)),
                  onPressed: _loadHistory,
                ),
              ],
            )
          : null,
      body: _loading
          ? const Center(
              child: CircularProgressIndicator(
                color: Color(AppConstants.accentBlue),
              ),
            )
          : _error != null
              ? Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      const Icon(Icons.error_outline,
                          size: 48,
                          color: Color(AppConstants.severityCritical)),
                      const SizedBox(height: 16),
                      Text(
                        'Error: $_error',
                        style: TextStyle(
                            color:
                                Theme.of(context).textTheme.bodyLarge!.color),
                      ),
                      const SizedBox(height: 16),
                      ElevatedButton(
                        onPressed: _loadHistory,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: const Color(AppConstants.accentBlue),
                          foregroundColor: Colors.white,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        child: Text(_tr('retry')),
                      ),
                    ],
                  ),
                )
              : _history.isEmpty
                  ? Center(
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.center,
                        children: [
                          Icon(Icons.history,
                              size: 64,
                              color: Theme.of(context)
                                  .textTheme
                                  .bodySmall!
                                  .color!
                                  .withOpacity(0.5)),
                          const SizedBox(height: 16),
                          Text(
                            'No scan history yet',
                            style: TextStyle(
                                color: Theme.of(context)
                                    .textTheme
                                    .bodyMedium!
                                    .color),
                          ),
                          const SizedBox(height: 24),
                          ElevatedButton.icon(
                            onPressed: () =>
                                Navigator.pushNamed(context, '/scan'),
                            icon: const Icon(Icons.add),
                            label: Text(_tr('scanNewTarget')),
                            style: ElevatedButton.styleFrom(
                              backgroundColor:
                                  const Color(AppConstants.accentBlue),
                              foregroundColor: Colors.white,
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                            ),
                          ),
                        ],
                      ),
                    )
                  : RefreshIndicator(
                      onRefresh: _loadHistory,
                      color: const Color(AppConstants.accentBlue),
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _history.length,
                        itemBuilder: (context, index) {
                          final item = _history[index];
                          return _buildHistoryCard(item);
                        },
                      ),
                    ),
    );
  }

  Widget _buildHistoryCard(ScanHistoryItem item) {
    final scoreColor = _getScoreColor(item.securityScore);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Theme.of(context).cardColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: Theme.of(context).dividerColor,
          width: 1,
        ),
      ),
      child: InkWell(
        onTap: item.status == 'completed'
            ? () => Navigator.pushNamed(context, '/results', arguments: item.id)
            : null,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    width: 10,
                    height: 10,
                    decoration: BoxDecoration(
                      color: _statusColor(item.status),
                      shape: BoxShape.circle,
                    ),
                  ),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      item.targetUrl,
                      style: TextStyle(
                        fontWeight: FontWeight.w500,
                        fontSize: 14,
                        color: Theme.of(context).textTheme.bodyLarge!.color,
                      ),
                      overflow: TextOverflow.ellipsis,
                    ),
                  ),
                  PopupMenuButton<String>(
                    icon: Icon(
                      Icons.more_vert,
                      color: Theme.of(context).textTheme.bodyMedium!.color,
                      size: 20,
                    ),
                    onSelected: (value) {
                      if (value == 'results' && item.status == 'completed') {
                        Navigator.pushNamed(context, '/results',
                            arguments: item.id);
                      } else if (value == 'delete') {
                        _deleteScan(item.id);
                      }
                    },
                    itemBuilder: (_) => [
                      if (item.status == 'completed')
                        PopupMenuItem(
                          value: 'results',
                          child: Row(
                            children: [
                              Icon(Icons.visibility,
                                  size: 18,
                                  color: Theme.of(context)
                                      .textTheme
                                      .bodyMedium!
                                      .color),
                              const SizedBox(width: 8),
                              Text(
                                _tr('viewResults'),
                                style: TextStyle(
                                    color: Theme.of(context)
                                        .textTheme
                                        .bodyLarge!
                                        .color),
                              ),
                            ],
                          ),
                        ),
                      PopupMenuItem(
                        value: 'delete',
                        child: Row(
                          children: [
                            const Icon(Icons.delete,
                                size: 18,
                                color: Color(AppConstants.severityCritical)),
                            const SizedBox(width: 8),
                            Text(
                              _tr('delete'),
                              style: const TextStyle(
                                  color: Color(AppConstants.severityCritical)),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ],
              ),
              const SizedBox(height: 12),
              Row(
                children: [
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: _statusColor(item.status).withOpacity(0.15),
                      borderRadius: BorderRadius.circular(4),
                    ),
                    child: Text(
                      _statusText(item.status),
                      style: TextStyle(
                        fontSize: 11,
                        color: _statusColor(item.status),
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  if (item.securityScore != null)
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: scoreColor,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        '${item.securityScore!.toStringAsFixed(0)}',
                        style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.bold,
                          color: Colors.white,
                        ),
                      ),
                    ),
                  const Spacer(),
                  if (item.vulnerabilityCount > 0)
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: Theme.of(context).dividerColor,
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: Text(
                        '${item.vulnerabilityCount} ${_tr('findings')}',
                        style: TextStyle(
                          fontSize: 11,
                          color: Theme.of(context).textTheme.bodyMedium!.color,
                        ),
                      ),
                    ),
                  const SizedBox(width: 8),
                  Text(
                    _formatDate(item.createdAt),
                    style: TextStyle(
                      fontSize: 11,
                      color: Theme.of(context).textTheme.bodySmall!.color,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final diff = now.difference(date);

    if (diff.inMinutes < 60) {
      return '${diff.inMinutes}m ago';
    } else if (diff.inHours < 24) {
      return '${diff.inHours}h ago';
    } else if (diff.inDays < 7) {
      return '${diff.inDays}d ago';
    } else {
      return '${date.month}/${date.day}/${date.year}';
    }
  }
}
