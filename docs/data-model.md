# Data Model

## Database Schema

### Persistent Storage
- **Database**: None identified
- **Storage Type**: In-memory state management only
- **Data Persistence**: No persistent data storage implemented

### External Data Source
- **Google Sheets**: Public spreadsheet as health data source
- **Format**: CSV export via HTTP GET request
- **Update Frequency**: Real-time polling every 3 seconds

## Key Entities

### HealthData Class
**Purpose**: Container for health monitoring metrics

**Properties**:
- `steps`: Step count (integer)
- `heartRate`: Heart rate in BPM (integer)
- `temperature`: Body temperature (double) [Unverified – requires repository inspection]
- `calories`: Estimated calories burned (double)
- `error`: Error message string (nullable)

**Data Source**: Google Sheets CSV parsing
**Validation**: Basic range checking for vital signs

### Image Analysis Results
**Purpose**: ML model classification output

**Properties**:
- `classification`: Predicted class label (string)
- `confidence`: Confidence score (float, 0.0-1.0)
- `modelType`: Which model generated result (skin/dental)

**Data Source**: TensorFlow Lite inference
**Validation**: Argmax selection from output tensor

### User Preferences
**Purpose**: UI and application settings

**Properties**:
- `isDarkTheme`: Boolean for theme selection
- `alertEnabled`: [Unverified – requires repository inspection] Alert preferences

**Data Source**: Widget state management
**Persistence**: Not persisted across app restarts

## Relationships

### Entity Relationships
- **No Relationships Identified**: Flat data structure
- **Independent Entities**: HealthData and analysis results are separate
- **No Foreign Keys**: No relational data structure

### Data Flow Relationships
```
Google Sheets → HTTP Request → CSV Parsing → HealthData Object
User Image → Image Picker → Preprocessing → ML Model → Analysis Result
```

## Storage Patterns

### In-Memory Storage
- **State Management**: StatefulWidget state variables
- **Lifecycle**: Data lost on app restart
- **Scope**: Component-level data isolation

### Temporary Storage
- **Image Processing**: In-memory image byte arrays
- **Model Outputs**: Temporary tensor results
- **Network Responses**: HTTP response data

### Asset Storage
- **ML Models**: Read-only access to bundled TensorFlow Lite models
- **Static Assets**: Application icons and images
- **Configuration**: Hardcoded URLs and settings

## Data Validation

### Input Validation
- **Image Formats**: Basic format validation by image picker
- **HTTP Responses**: Status code checking (200 expected)
- **Model Inputs**: Tensor shape validation by TensorFlow Lite

### Output Validation
- **Health Data**: Range checking for vital signs
- **ML Results**: Confidence score validation (0.0-1.0 range)
- **User Input**: [Unverified – requires repository inspection] Minimal input validation

## Data Integrity

### External Data Integrity
- **Google Sheets**: No authentication or validation of data source
- **Network Data**: No checksum or integrity verification
- **Model Files**: Asset integrity verified by Flutter build system

### Internal Data Integrity
- **Type Safety**: Dart static typing provides compile-time safety
- **Null Safety**: [Unverified – requires repository inspection] Modern Dart null safety features
- **Range Validation**: Basic bounds checking for numeric values

## Data Lifecycle

### Creation
- **Health Data**: Created during HTTP response parsing
- **Analysis Results**: Created during ML inference
- **User Preferences**: Created during UI interactions

### Usage
- **Display**: Data shown in UI components
- **Validation**: Data checked against thresholds
- **Processing**: Data used for calculations and alerts

### Destruction
- **Automatic**: Data lost when widget is disposed
- **Manual**: No explicit data cleanup implemented
- **Memory**: Garbage collection handles unused objects
