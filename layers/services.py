import json
import boto3
import redis
import psycopg2

class SecManagerService:
    def __init__(self):
        self.client = None 

    def connect(self):
        self.client = boto3.client('secretsmanager')
        
        return self
        
    def get_credentials(self, secret_id):
        secret = self.client.get_secret_value(SecretId=secret_id)
        secret_dict = json.loads(secret['SecretString'])
        
        return secret_dict
        
    def close_connection(self):
        self.client.close()

class RDSService:
    def __init__(self, host, port, dbname, user, password):
        self.host = host
        self.port = port
        self.dbname = dbname
        self.user = user
        self.password = password
        self.client = None
        self.cursor = None
    
    def connect(self):
        self.client = psycopg2.connect(
            host=self.host,
            port=self.port,
            dbname=self.dbname,
            user=self.user,
            password=self.password
        )
        
        return self
    
    def open_cursor(self):
        self.cursor = self.client.cursor()
        
        return self
        
    def close_cursor(self):
        self.cursor.close()
        
    def commit(self):
        self.client.commit()
        
    def rollback(self):
        self.client.rollback()
    
    def select(self, query, data):
        self.cursor.execute(query, data)
        result_rows = self.cursor.fetchall()
        
        return result_rows
    
    def update(self, query, data):
        self.cursor.executemany(query, data)
        
    def close_connection(self):
        self.client.close()
        
class RedisService:
    def __init__(self, address, port):
        self.address = address
        self.port = port
        self.client = None

    def connect(self):
        self.client = redis.Redis(
            host=self.address,
            port=self.port,
            decode_responses=True
        )
        
        return self
        
    def set_value(self, key, new_value):
        self.client.set(key, new_value)
        
    def get_value(self, key):
        value = self.client.get(key)
        
        return value
        
    def delete_value(self, key):
        self.client.delete(key)
        
    def close_connection(self):
        self.client.close()
        
class SQSService:
    def __init__(self):
        self.client = None 

    def connect(self):
        self.client = boto3.client('sqs')
        
        return self
        
    def create_queue(self, queue_name):
        result = self.client.create_queue(QueueName=queue_name)
        
        return result['QueueUrl']
        
    def get_queue_url(self, queue_name):
        try:
            queue_url = self.client.get_queue_url(QueueName=queue_name)
            
            return queue_url['QueueUrl']
        except Exception as e:
            raise #RuntimeError("An unexpected error occurred while getting the url of the queue.")
    
    def send_message(self, queue_url, message_body):
        try:
            self.client.send_message(QueueUrl=queue_url, MessageBody=message_body)
        except Exception as e:
            raise #RuntimeError("An unexpected error occurred while sending message.")
            
    def receive_message(self, queue_url):
        try:
            response = self.client.receive_message(QueueUrl=queue_url)
            
            return response
        except Exception as e:
            raise RuntimeError("An unexpected error occurred while receiving message.")
        
    def close_connection(self):
        self.client.close()

class CognitoService:
    def __init__(self):
        self.client = None

    def connect(self):
        self.client = boto3.client('cognito-idp')
        
        return self
    
    def init_auth(self, username, password, client_id, secret_hash, auth_flow):
        try:    
            auth_result = self.client.initiate_auth(
                ClientId=client_id,
                AuthFlow=auth_flow,
                AuthParameters={
                    'USERNAME': username,
                    'PASSWORD': password,
                    'SECRET_HASH': secret_hash
                }
            )
    
            return auth_result['AuthenticationResult']
        except self.client.exceptions.NotAuthorizedException:
            raise ValueError("Authentication failed. Please check your username, password, and client credentials.")
        except self.client.exceptions.UserNotFoundException:
            raise ValueError("User not found. Please check your username and client credentials.")
        except self.client.exceptions.InvalidParameterException:
            raise ValueError("Invalid parameters provided. Please check your input data.")
        except Exception as e:
            raise RuntimeError("An unexpected error occurred during the authentication process.")

    def get_client_secret(self, pool_id, client_id):
        try:
            description = self.client.describe_user_pool_client(
                UserPoolId=pool_id,
                ClientId=client_id
            )
            
            return description['UserPoolClient']['ClientSecret']
        except Exception as e:
            raise RuntimeError("An unexpected error occurred while retrieving the client secret.")
        
    def close_connection(self):
        self.client.close()