import json
import boto3
import redis
import psycopg2
import datetime
from decimal import Decimal
from redis import RedisError
from functools import wraps
import hmac, hashlib, base64
from abc import ABC, abstractmethod
from sql_queries import SqlQueriesEnum

class QueryWrapper(ABC):
            
    def __init__(self, request_body=None, path_params=None, services=None):
        self.request_body = request_body
        self.path_params = path_params
        self.services = services
        self.response_status_code = 200
        #TODO: REsponse code
        self.response_body = ""
    
    @staticmethod
    def serialize_json(obj):
        """
        JSON serializer which works with Decimal and DateTime types.
        """
        if isinstance(obj, Decimal):
            if float(obj).is_integer():
                return int(obj)
            else:
                return float(obj)
        
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        
        raise TypeError
    
    @abstractmethod
    def process(self, *args, **kwargs):
        pass
        
    def put_message_sqs(self):
        queue_url = self.services['sqs'].get_queue_url(queue_name=self.request_body['queue_name'])
        
        self.services['sqs'].send_message(
            queue_url=queue_url,
            message_body=json.dumps({
                    "statusCode": self.response_status_code,
                    "body": self.response_body
                },
                default=QueryWrapper.serialize_json
            )
        )

    def get_response(self):
        return json.dumps({
            "statusCode": self.response_status_code,
            "body": self.response_body
        })

class TotalUtilitiesQuery(QueryWrapper):
    
    def process(self):
        try:
            key = self.path_params['apartment_id'] + '#Unpaid'
            value = self.services['cache'].get_value(key)
            
            if value:
                self.response_status_code = 200
                self.response_body = json.loads(value)
            else:
                raise ValueError
    
        except KeyError as e:
            self.response_status_code = 400
            self.response_body = {
                "error": "The request has an invalid format."
            }
        except (RedisError, ValueError) as e:
            self.response_status_code = 500
            self.response_body = {
                "error": "The data was not received. There is an internal error on the server."
            }
            
class HistoryUtilitiesQuery(QueryWrapper):
    
    def get_history(self, date_up_client, date_down_client, apartment_id):
        data = {'date_up': date_up_client, 'date_down': date_down_client, 'apart_id': apartment_id}
        result_rows = []
        
        if date_up_client:
            date_up_server = self.services['cache'].get_value(apartment_id + "#DateUp")
            date_up_client = datetime.datetime.strptime(date_up_client, '%Y-%m-%d %H:%M:%S')
            date_up_server = datetime.datetime.strptime(date_up_server, '%Y-%m-%d %H:%M:%S')

            if date_up_client < date_up_server:
                result_rows = self.services['rds'].select(SqlQueriesEnum.hist_utils, data)
        elif date_down_client:
            date_down_server = self.services['cache'].get_value(apartment_id + "#DateDown")
            date_down_client = datetime.datetime.strptime(date_down_client, '%Y-%m-%d %H:%M:%S')
            date_down_server = datetime.datetime.strptime(date_down_server, '%Y-%m-%d %H:%M:%S')

            if date_down_client > date_down_server:
                result_rows = self.services['rds'].select(SqlQueriesEnum.hist_utils, data)
           
        return result_rows
    
    def process(self):
        try:
            date_up_client = self.request_body['date_up']
            date_down_client = self.request_body['date_down']
            apartment_id = self.path_params['apartment_id']
            
            result_rows = self.get_history(date_up_client, date_down_client, apartment_id)

            self.response_status_code = 200
            self.response_body = {"payments" : result_rows}
        except Exception as e:
            #TODO: Code of exceptions
            self.response_status_code = 400
            self.response_body = {
                "error": str(e) + ':::' + str(date_up_client is None) + ':::' + date_up_client + ':::' + str(date_down_client is None) + ':::' + date_down_client
            }

class PaymentUtilitiesQuery(QueryWrapper):

    def update_cache(self, apartment_id, bills_id):
        unpaid_utils = json.loads(self.services['cache'].get_value(apartment_id + "#Unpaid"))['bills']
        
        for bill_id in bills_id:
            for util_idx in range(len(unpaid_utils)):
                if bill_id in unpaid_utils[util_idx]['bills_id']:
                    del_idx = unpaid_utils[util_idx]['bills_id'].index(bill_id)
                    unpaid_utils[util_idx]['bills_id'].pop(del_idx)
                    unpaid_utils[util_idx]['pay_periods'].pop(del_idx)
                    unpaid_utils[util_idx]['payments'].pop(del_idx)
        
        self.services['cache'].set_value(
            apartment_id + "#Unpaid",
            json.dumps({
                'bills' : unpaid_utils
            })
        )
    
    def process(self):
        try:
            current_date = str(datetime.date.today())
            bills_upd = [(current_date, bill_id) for bill_id in self.request_body['bills_id']]
            
            self.services['rds'].update(SqlQueriesEnum.pay_utils, bills_upd)
            self.services['rds'].commit()
            
            self.update_cache(self.path_params['apartment_id'], self.request_body['bills_id'])
            
            self.response_status_code = 204
            self.response_body = {}
        except Exception as e:
            #TODO: Code of exceptions
            self.services['rds'].rollback()
            self.response_status_code = 400
            self.response_body = {
                "error": str(e)
            }
    
class LoginQuery(QueryWrapper):

    def calc_secret_hash(self, username, client_id, client_secret):
        try:
            message = bytes(f'{username}{client_id}', 'utf-8')
            client_secret = bytes(client_secret,'utf-8')
            secret_hash = base64.b64encode(hmac.new(client_secret, message, digestmod=hashlib.sha256).digest()).decode()
    
            return secret_hash
        except (TypeError, ValueError, UnicodeEncodeError) as e:
            raise ValueError("Invalid input data. Please check the username.")
        except Exception as e:
            raise RuntimeError("An unexpected error occurred while calculating the secret hash.")

    def process(self, pool_id, client_id):
        try:
            username = self.request_body['username']
            password = self.request_body['password']
            queue_name = self.request_body['queue_name']
            
            client_secret = self.services['cognito'].get_client_secret(pool_id, client_id)
            secret_hash = self.calc_secret_hash(username, client_id, client_secret)
    
            auth_result = self.services['cognito'].init_auth(username, password, client_id, secret_hash, 'USER_PASSWORD_AUTH')
            id_token = auth_result['IdToken']
    
            queue_url = self.services['sqs'].create_queue(queue_name)
    
            self.response_status_code = 200
            self.response_body = {
                "AuthIdToken" : id_token
            }
        except (KeyError, TypeError, ValueError, UnicodeEncodeError) as e:
            self.response_status_code = 400
            self.response_body = {
                "error": "Invalid request body data. Please check if all required fields are provided and have valid values."
            }
        except Exception as e:
            self.response_status_code = 500
            self.response_body = {
                "error": "An unexpected error occurred while processing the request."
            }