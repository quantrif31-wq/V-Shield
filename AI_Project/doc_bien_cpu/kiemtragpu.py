import torch

print("===== TORCH GPU CHECK =====")

if torch.cuda.is_available():
    print("GPU AVAILABLE ✅")
    
    gpu_name = torch.cuda.get_device_name(0)
    gpu_mem = torch.cuda.get_device_properties(0).total_memory / 1024**3
    
    print("GPU:", gpu_name)
    print("VRAM:", round(gpu_mem,2), "GB")
    print("CUDA version:", torch.version.cuda)
    
else:
    print("GPU NOT AVAILABLE ❌")
    print("Torch will run on CPU")

print("\n===== PADDLE GPU CHECK =====")

try:
    import paddle

    if paddle.device.is_compiled_with_cuda():
        print("Paddle compiled with CUDA ✅")
    else:
        print("Paddle CPU version ❌")

except Exception as e:
    print("Paddle check error:", e)