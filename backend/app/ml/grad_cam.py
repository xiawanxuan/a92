import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Tuple, Optional, Dict, List, Any
import cv2
from dataclasses import dataclass


@dataclass
class BoundingBox:
    x: int
    y: int
    width: int
    height: int
    area_ratio: float
    avg_intensity: float
    max_intensity: float
    confidence: float


class GradCAM:
    def __init__(self, model: nn.Module, target_layer: str = 'layer4'):
        self.model = model
        self.target_layer = target_layer
        self.gradients: Optional[torch.Tensor] = None
        self.activations: Optional[torch.Tensor] = None
        self._register_hooks()

    def _register_hooks(self):
        target_module = getattr(self.model, self.target_layer, None)
        if target_module is None:
            raise ValueError(f"Layer {self.target_layer} not found in model")

        def forward_hook(module, input, output):
            self.activations = output.detach()

        def backward_hook(module, grad_input, grad_output):
            self.gradients = grad_output[0].detach()

        target_module.register_forward_hook(forward_hook)
        target_module.register_full_backward_hook(backward_hook)

    def _compute_weights(self, gradients: torch.Tensor) -> torch.Tensor:
        return torch.mean(gradients, dim=(2, 3), keepdim=True)

    def generate_heatmap(
        self,
        input_tensor: torch.Tensor,
        target_class: int,
        original_h: Optional[torch.Tensor] = None,
        original_w: Optional[torch.Tensor] = None
    ) -> Tuple[np.ndarray, torch.Tensor, torch.Tensor]:
        self.model.eval()
        
        input_tensor = input_tensor.unsqueeze(0) if input_tensor.dim() == 3 else input_tensor
        input_tensor.requires_grad_(True)

        self.model.zero_grad()
        
        if original_h is not None and original_w is not None:
            logits, probs = self.model(input_tensor, original_h, original_w)
        else:
            logits, probs = self.model(input_tensor)

        target_score = logits[:, target_class].sum()
        target_score.backward()

        if self.gradients is None or self.activations is None:
            raise RuntimeError("Gradients or activations not captured")

        weights = self._compute_weights(self.gradients)
        weighted_activations = torch.sum(weights * self.activations, dim=1, keepdim=True)
        
        heatmap = F.relu(weighted_activations)
        
        batch_size = heatmap.shape[0]
        input_size = input_tensor.shape[2:]
        heatmap_resized = np.zeros((batch_size, input_size[0], input_size[1]), dtype=np.float32)
        
        for i in range(batch_size):
            heatmap_i = heatmap[i]
            min_val = torch.min(heatmap_i)
            max_val = torch.max(heatmap_i)
            if max_val > min_val:
                heatmap_i = (heatmap_i - min_val) / (max_val - min_val)
            else:
                heatmap_i = torch.zeros_like(heatmap_i)
            
            heatmap_np = heatmap_i.squeeze().cpu().numpy()
            heatmap_resized_i = cv2.resize(heatmap_np, (input_size[1], input_size[0]))
            
            if original_h is not None and original_w is not None:
                orig_h = int(original_h[i].item())
                orig_w = int(original_w[i].item())
                heatmap_mask = np.zeros_like(heatmap_resized_i)
                heatmap_mask[:orig_h, :orig_w] = heatmap_resized_i[:orig_h, :orig_w]
                heatmap_resized_i = heatmap_mask
            
            heatmap_resized[i] = heatmap_resized_i

        return heatmap_resized, weights, logits

    @staticmethod
    def generate_bounding_box(
        heatmap: np.ndarray,
        threshold: float = 0.5
    ) -> Optional[BoundingBox]:
        binary_mask = (heatmap > threshold).astype(np.uint8)
        
        if np.sum(binary_mask) == 0:
            return None

        contours, _ = cv2.findContours(
            binary_mask,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        if not contours:
            return None

        all_contours = np.concatenate(contours)
        x, y, w, h = cv2.boundingRect(all_contours)

        area = w * h
        total_area = heatmap.shape[0] * heatmap.shape[1]
        area_ratio = area / total_area

        heatmap_roi = heatmap[y:y+h, x:x+w]
        avg_intensity = np.mean(heatmap_roi) if heatmap_roi.size > 0 else 0
        max_intensity = np.max(heatmap_roi) if heatmap_roi.size > 0 else 0

        return BoundingBox(
            x=int(x),
            y=int(y),
            width=int(w),
            height=int(h),
            area_ratio=float(area_ratio),
            avg_intensity=float(avg_intensity),
            max_intensity=float(max_intensity),
            confidence=float(max_intensity)
        )

    def __call__(
        self,
        input_tensor: torch.Tensor,
        target_class: int,
        original_h: Optional[torch.Tensor] = None,
        original_w: Optional[torch.Tensor] = None,
        bbox_threshold: float = 0.5
    ) -> Dict:
        heatmap, weights, logits = self.generate_heatmap(
            input_tensor, target_class, original_h, original_w
        )
        
        probs = torch.softmax(logits, dim=1)
        confidence = probs[0, target_class].item() if probs.shape[0] > 0 else 0.0
        
        bbox = self.generate_bounding_box(heatmap[0], bbox_threshold)
        
        return {
            'heatmap': heatmap[0],
            'confidence': float(confidence),
            'target_class': int(target_class),
            'bbox': bbox
        }


class GradCAMManager:
    def __init__(self, model: nn.Module, device: Optional[torch.device] = None, target_layer: str = 'layer4'):
        self.device = device or torch.device('cpu')
        self.grad_cam = GradCAM(model, target_layer)
        self.model = model

    @torch.enable_grad()
    def process_tile(
        self,
        image_tensor: torch.Tensor,
        target_class: int,
        original_h: Optional[int] = None,
        original_w: Optional[int] = None,
        bbox_threshold: float = 0.5
    ) -> Optional[Dict]:
        if image_tensor.dim() == 4:
            image_tensor = image_tensor.squeeze(0)

        image_tensor = image_tensor.to(self.device).detach().clone()
        
        try:
            orig_h_t = torch.tensor([original_h], dtype=torch.float32, device=self.device) if original_h is not None else None
            orig_w_t = torch.tensor([original_w], dtype=torch.float32, device=self.device) if original_w is not None else None
            
            result = self.grad_cam(
                image_tensor, target_class, orig_h_t, orig_w_t, bbox_threshold
            )
            
            heatmap_uint8 = (result['heatmap'] * 255).astype(np.uint8)
            
            return {
                'heatmap_data': heatmap_uint8.tobytes(),
                'heatmap_shape': list(result['heatmap'].shape),
                'confidence': result['confidence'],
                'bbox': result['bbox'],
                'target_class': result['target_class']
            }
        except Exception as e:
            print(f"Grad-CAM processing failed: {e}")
            return None

    @torch.enable_grad()
    def process_batch(
        self,
        batch_images: torch.Tensor,
        predicted_classes: torch.Tensor,
        confidences: torch.Tensor,
        original_h: torch.Tensor,
        original_w: torch.Tensor,
        man_made_class: int,
        threshold: float
    ) -> List[Dict[str, Any]]:
        results = []
        batch_size = batch_images.shape[0]
        
        for i in range(batch_size):
            pred_class = predicted_classes[i].item()
            confidence = confidences[i].item()
            
            if pred_class != man_made_class or confidence <= threshold:
                continue
            
            orig_h = int(original_h[i].item())
            orig_w = int(original_w[i].item())
            
            image_tensor = batch_images[i:i+1].to(self.device)
            orig_h_t = original_h[i:i+1].to(self.device)
            orig_w_t = original_w[i:i+1].to(self.device)
            
            try:
                heatmap, weights, logits = self.grad_cam.generate_heatmap(
                    image_tensor, man_made_class, orig_h_t, orig_w_t
                )
                
                probs = torch.softmax(logits, dim=1)
                cam_confidence = probs[0, man_made_class].item()
                
                bbox = GradCAM.generate_bounding_box(heatmap[0])
                
                results.append({
                    'batch_index': i,
                    'heatmap': heatmap[0],
                    'weights': weights[0],
                    'logits': logits[0],
                    'confidence': cam_confidence,
                    'target_class': man_made_class,
                    'bbox': bbox,
                    'original_h': orig_h,
                    'original_w': orig_w
                })
            except Exception as e:
                print(f"Grad-CAM processing failed for batch {i}: {e}")
                continue
        
        return results
