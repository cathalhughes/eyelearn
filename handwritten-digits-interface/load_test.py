from locust import HttpLocust, TaskSet, task
import base64

class MyTaskSet(TaskSet):
    @task(1)
    def predictCharacter(self):
        with open("static/testing/emnist.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        self.client.post(
            '/predictCharacter',
            data=encoded_string,
            verify=False
        )

    @task(2)
    def predictNumber(self):
        with open("static/testing/emnist.png", "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read())
        self.client.post(
            '/predictNumber',
            data=encoded_string,
            verify=False
        )



class MyLocust(HttpLocust):
    task_set = MyTaskSet
    min_wait = 1000
    max_wait = 2000