import json
import boto3
from aws_lambda_powertools import Logger
from queries import TotalUtilitiesQuery
from services import RedisService, SecManagerService, SQSService

logger = Logger()

secman_serv = SecManagerService().connect()
sqs_serv = SQSService().connect()
redis_serv = RedisService(**secman_serv.get_credentials('UtilCacheSecret')).connect()

serv_dict = {'sqs': sqs_serv, 'cache': redis_serv}

@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):

    if event:
        batch_item_failures = []
        sqs_batch_response = {}

        for record in event["Records"]:
            try:
                body = json.loads(record['body'])
                query = TotalUtilitiesQuery(
                    request_body=body['request_body'],
                    path_params=body['path_params'],
                    services=serv_dict
                )
                query.process()
                query.put_message_sqs()
            except Exception as e:
                logger.exception("Received an exception while processing messages")
                batch_item_failures.append({"itemIdentifier": record['messageId']})

        sqs_batch_response["batchItemFailures"] = batch_item_failures
        
        return sqs_batch_response