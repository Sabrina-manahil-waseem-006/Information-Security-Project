from locust import HttpUser, task, constant


class NormalUser(HttpUser):
    wait_time = constant(1)

    @task
    def visit(self):
        self.client.get("/")


class VolumetricFlood(HttpUser):
    wait_time = constant(0.01)   # 10ms → ~100 req/s per user

    @task
    def flood(self):
        self.client.get("/")


class VolumetricFloodWithProbes(HttpUser):
    wait_time = constant(0.01)

    @task(9)
    def flood(self):
        self.client.get("/")

    @task(1)
    def probe(self):
        self.client.get("/health")
