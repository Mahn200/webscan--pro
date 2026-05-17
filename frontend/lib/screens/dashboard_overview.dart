import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:provider/provider.dart';
import '../core/app_strings.dart';
import '../core/constants.dart';
import '../main.dart';
import '../widgets/tilt_card.dart';

class DashboardOverviewWidget extends StatefulWidget {
  final void Function(int index)? onNavigate;

  const DashboardOverviewWidget({super.key, this.onNavigate});

  @override
  State<DashboardOverviewWidget> createState() =>
      _DashboardOverviewWidgetState();
}

class _DashboardOverviewWidgetState extends State<DashboardOverviewWidget> {
  bool _isLoading = true;
  String? _errorMessage;

  int _totalScans = 0;
  int _totalVulnerabilities = 0;
  double _avgSecurityScore = 0;
  int _activeThreats = 0;

  Map<String, int> _severityData = {};

  List<int> _trendsData = [];

  List<Map<String, dynamic>> _recentScans = [];

  @override
  void initState() {
    super.initState();
    _loadDashboardData();
  }

  Future<void> _loadDashboardData() async {
    try {
      final appState = context.read<AppState>();
      final history = await appState.apiClient.getHistory(limit: 100);

      if (!mounted) return;

      setState(() {
        _totalScans = history.length;

        _recentScans = history.take(4).toList();

        final scores = history
            .where((s) => s['security_score'] != null)
            .map((s) => (s['security_score'] as num).toDouble())
            .toList();
        _avgSecurityScore =
            scores.isEmpty ? 0 : scores.reduce((a, b) => a + b) / scores.length;

        _totalVulnerabilities = history
            .map((s) => (s['vulnerability_count'] as num? ?? 0).toInt())
            .fold(0, (a, b) => a + b);

        _activeThreats = history
            .where((s) =>
                s['risk_level'] == 'critical' || s['risk_level'] == 'high')
            .length;

        _severityData = {
          'Critical':
              history.where((s) => s['risk_level'] == 'critical').length,
          'High': history.where((s) => s['risk_level'] == 'high').length,
          'Medium': history.where((s) => s['risk_level'] == 'medium').length,
          'Low': history.where((s) => s['risk_level'] == 'low').length,
        };

        final now = DateTime.now();
        _trendsData = List.generate(30, (dayIndex) {
          final day = now.subtract(Duration(days: 29 - dayIndex));
          return history.where((s) {
            final created = DateTime.parse(s['created_at']);
            return created.year == day.year &&
                created.month == day.month &&
                created.day == day.day;
          }).length;
        });

        _isLoading = false;
      });
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
          _errorMessage =
              'Failed to load dashboard data. Please check your connection.';
        });
      }
    }
  }

  String _capitalizeFirst(String s) =>
      s.isEmpty ? s : s[0].toUpperCase() + s.substring(1);

  Color _severityColor(String severity) {
    switch (severity) {
      case 'Critical':
        return const Color(AppConstants.severityCritical);
      case 'High':
        return const Color(AppConstants.severityHigh);
      case 'Medium':
        return const Color(AppConstants.severityMedium);
      case 'Low':
        return const Color(AppConstants.severityLow);
      default:
        return const Color(AppConstants.severityInfo);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_isLoading) {
      return const Center(
        child: CircularProgressIndicator(color: Color(0xFF1F6FEB)),
      );
    }

    if (_errorMessage != null) {
      return Center(
        child: Text(
          _errorMessage!,
          style: const TextStyle(color: Color(0xFFF85149)),
        ),
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildMetricCards(context),
          const SizedBox(height: 20),
          _buildChartsRow(context),
          const SizedBox(height: 20),
          _buildRecentScans(context),
        ],
      ),
    );
  }

  Widget _buildMetricCards(BuildContext context) {
    return Row(
      children: [
        Expanded(
          child: _buildMetricCard(
            AppStrings.get(context, 'total_scans'),
            _totalScans.toString(),
            Icons.analytics_outlined,
            null,
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: _buildMetricCard(
            AppStrings.get(context, 'vulnerabilities'),
            _totalVulnerabilities.toString(),
            Icons.bug_report_outlined,
            null,
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: _buildScoreMetricCard(
            AppStrings.get(context, 'security_score'),
            _avgSecurityScore.round(),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: _buildMetricCard(
            AppStrings.get(context, 'active_threats'),
            _activeThreats.toString(),
            Icons.warning_amber_rounded,
            const Color(AppConstants.severityCritical),
          ),
        ),
      ],
    );
  }

  Widget _buildMetricCard(
      String title, String value, IconData icon, Color? accentColor) {
    final isActiveThreat = accentColor != null;
    return TiltCard(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Theme.of(context).brightness == Brightness.dark
              ? const Color(0xFF1a1a2e).withOpacity(0.6)
              : Colors.white,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: isActiveThreat
                ? accentColor
                : const Color(AppConstants.borderSubtle),
            width: 1,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 12,
                    color: Theme.of(context).brightness == Brightness.dark
                        ? const Color(AppConstants.textSecondary)
                        : const Color(0xFF656D76),
                  ),
                ),
                Icon(icon,
                    size: 18,
                    color: isActiveThreat
                        ? accentColor
                        : const Color(AppConstants.textSecondary)),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              value,
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: isActiveThreat
                    ? accentColor
                    : Theme.of(context).brightness == Brightness.dark
                        ? const Color(AppConstants.textPrimary)
                        : const Color(0xFF1F2328),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildScoreMetricCard(String title, int score) {
    return TiltCard(
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Theme.of(context).brightness == Brightness.dark
              ? const Color(0xFF1a1a2e).withOpacity(0.6)
              : Colors.white,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: const Color(AppConstants.borderSubtle),
            width: 1,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  title,
                  style: TextStyle(
                    fontSize: 12,
                    color: Theme.of(context).brightness == Brightness.dark
                        ? const Color(AppConstants.textSecondary)
                        : const Color(0xFF656D76),
                  ),
                ),
                const Icon(Icons.security,
                    size: 18, color: Color(AppConstants.textSecondary)),
              ],
            ),
            const SizedBox(height: 12),
            SizedBox(
              height: 60,
              child: Stack(
                alignment: Alignment.center,
                children: [
                  SizedBox(
                    width: 60,
                    height: 60,
                    child: CircularProgressIndicator(
                      value: score / 100,
                      strokeWidth: 4,
                      backgroundColor: const Color(AppConstants.borderSubtle),
                      valueColor: AlwaysStoppedAnimation<Color>(
                        score >= 80
                            ? const Color(AppConstants.severityLow)
                            : score >= 50
                                ? const Color(AppConstants.severityMedium)
                                : score >= 25
                                    ? const Color(AppConstants.severityHigh)
                                    : const Color(
                                        AppConstants.severityCritical),
                      ),
                    ),
                  ),
                  Text(
                    '$score',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: Theme.of(context).brightness == Brightness.dark
                          ? const Color(AppConstants.textPrimary)
                          : const Color(0xFF1F2328),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildChartsRow(BuildContext context) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          flex: 5,
          child: _buildPieChartPanel(context),
        ),
        const SizedBox(width: 16),
        Expanded(
          flex: 7,
          child: _buildLineChartPanel(context),
        ),
      ],
    );
  }

  Widget _buildPanelHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 16),
      child: Text(
        title,
        style: const TextStyle(
          fontSize: 13,
          fontWeight: FontWeight.bold,
          color: Color(AppConstants.textSecondary),
        ),
      ),
    );
  }

  Widget _buildPieChartPanel(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).brightness == Brightness.dark
            ? const Color(0xFF1a1a2e).withOpacity(0.6)
            : Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: const Color(AppConstants.borderSubtle),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildPanelHeader(
            AppStrings.get(context, 'vuln_distribution'),
          ),
          SizedBox(
            height: 200,
            child: Row(
              children: [
                Expanded(
                  child: PieChart(
                    PieChartData(
                      sections: _severityData.entries.map((entry) {
                        return PieChartSectionData(
                          color: _severityColor(entry.key),
                          value:
                              entry.value > 0 ? entry.value.toDouble() : 0.001,
                          title: '',
                          radius: 50,
                        );
                      }).toList(),
                      sectionsSpace: 2,
                      centerSpaceRadius: 32,
                      centerSpaceColor: Colors.transparent,
                    ),
                  ),
                ),
                const SizedBox(width: 16),
                Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: _severityData.entries.map((entry) {
                    return Padding(
                      padding: const EdgeInsets.symmetric(vertical: 3),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Container(
                            width: 10,
                            height: 10,
                            decoration: BoxDecoration(
                              color: _severityColor(entry.key),
                              shape: BoxShape.circle,
                            ),
                          ),
                          const SizedBox(width: 6),
                          Text(
                            '${entry.key} (${entry.value})',
                            style: const TextStyle(
                              fontSize: 11,
                              color: Color(AppConstants.textSecondary),
                            ),
                          ),
                        ],
                      ),
                    );
                  }).toList(),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLineChartPanel(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Theme.of(context).brightness == Brightness.dark
            ? const Color(0xFF1a1a2e).withOpacity(0.6)
            : Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(
          color: const Color(AppConstants.borderSubtle),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _buildPanelHeader(
            AppStrings.get(context, 'scan_trends'),
          ),
          SizedBox(
            height: 200,
            child: LineChart(
              LineChartData(
                gridData: FlGridData(
                  show: true,
                  drawVerticalLine: false,
                  horizontalInterval: 10,
                  getDrawingHorizontalLine: (value) {
                    return FlLine(
                      color: const Color(AppConstants.borderSubtle)
                          .withOpacity(0.5),
                      strokeWidth: 1,
                    );
                  },
                ),
                titlesData: FlTitlesData(
                  leftTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      reservedSize: 32,
                      getTitlesWidget: (value, meta) {
                        return Text(
                          '${value.toInt()}',
                          style: const TextStyle(
                            fontSize: 10,
                            color: Color(AppConstants.textDisabled),
                          ),
                        );
                      },
                    ),
                  ),
                  bottomTitles: AxisTitles(
                    sideTitles: SideTitles(
                      showTitles: true,
                      interval: 5,
                      getTitlesWidget: (value, meta) {
                        return Text(
                          'Day ${value.toInt()}',
                          style: const TextStyle(
                            fontSize: 10,
                            color: Color(AppConstants.textDisabled),
                          ),
                        );
                      },
                    ),
                  ),
                  topTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                  rightTitles: const AxisTitles(
                    sideTitles: SideTitles(showTitles: false),
                  ),
                ),
                borderData: FlBorderData(show: false),
                minX: 0,
                maxX: 29,
                minY: 0,
                maxY: 60,
                lineBarsData: [
                  LineChartBarData(
                    spots: List.generate(
                      _trendsData.length,
                      (i) => FlSpot(i.toDouble(), _trendsData[i].toDouble()),
                    ),
                    isCurved: true,
                    preventCurveOverShooting: true,
                    color: const Color(0xFF1F6FEB),
                    barWidth: 2,
                    isStrokeCapRound: true,
                    dotData: const FlDotData(show: false),
                    belowBarData: BarAreaData(
                      show: true,
                      color: const Color(0xFF1F6FEB).withOpacity(0.1),
                    ),
                  ),
                ],
                lineTouchData: LineTouchData(
                  touchTooltipData: LineTouchTooltipData(
                    getTooltipItems: (touchedSpots) {
                      return touchedSpots.map((spot) {
                        return LineTooltipItem(
                          '${spot.y.toInt()} scans',
                          const TextStyle(
                            color: Colors.white,
                            fontSize: 11,
                            fontWeight: FontWeight.w500,
                          ),
                        );
                      }).toList();
                    },
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildRecentScans(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: isDark ? const Color(0xFF1a1a2e) : const Color(0xFFF6F8FA),
        border: Border.all(
          color: isDark ? const Color(0xFF30363D) : const Color(0xFFD0D7DE),
          width: 1,
        ),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(20, 16, 12, 0),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  AppStrings.get(context, 'recent_scans'),
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.w600,
                    color: isDark ? Colors.white : const Color(0xFF1F2328),
                  ),
                ),
                TextButton(
                  onPressed: () {
                    widget.onNavigate?.call(2);
                  },
                  child: Text(
                    AppStrings.get(context, 'view_all'),
                    style: const TextStyle(
                      fontSize: 12,
                      color: Color(0xFF1F6FEB),
                    ),
                  ),
                ),
              ],
            ),
          ),
          Divider(
            color: isDark ? const Color(0xFF30363D) : const Color(0xFFD0D7DE),
            height: 1,
            thickness: 1,
          ),
          LayoutBuilder(
            builder: (context, constraints) {
              return SizedBox(
                width: constraints.maxWidth,
                child: DataTable(
                  headingRowHeight: 36,
                  dataRowMinHeight: 44,
                  dataRowMaxHeight: 44,
                  columnSpacing: 24,
                  headingRowColor: WidgetStateProperty.all(
                    isDark ? const Color(0xFF0D1117) : const Color(0xFFE8ECF0),
                  ),
                  border: TableBorder(
                    horizontalInside: BorderSide(
                      color: isDark
                          ? const Color(0xFF30363D)
                          : const Color(0xFFD0D7DE),
                      width: 1,
                    ),
                  ),
                  columns: [
                    DataColumn(
                      label: Text(
                        AppStrings.get(context, 'target_url'),
                        style: TextStyle(
                          fontSize: 12,
                          color: isDark
                              ? const Color(0xFF8B949E)
                              : const Color(0xFF656D76),
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                    DataColumn(
                      label: Text(
                        AppStrings.get(context, 'date'),
                        style: TextStyle(
                          fontSize: 12,
                          color: isDark
                              ? const Color(0xFF8B949E)
                              : const Color(0xFF656D76),
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                    DataColumn(
                      label: Text(
                        AppStrings.get(context, 'status'),
                        style: TextStyle(
                          fontSize: 12,
                          color: isDark
                              ? const Color(0xFF8B949E)
                              : const Color(0xFF656D76),
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                    DataColumn(
                      label: Text(
                        AppStrings.get(context, 'risk_level'),
                        style: TextStyle(
                          fontSize: 12,
                          color: isDark
                              ? const Color(0xFF8B949E)
                              : const Color(0xFF656D76),
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                  rows: _recentScans
                      .map((scan) => DataRow(
                            cells: [
                              DataCell(
                                Text(
                                  scan['target_url'] ?? '',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: isDark
                                        ? Colors.white
                                        : const Color(0xFF1F2328),
                                  ),
                                ),
                              ),
                              DataCell(
                                Text(
                                  scan['created_at']
                                          ?.toString()
                                          .substring(0, 10) ??
                                      '',
                                  style: TextStyle(
                                    fontSize: 12,
                                    color: isDark
                                        ? const Color(0xFF8B949E)
                                        : const Color(0xFF656D76),
                                  ),
                                ),
                              ),
                              DataCell(_buildStatusBadge(
                                scan['status'] == 'completed'
                                    ? 'Completed'
                                    : 'Failed',
                                isDark,
                              )),
                              DataCell(_buildRiskBadge(
                                _capitalizeFirst(
                                    scan['risk_level'] ?? 'unknown'),
                                isDark,
                              )),
                            ],
                          ))
                      .toList(),
                ),
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildStatusBadge(String status, bool isDark) {
    final isCompleted = status == 'Completed';
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: isCompleted
            ? (isDark ? const Color(0xFF1A4731) : const Color(0xFFDCFCE7))
            : (isDark ? const Color(0xFF3D1F1F) : const Color(0xFFFEE2E2)),
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        isCompleted
            ? AppStrings.get(context, 'completed')
            : AppStrings.get(context, 'failed'),
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w500,
          color:
              isCompleted ? const Color(0xFF3FB950) : const Color(0xFFF85149),
        ),
      ),
    );
  }

  Widget _buildRiskBadge(String risk, bool isDark) {
    final colorMap = <String, (Color, Color)>{
      'Critical': (
        isDark ? const Color(0xFF3D1F1F) : const Color(0xFFFEE2E2),
        const Color(0xFFF85149),
      ),
      'High': (
        isDark ? const Color(0xFF3D2B1F) : const Color(0xFFFEF3C7),
        const Color(0xFFF0883E),
      ),
      'Medium': (
        isDark ? const Color(0xFF3D3419) : const Color(0xFFFEF9C3),
        const Color(0xFFE3B341),
      ),
      'Low': (
        isDark ? const Color(0xFF1A3640) : const Color(0xFFDBEAFE),
        const Color(0xFF58A6FF),
      ),
      'Unknown': (
        isDark ? const Color(0xFF21262D) : const Color(0xFFF3F4F6),
        isDark ? const Color(0xFF8B949E) : const Color(0xFF6B7280),
      ),
    };
    final (bg, fg) = colorMap[risk] ?? colorMap['Unknown']!;
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        risk,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w500,
          color: fg,
        ),
      ),
    );
  }
}
