// lib/main.dart

import 'dart:async';
import 'dart:typed_data';
import 'dart:io'; // for SocketException

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import 'package:image_picker/image_picker.dart';
import 'package:tflite_flutter/tflite_flutter.dart';
import 'package:image/image.dart' as img;

void main() {
  runApp(const MajorProjectApp());
}

/// ======================= APP ROOT + THEME + SPLASH =======================

class MajorProjectApp extends StatefulWidget {
  const MajorProjectApp({super.key});

  @override
  State<MajorProjectApp> createState() => _MajorProjectAppState();
}

class _MajorProjectAppState extends State<MajorProjectApp> {
  bool _isDark = true;
  bool _showSplash = true;

  void _toggleTheme() {
    setState(() => _isDark = !_isDark);
  }

  @override
  void initState() {
    super.initState();
    Future.delayed(const Duration(seconds: 5), () {
      if (mounted) setState(() => _showSplash = false);
    });
  }

  @override
  Widget build(BuildContext context) {
    final lightTheme = ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      colorSchemeSeed: const Color(0xFF1F8BFF),
      scaffoldBackgroundColor: const Color(0xFFF3F5FF),
      fontFamily: 'Roboto',
    );

    final darkTheme = ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorSchemeSeed: const Color(0xFF1F8BFF),
      scaffoldBackgroundColor: const Color(0xFF050A18),
      fontFamily: 'Roboto',
    );

    return MaterialApp(
      title: 'Ayusanjeevini',
      debugShowCheckedModeBanner: false,
      theme: lightTheme,
      darkTheme: darkTheme,
      themeMode: _isDark ? ThemeMode.dark : ThemeMode.light,
      home: _showSplash
          ? const SplashScreen()
          : MainShell(
        isDark: _isDark,
        onToggleTheme: _toggleTheme,
      ),
    );
  }
}

/// ======================= FANCY SPLASH =======================

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen>
    with SingleTickerProviderStateMixin {
  late AnimationController _controller;
  late Animation<double> _logoScale;
  late Animation<double> _logoRotation;
  late Animation<double> _ringOpacity;
  late Animation<Offset> _textSlide;

  @override
  void initState() {
    super.initState();

    _controller = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 2),
    )..repeat(reverse: true);

    _logoScale = Tween<double>(begin: 0.85, end: 1.05).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );

    _logoRotation = Tween<double>(begin: -0.05, end: 0.05).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );

    _ringOpacity = Tween<double>(begin: 0.15, end: 0.45).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeInOut),
    );

    _textSlide = Tween<Offset>(
      begin: const Offset(0, 0.35),
      end: const Offset(0, 0.0),
    ).animate(
      CurvedAnimation(parent: _controller, curve: Curves.easeOut),
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Widget _buildGlowRing() {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, child) {
        return Container(
          width: 180,
          height: 180,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: SweepGradient(
              colors: [
                const Color(0xFF4F9BFF).withOpacity(_ringOpacity.value),
                const Color(0xFF34D399).withOpacity(_ringOpacity.value),
                const Color(0xFFFF6B81).withOpacity(_ringOpacity.value),
                const Color(0xFF4F9BFF).withOpacity(_ringOpacity.value),
              ],
            ),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF4F9BFF).withOpacity(_ringOpacity.value),
                blurRadius: 28,
                spreadRadius: 4,
              ),
            ],
          ),
        );
      },
    );
  }

  Widget _buildLogo() {
    return ScaleTransition(
      scale: _logoScale,
      child: RotationTransition(
        turns: _logoRotation,
        child: Container(
          width: 110,
          height: 110,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: const LinearGradient(
              colors: [Color(0xFF4F9BFF), Color(0xFF1F8BFF)],
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
            ),
            boxShadow: [
              BoxShadow(
                color: const Color(0xFF4F9BFF).withOpacity(0.55),
                blurRadius: 24,
                offset: const Offset(0, 10),
              ),
            ],
          ),
          child: const Center(
            child: Icon(
              Icons.monitor_heart_rounded,
              size: 52,
              color: Colors.white,
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTexts() {
    return SlideTransition(
      position: _textSlide,
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: const [
          Text(
            'Ayusanjeevini',
            style: TextStyle(
              fontSize: 32,
              fontWeight: FontWeight.w800,
              letterSpacing: 1.2,
              color: Colors.white,
            ),
          ),
          SizedBox(height: 8),
          Text(
            'Keeping an eye on your health, gently.',
            style: TextStyle(
              fontSize: 14,
              color: Colors.white70,
            ),
          ),
          SizedBox(height: 26),
          SizedBox(
            height: 22,
            width: 22,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              valueColor: AlwaysStoppedAnimation<Color>(
                Color(0xFF4F9BFF),
              ),
            ),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFF050A18), Color(0xFF071937)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Stack(
                alignment: Alignment.center,
                children: [
                  _buildGlowRing(),
                  _buildLogo(),
                ],
              ),
              const SizedBox(height: 30),
              _buildTexts(),
            ],
          ),
        ),
      ),
    );
  }
}

/// ============================ APP SHELL / NAVIGATION ============================

class MainShell extends StatefulWidget {
  final bool isDark;
  final VoidCallback onToggleTheme;

  const MainShell({super.key, required this.isDark, required this.onToggleTheme});

  @override
  State<MainShell> createState() => _MainShellState();
}

class _MainShellState extends State<MainShell> {
  int _selectedIndex = 0;

  @override
  Widget build(BuildContext context) {
    final pages = <Widget>[
      HomeVitalsPage(onToggleTheme: widget.onToggleTheme, isDark: widget.isDark),
      const ScanLandingPage(),
    ];

    return Scaffold(
      backgroundColor: Colors.transparent,
      body: IndexedStack(
        index: _selectedIndex,
        children: pages,
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _selectedIndex,
        onTap: (i) => setState(() => _selectedIndex = i),
        items: const [
          BottomNavigationBarItem(
            icon: Icon(Icons.home_outlined),
            label: 'Home',
          ),
          BottomNavigationBarItem(
            icon: Icon(Icons.camera_alt_outlined),
            label: 'Scan',
          ),
        ],
      ),
    );
  }
}

/// ============================ GOOGLE SHEET ============================

class HealthData {
  final DateTime? timestamp;
  final int steps;
  final int bpm;
  final int avgBpm;
  final int spo2;
  final double temperature; // 🔥 IR column mapped as temperature
  final bool fingerDetected;
  final String? error;

  HealthData({
    required this.timestamp,
    required this.steps,
    required this.bpm,
    required this.avgBpm,
    required this.spo2,
    required this.temperature,
    required this.fingerDetected,
    this.error,
  });
}

/// ✅ UPDATED GOOGLE SHEET (IR column used as temperature)
const String _sheetCsvUrl =
    'https://docs.google.com/spreadsheets/d/1rz_Mj739pGbK65mFIJnSD6b4XoRkotpUTGRbVjRtzFg/export?format=csv&gid=0';

Future<HealthData> fetchHealthData() async {
  try {
    final resp = await http.get(Uri.parse(_sheetCsvUrl));

    if (resp.statusCode != 200) {
      return _errorData('Unable to reach the live data source.');
    }

    final lines = resp.body.trim().split('\n');
    if (lines.length < 2) {
      return _errorData('No recent readings available.');
    }

    final parts = lines.last.split(',');

    int _toInt(int i) => int.tryParse(parts[i].trim()) ?? 0;
    double _toDouble(int i) => double.tryParse(parts[i].trim()) ?? 0.0;

    return HealthData(
      timestamp:
      DateTime.fromMillisecondsSinceEpoch(_toInt(0) * 1000),
      steps: _toInt(1),
      bpm: _toInt(2),
      avgBpm: _toInt(3),
      spo2: _toInt(4),
      temperature: _toDouble(5), // IR VALUE USED HERE
      fingerDetected: parts[6].trim().toUpperCase() == 'YES',
      error: null,
    );
  } catch (_) {
    return _errorData('Error loading data.');
  }
}

HealthData _errorData(String msg) => HealthData(
  timestamp: null,
  steps: 0,
  bpm: 0,
  avgBpm: 0,
  spo2: 0,
  temperature: 0.0,
  fingerDetected: false,
  error: msg,
);


/// =============================== HOME PAGE ===============================

class HomeVitalsPage extends StatefulWidget {
  final VoidCallback onToggleTheme;
  final bool isDark;

  const HomeVitalsPage({
    super.key,
    required this.onToggleTheme,
    required this.isDark,
  });

  @override
  State<HomeVitalsPage> createState() => _HomeVitalsPageState();
}

class _HomeVitalsPageState extends State<HomeVitalsPage> {
  HealthData? _data;
  String? _error;
  bool _initialLoading = true;
  Timer? _timer;

  bool _alertShowing = false;
  DateTime? _lastAlertTime;

  @override
  void initState() {
    super.initState();
    _loadOnce();
    _timer = Timer.periodic(const Duration(seconds: 3), (_) => _loadOnce());
  }

  Future<void> _loadOnce() async {
    final d = await fetchHealthData();
    if (!mounted) return;
    setState(() {
      _data = d;
      _error = d.error;
      _initialLoading = false;
    });
  }

  @override
  void dispose() {
    _timer?.cancel();
    super.dispose();
  }

  // Simple calorie estimate: ~0.04 kcal per step
  double _estimateCalories(int steps) {
    return steps * 0.04;
  }

  Future<void> _maybeShowBpmAlert(int bpm, bool fingerOk) async {
    if (!mounted) return;
    if (!fingerOk || bpm <= 0) return;

    const int minBpm = 50; // low threshold
    const int maxBpm = 120; // high threshold

    final now = DateTime.now();
    if (_alertShowing) return;
    if (_lastAlertTime != null &&
        now.difference(_lastAlertTime!) < const Duration(seconds: 30)) {
      return;
    }

    if (bpm < minBpm || bpm > maxBpm) {
      _alertShowing = true;
      _lastAlertTime = now;
      final isHigh = bpm > maxBpm;

      await showDialog(
        context: context,
        barrierDismissible: true,
        builder: (ctx) {
          return AlertDialog(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(18),
            ),
            title: Row(
              children: [
                Icon(
                  Icons.health_and_safety_rounded,
                  color: isHigh ? Colors.redAccent : Colors.orangeAccent,
                ),
                const SizedBox(width: 8),
                Text(isHigh ? 'Heart rate is high' : 'Heart rate is low'),
              ],
            ),
            content: Text(
              'Your current heart rate is $bpm bpm.\n\n'
                  'Take a short break, breathe slowly, and check again in a minute. '
                  'If you feel dizzy, breathless, or uncomfortable, please reach out to a doctor.\n\n'
                  'This app is only a helper and does not replace medical advice.',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(),
                child: const Text('Okay'),
              ),
            ],
          );
        },
      );

      if (!mounted) return;
      setState(() {
        _alertShowing = false;
      });
    }
  }

  Future<void> _maybeShowTempAlert(double temperature) async {
    if (!mounted) return;
    if (temperature <= 0) return;

    // Very soft thresholds, since watch sensors are approximate
    const double highTempThreshold = 37.8; // ~100°F

    final now = DateTime.now();
    if (_alertShowing) return;
    if (_lastAlertTime != null &&
        now.difference(_lastAlertTime!) < const Duration(seconds: 30)) {
      return;
    }

    if (temperature > highTempThreshold) {
      _alertShowing = true;
      _lastAlertTime = now;

      await showDialog(
        context: context,
        barrierDismissible: true,
        builder: (ctx) {
          return AlertDialog(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(18),
            ),
            title: Row(
              children: const [
                Icon(
                  Icons.thermostat_rounded,
                  color: Colors.orangeAccent,
                ),
                SizedBox(width: 8),
                Text('Temperature looks high'),
              ],
            ),
            content: Text(
              'Your watch is showing a body temperature of '
                  '${temperature.toStringAsFixed(1)}°C.\n\n'
                  'If you feel warm, tired, or unwell, please confirm with a proper thermometer. '
                  'If fever persists or you feel sick, talk to a doctor.\n\n'
                  'This reading is only an estimate from the wearable sensor.',
            ),
            actions: [
              TextButton(
                onPressed: () => Navigator.of(ctx).pop(),
                child: const Text('Got it'),
              ),
            ],
          );
        },
      );

      if (!mounted) return;
      setState(() {
        _alertShowing = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDarkMode = Theme.of(context).brightness == Brightness.dark;
    final primaryText = isDarkMode ? Colors.white : const Color(0xFF101828);
    final secondaryText =
    isDarkMode ? Colors.white70 : const Color(0xFF667085);
    final surfaceShadow =
    isDarkMode ? Colors.black.withOpacity(0.4) : Colors.black.withOpacity(0.06);

    final bpm = _data?.bpm ?? 0;
    final spo2 = _data?.spo2 ?? 0;
    final temperature = _data?.temperature ?? 0.0;
    final steps = _data?.steps ?? 0;
    final avgBpm = _data?.avgBpm ?? 0;
    final fingerOk = _data?.fingerDetected ?? false;
    final calories = _estimateCalories(steps);

    if (!_initialLoading && _data != null && _error == null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _maybeShowBpmAlert(bpm, fingerOk);
        _maybeShowTempAlert(temperature);
      });
    }

    return SafeArea(
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: isDarkMode
                ? const [Color(0xFF050A18), Color(0xFF041824)]
                : const [Color(0xFFF5F8FF), Color(0xFFE8F0FF)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 14, 20, 0),
          child: _initialLoading && _data == null
              ? const Center(child: CircularProgressIndicator())
              : Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // HEADER
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          'Health dashboard',
                          style: TextStyle(
                            color: primaryText,
                            fontSize: 24,
                            fontWeight: FontWeight.w800,
                          ),
                        ),
                        const SizedBox(height: 4),
                        if (_error != null)
                          Text(
                            _error!,
                            style: const TextStyle(
                              color: Colors.redAccent,
                              fontSize: 12,
                            ),
                          )
                        else
                          Text(
                            'Showing your latest heartbeat, oxygen and activity.',
                            style: TextStyle(
                              color: secondaryText,
                              fontSize: 13,
                            ),
                          ),
                      ],
                    ),
                  ),
                  IconButton(
                    onPressed: widget.onToggleTheme,
                    icon: Icon(
                      isDarkMode
                          ? Icons.light_mode_rounded
                          : Icons.dark_mode_rounded,
                      color: isDarkMode
                          ? Colors.amberAccent
                          : const Color(0xFF475467),
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: isDarkMode
                          ? const Color(0xFF0B1220)
                          : Colors.white,
                      shape: BoxShape.circle,
                      boxShadow: [
                        BoxShadow(
                          blurRadius: 12,
                          offset: const Offset(0, 4),
                          color: surfaceShadow,
                        ),
                      ],
                    ),
                    child: Icon(
                      Icons.person_outline,
                      color: isDarkMode
                          ? Colors.white
                          : const Color(0xFF1F8BFF),
                      size: 24,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),

              // HEART RATE CARD
              Container(
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(24),
                  gradient: const LinearGradient(
                    colors: [Color(0xFFFF4B5C), Color(0xFFFF6F91)],
                    begin: Alignment.topLeft,
                    end: Alignment.bottomRight,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: const Color(0xFFFF4B5C).withOpacity(0.35),
                      blurRadius: 22,
                      offset: const Offset(0, 10),
                    ),
                  ],
                ),
                padding: const EdgeInsets.symmetric(
                    horizontal: 18, vertical: 16),
                child: Row(
                  children: [
                    SizedBox(
                      width: 96, // slightly smaller to give text more room
                      height: 96,
                      child: Stack(
                        alignment: Alignment.center,
                        children: [
                          Container(
                            width: 96,
                            height: 96,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: Colors.white.withOpacity(0.12),
                            ),
                          ),
                          Container(
                            width: 80,
                            height: 80,
                            decoration: const BoxDecoration(
                              shape: BoxShape.circle,
                              color: Colors.white,
                            ),
                            child: Column(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                const Icon(
                                  Icons.favorite_rounded,
                                  color: Color(0xFFFF4B5C),
                                  size: 24,
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  bpm > 0 ? bpm.toString() : '--',
                                  style: const TextStyle(
                                    color: Color(0xFF101828),
                                    fontSize: 22,
                                    fontWeight: FontWeight.w800,
                                  ),
                                ),
                                const Text(
                                  'bpm',
                                  style: TextStyle(
                                    color: Color(0xFF667085),
                                    fontSize: 11,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Heart rate',
                            style: TextStyle(
                              color: Colors.white,
                              fontSize: 18,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          const SizedBox(height: 6),
                          Text(
                            avgBpm > 0
                                ? 'Average today: $avgBpm bpm'
                                : 'Average today: --',
                            style: const TextStyle(
                              color: Color(0xFFFFE8ED),
                              fontSize: 13,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            'Steps counted: $steps',
                            style: const TextStyle(
                              color: Color(0xFFFFE8ED),
                              fontSize: 13,
                            ),
                          ),
                          const SizedBox(height: 10),
                          _HeartStatusChip(ok: fingerOk),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),

              // GRID OF OTHER VITALS
              Expanded(
                child: GridView.count(
                  crossAxisCount: 2,
                  mainAxisSpacing: 14,
                  crossAxisSpacing: 14,
                  childAspectRatio: 0.85,
                  padding: EdgeInsets.zero,
                  children: [
                    _VitalCard(
                      icon: Icons.water_drop_rounded,
                      title: 'Blood oxygen',
                      value: spo2 > 0 ? '$spo2%' : '--',
                      subtitle: 'SpO₂ saturation level',
                      gradient: const LinearGradient(
                        colors: [Color(0xFF1F8BFF), Color(0xFF4FD1FF)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      pillText:
                      spo2 >= 95 ? 'Looks good' : 'Re-check calmly',
                    ),
                    _VitalCard(
                      icon: Icons.thermostat_rounded,
                      title: 'Temperature',
                      value: temperature > 0
                          ? '${temperature.toStringAsFixed(1)}°C'
                          : '--',
                      subtitle: 'Approx. body temperature',
                      gradient: const LinearGradient(
                        colors: [Color(0xFFFFA726), Color(0xFFFF7043)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      pillText: 'Watch estimate only',
                    ),
                    _VitalCard(
                      icon: Icons.directions_walk_rounded,
                      title: 'Steps today',
                      value: '$steps',
                      subtitle: 'Based on tracker readings',
                      gradient: const LinearGradient(
                        colors: [Color(0xFF6366F1), Color(0xFF4F46E5)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      pillText: steps > 0 ? 'Keep moving' : 'Let\'s start',
                    ),
                    _VitalCard(
                      icon: Icons.local_fire_department_rounded,
                      title: 'Calories burned',
                      value: calories > 0
                          ? '${calories.toStringAsFixed(0)} kcal'
                          : '--',
                      subtitle: 'Estimated from your steps',
                      gradient: const LinearGradient(
                        colors: [Color(0xFF34D399), Color(0xFF10B981)],
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                      ),
                      pillText:
                      calories > 0 ? 'Nice effort' : 'You can do it',
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _HeartStatusChip extends StatelessWidget {
  final bool ok;

  const _HeartStatusChip({required this.ok});

  @override
  Widget build(BuildContext context) {
    // FittedBox makes sure the chip scales down instead of overflowing
    return FittedBox(
      fit: BoxFit.scaleDown,
      alignment: Alignment.centerLeft,
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.16),
          borderRadius: BorderRadius.circular(999),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(
              ok ? Icons.check_circle : Icons.error_outline,
              size: 16,
              color: Colors.white,
            ),
            const SizedBox(width: 6),
            Flexible(
              child: Text(
                ok ? 'Finger detected' : 'Adjust finger placement',
                softWrap: false,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: Colors.white,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _VitalCard extends StatelessWidget {
  final IconData icon;
  final String title;
  final String value;
  final String subtitle;
  final Gradient gradient;
  final String pillText;

  const _VitalCard({
    super.key,
    required this.icon,
    required this.title,
    required this.value,
    required this.subtitle,
    required this.gradient,
    required this.pillText,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(22),
        gradient: gradient,
        boxShadow: [
          BoxShadow(
            blurRadius: 12,
            offset: const Offset(0, 8),
            color: Colors.black.withOpacity(0.14),
          ),
        ],
      ),
      padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Icon(icon, color: Colors.white, size: 24),
          const SizedBox(height: 6),
          Text(
            title,
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 12,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            value,
            style: const TextStyle(
              color: Colors.white,
              fontSize: 18,
              fontWeight: FontWeight.w700,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            subtitle,
            style: const TextStyle(
              color: Colors.white70,
              fontSize: 11,
            ),
          ),
          const Spacer(),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 5),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.18),
              borderRadius: BorderRadius.circular(999),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.check_circle, size: 14, color: Colors.white),
                const SizedBox(width: 4),
                Flexible(
                  child: Text(
                    pillText,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Colors.white,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

/// =============================== SCAN PAGE ===============================

class ScanLandingPage extends StatefulWidget {
  const ScanLandingPage({super.key});

  @override
  State<ScanLandingPage> createState() => _ScanLandingPageState();
}

class _ScanLandingPageState extends State<ScanLandingPage> {
  Interpreter? _routerInterpreter; // routing model
  Interpreter? _modelAInterpreter; // skin analysis model
  Interpreter? _modelBInterpreter; // dental analysis model

  Uint8List? _imageBytes;
  bool _loading = false;
  String _result = 'No prediction yet';

  static const List<String> _modelALabels = [
    'Acne',
    'Carcinoma',
    'Eczema',
    'Keratosis',
    'Milia',
    'Rosacea',
  ];

  static const List<String> _modelBLabels = [
    'Calculus',
    'Gingivitis',
  ];

  @override
  void initState() {
    super.initState();
    _loadAllModels();
  }

  Future<void> _loadAllModels() async {
    try {
      _routerInterpreter = await Interpreter.fromAsset(
        'assets/models/skin_vs_teeth.tflite',
        options: InterpreterOptions()..threads = 4,
      );
    } catch (e) {
      setState(() => _result = 'Could not load routing model.');
    }

    try {
      _modelAInterpreter = await Interpreter.fromAsset(
        'assets/models/skin_model.tflite',
        options: InterpreterOptions()..threads = 4,
      );
    } catch (e) {
      setState(() => _result = 'Could not load skin analysis model.');
    }

    try {
      _modelBInterpreter = await Interpreter.fromAsset(
        'assets/models/best_dental_model.tflite',
        options: InterpreterOptions()..threads = 4,
      );
    } catch (e) {
      setState(() => _result = 'Could not load dental analysis model.');
    }
  }

  Future<void> _pickImage() async {
    final picker = ImagePicker();
    final XFile? file = await picker.pickImage(source: ImageSource.gallery);
    if (file == null) return;

    final bytes = await file.readAsBytes();
    setState(() {
      _imageBytes = bytes;
      _result = 'Analysing your scan...';
    });

    await _runRouterPipeline(bytes);
  }

  Future<void> _runRouterPipeline(Uint8List imageBytes) async {
    if (_routerInterpreter == null) {
      setState(() => _result = 'Routing model is not available.');
      return;
    }

    setState(() => _loading = true);

    try {
      img.Image? image = img.decodeImage(imageBytes);
      if (image == null) throw 'Could not decode image';

      final inputTensor = _routerInterpreter!.getInputTensor(0);
      final shape = inputTensor.shape;
      final h = shape[1];
      final w = shape[2];

      final resized = img.copyResize(image, width: w, height: h);

      final input = List.generate(
        1,
            (_) => List.generate(
          h,
              (y) => List.generate(
            w,
                (x) {
              final px = resized.getPixel(x, y);
              return [
                px.r.toDouble(),
                px.g.toDouble(),
                px.b.toDouble(),
              ];
            },
          ),
        ),
      );

      final outputTensor = _routerInterpreter!.getOutputTensor(0);
      final outShape = outputTensor.shape;
      final numClasses = outShape.last;

      final output = List.generate(
        1,
            (_) => List.filled(numClasses, 0.0),
      );

      _routerInterpreter!.run(input, output);

      final scores = output[0];

      bool useModelB;

      if (numClasses == 2) {
        final idx = _argMax(scores);
        useModelB = idx == 1;
      } else if (numClasses == 1) {
        final prob = scores[0];
        useModelB = prob >= 0.5;
      } else {
        final idx = _argMax(scores);
        useModelB = idx == 1;
      }

      setState(() {
        _result = 'Choosing the right model for this scan...';
      });

      if (useModelB) {
        await _runModelB(imageBytes);
      } else {
        await _runModelA(imageBytes);
      }
    } catch (e) {
      setState(() => _result = 'There was an issue while routing the image.');
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _runModelA(Uint8List imageBytes) async {
    if (_modelAInterpreter == null) {
      setState(() => _result = 'Skin analysis model is not loaded yet.');
      return;
    }

    setState(() => _loading = true);

    try {
      img.Image? image = img.decodeImage(imageBytes);
      if (image == null) throw 'Could not decode image';

      final inputTensor = _modelAInterpreter!.getInputTensor(0);
      final shape = inputTensor.shape;
      final h = shape[1];
      final w = shape[2];

      final resized = img.copyResize(image, width: w, height: h);

      final input = List.generate(
        1,
            (_) => List.generate(
          h,
              (y) => List.generate(
            w,
                (x) {
              final px = resized.getPixel(x, y);
              return [
                px.r.toDouble(),
                px.g.toDouble(),
                px.b.toDouble(),
              ];
            },
          ),
        ),
      );

      final outputTensor = _modelAInterpreter!.getOutputTensor(0);
      final outShape = outputTensor.shape;
      final numClasses = outShape.last;

      final output = List.generate(
        1,
            (_) => List.filled(numClasses, 0.0),
      );

      _modelAInterpreter!.run(input, output);

      final scores = output[0];
      final bestIdx = _argMax(scores);
      final label = bestIdx >= 0 && bestIdx < _modelALabels.length
          ? _modelALabels[bestIdx]
          : 'Unknown';

      setState(() {
        _result = 'Result: likely a skin condition related to "$label".';
      });
    } catch (e) {
      setState(() => _result = 'There was an issue during skin analysis.');
    } finally {
      setState(() => _loading = false);
    }
  }

  Future<void> _runModelB(Uint8List imageBytes) async {
    if (_modelBInterpreter == null) {
      setState(() => _result = 'Dental analysis model is not loaded yet.');
      return;
    }

    setState(() => _loading = true);

    try {
      img.Image? image = img.decodeImage(imageBytes);
      if (image == null) throw 'Could not decode image';

      final inputTensor = _modelBInterpreter!.getInputTensor(0);
      final shape = inputTensor.shape;
      final h = shape[1];
      final w = shape[2];

      final resized = img.copyResize(image, width: w, height: h);

      final input = List.generate(
        1,
            (_) => List.generate(
          h,
              (y) => List.generate(
            w,
                (x) {
              final px = resized.getPixel(x, y);
              return [
                px.r / 255.0,
                px.g / 255.0,
                px.b / 255.0,
              ];
            },
          ),
        ),
      );

      final outputTensor = _modelBInterpreter!.getOutputTensor(0);
      final outShape = outputTensor.shape;
      final numClasses = outShape.last;

      final output = List.generate(
        1,
            (_) => List.filled(numClasses, 0.0),
      );

      _modelBInterpreter!.run(input, output);

      final scores = output[0];

      int bestIdx;
      if (numClasses == 1 && _modelBLabels.length == 2) {
        final score = scores[0];
        bestIdx = score >= 0.5 ? 1 : 0;
      } else {
        bestIdx = _argMax(scores);
      }

      final label = bestIdx >= 0 && bestIdx < _modelBLabels.length
          ? _modelBLabels[bestIdx]
          : 'Unknown';

      setState(() {
        _result = 'Result: likely a dental issue related to "$label".';
      });
    } catch (e) {
      setState(() => _result = 'There was an issue during dental analysis.');
    } finally {
      setState(() => _loading = false);
    }
  }

  int _argMax(List<double> list) {
    var maxVal = list[0];
    var maxIdx = 0;
    for (var i = 1; i < list.length; i++) {
      if (list[i] > maxVal) {
        maxVal = list[i];
        maxIdx = i;
      }
    }
    return maxIdx;
  }

  @override
  void dispose() {
    _routerInterpreter?.close();
    _modelAInterpreter?.close();
    _modelBInterpreter?.close();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isDarkMode = Theme.of(context).brightness == Brightness.dark;
    final cardBg = isDarkMode ? const Color(0xFF0B1220) : Colors.white;
    final primaryText =
    isDarkMode ? Colors.white : const Color(0xFF101828);
    final secondaryText =
    isDarkMode ? Colors.white70 : const Color(0xFF667085);

    return SafeArea(
      child: Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: isDarkMode
                ? const [Color(0xFF050A18), Color(0xFF041824)]
                : const [Color(0xFFF5F8FF), Color(0xFFE8F0FF)],
            begin: Alignment.topCenter,
            end: Alignment.bottomCenter,
          ),
        ),
        child: Scaffold(
          backgroundColor: Colors.transparent,
          appBar: AppBar(
            title: Text(
              'Scan analysis',
              style: TextStyle(
                color: primaryText,
                fontWeight: FontWeight.w700,
              ),
            ),
            backgroundColor: Colors.transparent,
            elevation: 0,
            iconTheme: IconThemeData(color: primaryText),
          ),
          body: Padding(
            padding: const EdgeInsets.all(18),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'Upload a clear scanned image. The app will decide whether it belongs to skin or teeth and analyse it accordingly.',
                  style: TextStyle(
                    color: secondaryText,
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 16),
                Expanded(
                  child: Container(
                    decoration: BoxDecoration(
                      color: cardBg,
                      borderRadius: BorderRadius.circular(24),
                      boxShadow: [
                        BoxShadow(
                          blurRadius: 18,
                          offset: const Offset(0, 8),
                          color: Colors.black.withOpacity(0.12),
                        ),
                      ],
                    ),
                    child: Center(
                      child: _imageBytes == null
                          ? Padding(
                        padding: const EdgeInsets.all(20),
                        child: Text(
                          'No image selected yet.\nChoose a scan from your gallery to begin.',
                          textAlign: TextAlign.center,
                          style: TextStyle(
                            color: secondaryText,
                            fontSize: 14,
                          ),
                        ),
                      )
                          : ClipRRect(
                        borderRadius: BorderRadius.circular(24),
                        child: Image.memory(
                          _imageBytes!,
                          fit: BoxFit.cover,
                        ),
                      ),
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Container(
                  width: double.infinity,
                  padding: const EdgeInsets.all(16),
                  decoration: BoxDecoration(
                    color: cardBg,
                    borderRadius: BorderRadius.circular(20),
                    boxShadow: [
                      BoxShadow(
                        blurRadius: 14,
                        offset: const Offset(0, 6),
                        color: Colors.black.withOpacity(0.10),
                      ),
                    ],
                  ),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Result',
                        style: TextStyle(
                          color: secondaryText,
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _result,
                        style: TextStyle(
                          color: primaryText,
                          fontSize: 15,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                      const SizedBox(height: 6),
                    ],
                  ),
                ),
                const SizedBox(height: 14),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    style: ElevatedButton.styleFrom(
                      backgroundColor: isDarkMode
                          ? const Color(0xFF0F172A)
                          : const Color(0xFFE0EDFF),
                      foregroundColor: const Color(0xFF1F8BFF),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                      ),
                      elevation: 0,
                    ),
                    icon: const Icon(Icons.photo),
                    label: Text(
                      _loading ? 'Analyzing...' : 'Upload scanned image',
                    ),
                    onPressed: _loading ? null : _pickImage,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }
}
