# Core Modules and Responsibilities

## HomeVitalsPage Module

### Purpose
Real-time health monitoring dashboard that displays and alerts on vital signs including heart rate, temperature, steps, and estimated calories.

### Public Interfaces
- `fetchHealthData()`: Retrieves health data from Google Sheets
- Alert dialogs for abnormal vitals
- Theme toggle functionality

### Internal Logic Summary
- **Timer-based Polling**: Executes every 3 seconds using `Timer.periodic`
- **HTTP Integration**: GET request to Google Sheets CSV export
- **Threshold Validation**: 
  - Heart rate: 50-120 BPM range
  - Temperature: [Unverified – requires repository inspection] thresholds
- **Alert Management**: Prevents alert spam with 30-second cooldown
- **Calorie Estimation**: Simple calculation (steps × 0.04 kcal)

### External Dependencies
- **Google Sheets API**: Public CSV export endpoint
- **HTTP Package**: Network communication
- **Timer**: Flutter periodic timer implementation

### Risk Points
- **Network Dependency**: Application loses functionality without internet
- **Data Format Changes**: Google Sheets structure changes break parsing
- **Alert Fatigue**: Frequent notifications may annoy users
- **Hardcoded URL**: No fallback mechanism for data source

## ScanLandingPage Module

### Purpose
Medical image analysis interface that routes images to appropriate ML models and displays classification results.

### Public Interfaces
- Image capture from gallery or camera
- ML model loading and inference
- Results display with confidence scores

### Internal Logic Summary
- **Three-Stage Pipeline**:
  1. **Router Model**: Determines if image is skin or dental related
  2. **Specialized Analysis**: Routes to appropriate model
  3. **Result Processing**: Formats and displays classification results
- **Image Preprocessing**: Resizing and normalization for model input
- **Multi-threading**: 4-thread configuration for TF Lite inference
- **Memory Management**: Proper model disposal in dispose() method

### External Dependencies
- **TensorFlow Lite**: On-device ML inference
- **Image Picker**: Device camera/gallery access
- **Image Package**: Image processing and manipulation

### Risk Points
- **Model Loading Failures**: Application crashes if models fail to load
- **Memory Constraints**: Multiple large models may exceed device memory
- **Inference Accuracy**: Model performance directly impacts user experience
- **Thread Management**: Improper thread configuration may affect performance

## ML Pipeline Module

### Purpose
Core inference engine that processes medical images through TensorFlow Lite models.

### Public Interfaces
- `_runRouterPipeline()`: Routes images to appropriate analysis model
- `_runModelA()`: Executes skin analysis model
- `_runModelB()`: Executes dental analysis model
- `_loadAllModels()`: Initializes all three TF Lite models

### Internal Logic Summary
- **Tensor Management**: Input/output tensor shape handling
- **Image Preprocessing**: Decoding, resizing, and normalization
- **Post-processing**: Argmax operations for classification results
- **Error Handling**: Basic exception catching with user feedback

### External Dependencies
- **tflite_flutter**: TensorFlow Lite runtime
- **image**: Image processing library
- **dart:typed_data`: Binary data handling

### Risk Points
- **Model Compatibility**: Tensor shape mismatches cause runtime errors
- **Memory Leaks**: Improper interpreter disposal
- **Performance**: Synchronous inference may block UI thread
- **Accuracy**: No confidence threshold filtering

## Health Data Integration Module

### Purpose
External data fetching and parsing for real-time health monitoring.

### Public Interfaces
- `fetchHealthData()`: Main data retrieval function
- `HealthData` class: Data structure for health metrics

### Internal Logic Summary
- **CSV Parsing**: Manual parsing of Google Sheets export
- **Error Handling**: Network timeout and parsing error management
- **Data Validation**: Basic range checking for vital signs

### External Dependencies
- **Google Sheets**: Public spreadsheet as data source
- **HTTP Package**: Network communication layer

### Risk Points
- **Single Point of Failure**: No backup data source
- **Public Access**: Data source accessible to anyone
- **Rate Limiting**: [Unverified – requires repository inspection] Potential API limits
- **Data Integrity**: No validation of data authenticity
