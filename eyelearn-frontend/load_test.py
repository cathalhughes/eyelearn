from locust import HttpLocust, TaskSet, task

class MyTaskSet(TaskSet):
    def on_start(self):
        res = self.client.post('/login', data=dict(
            username="student",
            password="1"
        ))
        res.raise_for_status()

    @task(1)
    def index(self):
        self.client.get("/")

    @task(1)
    def diff(self):
        self.client.post("/difficulty")

    @task(1)
    def chooseGame(self):
        self.client.post("/chooseGame")

    @task(1)
    def checkGuess(self):
        self.client.cookies["languageIndex"] = "0"
        self.client.cookies["word"] = "car"
        self.client.cookies["numGames"] = "0"
        self.client.cookies["correct"] = "0"
        self.client.cookies["activity_id"] = "6"
        self.client.post(
            '/checkguess',
            data={"guess": "car"}
        )

    @task(1)
    def scramble(self):
        self.client.cookies["word"] = "car"
        self.client.cookies["languageIndex"] = "0"
        self.client.cookies["activity_id"] = "6"
        self.client.post(
            '/scramble'
        )

    @task(1)
    def tts(self):
        self.client.cookies["word"] = "car"
        self.client.cookies["languageIndex"] = "0"
        self.client.cookies["activity_id"] = "6"
        self.client.post(
            '/tts'
        )

    @task(1)
    def about(self):
        self.client.get("/about")

    @task(1)
    def playAgain(self):
        self.client.post(
            '/playAgain',
            data={"status": "correct",
                  "path": "/tts"},

        )

    @task(1)
    def answer(self):
        self.client.cookies['languageIndex'] = "0"
        self.client.cookies['word'] = "car"
        self.client.post(
            '/answer',
            data={"path": "/tts"}
        )

    def endGame(self):
        pass

    @task(1)
    def selfie(self):
        self.client.cookies['languageIndex'] = "0"
        self.client.cookies['word'] = "car"
        self.client.cookies["activity_id"] = "3"
        self.client.post(
            '/selfie/sports'
        )

    @task(1)
    def imagenet(self):
        self.client.cookies['languageIndex'] = "0"
        self.client.cookies['word'] = "car"
        self.client.cookies["activity_id"] = "5"
        self.client.post(
            '/imagenet/classroom'
        )








class MyLocust(HttpLocust):
    task_set = MyTaskSet
    min_wait = 1000
    max_wait = 2000