# API Documentation

## Base URL

```
http://localhost:8000
```

## Endpoints

### Health Checks

#### GET /health

Liveness probe - indicates service is running.

**Response**:
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

#### GET /ready

Readiness probe - indicates service is ready to serve traffic.

Checks database connectivity and table existence.

**Response**:
```json
{
  "status": "ready",
  "timestamp": "2024-01-01T00:00:00Z",
  "database": "connected",
  "tables_exist": true,
  "connected": true
}
```

**Response when not ready**:
```json
{
  "status": "not_ready",
  "timestamp": "2024-01-01T00:00:00Z",
  "database": "disconnected",
  "tables_exist": false,
  "connected": false
}
```

#### POST /init

Initialize database by creating tables.

Creates all database tables if they don't exist.

**Response**:
```json
{
  "status": "success",
  "message": "Database tables created successfully",
  "tables_created": true
}
```

**Response if tables already exist**:
```json
{
  "status": "success",
  "message": "Database tables already exist",
  "tables_created": false
}
```

### Frame Endpoints

#### GET /frames

Get image frames as JSON array.

**Query Parameters**:
- `depth_min` (required): Minimum depth value (decimal)
- `depth_max` (required): Maximum depth value (decimal)
- `colormap` (optional): Colormap name (default: "viridis")
  - Options: `viridis`, `plasma`, `inferno`, `magma`, `hot`, `cool`, `gray`, `jet`, `turbo`, `rainbow`
- `limit` (optional): Maximum number of frames (1-10000)

**Example Request**:
```bash
curl "http://localhost:8000/frames?depth_min=9000&depth_max=9100&colormap=viridis&limit=10"
```

**Response**:
```json
[
  {
    "depth": 9000.1,
    "data": "base64_encoded_rgb_data",
    "metadata": {
      "min": 0.0,
      "max": 255.0,
      "mean": 128.5,
      "std": 50.2,
      "compression_ratio_original": 4.8,
      "compression_ratio_resized": 3.9
    }
  },
  ...
]
```

### Root Endpoint

#### GET /

API information.

**Response**:
```json
{
  "name": "Image Frame API",
  "version": "0.1.0",
  "docs": "/swagger",
  "health": "/health",
  "ready": "/ready"
}
```

## Error Responses

### 400 Bad Request

Invalid query parameters.

```json
{
  "detail": "depth_min must be less than or equal to depth_max"
}
```

### 422 Unprocessable Entity

Missing required parameters.

```json
{
  "detail": [
    {
      "loc": ["query", "depth_min"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}
```

### 500 Internal Server Error

Server error.

```json
{
  "detail": "Internal server error"
}
```

## Data Format

### Frame Response

- `depth`: Float value representing depth
- `data`: Base64-encoded RGB image data
  - Shape: (1, 150, 3) - single row, 150 pixels, RGB channels
  - Decode: `base64.b64decode(data)` → bytes → reshape to (1, 150, 3)
- `metadata`: Frame statistics
  - `min`: Minimum pixel value
  - `max`: Maximum pixel value
  - `mean`: Mean pixel value
  - `std`: Standard deviation
  - `compression_ratio_original`: Compression ratio for original data
  - `compression_ratio_resized`: Compression ratio for resized data

## Colormaps

Available colormaps (matplotlib):

- `viridis`: Perceptually uniform, colorblind-friendly
- `plasma`: High contrast, colorblind-friendly
- `inferno`: Dark background, high contrast
- `magma`: Dark background, smooth transitions
- `hot`: Black-red-yellow-white
- `cool`: Cyan-magenta
- `gray`: Grayscale
- `jet`: Classic rainbow (not recommended)
- `turbo`: Improved rainbow
- `rainbow`: Full spectrum

## Examples

### Python

```python
import requests
import base64
import numpy as np

# Get frames
response = requests.get(
    "http://localhost:8000/frames",
    params={
        "depth_min": 9000,
        "depth_max": 9100,
        "colormap": "viridis",
        "limit": 10
    }
)

frames = response.json()
for frame in frames:
    # Decode base64 data
    rgb_bytes = base64.b64decode(frame["data"])
    rgb_array = np.frombuffer(rgb_bytes, dtype=np.uint8)
    rgb_array = rgb_array.reshape(1, 150, 3)
    
    print(f"Depth: {frame['depth']}, Shape: {rgb_array.shape}")
```

### JavaScript

```javascript
// Get frames
const response = await fetch(
  'http://localhost:8000/frames?depth_min=9000&depth_max=9100&colormap=viridis'
);

const frames = await response.json();
frames.forEach(frame => {
  console.log(`Depth: ${frame.depth}`);
});
```

### cURL

```bash
curl "http://localhost:8000/frames?depth_min=9000&depth_max=9100&colormap=viridis"
```

## Performance Notes

- **Latency**: ~420ms total latency for 100 frames
- **Memory**: Memory usage scales with response size
- **Concurrent Requests**: Supports multiple concurrent requests with connection pooling

## Rate Limiting

Currently not implemented. Add rate limiting for production use.

## Authentication

Currently not implemented. Add authentication for production use.

