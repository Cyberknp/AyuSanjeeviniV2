# Technology Stack

## Languages

### Primary Language
- **Dart**: Flutter application development
  - Version: ^3.10.0 (specified in pubspec.yaml)
  - Usage: Complete application logic, UI, and state management

### Secondary Languages
- **Python**: ML training and data processing
  - Usage: Model training pipeline in `Models/` directory
  - Libraries: PIL, matplotlib, numpy

## Frameworks

### Mobile Framework
- **Flutter**: Cross-platform UI framework
  - Version: 3.10+
  - Features: Material Design 3, hot reload, cross-platform compilation
  - Platforms: Android, iOS, Web, Desktop (Linux, macOS, Windows)

### UI Framework
- **Material Design 3**: Google's design system
  - Implementation: Flutter Material widgets
  - Features: Dark/light theme support, adaptive UI

## Machine Learning

### Inference Engine
- **TensorFlow Lite**: On-device ML inference
  - Package: `tflite_flutter: ^0.12.1`
  - Features: Multi-threading, model quantization support
  - Models: 3 specialized medical classification models

### Image Processing
- **Image Package**: `image: ^4.1.7`
  - Features: Image decoding, resizing, format conversion
  - Usage: Preprocessing for ML models

## Networking

### HTTP Client
- **HTTP Package**: `http: ^1.2.0`
  - Usage: Google Sheets API integration
  - Features: GET requests, response handling

## Media Handling

### Image Capture
- **Image Picker**: `image_picker: ^1.1.0`
  - Features: Camera and gallery access
  - Platforms: Android, iOS, Web

## Development Tools

### Code Quality
- **Flutter Lints**: `flutter_lints: ^6.0.0`
  - Purpose: Static analysis and code quality enforcement
  - Configuration: `analysis_options.yaml`

### Testing
- **Flutter Test**: Built-in testing framework
  - Current State: Minimal placeholder tests
  - Coverage: <1% of codebase

## Databases

### Persistent Storage
- **None Identified**: No database dependencies found
- **Data Storage**: In-memory state management only
- **External Data**: Google Sheets as data source

## Runtime Environment

### Supported Platforms
- **Android**: Native Android application
- **iOS**: Native iOS application  
- **Web**: Browser-based deployment
- **Desktop**: Linux, macOS, Windows support

### System Requirements
- **Flutter SDK**: 3.10+
- **Dart SDK**: Compatible with Flutter version
- **Device Requirements**: Camera access, internet connectivity

## Infrastructure Assumptions

### External Dependencies
- **Google Sheets**: Publicly accessible spreadsheet
- **Internet Connection**: Required for health data fetching
- **Device Storage**: For model files and temporary images

### Deployment Targets
- **App Stores**: Google Play Store, Apple App Store
- **Web Hosting**: Static web hosting for web deployment
- **Desktop Distribution**: Platform-specific installers

## Version Management

### Dependency Locking
- **pubspec.lock`: Contains exact dependency versions
- **Model Versions**: [Unverified – requires repository inspection] No version tracking for ML models

### Build Configuration
- **Flutter Build**: Platform-specific compilation
- **Asset Bundling**: TensorFlow Lite models included in app bundle
