import os
import sys
import json
import boto3
import pytest
import requests
import time
import elasticache_auto_discovery
from pymemcache.client.hash import HashClient

sys.path.append('/home/ec2-user/environment/util-payments/layers')

from layers.queries import TotalUtilitiesQuery
from layers.services import SecManagerService, RDSService, RedisService, SQSService, RDSService

class TestApiGateway:
        
    @pytest.fixture
    def apart_id(self):
        return "1"
        
    @pytest.fixture
    def test_queue(self):
        return "test_queue"
        
    @pytest.fixture
    def login_queue_name(self):
        return "util-app-SignInQueue-xYQyERFth14Z"
    
    @pytest.fixture(scope='module')
    def dict_serv(self):
        sqs_serv = SQSService().connect()
        
        yield {'sqs': sqs_serv}
        
        sqs_serv.close_connection()
    
    @pytest.fixture(scope='module')
    def api_gateway_url(self):
        stack_name = os.environ.get("AWS_SAM_STACK_NAME")

        if stack_name is None:
            raise ValueError('Please set the AWS_SAM_STACK_NAME environment variable to the name of your stack')

        client = boto3.client("cloudformation")

        try:
            response = client.describe_stacks(StackName=stack_name)
        except Exception as e:
            raise Exception(
                f"Cannot find stack {stack_name} \n" f'Please make sure a stack with the name "{stack_name}" exists'
            ) from e

        stacks = response["Stacks"]
        stack_outputs = stacks[0]["Outputs"]
        api_outputs = [output for output in stack_outputs if output["OutputKey"] == "UtilApiEndpoint"]

        if not api_outputs:
            raise KeyError(f"UtilApiEndpoint not found in stack {stack_name}")

        return api_outputs[0]["OutputValue"]
    
    @pytest.fixture(scope='module')
    def auth_id_token(self, api_gateway_url):
        auth_token = 'eyJraWQiOiJJb2M4aGhoMVkrUEpzT1M4OXg1XC9Pb0FnNmxHc3pMTDdvcXlMdElnakZ3cz0iLCJhbGciOiJSUzI1NiJ9.eyJzdWIiOiI4MmQ3OWRjYy0xMThiLTQ4ZDEtYTBmMi03ZGRhZmU1NTdiOGUiLCJlbWFpbF92ZXJpZmllZCI6dHJ1ZSwiaXNzIjoiaHR0cHM6XC9cL2NvZ25pdG8taWRwLnVzLWVhc3QtMS5hbWF6b25hd3MuY29tXC91cy1lYXN0LTFfdGxlM2x5ZFl0IiwiY29nbml0bzp1c2VybmFtZSI6IjgyZDc5ZGNjLTExOGItNDhkMS1hMGYyLTdkZGFmZTU1N2I4ZSIsIm9yaWdpbl9qdGkiOiI0ZjE0ZjZlZS0zMTkyLTQzMGUtODEwMi1hNmFmZjA5OGQ1MWQiLCJhdWQiOiIxaGZrcWJzdjdlZ3NtMm5uY2szbHNyc3B2IiwiZXZlbnRfaWQiOiIwNTI2ZjAzMC03ZjJkLTQ4YzItYjlkMC0wNDRlZTIyZDRhOTkiLCJ0b2tlbl91c2UiOiJpZCIsImF1dGhfdGltZSI6MTY5Mzk0NDY0OCwiZXhwIjoxNjkzOTQ4MjQ4LCJpYXQiOjE2OTM5NDQ2NDgsImp0aSI6IjZhNTcwZDYzLWRkNzItNDVkYi1iZDEzLWRhZjFmODQ0ODE4YiIsImVtYWlsIjoidGVzdF9lbWFpbEBnbWFpbC5jb20ifQ.CF4YY4PNMAa71dnj_E27xPuAsRmVq1bNESBJ-GNtM-cfbCYPO2WeETH0KOAH0IaMAhiFsdK5P6C6YAUb9f0RNEHLnBIhnL59RkObQroMb3Cyjn5Ah5P3rbMBR_WY_-q_RKFAiYi9nkvhDiAqZZh_Hu67AeFsf-2J3wLE7Jw-TRJ1AipzMP-EDrhoUc-_l1l5Xmc5Tn8Z6FzIfalunr-RPF_juxJhma7gTI3dF2z1NXAfPi3YMeRCFCqq81Rx_wsgzEVmUkJWg2N2N8Q6rXb8yLlOeMJ5cQxq10zVmmAkoM3wVVMHNDPGXZ9qgJTvLN9thkTg8qGIzgrr638kq7t0nQ'
        
        response = requests.post(
            url=api_gateway_url + 'login', 
            data=json.dumps({
                "username": "test_email@gmail.com",
                "password": "test1234",
                "queue_name": "test_queue"
            }),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_token}"
            }
        )
        
        time.sleep(3)
        
        response = requests.get(
            url=api_gateway_url + 'login/test_queue',
            headers={
                "Authorization": f"Bearer {auth_token}"
            }
        )
        
        response_text = json.loads(response.text)
        response_body = json.loads(response_text['ReceiveMessageResponse']['ReceiveMessageResult']['messages'][0]['Body'])
        response_auth_id_token = response_body['body']['AuthIdToken']
        
        return response_auth_id_token
    
    def test_login_queue(self, api_gateway_url, test_queue, login_queue_name):
        
        login_data = json.dumps({
            "request_body": {
                "username": "test_email@gmail.com",
                "password": "test1234",
                "queue_name": test_queue
            }
        })
        sqs_serv = SQSService().connect()
        
        queue_url = sqs_serv.get_queue_url(queue_name=login_queue_name)
        sqs_serv.send_message(
            queue_url=queue_url,
            message_body=login_data
        )
        
        time.sleep(3)
        
        test_queue_url = sqs_serv.get_queue_url(queue_name=test_queue)
        response = sqs_serv.receive_message(queue_url=test_queue_url)
        response_body = json.loads(response['Messages'][0]['Body'])
        
        assert response_body['statusCode'] == 200
        assert response_body['body']['AuthIdToken'] is not None
        
    def test_unpaid_utils(self, api_gateway_url, apart_id, auth_id_token, test_queue):
        
        response = requests.post(
            url=api_gateway_url + 'get_utils/' + apart_id,
            data=json.dumps({
                "queue_name": "test_queue"
            }),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_id_token}"
            }
        )

        time.sleep(3)

        response = requests.get(
            url=api_gateway_url + 'get_utils/' + apart_id + '/' + test_queue,
            headers={
                "Authorization": f"Bearer {auth_id_token}"
            }
        )

        response_text = json.loads(response.text)
        response_body = json.loads(response_text['ReceiveMessageResponse']['ReceiveMessageResult']['messages'][0]['Body'])
        
        assert response_body['body']['bills'][0]['util_name'] == 'Util_1'
        assert response_body['body']['bills'][1]['util_name'] == 'Util_2'
        
    def test_paid_utils(self, api_gateway_url, apart_id, auth_id_token, test_queue):
        
        response = requests.post(
            url=api_gateway_url + 'get_history/' + apart_id,
            data=json.dumps({
                "queue_name": "test_queue",
                "date_up": "",
                "date_down": "2023-09-05 23:09:10"
            }),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_id_token}"
            }
        )

        time.sleep(3)

        response = requests.get(
            url=api_gateway_url + 'get_history/' + apart_id + '/' + test_queue,
            headers={
                "Authorization": f"Bearer {auth_id_token}"
            }
        )

        response_text = json.loads(response.text)
        response_body = json.loads(response_text['ReceiveMessageResponse']['ReceiveMessageResult']['messages'][0]['Body'])
        
        assert response_body['statusCode'] == 200
        assert response_body['body']['payments'][0][3] == '2023-03-01;2023-01-01'
        
    def test_payment_utils(self, api_gateway_url, apart_id, auth_id_token, test_queue):
        
        response = requests.post(
            url=api_gateway_url + 'pay_utils/' + apart_id,
            data=json.dumps({
                "queue_name": test_queue,
                "bills_id": [10, 11, 13, 14]
            }),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {auth_id_token}"
            }
        )

        time.sleep(3)

        response = requests.get(
            url=api_gateway_url + 'get_utils/' + apart_id + '/' + test_queue,
            headers={
                "Authorization": f"Bearer {auth_id_token}"
            }
        )
        
        response_text = json.loads(response.text)
        response_body = json.loads(response_text['ReceiveMessageResponse']['ReceiveMessageResult']['messages'][0]['Body'])
        
        assert response_body['statusCode'] == 204
        assert response_body['body'] == {}