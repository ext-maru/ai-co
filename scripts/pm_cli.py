import pika
import json

def send_task(prompt, task_type="general"):
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='task_queue', durable=True)

    task = {
        "task_id": "pm_cli_task",
        "type": task_type,
        "prompt": prompt
    }

    channel.basic_publish(exchange='', routing_key='task_queue',
                          body=json.dumps(task),
                          properties=pika.BasicProperties(delivery_mode=2))
    print("タスク送信完了:", task)

def main():
    print("PM CLI 簡易版 - タスク送信用")
    while True:
        prompt = input("タスク内容（終了はexit）> ")
        if prompt.lower() == "exit":
            break
        send_task(prompt)

if __name__ == "__main__":
    main()
