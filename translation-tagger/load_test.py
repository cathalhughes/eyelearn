from locust import HttpLocust, TaskSet, task

class MyTaskSet(TaskSet):
    @task(1)
    def getPhraseTranslation(self):
        data = {"phrase": "I am free", "language": "fr"}
        self.client.post("/getPhraseTranslation1", data=data)


class MyLocust(HttpLocust):
    task_set = MyTaskSet
    min_wait = 1000
    max_wait = 2000