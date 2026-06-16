import torch
import torch.nn as nn
import torchvision.models as models
from typing import Tuple, Dict, Optional
from pathlib import Path

from .grad_cam import GradCAMManager


class SonarResNet50(nn.Module):
    def __init__(self, num_classes: int = 4, pretrained: bool = True):
        super().__init__()
        self.num_classes = num_classes
        self.downsample_factor = 32

        weights = models.ResNet50_Weights.IMAGENET1K_V2 if pretrained else None
        backbone = models.resnet50(weights=weights)

        self.conv1 = backbone.conv1
        self.bn1 = backbone.bn1
        self.relu = backbone.relu
        self.maxpool = backbone.maxpool
        self.layer1 = backbone.layer1
        self.layer2 = backbone.layer2
        self.layer3 = backbone.layer3
        self.layer4 = backbone.layer4
        self.avgpool = backbone.avgpool

        in_features = backbone.fc.in_features
        self.fc = nn.Sequential(
            nn.Linear(in_features, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, num_classes)
        )

    def _create_spatial_mask(
        self,
        batch_size: int,
        feat_h: int,
        feat_w: int,
        original_h: torch.Tensor,
        original_w: torch.Tensor,
        input_size: int,
        device: torch.device,
        dtype: torch.dtype
    ) -> torch.Tensor:
        valid_feat_h = torch.ceil(original_h * feat_h / input_size).long()
        valid_feat_w = torch.ceil(original_w * feat_w / input_size).long()

        h_idx = torch.arange(feat_h, device=device).view(1, 1, feat_h, 1)
        w_idx = torch.arange(feat_w, device=device).view(1, 1, 1, feat_w)

        valid_feat_h_exp = valid_feat_h.view(-1, 1, 1, 1)
        valid_feat_w_exp = valid_feat_w.view(-1, 1, 1, 1)

        mask = (h_idx < valid_feat_h_exp) & (w_idx < valid_feat_w_exp)
        return mask.to(dtype=dtype)

    def _masked_global_avg_pool(
        self,
        features: torch.Tensor,
        mask: torch.Tensor
    ) -> torch.Tensor:
        B, C, H, W = features.shape
        masked_features = features * mask
        
        sum_pooled = masked_features.sum(dim=(2, 3))
        valid_count = mask.sum(dim=(2, 3)).clamp(min=1)
        
        return sum_pooled / valid_count

    def forward(
        self,
        x: torch.Tensor,
        original_h: Optional[torch.Tensor] = None,
        original_w: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor]:
        input_size = x.shape[2]
        
        x = self.conv1(x)
        x = self.bn1(x)
        x = self.relu(x)
        x = self.maxpool(x)

        x = self.layer1(x)
        x = self.layer2(x)
        x = self.layer3(x)
        features = self.layer4(x)

        B, C, feat_h, feat_w = features.shape

        if original_h is not None and original_w is not None:
            mask = self._create_spatial_mask(
                B, feat_h, feat_w,
                original_h, original_w,
                input_size,
                features.device,
                features.dtype
            )
            pooled = self._masked_global_avg_pool(features, mask)
        else:
            pooled = self.avgpool(features).flatten(1)

        logits = self.fc(pooled)
        probs = torch.softmax(logits, dim=1)
        return logits, probs


class ClassificationModel:
    def __init__(self, model_path: str, device: str = "cpu", num_classes: int = 4):
        self.device = torch.device(device if torch.cuda.is_available() else "cpu")
        self.num_classes = num_classes
        self.class_names = ['sediment', 'rock', 'coral', 'man_made']

        self.model = SonarResNet50(num_classes=num_classes, pretrained=False)

        model_file = Path(model_path)
        if model_file.exists():
            state_dict = torch.load(model_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
        else:
            print(f"Warning: Model file not found at {model_path}, using initialized weights")

        self.model.to(self.device)
        self.model.eval()

        if self.device.type == 'cuda':
            self.model = self.model.half()

        self._dummy_inference()

    def _dummy_inference(self):
        dummy_input = torch.randn(1, 3, 512, 512).to(self.device)
        if self.device.type == 'cuda':
            dummy_input = dummy_input.half()
        with torch.no_grad():
            _ = self.model(dummy_input)

    @torch.no_grad()
    def predict(
        self,
        images: torch.Tensor,
        original_h: Optional[torch.Tensor] = None,
        original_w: Optional[torch.Tensor] = None
    ) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        images = images.to(self.device)
        if self.device.type == 'cuda':
            images = images.half()
        
        if original_h is not None:
            original_h = original_h.to(self.device).float()
        if original_w is not None:
            original_w = original_w.to(self.device).float()

        logits, probs = self.model(images, original_h, original_w)
        confidences, predictions = torch.max(probs, dim=1)

        return predictions, confidences, probs

    def get_class_name(self, class_idx: int) -> str:
        return self.class_names[class_idx]

    def get_class_idx(self, class_name: str) -> int:
        return self.class_names.index(class_name)

    def get_grad_cam_manager(self) -> GradCAMManager:
        if not hasattr(self, '_grad_cam_manager'):
            self._grad_cam_manager = GradCAMManager(
                self.model,
                self.device,
                target_layer='layer4'
            )
        return self._grad_cam_manager

    def generate_grad_cam(
        self,
        image_tensor: torch.Tensor,
        target_class: int,
        original_h: Optional[int] = None,
        original_w: Optional[int] = None,
        bbox_threshold: float = 0.5
    ) -> Optional[Dict]:
        grad_cam = self.get_grad_cam_manager()
        return grad_cam.process_tile(
            image_tensor, target_class, original_h, original_w, bbox_threshold
        )


def get_model(model_path: str, device: str = "cpu") -> ClassificationModel:
    return ClassificationModel(model_path, device)
