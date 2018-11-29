import google.auth

def login():
    credentials, project = google.auth.default()
    print(credentials)
    print(project)
    print("ok")

login()

