from locust import HttpLocust, TaskSet, task

class MyTaskSet(TaskSet):
    @task(1)
    def translateObject(self):
        self.client.post("/translateObject", files={'image1': open('object.png', 'rb')}, data={'language':'fr'})

class MyLocust(HttpLocust):
    task_set = MyTaskSet
    min_wait = 1000
    max_wait = 2000