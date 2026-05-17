import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../core/app_strings.dart';
import '../main.dart';
import '../widgets/language_selector.dart';
import 'scan_screen.dart';
import 'history_screen.dart';
import 'dashboard_overview.dart';
import 'settings_screen.dart';
import '../core/settings_sync.dart';

class _NavItem {
  final int index;
  final IconData icon;
  final String label;
  final String sublabel;
  const _NavItem(this.index, this.icon, this.label, this.sublabel);
}

class MainDashboard extends StatefulWidget {
  const MainDashboard({super.key});

  @override
  State<MainDashboard> createState() => _MainDashboardState();
}

class _MainDashboardState extends State<MainDashboard> {
  int _selectedIndex = 0;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      syncSettingsToBackend();
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          _buildSidebar(context),
          Expanded(
            child: Consumer<AppState>(
              builder: (context, appState, _) {
                return IndexedStack(
                  index: _selectedIndex,
                  children: [
                    DashboardOverviewWidget(
                      onNavigate: (i) => setState(() => _selectedIndex = i),
                    ),
                    const ScanScreen(showAppBar: false),
                    const HistoryScreen(showAppBar: false),
                    const SettingsScreen(),
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }

  List<_NavItem> _getNavItems(BuildContext context) => [
        _NavItem(
          0,
          Icons.dashboard_outlined,
          AppStrings.get(context, 'dashboard'),
          AppStrings.get(context, 'overview'),
        ),
        _NavItem(
          1,
          Icons.shield_outlined,
          AppStrings.get(context, 'new_scan'),
          AppStrings.get(context, 'start_scanning'),
        ),
        _NavItem(
          2,
          Icons.history,
          AppStrings.get(context, 'scan_history'),
          AppStrings.get(context, 'past_results'),
        ),
        _NavItem(
          3,
          Icons.settings_outlined,
          AppStrings.get(context, 'settings'),
          AppStrings.get(context, 'configuration'),
        ),
      ];

  Widget _buildSidebar(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, _) {
        final navItems = _getNavItems(context);
        return Container(
          width: 220,
          decoration: BoxDecoration(
            color: Theme.of(context).brightness == Brightness.dark
                ? Colors.black
                : const Color(0xFFF6F8FA),
            border: Border(
              right: BorderSide(
                color: Theme.of(context).brightness == Brightness.dark
                    ? const Color(0xFF21262D)
                    : const Color(0xFFD0D7DE),
                width: 1,
              ),
            ),
          ),
          child: Column(
            children: [
              _buildLogo(context),
              Expanded(
                child: ListView.builder(
                  padding: EdgeInsets.zero,
                  itemCount: navItems.length,
                  itemBuilder: (context, i) {
                    final item = navItems[i];
                    final isActive = _selectedIndex == item.index;
                    return MouseRegion(
                      cursor: SystemMouseCursors.click,
                      child: InkWell(
                        onTap: () => setState(() {
                          _selectedIndex = item.index;
                        }),
                        child: _buildNavItem(item, isActive),
                      ),
                    );
                  },
                ),
              ),
              _buildSidebarFooter(context),
            ],
          ),
        );
      },
    );
  }

  Widget _buildLogo(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    return Column(
      children: [
        const SizedBox(height: 16),
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 16),
          child: Row(
            children: [
              const Icon(
                Icons.shield,
                color: Color(0xFF1F6FEB),
                size: 20,
              ),
              const SizedBox(width: 8),
              Text(
                'WebScan Pro',
                style: TextStyle(
                  color: isDark ? Colors.white : const Color(0xFF1F2328),
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),
        Divider(
          height: 1,
          thickness: 1,
          color: isDark ? const Color(0xFF21262D) : const Color(0xFFD0D7DE),
        ),
      ],
    );
  }

  Widget _buildNavItem(_NavItem item, bool isActive) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: isActive ? const Color(0xFF1F6FEB) : Colors.transparent,
        borderRadius: BorderRadius.circular(6),
      ),
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      child: Row(
        children: [
          Icon(
            item.icon,
            size: 18,
            color: isActive ? Colors.white : const Color(0xFF8B949E),
          ),
          const SizedBox(width: 10),
          Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                item.label,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w500,
                  color: isActive ? Colors.white : const Color(0xFF8B949E),
                ),
              ),
              Text(
                item.sublabel,
                style: const TextStyle(
                  fontSize: 10,
                  color: Color(0xFF8B949E),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildSidebarFooter(BuildContext context) {
    return Consumer<AppState>(
      builder: (context, appState, _) {
        return Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Divider(
              height: 1,
              thickness: 1,
              color: Theme.of(context).brightness == Brightness.dark
                  ? const Color(0xFF21262D)
                  : const Color(0xFFD0D7DE),
            ),
            const SizedBox(height: 8),
            const LanguageSelector(),
            IconButton(
              onPressed: () => appState.toggleDarkMode(),
              icon: Icon(
                appState.isDarkMode ? Icons.dark_mode : Icons.light_mode,
                size: 18,
                color: const Color(0xFF8B949E),
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'v2.0',
              style: TextStyle(
                fontSize: 12,
                color: Color(0xFF8B949E),
              ),
            ),
            const SizedBox(height: 12),
          ],
        );
      },
    );
  }
}
