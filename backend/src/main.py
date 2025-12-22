import json

def handler(event, context):
    """Simple Lambda handler for testing"""
    path = event.get('path', '/')
    method = event.get('httpMethod', 'GET')
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': 'Hello from Tally API!',
            'status': 'healthy',
            'version': '0.1.0',
            'path': path,
            'method': method
        })
    }
