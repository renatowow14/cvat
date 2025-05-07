import json
from model_handler import ModelHandler

def init_context(context):
    context.logger.info("Initializing context")
    try:
        model_handler = ModelHandler()
        context.user_data.model = model_handler
    except Exception as e:
        context.logger.error(f"Failed to initialize model: {str(e)}")
        raise

def handler(context, event):
    try:
        if not event.body:
            return context.Response(body='{"error": "No data provided"}', status_code=400)
        data = json.loads(event.body) if isinstance(event.body, (str, bytes)) else event.body
        if "image" not in data or data["image"] is None:
            return context.Response(body='{"error": "Image is required"}', status_code=400)

        points = data.get("points", [])
        labels = data.get("labels", [])
        image = data["image"]
        box = data.get("box", None)

        if points and not labels:
            return context.Response(body='{"error": "Labels are required when points are provided"}', status_code=400)
        if points and len(points) != len(labels):
            return context.Response(body='{"error": "Number of points must match number of labels"}', status_code=400)

        model = context.user_data.model
        mask = model.handle(image, points, labels, box)
        return context.Response(body=json.dumps({"mask": mask.tolist()}), status_code=200)
    except Exception as e:
        context.logger.error(f"Error in handler: {str(e)}")
        return context.Response(body=f'{{"error": "{str(e)}"}}', status_code=500)