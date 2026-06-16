import torch
import torch.nn as nn
import torchvision.models as models
from typing import Tuple, Dict
from pathlib import Path


class SonarResNet50(nn.Module):
    def __init__(self, num_classes: int = 4, pretrained: bool = True):
        super().__init__()
        self.num_classes = num_classes

        weights = models.ResNet50_Weights.IMAGENET1K_V2 if pretrained else None
        self.backbone = models.resnet50(weights=weights)

        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Sequential(
            nn.Linear(in_features, 512),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(512, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, num_classes)
        )

    def forward(self, x: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor]:
        logits = self.backbone(x)
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
    def predict(self, images: torch.Tensor) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        images = images.to(self.device)
        if self.device.type == 'cuda':
            images = images.half()

        logits, probs = self.model(images)
        confidences, predictions = torch.max(probs, dim=1)

        return predictions, confidences, probs

    def get_class_name(self, class_idx: int) -> str:
        return self.class_names[class_idx]

    def get_class_idx(self, class_name: str) -> int:
        return self.class_names.index(class_name)


def get_model(model_path: str, device: str = "cpu") -> ClassificationModel:
    return ClassificationModel(model_path, device)
