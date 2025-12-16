import azure.functions as func
import logging

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)

@app.route(route="score_check")
@app.blob_output(arg_name="outputblob",
                 path="messages-from-http/message-{datetime}.txt",
                 connection="AzureWebJobsStorage")
def score_check(req: func.HttpRequest, outputblob: func.Out[str]) -> func.HttpResponse:
    # logging.info('Python HTTP trigger function processed a request.')

    # name = req.params.get('name')
    # if not name:
    #     try:
    #         req_body = req.get_json()
    #     except ValueError:
    #         pass
    #     else:
    #         name = req_body.get('name')

    # if name:
    #     return func.HttpResponse(f"Hello, {name}. This HTTP triggered function executed successfully.")
    # else:
    #     return func.HttpResponse(
    #          "This HTTP triggered function executed successfully. Pass a name in the query string or in the request body for a personalized response.",
    #          status_code=200
    #     )
    logging.info('Python HTTP trigger function processed a request to write a blob.')

    message = req.params.get('message')
    if not message:
        return func.HttpResponse("Please pass a 'message' on the query string.", status_code=400)
    
    # 将消息内容设置给输出绑定，它会自动写入到 blob
    outputblob.set(message)
    
    return func.HttpResponse(f"OK. Message '{message}' was written to the default blob storage.")