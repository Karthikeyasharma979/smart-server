from app import app
import serverless_wsgi

# If you need to handle binary data (like images/PDFs), 
# you might need to configure text_mime_types.
def handler(event, context):
    return serverless_wsgi.handle_request(app, event, context)
