def register(client, username="alice", password="Correct-Horse-42!"):
    return client.post("/api/register", json={"username": username, "password": password})


def login(client, username="alice", password="Correct-Horse-42!"):
    return client.post("/api/login", json={"username": username, "password": password})
