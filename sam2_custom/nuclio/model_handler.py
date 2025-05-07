import os
import torch
import numpy as np
import base64
import cv2
from sam2.build_sam import build_sam2
from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator

class ModelHandler:
    def __init__(self):
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_path = os.path.join("/opt/nuclio/sam2", os.getenv("MODEL", "sam2_hiera_tiny.pt"))
        self.model_cfg = os.getenv("MODEL_CFG", "sam2_hiera_t.yaml")
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"Model file not found: {self.model_path}")
        self.model = build_sam2(self.model_cfg, self.model_path, device=self.device)
        self.mask_generator = SAM2AutomaticMaskGenerator(self.model)
        self.model.eval()
        torch.cuda.empty_cache()

    def handle(self, image, points, labels, box):
        try:
            if image is None:
                raise ValueError("Image is required")

            if isinstance(image, str):
                image_data = base64.b64decode(image)
                nparr = np.frombuffer(image_data, np.uint8)
                img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            else:
                img = image

            if img is None:
                raise ValueError("Failed to decode image")

            max_size = 256
            h, w = img.shape[:2]
            if max(h, w) > max_size:
                scale = max_size / max(h, w)
                new_w, new_h = int(w * scale), int(h * scale)
                img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            else:
                scale = 1.0

            if points:
                points = [[x * scale, y * scale] for x, y in points]
            if box:
                box = [x * scale for x in box]

            img_tensor = torch.from_numpy(img).permute(2, 0, 1).unsqueeze(0).to(self.device).float() / 255.0

            if points or box:
                if points and not labels:
                    raise ValueError("Labels are required when points are provided")
                if points and len(points) != len(labels):
                    raise ValueError("Number of points must match number of labels")

                points_tensor = torch.tensor(points, dtype=torch.float32).to(self.device) if points else None
                labels_tensor = torch.tensor(labels, dtype=torch.int64).to(self.device) if labels else None
                box_tensor = torch.tensor(box, dtype=torch.float32).to(self.device) if box else None

                if points_tensor is not None and labels_tensor is not None:
                    if points_tensor.shape[0] != labels_tensor.shape[0]:
                        raise ValueError("Points and labels must have the same length")

                with torch.no_grad():
                    outputs = self.model(img_tensor, points=points_tensor, labels=labels_tensor, box=box_tensor)
                    mask = outputs[0]["masks"].cpu().numpy()
            else:
                with torch.no_grad():
                    outputs = self.mask_generator.generate(img)
                    if not outputs:
                        raise ValueError("No masks generated")
                    mask = outputs[0]["segmentation"]

            if max(h, w) > max_size:
                mask = cv2.resize(mask.astype(np.uint8), (w, h), interpolation=cv2.INTER_NEAREST)

            torch.cuda.empty_cache()
            return mask
        except Exception as e:
            torch.cuda.empty_cache()
            raise ValueError(f"Failed to process request: {str(e)}")