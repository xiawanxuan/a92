import sys
print("Python version:", sys.version)

try:
    import torch
    print("[OK] PyTorch:", torch.__version__)
except ImportError as e:
    print("[ERROR] PyTorch not installed:", e)

try:
    import torchvision
    print("[OK] torchvision:", torchvision.__version__)
except ImportError as e:
    print("[ERROR] torchvision not installed:", e)

try:
    import numpy
    print("[OK] NumPy:", numpy.__version__)
except ImportError as e:
    print("[ERROR] NumPy not installed:", e)

try:
    import cv2
    print("[OK] OpenCV:", cv2.__version__)
except ImportError as e:
    print("[ERROR] OpenCV not installed:", e)

try:
    import PIL
    print("[OK] Pillow:", PIL.__version__)
except ImportError as e:
    print("[ERROR] Pillow not installed:", e)

try:
    import scipy
    print("[OK] SciPy:", scipy.__version__)
except ImportError as e:
    print("[ERROR] SciPy not installed:", e)
