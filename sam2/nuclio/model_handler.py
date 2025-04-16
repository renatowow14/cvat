# Copyright (C) 2023-2024 CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

import numpy as np
import torch
import os

from sam2.build_sam import build_sam2
from sam2.sam2_image_predictor import SAM2ImagePredictor

# Most of this code is based on https://github.com/facebookresearch/segment-anything-2/blob/main/notebooks/image_predictor_example.ipynb

class ModelHandler:
    def __init__(self):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        # turn on tfloat32 for Ampere GPUs (https://pytorch.org/docs/stable/notes/cuda.html#tensorfloat-32-tf32-on-ampere-devices)
        if self.device.type == 'cuda' and torch.cuda.get_device_properties(0).major >= 8:
            torch.backends.cuda.matmul.allow_tf32 = True
            torch.backends.cudnn.allow_tf32 = True


        self.sam2_checkpoint = '/opt/nuclio/sam2/' + os.getenv('MODEL_PATH', 'sam2_hiera_large.pt')
        self.model_cfg = os.getenv('MODEL_CFG', 'sam2_hiera_l.yaml') 
        self.predictor = SAM2ImagePredictor(build_sam2(self.model_cfg, self.sam2_checkpoint, device=self.device))

    def handle(self, image, pos_points, neg_points, obj_bbox):
        pos_points, neg_points = list(pos_points), list(neg_points)
        
        self.predictor.set_image(np.array(image))
        masks, scores, _ = self.predictor.predict(point_coords=np.array(pos_points + neg_points),
                                                    # Adjust the labels to match the points shape
                                                    point_labels=np.array([1]*len(pos_points) + [0]*len(neg_points)),
                                                    #For ambiguous prompts such as a single point, it is recommended \
                                                    # to use multimask_output=True even if only a single mask is desired;
                                                    # the best single mask can be chosen by picking the one with the 
                                                    # highest score returned in scores
                                                    box=obj_bbox, # starting bounding box of the object to segment
                                                    multimask_output=True,
                                                )
        sorted_ind = np.argsort(scores)[::-1]
        masks = masks[sorted_ind]
        # scores = scores[sorted_ind]
        # logits = logits[sorted_ind]
        best_mask = masks[0]
        return best_mask