import json
import boto3
from aws_lambda_powertools import Logger
from queries import LoginQuery
from services import SecManagerService, SQSService, CognitoService

logger = Logger()

secman_serv = SecManagerService().connect()
sqs_serv = SQSService().connect()
cgn_serv = CognitoService().connect()
cgn_secret = secman_serv.get_credentials('UtilCgnSecret')

serv_dict = {'sqs': sqs_serv, 'cognito': cgn_serv}

@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    
    if event:
        batch_item_failures = []
        sqs_batch_response = {}
        
        for record in event["Records"]:
            try:
                query = LoginQuery(request_body=json.loads(record['body'])['request_body'], services=serv_dict)
                query.process(**cgn_secret)
                query.put_message_sqs()
            except Exception as e:
                logger.exception("Received an exception while processing messages")
                batch_item_failures.append({"itemIdentifier": record['messageId']})

        sqs_batch_response["batchItemFailures"] = batch_item_failures
        
        return sqs_batch_response