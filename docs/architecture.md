# System Architecture

## Architectural Style

AyuSanjeeviniV2 follows a **mobile monolith** pattern with on-device inference capabilities. The application is structured as a single Flutter application with embedded TensorFlow Lite models for medical image analysis.

## ASCII Architecture Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Flutter App                          │
├─────────────────────────────────────────────────────────┤
│  UI Layer (Material Design 3)                          │
│  ├── HomeVitalsPage (Health monitoring)                │
│  └── ScanLandingPage (ML analysis)                     │
├─────────────────────────────────────────────────────────┤
│  Business Logic                                        │
│  ├── Health data fetching (HTTP)                       │
│  ├── Image processing                                   │
│  └── ML inference orchestration                        │
├─────────────────────────────────────────────────────────┤
│  ML Inference Layer                                    │
│  ├── Router model (skin_vs_teeth.tflite)               │
│  ├── Skin analysis model (skin_model.tflite)           │
│  └── Dental analysis model (best_dental_model.tflite)  │
├─────────────────────────────────────────────────────────┤
│  External Integration                                  │
│  └── Google Sheets API (health vitals)                 │
└─────────────────────────────────────────────────────────┘
```

## Component Interaction

### Health Monitoring Flow
1. **Timer Initiation**: Every 3 seconds, `HomeVitalsPage` triggers data fetch
2. **HTTP Request**: GET request to Google Sheets CSV export endpoint
3. **Data Parsing**: CSV response parsed into `HealthData` object
4. **Threshold Validation**: Heart rate (50-120 BPM) and temperature checks
5. **Alert System**: Modal dialogs for out-of-range values

### ML Analysis Flow
1. **Image Capture**: User selects image via `image_picker`
2. **Router Inference**: `skin_vs_teeth.tflite` determines analysis type
3. **Specialized Analysis**: Either `skin_model.tflite` or `best_dental_model.tflite`
4. **Result Display**: Classification results with confidence scores

## Data Flow

```
User Input → Image Picker → Preprocessing → TF Lite Inference → Results → UI Display
     ↓
Health Monitoring → HTTP Polling → CSV Parsing → Validation → Alerts
```

## Trust Boundaries

- **Trusted Zone**: On-device ML models, Flutter application code
- **Untrusted Zone**: External Google Sheets data, user-provided images
- **Validation Points**: HTTP response handling, image format validation

## Design Patterns

- **StatefulWidget**: For dynamic UI components with lifecycle management
- **Async/Await**: For network operations and ML inference
- **Singleton Pattern**: [Unverified – requires repository inspection] Model loading
- **Observer Pattern**: Timer-based health monitoring updates

## Architectural Decisions

### Single File Architecture
The entire application is implemented in `lib/main.dart` (1467 lines), representing a monolithic design choice that prioritizes simplicity over maintainability.

### On-Device Inference
All ML processing occurs locally using TensorFlow Lite, eliminating cloud dependencies and ensuring privacy.

### External Data Source
Health vitals are sourced from a publicly accessible Google Sheet, representing a lightweight backend solution.
