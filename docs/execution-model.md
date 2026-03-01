# Execution Model

## Build Process

### Flutter Build System
- **Command**: `flutter build <platform>`
- **Platforms Supported**: 
  - `flutter build apk` - Android
  - `flutter build ios` - iOS
  - `flutter build web` - Web
  - `flutter build linux` - Linux desktop
  - `flutter build macos` - macOS desktop
  - `flutter build windows` - Windows desktop

### Asset Processing
- **Model Bundling**: TensorFlow Lite models included in app assets
- **Asset Declaration**: Models specified in `pubspec.yaml` under assets section
- **Compression**: [Unverified – requires repository inspection] Default Flutter asset compression

### Dependency Resolution
- **Package Manager**: Flutter pub
- **Lock File**: `pubspec.lock` ensures reproducible builds
- **Source**: pub.dev for Dart packages

## Runtime Process

### Application Lifecycle
1. **Initialization**: `main()` function executes
2. **Widget Tree**: `MajorProjectApp` creates root widget
3. **Splash Screen**: 5-second animated splash display
4. **Main Interface**: Navigation between health monitoring and scan analysis

### State Management
- **Pattern**: StatefulWidget with setState()
- **State Scope**: Component-level state management
- **Persistence**: No persistent state storage

### Concurrency Model
- **Async Operations**: HTTP requests and ML inference
- **Timer-based Updates**: Health monitoring every 3 seconds
- **Multi-threading**: TensorFlow Lite uses 4 threads for inference
- **UI Thread**: Main thread handles UI updates

## Deployment Model

### Mobile Deployment
- **Android**: APK/AAB distribution via Google Play Store
- **iOS**: IPA distribution via Apple App Store
- **Permissions**: Camera, internet access required

### Web Deployment
- **Target**: Static web assets
- **Hosting**: Any static web server
- **Limitations**: [Unverified – requires repository inspection] Camera access restrictions

### Desktop Deployment
- **Linux**: [Unverified – requires repository inspection] Executable distribution
- **macOS**: [Unverified – requires repository inspection] .app bundle distribution
- **Windows**: [Unverified – requires repository inspection] .exe distribution

## Environment Variables

### Configuration Management
- **Environment Variables**: None identified in codebase
- **Hardcoded Values**: Google Sheets URL, model paths
- **Configuration**: Static values in source code

### Runtime Configuration
- **Model Paths**: Asset-based loading (`assets/models/`)
- **API Endpoints**: Hardcoded Google Sheets URL
- **Thread Configuration**: Fixed 4 threads for TF Lite

## Configuration Handling

### Static Configuration
- **Theme**: Dark/light mode toggle in UI
- **Polling Interval**: Fixed 3-second health data refresh
- **Alert Thresholds**: Hardcoded vital sign ranges

### Dynamic Configuration
- **User Preferences**: Theme selection stored in widget state
- **Model Loading**: On-demand model initialization
- **Image Selection**: User-chosen images for analysis

## Error Handling

### Network Errors
- **HTTP Failures**: Basic error messages displayed to user
- **Timeout Handling**: [Unverified – requires repository inspection] Default HTTP timeouts
- **Offline Mode**: No offline functionality implemented

### Model Errors
- **Loading Failures**: Error messages shown to user
- **Inference Failures**: Basic exception handling
- **Memory Issues**: [Unverified – requires repository inspection] No proactive memory management

## Performance Considerations

### Startup Performance
- **Model Loading**: Lazy loading of TensorFlow Lite models
- **Splash Screen**: 5-second delay for perceived performance
- **Asset Loading**: Models bundled with app reduce load time

### Runtime Performance
- **Inference Speed**: Multi-threaded TensorFlow Lite execution
- **Memory Usage**: Models kept in memory after loading
- **UI Responsiveness**: Async operations prevent UI blocking
