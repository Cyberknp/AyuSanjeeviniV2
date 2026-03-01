# Repository Structure

## Directory Breakdown

```
AyuSanjeeviniV2/
├── lib/
│   └── main.dart (1467 lines) - Complete application source
├── assets/
│   └── models/ - TensorFlow Lite model files
│       ├── skin_model.tflite (Medical skin analysis)
│       ├── best_dental_model.tflite (Dental analysis)
│       └── skin_vs_teeth.tflite (Routing classifier)
├── Models/ - ML training and data processing (Python)
│   ├── augmentations.py (737 lines) - Data augmentation pipeline
│   ├── preprocessing.py (559 lines) - Data preprocessing utilities
│   ├── data_cleaning.py - Dataset cleaning operations
│   └── Tooth_dataset_augmented/ - Augmented training dataset
├── android/ - Android platform configuration
├── ios/ - iOS platform configuration  
├── web/ - Web platform configuration
├── linux/ - Linux desktop configuration
├── macos/ - macOS desktop configuration
├── windows/ - Windows desktop configuration
├── test/
│   └── widget_test.dart (31 lines) - Placeholder Flutter test
├── pubspec.yaml - Flutter dependencies and configuration
├── pubspec.lock - Locked dependency versions
├── analysis_options.yaml - Dart linting rules
└── .gitignore - Version control exclusions
```

## Module Responsibilities

### Core Application (`lib/main.dart`)
- **UI Components**: Splash screen, navigation, health dashboard, scan interface
- **Business Logic**: Health data fetching, ML inference orchestration, alert management
- **State Management**: StatefulWidget pattern with setState updates

### ML Models (`assets/models/`)
- **skin_vs_teeth.tflite**: Binary classifier for routing to appropriate analysis model
- **skin_model.tflite**: Multi-class skin condition classifier
- **best_dental_model.tflite**: Multi-class dental condition classifier

### Training Pipeline (`Models/`)
- **Data Preparation**: Augmentation, cleaning, and preprocessing utilities
- **Dataset Management**: Organized training data structure
- **Model Training**: [Unverified – requires repository inspection] Training scripts

### Platform Configurations
- **android/**: Android-specific build configuration and permissions
- **ios/**: iOS-specific build configuration and permissions
- **web/**: Web deployment configuration
- **desktop/**: Cross-platform desktop configurations

## Entry Points

### Primary Entry Point
- **File**: `lib/main.dart`
- **Function**: `main()` → `runApp(MajorProjectApp())`

### Model Loading Entry Points
- **Router Model**: `assets/models/skin_vs_teeth.tflite`
- **Skin Model**: `assets/models/skin_model.tflite`
- **Dental Model**: `assets/models/best_dental_model.tflite`

### External Data Entry Point
- **Health Data**: Google Sheets CSV export URL
- **URL**: `https://docs.google.com/spreadsheets/d/1rz_Mj739pGbK65mFIJnSD6b4XoRkotpUTGRbVjRtzFg/export?format=csv&gid=0`

## Configuration Files

### pubspec.yaml
- **Flutter SDK**: ^3.10.0
- **Dependencies**: tflite_flutter, image_picker, http, image, cupertino_icons
- **Assets**: Three TensorFlow Lite model files

### analysis_options.yaml
- **Linting**: Flutter recommended lints
- **Rules**: Default Flutter linting configuration
