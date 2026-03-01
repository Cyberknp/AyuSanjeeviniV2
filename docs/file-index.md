# File-Level Index

## Core Application Files

### lib/main.dart (1467 lines)
**Purpose**: Complete Flutter application containing all functionality
**Key Components**:
- `MajorProjectApp`: Root application widget with theme management
- `SplashScreen`: Animated 5-second splash screen with logo and text
- `MainShell`: Navigation shell with theme toggle
- `HomeVitalsPage`: Health monitoring dashboard with real-time data
- `ScanLandingPage`: Medical image analysis interface
**Responsibilities**:
- UI rendering and user interactions
- Health data fetching from Google Sheets
- TensorFlow Lite model loading and inference
- Image processing and classification
- Alert system for abnormal vitals
**Dependencies**: Flutter framework, TensorFlow Lite, HTTP client, image picker
**Risk Points**: Monolithic structure, mixed concerns, high coupling

## Configuration Files

### pubspec.yaml (41 lines)
**Purpose**: Flutter project configuration and dependency management
**Key Sections**:
- Flutter SDK requirement: ^3.10.0
- Dependencies: tflite_flutter, image_picker, http, image, cupertino_icons
- Asset declarations for TensorFlow Lite models
- Development dependencies: flutter_test, flutter_lints
**Responsibilities**: Package management, build configuration, asset bundling
**Dependencies**: Flutter SDK, pub.dev package repository

### pubspec.lock (13,124 lines)
**Purpose**: Locked dependency versions for reproducible builds
**Key Information**: Exact versions of all transitive dependencies
**Responsibilities**: Build reproducibility, dependency resolution
**Dependencies**: Generated from pubspec.yaml

### analysis_options.yaml (29 lines)
**Purpose**: Dart static analysis and linting configuration
**Key Settings**:
- Includes Flutter recommended lints
- Configures analysis rules
- Sets up code quality enforcement
**Responsibilities**: Code quality, static analysis, linting rules
**Dependencies**: Flutter analysis tools

### .gitignore (425 lines)
**Purpose**: Version control exclusions for repository cleanliness
**Key Exclusions**:
- Flutter build artifacts and cache
- Python virtual environments and cache
- Dataset files and ML models
- IDE configuration files
- Credentials and sensitive data
**Responsibilities**: Repository hygiene, security, build artifact management
**Dependencies**: Git version control

## ML Model Files

### assets/models/skin_model.tflite
**Purpose**: TensorFlow Lite model for skin condition analysis
**Size**: [Unverified – requires repository inspection] Model file size
**Function**: Multi-class classification of skin conditions
**Input**: Preprocessed skin images
**Output**: Classification probabilities for skin conditions
**Dependencies**: TensorFlow Lite runtime

### assets/models/best_dental_model.tflite
**Purpose**: TensorFlow Lite model for dental condition analysis
**Size**: [Unverified – requires repository inspection] Model file size
**Function**: Multi-class classification of dental conditions
**Input**: Preprocessed dental images
**Output**: Classification probabilities for dental conditions
**Dependencies**: TensorFlow Lite runtime

### assets/models/skin_vs_teeth.tflite
**Purpose**: TensorFlow Lite routing model for image classification
**Size**: [Unverified – requires repository inspection] Model file size
**Function**: Binary classifier determining skin vs dental analysis route
**Input**: Preprocessed medical images
**Output**: Routing decision (skin or dental)
**Dependencies**: TensorFlow Lite runtime

## ML Training Pipeline Files

### Models/augmentations.py (737 lines)
**Purpose**: Data augmentation pipeline for ML model training
**Key Functions**:
- Dataset path resolution with environment variable support
- Image augmentation techniques (rotation, flip, color adjustments)
- Data visualization and analysis
- Output generation for augmented datasets
**Responsibilities**: Training data preparation, data diversity enhancement
**Dependencies**: Python, PIL, matplotlib, numpy
**Risk Points**: Hardcoded paths, environment variable dependencies

### Models/preprocessing.py (559 lines)
**Purpose**: Data preprocessing utilities for ML model training
**Key Functions**:
- Dataset path resolution and validation
- Image preprocessing and normalization
- Data analysis and statistics
- Output directory management
**Responsibilities**: Data cleaning, normalization, format standardization
**Dependencies**: Python, PIL, matplotlib, numpy
**Risk Points**: Similar path resolution logic as augmentations.py

### Models/data_cleaning.py (7,494 lines)
**Purpose**: Dataset cleaning and preparation utilities
**Key Functions**: [Unverified – requires repository inspection] Large file suggests comprehensive cleaning operations
**Responsibilities**: Data quality improvement, outlier removal, format standardization
**Dependencies**: Python, data processing libraries
**Risk Points**: Large file size may indicate complex or inefficient operations

### Models/Tooth_dataset_augmented/
**Purpose**: Augmented training dataset for dental model
**Contents**: [Unverified – requires repository inspection] Augmented tooth images
**Size**: 909 items (large dataset)
**Responsibilities**: Training data for dental analysis model
**Dependencies**: File system, image processing utilities
**Risk Points**: Large dataset may impact repository size and clone times

## Platform Configuration Files

### android/
**Purpose**: Android platform configuration and build files
**Key Components**:
- AndroidManifest.xml: App permissions and configuration
- build.gradle: Android build configuration
- gradle.properties: Build properties
- app/: Application-specific Android configuration
**Responsibilities**: Android app compilation, permissions, deployment
**Dependencies**: Android SDK, Gradle build system

### ios/
**Purpose**: iOS platform configuration and build files
**Key Components**:
- Info.plist: iOS app configuration
- Runner.xcodeproj: Xcode project configuration
- AppDelegate.swift: iOS app lifecycle management
**Responsibilities**: iOS app compilation, permissions, deployment
**Dependencies**: Xcode, iOS SDK

### web/
**Purpose**: Web platform configuration
**Key Components**: [Unverified – requires repository inspection] Web-specific configuration
**Responsibilities**: Web app compilation and deployment
**Dependencies**: Web build tools, browsers

### linux/, macos/, windows/
**Purpose**: Desktop platform configurations
**Key Components**: [Unverified – requires repository inspection] Platform-specific build files
**Responsibilities**: Desktop app compilation and deployment
**Dependencies**: Platform-specific SDKs and build tools

## Testing Files

### test/widget_test.dart (31 lines)
**Purpose**: Placeholder Flutter widget test
**Key Content**: Basic counter test template (not application-specific)
**Responsibilities**: Testing framework setup and example
**Dependencies**: Flutter test framework
**Risk Points**: Does not test actual application functionality

## Documentation Files

### README.md (292 lines)
**Purpose**: Project overview and setup instructions
**Key Sections**:
- Project description and features
- Technology stack overview
- Installation and running instructions
- Project structure explanation
- Contributing guidelines
**Responsibilities**: Project introduction, developer onboarding
**Dependencies**: Markdown rendering

### docs/ (Directory)
**Purpose**: Comprehensive technical documentation
**Contents**: 15 markdown files covering all aspects of the project
**Responsibilities**: Technical reference, architecture documentation, developer guidance
**Dependencies**: Markdown rendering, documentation hosting

## Asset Files

### assets/ (Directory)
**Purpose**: Static assets bundled with application
**Contents**:
- models/: TensorFlow Lite model files
- [Unverified – requires repository inspection] Other assets (images, icons)
**Responsibilities**: Resource management, static content delivery
**Dependencies**: Flutter asset bundling system

## Metadata Files

### .metadata (1,706 bytes)
**Purpose**: Flutter project metadata
**Content**: [Unverified – requires repository inspection] Project configuration metadata
**Responsibilities**: Project identification, tooling configuration
**Dependencies**: Flutter development tools

## File Organization Analysis

### Critical Files
- **lib/main.dart**: Core application logic (high priority)
- **assets/models/*.tflite**: ML models (high priority)
- **pubspec.yaml**: Dependency management (high priority)
- **Models/*.py**: Training pipeline (medium priority)

### Configuration Files
- **analysis_options.yaml**: Code quality configuration
- **.gitignore**: Repository management
- **Platform configs**: Deployment configuration

### Documentation Files
- **README.md**: Project overview
- **docs/**: Comprehensive technical documentation
- **Code comments**: [Unverified – requires repository inspection] Inline documentation

### Risk Assessment by File
- **High Risk**: main.dart (monolithic, complex), large Python files
- **Medium Risk**: Configuration files, platform-specific files
- **Low Risk**: Documentation, test files, asset files

## Maintenance Considerations

### File Size Monitoring
- **Large Files**: data_cleaning.py (7,494 lines), main.dart (1,467 lines)
- **Growing Directories**: Models/Tooth_dataset_augmented/ (909 items)
- **Asset Management**: Model files may increase in size

### Dependency Management
- **Flutter Dependencies**: Managed via pubspec.yaml
- **Python Dependencies**: [Unverified – requires repository inspection] requirements.txt
- **System Dependencies**: Flutter SDK, platform SDKs

### Backup Strategy
- **Source Code**: Git repository backup
- **Models**: Version controlled in repository
- **Datasets**: [Unverified – requires repository inspection] Backup strategy needed
- **Configuration**: Documented and version controlled
