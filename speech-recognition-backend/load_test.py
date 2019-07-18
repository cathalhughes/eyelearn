from locust import HttpLocust, TaskSet, task

class MyTaskSet(TaskSet):
    @task(1)
    def predictWord(self):
        audio = open("static/testing/hello.wav", "rb")
        self.client.post(
            '/predictWord',
            files={'audio_data': audio, 'recognition_language': 'EN-en'}
        )

    ##https://34.73.3.3


class MyLocust(HttpLocust):
    task_set = MyTaskSet
    min_wait = 1000
    max_wait = 2000