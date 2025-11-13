---
status: Active
maintainer: pacoxu
last_updated: 2025-11-13
tags: kubernetes, gpu, cold-start, optimization, ai-workloads
canonical_path: docs/kubernetes/gpu-pod-cold-start.md
---

# GPU Pod Cold Start Optimization

This guide covers strategies to minimize cold start latency for GPU-accelerated
Pods in Kubernetes, particularly for AI/ML inference workloads. Based on
KubeCon NA 2024 presentation and production implementations from cloud
providers.

## Why GPU Pod Cold Start Matters

GPU Pod cold start refers to the time from Pod creation to when it's ready to
serve inference requests with a loaded model. For AI workloads, this includes:

- Pod scheduling and creation
- Container image pulling
- GPU device initialization
- Model weight loading into GPU memory
- Model compilation and optimization
- Cache warming and readiness

**Key Challenges:**

- Large model sizes (7B-70B+ parameters, 10GB-100GB+ weights)
- GPU memory initialization overhead
- Model loading and compilation time
- User expectations for low latency
- Cost of keeping GPUs idle during cold start

**Impact on Production:**

- **Serverless AI**: Cold starts block request processing
- **Auto-scaling**: Slow cold starts reduce scaling effectiveness
- **Multi-tenancy**: Model switching creates cold start penalties
- **Cost efficiency**: Idle GPUs during cold start waste resources

## Typical GPU Pod Cold Start Times

Cold start times vary significantly based on model size and optimization:

- **10-30 seconds**: Small models (1B-7B parameters) with optimized loading
- **30-60 seconds**: Medium models (7B-13B parameters) with standard formats
- **1-3 minutes**: Large models (13B-70B parameters) with PyTorch pickle
- **3-10 minutes**: Very large models (70B+ parameters) without optimization

## Three Primary Solutions

### Solution 1: Pre-warmed GPU Pools

Pre-warming maintains a pool of GPU Pods with models already loaded in memory,
ready to serve requests immediately.

#### Architecture

```text
┌─────────────────────────────────────────────────────────────┐
│                       Load Balancer                         │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                     Request Queue                           │
└──────────────┬────────────────────┬─────────────────────────┘
               │                    │
               ▼                    ▼
┌──────────────────────┐  ┌──────────────────────┐
│   GPU 1 (warm)       │  │   GPU 2 (warm)       │
│   Model loaded       │  │   Model loaded       │
│   Ready to serve     │  │   Ready to serve     │
└──────────────────────┘  └──────────────────────┘
```

#### Key Characteristics

**Pre-warming Process:**

1. Create pool of GPU Pods during initialization
2. Load models into GPU memory
3. Warm up caches and compile kernels
4. Mark Pods as ready in load balancer
5. Route incoming requests to pre-warmed pool
6. Dynamically maintain pool size based on demand

**Benefits:**

- **Zero cold start latency** for requests hitting warm pool
- **Predictable performance** with consistent response times
- **Immediate scalability** up to pool size
- **Better resource utilization** for steady workloads

**Trade-offs:**

- **Cost overhead**: GPUs remain allocated even when idle
- **Memory waste**: Models stay in memory regardless of usage
- **Pool sizing**: Under-sizing causes cold starts, over-sizing wastes money
- **Multi-model complexity**: Each model variant requires separate pool

#### Implementation Strategies

**Static Pre-warming:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-inference-warm-pool
spec:
  replicas: 3  # Maintain 3 pre-warmed instances
  template:
    spec:
      containers:
      - name: vllm-server
        image: vllm/vllm-openai:latest
        command: ["python", "-m", "vllm.entrypoints.openai.api_server"]
        args:
        - --model=/models/llama-2-7b
        - --gpu-memory-utilization=0.95
        resources:
          limits:
            nvidia.com/gpu: 1
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 60  # Allow time for model loading
          periodSeconds: 10
```

**Dynamic Pre-warming with HPA:**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: llm-inference-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llm-inference-warm-pool
  minReplicas: 2  # Minimum warm pool size
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: gpu-utilization
      target:
        type: Utilization
        averageUtilization: 70
  - type: Pods
    pods:
      metric:
        name: inference_queue_length
      target:
        type: AverageValue
        averageValue: "5"
```

**Multi-Model Pool Management:**

For serving multiple models, implement intelligent pool allocation:

```yaml
# Model A: High traffic, large pool
apiVersion: apps/v1
kind: Deployment
metadata:
  name: model-a-warm-pool
spec:
  replicas: 5
  # ... model-a configuration

---
# Model B: Medium traffic, medium pool
apiVersion: apps/v1
kind: Deployment
metadata:
  name: model-b-warm-pool
spec:
  replicas: 2
  # ... model-b configuration

---
# Model C: Low traffic, small pool or scale-to-one
apiVersion: apps/v1
kind: Deployment
metadata:
  name: model-c-warm-pool
spec:
  replicas: 1
  # ... model-c configuration
```

#### Production Implementations

**GKE Agent Sandbox:**

Google Kubernetes Engine's Agent Sandbox combines pre-warmed pools with gVisor
snapshots:

- **Sub-second latency**: Up to 90% improvement over cold starts
- **Strong isolation**: gVisor sandbox security per instance
- **Snapshot-based**: Pre-warmed containers restored from snapshots
- **Production-ready**: Available in GKE for agentic AI workloads

**Configuration Example:**

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: agent-sandbox-pod
spec:
  runtimeClassName: gvisor  # Use gVisor for isolation
  containers:
  - name: agent-executor
    image: gcr.io/project/agent-runtime:latest
    resources:
      limits:
        nvidia.com/gpu: 1
```

**AWS Lambda GPU (in preview):**

- Pre-warmed Lambda instances with GPU access
- Automatic scaling from zero to thousands of instances
- Pay only for compute time, not idle periods

**Azure Container Instances with GPU:**

- Fast GPU-enabled container startup
- Pre-pulled images reduce cold start
- Serverless GPU instances

#### Best Practices

**Pool Sizing:**

- Monitor queue length and request latency
- Right-size pools based on traffic patterns (daily/weekly cycles)
- Maintain minimum pool for guaranteed responsiveness
- Scale up proactively before traffic spikes

**Cost Optimization:**

- Use spot/preemptible instances for non-critical pools
- Scale down pools during low-traffic periods
- Implement model sharing across requests when possible
- Monitor cost per inference and optimize pool size

**Monitoring:**

```text
Key Metrics for Pre-warmed Pools:
- Pool utilization percentage (target: 70-85%)
- Cold start frequency (requests hitting non-warm Pods)
- Average request latency (P50, P95, P99)
- GPU idle time per instance
- Cost per inference request
```

---

### Solution 2: Faster Serialization

Model serialization format dramatically impacts loading time. Different formats
have different load times due to deserialization overhead, memory copying, and
initialization requirements.

#### Serialization Format Comparison

Based on production benchmarks for loading a 7B parameter LLM:

| Format         | Load Time | Speed Rating | Notes                    |
|----------------|-----------|--------------|--------------------------|
| PyTorch pickle | 12s       | Slow         | Legacy format, insecure  |
| TorchScript    | 7s        | Better       | Optimized for inference  |
| Safetensors    | 5s        | Good         | Safe, fast, recommended  |
| ONNX           | 4s        | Fastest      | Cross-platform, optimized|

**Relative Performance:**

```text
PyTorch pickle: ██████████████████████████ 12s (slowest)
TorchScript:    ██████████████████ 7s
Safetensors:    ████████████ 5s
ONNX:           ██████████ 4s (fastest)
```

#### Format Characteristics

**PyTorch Pickle (.bin, .pt files):**

- **Load Time**: ~12 seconds for 7B model
- **Security**: Vulnerable to arbitrary code execution
- **Compatibility**: Native PyTorch format
- **Use Case**: Legacy models, development only

**Disadvantages:**

- Slowest loading due to Python pickle deserialization
- Security risk from untrusted model files
- Inefficient memory copying
- No memory mapping support

**TorchScript (.pt, .pth files):**

- **Load Time**: ~7 seconds for 7B model
- **Security**: Safer than pickle, but still PyTorch-dependent
- **Compatibility**: PyTorch inference optimization
- **Use Case**: Production PyTorch deployments

**Advantages:**

- 40% faster than pickle format
- Optimized for inference workloads
- Supports graph optimization
- Better cross-version compatibility

**Safetensors (.safetensors files):**

- **Load Time**: ~5 seconds for 7B model
- **Security**: Safe by design, no arbitrary code execution
- **Compatibility**: Supported by Hugging Face, vLLM, and major frameworks
- **Use Case**: **Recommended for most production deployments**

**Advantages:**

- 58% faster than pickle format
- Memory-mapped file loading (zero-copy)
- Safe format with no code execution
- Lazy tensor loading support
- Cross-framework compatibility

**Implementation:**

```python
# Converting PyTorch checkpoint to Safetensors
from safetensors.torch import save_file
import torch

# Load PyTorch checkpoint
checkpoint = torch.load("model.bin")

# Save as Safetensors
save_file(checkpoint, "model.safetensors")
```

**ONNX (.onnx files):**

- **Load Time**: ~4 seconds for 7B model
- **Security**: Safe, standardized format
- **Compatibility**: Cross-framework, cross-platform
- **Use Case**: Production deployments with ONNX Runtime

**Advantages:**

- 67% faster than pickle format (fastest loading)
- Hardware-specific optimizations
- Supports quantization and graph optimization
- Excellent cross-platform support
- Memory-efficient loading

**Disadvantages:**

- Requires conversion from PyTorch/TensorFlow
- Not all model architectures fully supported
- May lose some dynamic features

**Implementation:**

```python
# Export PyTorch model to ONNX
import torch

model = load_pytorch_model()
dummy_input = torch.randn(1, 512)

torch.onnx.export(
    model,
    dummy_input,
    "model.onnx",
    export_params=True,
    opset_version=17,
    do_constant_folding=True,
    input_names=["input"],
    output_names=["output"],
    dynamic_axes={"input": {0: "batch_size"}, "output": {0: "batch_size"}}
)
```

#### Optimization Strategies

**Choose the Right Format:**

```text
Decision Matrix:

PyTorch pickle: ❌ Avoid in production (slow, insecure)
TorchScript:    ✓  Use for PyTorch-only deployments
Safetensors:    ✓✓ Recommended for most use cases
ONNX:           ✓✓ Best for performance-critical deployments
```

**Hybrid Approach:**

For maximum flexibility, maintain models in multiple formats:

```bash
/models/
  ├── llama-2-7b/
  │   ├── model.safetensors      # Primary format
  │   ├── model.onnx             # Optimized for inference
  │   └── model.bin              # Backup/fallback
```

**Quantization:**

Combine format optimization with quantization for further improvements:

- **4-bit quantization**: 4x smaller models, 2-3x faster loading
- **8-bit quantization**: 2x smaller models, 1.5-2x faster loading

```python
# Load quantized Safetensors model with vLLM
from vllm import LLM

llm = LLM(
    model="/models/llama-2-7b",
    quantization="awq",  # or "gptq", "bitsandbytes"
    dtype="auto"
)
```

**Memory-Mapped Loading:**

Leverage memory-mapped files to avoid copying model weights:

```python
# Safetensors supports memory mapping
from safetensors import safe_open

tensors = {}
with safe_open("model.safetensors", framework="pt", device="cuda:0") as f:
    for key in f.keys():
        tensors[key] = f.get_tensor(key)  # Zero-copy loading
```

#### Implementation Example

**Dockerfile with Optimized Model Format:**

```dockerfile
FROM vllm/vllm-openai:latest

# Copy pre-converted Safetensors model
COPY models/llama-2-7b-safetensors /models/llama-2-7b

# Set environment for optimal loading
ENV VLLM_ATTENTION_BACKEND=FLASHINFER
ENV VLLM_WORKER_MULTIPROC_METHOD=spawn

# Start server with Safetensors model
CMD ["python", "-m", "vllm.entrypoints.openai.api_server", \
     "--model", "/models/llama-2-7b", \
     "--dtype", "auto", \
     "--max-model-len", "4096"]
```

**Model Conversion Pipeline:**

```bash
#!/bin/bash
# convert_model.sh - Convert models to optimized formats

MODEL_NAME="llama-2-7b"
MODEL_PATH="./models/${MODEL_NAME}"

echo "Converting ${MODEL_NAME} to optimized formats..."

# 1. Convert to Safetensors
python -c "
from transformers import AutoModelForCausalLM
from safetensors.torch import save_file

model = AutoModelForCausalLM.from_pretrained('${MODEL_PATH}')
state_dict = model.state_dict()
save_file(state_dict, '${MODEL_PATH}/model.safetensors')
print('✓ Converted to Safetensors')
"

# 2. Convert to ONNX
python -c "
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model = AutoModelForCausalLM.from_pretrained('${MODEL_PATH}')
tokenizer = AutoTokenizer.from_pretrained('${MODEL_PATH}')

dummy_input = tokenizer('Hello world', return_tensors='pt')
torch.onnx.export(
    model,
    (dummy_input['input_ids'],),
    '${MODEL_PATH}/model.onnx',
    opset_version=17
)
print('✓ Converted to ONNX')
"

echo "Conversion complete. Load times comparison:"
echo "  Safetensors: ~5s (recommended)"
echo "  ONNX: ~4s (fastest, if compatible)"
```

#### Format Selection Best Practices

**Model Distribution:**

- Pre-convert models to Safetensors or ONNX before deployment
- Store converted models in container images or fast storage (SSD, NVMe)
- Use image pull secrets and private registries for proprietary models
- Implement model caching layers (see P2P distribution below)

**Version Management:**

```yaml
# Track model formats in metadata
apiVersion: v1
kind: ConfigMap
metadata:
  name: model-formats
data:
  llama-2-7b.json: |
    {
      "formats": {
        "safetensors": {
          "path": "/models/llama-2-7b/model.safetensors",
          "load_time_ms": 5000,
          "recommended": true
        },
        "onnx": {
          "path": "/models/llama-2-7b/model.onnx",
          "load_time_ms": 4000,
          "recommended": false,
          "note": "Limited ops support"
        }
      }
    }
```

**Performance Testing:**

Benchmark your specific models and hardware:

```python
# benchmark_loading.py
import time
from safetensors.torch import load_file
import torch

def benchmark_format(model_path, format_name):
    start = time.time()
    
    if format_name == "safetensors":
        tensors = load_file(model_path)
    elif format_name == "pytorch":
        tensors = torch.load(model_path)
    
    elapsed = time.time() - start
    print(f"{format_name}: {elapsed:.2f}s")
    return elapsed

# Compare formats
benchmark_format("model.safetensors", "safetensors")
benchmark_format("model.bin", "pytorch")
```

---

### Solution 3: Lazy Loading

Lazy loading defers model loading until the first inference request, enabling
instant container startup at the cost of first-request latency.

#### The Pattern

**Traditional Loading:**

```text
Pod Start → Load Model (30s) → Ready → Serve Requests
           └─ Cold Start ─────┘
```

**Lazy Loading:**

```text
Pod Start → Ready (instant) → First Request → Load Model (30s) → Serve
           └─ No Cold Start  └─ First Request Penalty ────────┘
```

#### Lazy Loading Characteristics

**Container Lifecycle:**

1. **Container starts instantly**: No model loading during initialization
2. **Model remains unloaded**: GPU memory is empty
3. **First request triggers load**: Model loads on-demand
4. **Subsequent requests are fast**: Model stays in memory after first load

**Benefits:**

- **Zero container cold start**: Pod becomes ready immediately
- **Efficient resource usage**: Don't load models that aren't used
- **Better scaling**: Can overprovision Pods without memory waste
- **Multi-model serving**: Load models dynamically based on requests

**Trade-offs:**

- **First request latency**: Users experience model loading delay
- **Unpredictable performance**: First vs. subsequent request latency differs
- **Complexity**: Requires application-level lazy loading logic
- **Resource spikes**: Multiple first requests may cause memory pressure

#### Implementation Patterns

**Basic Lazy Loading Server:**

```python
# lazy_model_server.py
from fastapi import FastAPI
import asyncio

app = FastAPI()

class LazyModelServer:
    def __init__(self):
        self.model = None
        self.loading_lock = asyncio.Lock()
    
    async def load_model(self):
        """Load model on first request"""
        if self.model is None:
            async with self.loading_lock:
                # Double-check after acquiring lock
                if self.model is None:
                    print("Loading model (this will take ~30s)...")
                    # Simulate model loading
                    await asyncio.sleep(30)  # Replace with actual model load
                    self.model = "loaded_model"
                    print("Model loaded and ready")
        return self.model
    
    async def predict(self, input):
        # Lazy load on first request
        model = await self.load_model()
        # Run inference
        return f"Result from {model} for {input}"

server = LazyModelServer()

@app.get("/health")
async def health():
    """Health check passes immediately"""
    return {"status": "healthy", "model_loaded": server.model is not None}

@app.post("/predict")
async def predict(input: str):
    """First request loads model, subsequent requests are fast"""
    result = await server.predict(input)
    return {"result": result}
```

**Advanced: Progressive Loading:**

Load model layers progressively to provide partial responses faster:

```python
class ProgressiveLazyLoader:
    def __init__(self):
        self.layers_loaded = 0
        self.total_layers = 32
        self.model = None
    
    async def load_layer(self, layer_idx):
        """Load single model layer"""
        # Load layer weights
        await asyncio.sleep(0.5)  # Simulate layer loading
        self.layers_loaded += 1
    
    async def ensure_loaded(self, required_layers=None):
        """Load minimum required layers"""
        if required_layers is None:
            required_layers = self.total_layers
        
        while self.layers_loaded < required_layers:
            await self.load_layer(self.layers_loaded)
    
    async def predict(self, input, quality="full"):
        """Support different quality levels"""
        if quality == "fast":
            await self.ensure_loaded(required_layers=16)  # Load half
        else:
            await self.ensure_loaded(required_layers=32)  # Load all
        
        return f"Result with {self.layers_loaded} layers"
```

**Kubernetes Deployment with Lazy Loading:**

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lazy-load-inference
spec:
  replicas: 5  # Can overprovision since models not loaded
  template:
    metadata:
      labels:
        app: lazy-load-inference
    spec:
      containers:
      - name: inference-server
        image: my-registry/lazy-llm-server:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "4Gi"  # Lower initial memory
            nvidia.com/gpu: 1
          limits:
            memory: "32Gi"  # Higher limit for loaded model
            nvidia.com/gpu: 1
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5  # Fast startup
          periodSeconds: 10
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 10
          periodSeconds: 30
        env:
        - name: LAZY_LOAD
          value: "true"
        - name: MODEL_PATH
          value: "/models/llama-2-7b"
```

#### When to Use Lazy Loading

**Good Use Cases:**

- **Development and testing**: Fast iteration without waiting for model loads
- **Multi-model serving**: Serve many models with limited GPU memory
- **Bursty traffic**: Models used infrequently but need fast scaling
- **Cost-sensitive deployments**: Can tolerate first-request penalty

**Not Recommended:**

- **Latency-critical applications**: First-request penalty unacceptable
- **High-QPS services**: Constant traffic means models always loaded
- **Real-time inference**: Predictable latency required

**Hybrid Approach:**

Combine lazy loading with background warming:

```python
class HybridLazyLoader:
    def __init__(self, warmup_delay=60):
        self.model = None
        self.warmup_delay = warmup_delay
        # Start background warmup after delay
        asyncio.create_task(self.background_warmup())
    
    async def background_warmup(self):
        """Warm up model in background after container starts"""
        await asyncio.sleep(self.warmup_delay)
        if self.model is None:
            print("Background warmup: loading model...")
            await self.load_model()
    
    async def load_model(self):
        if self.model is None:
            # Load model logic
            self.model = "loaded_model"
    
    async def predict(self, input):
        # Lazy load if not already warming up
        if self.model is None:
            await self.load_model()
        return f"Result from {self.model}"
```

#### Lazy Loading Best Practices

**User Experience:**

- Communicate loading status to users
- Provide progress indicators for first requests
- Consider queueing subsequent requests during initial load
- Set appropriate timeouts for model loading

**Example User Feedback:**

```python
@app.post("/predict")
async def predict_with_feedback(input: str):
    if server.model is None:
        # Return status indicating loading
        return {
            "status": "loading",
            "message": "Model is loading, please retry in 30s",
            "retry_after": 30
        }
    
    result = await server.predict(input)
    return {"status": "success", "result": result}
```

**Resource Management:**

```yaml
# Use Vertical Pod Autoscaling to adjust resources after loading
apiVersion: autoscaling.k8s.io/v1
kind: VerticalPodAutoscaler
metadata:
  name: lazy-load-vpa
spec:
  targetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: lazy-load-inference
  updatePolicy:
    updateMode: "Auto"  # Automatically adjust resources
  resourcePolicy:
    containerPolicies:
    - containerName: inference-server
      minAllowed:
        memory: 4Gi
      maxAllowed:
        memory: 64Gi
```

**Monitoring:**

Track key metrics for lazy loading:

```text
Lazy Loading Metrics:
- First request latency (P95, P99)
- Model load time
- Model loaded percentage (across replicas)
- Memory usage before/after model load
- User-facing request timeout rate
```

---

## Combining Strategies

The most effective approach often combines multiple strategies:

### Strategy Matrix

| Workload Type | Primary Strategy | Secondary Strategy | Tertiary |
|---------------|------------------|-------------------|----------|
| High QPS, latency-critical | Pre-warmed pools | Faster format | — |
| Moderate QPS, cost-sensitive | Faster format | Lazy loading | Warm pool |
| Low QPS, bursty traffic | Lazy loading | Faster format | — |
| Multi-model serving | Pre-warmed pools | Faster format | Lazy load |
| Development/testing | Lazy loading | Faster format | — |

### Example: Hybrid Production Architecture

```text
┌─────────────────────────────────────────────────────────┐
│                    Load Balancer                        │
│            (Route based on model & priority)            │
└────────┬─────────────────────────────────┬──────────────┘
         │                                 │
         ▼                                 ▼
┌─────────────────┐              ┌─────────────────────────┐
│  Warm Pool      │              │   Lazy Load Pool        │
│  (Popular       │              │   (Rare models,         │
│   models)       │              │    overflow requests)   │
│                 │              │                         │
│  - Model A: 5x  │              │  - All models: 10x      │
│  - Model B: 3x  │              │  - Load on demand       │
│  - Model C: 2x  │              │  - Safetensors format   │
│                 │              │                         │
│  Safetensors    │              │  First request: 5s      │
│  Zero latency   │              │  Subsequent: <100ms     │
└─────────────────┘              └─────────────────────────┘
```

### Hybrid Deployment Example

**Multi-tier service with intelligent routing:**

```yaml
apiVersion: v1
kind: Service
metadata:
  name: inference-router
spec:
  selector:
    app: inference
  ports:
  - port: 80
    targetPort: 8000

---
# Tier 1: Pre-warmed popular models
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inference-warm-popular
  labels:
    tier: warm
    model-type: popular
spec:
  replicas: 5
  selector:
    matchLabels:
      app: inference
      tier: warm
  template:
    spec:
      containers:
      - name: vllm
        image: vllm/vllm-openai:latest
        args: ["--model", "/models/llama-2-7b-safetensors"]
        resources:
          limits:
            nvidia.com/gpu: 1

---
# Tier 2: Lazy loading for rare models
apiVersion: apps/v1
kind: Deployment
metadata:
  name: inference-lazy-rare
  labels:
    tier: lazy
    model-type: rare
spec:
  replicas: 10
  selector:
    matchLabels:
      app: inference
      tier: lazy
  template:
    spec:
      containers:
      - name: lazy-server
        image: my-registry/lazy-llm-server:latest
        env:
        - name: LAZY_LOAD
          value: "true"
        resources:
          limits:
            nvidia.com/gpu: 1
```

---

## Best Practices Summary

### 1. Choose Strategy Based on Workload

**Pre-warmed Pools:**

- Best for: High QPS, latency-critical workloads
- Pros: Zero latency, predictable performance
- Cons: Cost overhead, resource waste

**Faster Serialization:**

- Best for: All production deployments
- Pros: Simple, effective, no downside
- Cons: Requires one-time model conversion

**Lazy Loading:**

- Best for: Development, testing, low QPS workloads
- Pros: Fast container startup, efficient resources
- Cons: First-request latency, complexity

### 2. Optimize Model Format

**Action Items:**

- Convert all production models to Safetensors or ONNX
- Test loading performance on target hardware
- Implement automated conversion pipeline
- Version models with format metadata

### 3. Implement Comprehensive Monitoring

**Key Metrics:**

```text
Cold Start Metrics:
- Pod creation to ready time
- Model loading time (by format)
- First request latency (P95, P99)
- GPU memory utilization timeline
- Cold start frequency per hour

Cost Metrics:
- GPU hours utilized vs. idle
- Cost per inference request
- Resource efficiency percentage
```

### 4. Plan for Multi-Model Scenarios

**Strategies:**

- High-traffic models: Pre-warmed dedicated pools
- Medium-traffic models: Smaller warm pools + auto-scaling
- Low-traffic models: Lazy loading with shared resources
- Model switching: Use LoRA adapters when possible

### 5. Test and Validate

**Validation Steps:**

1. Benchmark model loading times for each format
2. Load test warm pools under realistic traffic
3. Test lazy loading first-request experience
4. Measure end-to-end cold start times
5. Validate cost efficiency vs. latency trade-offs

---

## References

### Presentations

- [KubeCon NA 2024: GPU Pod Cold Start Optimization](https://sched.co/27Fa0)

### Cloud Provider Implementations

- [GKE Agent Sandbox: Strong Guardrails for Agentic AI on Kubernetes](https://cloud.google.com/blog/products/containers-kubernetes/agentic-ai-on-kubernetes-and-gke)
- [vLLM: High-throughput LLM Inference](https://github.com/vllm-project/vllm)
- [Safetensors: Safe Tensor Serialization](https://github.com/huggingface/safetensors)

### Related Documentation

- [Pod Startup Speed Optimization](./pod-startup-speed.md)
- [Model Lifecycle Management](../inference/model-lifecycle.md)
- [Workload Isolation](./isolation.md)
- [Dynamic Resource Allocation](./dra.md)

### Additional Resources

- [ONNX Runtime Documentation](https://onnxruntime.ai/)
- [PyTorch TorchScript Guide](https://pytorch.org/docs/stable/jit.html)
- [Hugging Face Model Hub](https://huggingface.co/models)
- [Kubernetes GPU Scheduling](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/)

---

**Note**: This document synthesizes information from KubeCon presentations,
production implementations, and industry best practices. Always validate
specific performance numbers and strategies for your hardware, models, and
workload patterns.
