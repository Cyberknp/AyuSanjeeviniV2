import 'package:flutter/material.dart';

void main() {
  runApp(const AyuSanjeeviniApp());
}

class AyuSanjeeviniApp extends StatelessWidget {
  const AyuSanjeeviniApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'AyuSanjeevini',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(
        colorSchemeSeed: Colors.teal,
        useMaterial3: true,
      ),
      initialRoute: LoginScreen.routeName,
      routes: {
        LoginScreen.routeName: (_) => const LoginScreen(),
        FeatureHubScreen.routeName: (_) => const FeatureHubScreen(),
      },
      onGenerateRoute: (settings) {
        if (settings.name == PlaceholderModuleScreen.routeName &&
            settings.arguments is ModuleArgs) {
          final args = settings.arguments as ModuleArgs;
          return MaterialPageRoute(
            builder: (_) => PlaceholderModuleScreen(args: args),
          );
        }
        return null;
      },
    );
  }
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  static const String routeName = '/login';

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  bool _obscurePassword = true;
  bool _isSubmitting = false;

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    final isValid = _formKey.currentState?.validate() ?? false;
    if (!isValid) return;

    setState(() => _isSubmitting = true);

    // Mock auth delay for UX.
    await Future<void>.delayed(const Duration(milliseconds: 600));

    if (!mounted) return;
    setState(() => _isSubmitting = false);

    Navigator.pushReplacementNamed(context, FeatureHubScreen.routeName);
  }

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;

    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 420),
              child: Card(
                elevation: 2,
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Icon(
                          Icons.health_and_safety_rounded,
                          size: 48,
                          color: cs.primary,
                        ),
                        const SizedBox(height: 12),
                        Text(
                          'Welcome to AyuSanjeevini',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.headlineSmall,
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'Login with your credentials to continue',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.bodyMedium,
                        ),
                        const SizedBox(height: 20),
                        TextFormField(
                          controller: _emailController,
                          keyboardType: TextInputType.emailAddress,
                          autofillHints: const [AutofillHints.username],
                          decoration: const InputDecoration(
                            labelText: 'Email / Username',
                            prefixIcon: Icon(Icons.person_outline),
                            border: OutlineInputBorder(),
                          ),
                          validator: (value) {
                            final v = (value ?? '').trim();
                            if (v.isEmpty) return 'Please enter your email or username';
                            if (v.length < 3) return 'Value is too short';
                            return null;
                          },
                        ),
                        const SizedBox(height: 14),
                        TextFormField(
                          controller: _passwordController,
                          obscureText: _obscurePassword,
                          autofillHints: const [AutofillHints.password],
                          decoration: InputDecoration(
                            labelText: 'Password',
                            prefixIcon: const Icon(Icons.lock_outline),
                            border: const OutlineInputBorder(),
                            suffixIcon: IconButton(
                              onPressed: () {
                                setState(() => _obscurePassword = !_obscurePassword);
                              },
                              icon: Icon(
                                _obscurePassword
                                    ? Icons.visibility_off_outlined
                                    : Icons.visibility_outlined,
                              ),
                            ),
                          ),
                          validator: (value) {
                            final v = value ?? '';
                            if (v.isEmpty) return 'Please enter your password';
                            if (v.length < 6) return 'Password must be at least 6 characters';
                            return null;
                          },
                        ),
                        const SizedBox(height: 18),
                        FilledButton.icon(
                          onPressed: _isSubmitting ? null : _handleLogin,
                          icon: _isSubmitting
                              ? const SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(strokeWidth: 2),
                                )
                              : const Icon(Icons.login_rounded),
                          label: Text(_isSubmitting ? 'Signing in...' : 'Login'),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          'Note: Authentication is UI-only for now.',
                          textAlign: TextAlign.center,
                          style: Theme.of(context).textTheme.bodySmall?.copyWith(
                                color: cs.outline,
                              ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class FeatureHubScreen extends StatelessWidget {
  const FeatureHubScreen({super.key});

  static const String routeName = '/feature-hub';

  @override
  Widget build(BuildContext context) {
    final features = <_FeatureCardData>[
      const _FeatureCardData(
        title: 'Mental Health Bot',
        subtitle: 'Chat-based support and guidance',
        icon: Icons.psychology_alt_outlined,
        color: Colors.deepPurple,
      ),
      const _FeatureCardData(
        title: 'Disease Detection',
        subtitle: 'Upload image and view AI screening result',
        icon: Icons.medical_information_outlined,
        color: Colors.teal,
      ),
      const _FeatureCardData(
        title: 'Heart Health Dashboard',
        subtitle: 'Track vitals, trends, and lifestyle metrics',
        icon: Icons.favorite_border,
        color: Colors.redAccent,
      ),
    ];

    return Scaffold(
      appBar: AppBar(
        title: const Text('Choose a Feature'),
        actions: [
          IconButton(
            tooltip: 'Logout',
            onPressed: () {
              Navigator.pushNamedAndRemoveUntil(
                context,
                LoginScreen.routeName,
                (route) => false,
              );
            },
            icon: const Icon(Icons.logout_rounded),
          ),
        ],
      ),
      body: SafeArea(
        child: ListView.separated(
          padding: const EdgeInsets.all(16),
          itemCount: features.length,
          separatorBuilder: (_, __) => const SizedBox(height: 12),
          itemBuilder: (context, index) {
            final item = features[index];
            return _FeatureCard(
              data: item,
              onTap: () {
                Navigator.pushNamed(
                  context,
                  PlaceholderModuleScreen.routeName,
                  arguments: ModuleArgs(
                    title: item.title,
                    subtitle: item.subtitle,
                  ),
                );
              },
            );
          },
        ),
      ),
    );
  }
}

class _FeatureCardData {
  final String title;
  final String subtitle;
  final IconData icon;
  final Color color;

  const _FeatureCardData({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.color,
  });
}

class _FeatureCard extends StatelessWidget {
  final _FeatureCardData data;
  final VoidCallback onTap;

  const _FeatureCard({
    required this.data,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final cs = Theme.of(context).colorScheme;
    return InkWell(
      borderRadius: BorderRadius.circular(16),
      onTap: onTap,
      child: Ink(
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(16),
          color: cs.surfaceContainerHighest.withValues(alpha: 0.4),
          border: Border.all(color: cs.outlineVariant),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              CircleAvatar(
                radius: 24,
                backgroundColor: data.color.withValues(alpha: 0.15),
                child: Icon(data.icon, color: data.color),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      data.title,
                      style: Theme.of(context).textTheme.titleMedium?.copyWith(
                            fontWeight: FontWeight.w700,
                          ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      data.subtitle,
                      style: Theme.of(context).textTheme.bodyMedium,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 8),
              const Icon(Icons.arrow_forward_ios_rounded, size: 18),
            ],
          ),
        ),
      ),
    );
  }
}

class ModuleArgs {
  final String title;
  final String subtitle;

  const ModuleArgs({
    required this.title,
    required this.subtitle,
  });
}

class PlaceholderModuleScreen extends StatelessWidget {
  const PlaceholderModuleScreen({
    super.key,
    required this.args,
  });

  static const String routeName = '/module-placeholder';
  final ModuleArgs args;

  @override
  Widget build(BuildContext context) {
    final isDiseaseDetection =
        args.title.toLowerCase().contains('disease detection');

    return Scaffold(
      appBar: AppBar(
        title: Text(args.title),
      ),
      body: Center(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Card(
            child: Padding(
              padding: const EdgeInsets.all(22),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(
                    isDiseaseDetection
                        ? Icons.info_outline_rounded
                        : Icons.construction_rounded,
                    size: 46,
                    color: Theme.of(context).colorScheme.primary,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    args.title,
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.headlineSmall,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    args.subtitle,
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 14),
                  Text(
                    isDiseaseDetection
                        ? 'Disease detection model integration is intentionally not connected yet.'
                        : 'This module UI is ready. Backend/business integration can be added next.',
                    textAlign: TextAlign.center,
                    style: Theme.of(context).textTheme.bodyMedium,
                  ),
                  const SizedBox(height: 18),
                  FilledButton.icon(
                    onPressed: () => Navigator.pop(context),
                    icon: const Icon(Icons.arrow_back_rounded),
                    label: const Text('Back to Feature Hub'),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
