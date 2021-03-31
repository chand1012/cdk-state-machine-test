import os

def handler(event, context):
    print(event)
    print(context)
    print(os.environ)

    event['status'] = "SUCCEEDED"

    return event