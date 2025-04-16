# Copyright (C) 2023-2024 CVAT.ai Corporation
#
# SPDX-License-Identifier: MIT

import json
import base64
from PIL import Image
import io
from model_handler import ModelHandler

def init_context(context):
    context.logger.info("Init context...  0%")
    model = ModelHandler()
    context.user_data.model = model
    context.logger.info("Init context...100%")

def handler(context, event):
    try:
        context.logger.info("call handler")
        data = event.body
        buf = io.BytesIO(base64.b64decode(data["image"]))
        image = Image.open(buf)
        image = image.convert("RGB")  # to make sure image comes in RGB
        # From serverless/pytorch/shiyinzhang/iog/nuclio/main.py
        pos_points = data["pos_points"]
        neg_points = data["neg_points"]
        obj_bbox = data.get("obj_bbox", None)
        mask = context.user_data.model.handle(image, pos_points, neg_points, obj_bbox)

        return context.Response(
            body=json.dumps({'mask': mask.tolist()}),
            headers={},
            content_type='application/json',
            status_code=200
        )
    except Exception as e:
        context.logger.error(f'Unexpected error in handler: {str(e)}')
        return context.Response(
            body=json.dumps({'error': str(e)}),
            headers={},
            content_type='application/json',
            status_code=500
        )