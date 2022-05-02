#!/usr/bin/env python3
import os
import sys
import pika
import json
import time

sys.path.insert(0, '.')

from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

from mos.compute import tasks

def main():

    print('MOS Python worker')
    print('-----------------')

    credentials = pika.PlainCredentials(
      os.getenv('MOS_RABBIT_USR', 'guest'),  
      os.getenv('MOS_RABBIT_PWD', 'guest'),
    )

    conn_retries = 0
    conn_retries_max = int(os.getenv('MOS_COMPUTE_CONN_RETRIES_MAX', 60))
    conn_retries_int = int(os.getenv('MOS_COMPUTE_CONN_RETRIES_INT', 5))
    while conn_retries < conn_retries_max:
        try:
            connection = pika.BlockingConnection(pika.ConnectionParameters(
                host=os.getenv('MOS_RABBIT_HOST', 'localhost'),
                port=os.getenv('MOS_RABBIT_PORT', 5672),
                credentials=credentials
            )) 
            break
        except pika.exceptions.AMQPConnectionError:
            print('Waiting for message queue to be available ...')
            time.sleep(conn_retries_int)
            conn_retries += 1
    else:
        raise Exception("Unable to connect to rabbitmq")

    channel = connection.channel()
    channel.queue_declare(queue='mos-python')

    def callback(ch, method, properties, body):
        body = json.loads(body)
        print("Task received %r" %body)
        tasks.model_run(body['model_id'],
                        body['model_name'],
                        body['caller_id'])
        print("Task done")  

    print('Consuming messages ...')
    channel.basic_consume(queue='mos-python', on_message_callback=callback, auto_ack=True)
    channel.start_consuming()

if __name__ == '__main__':

    try:
        main()
    except KeyboardInterrupt:
        print('Interrupted')
        sys.exit(0)