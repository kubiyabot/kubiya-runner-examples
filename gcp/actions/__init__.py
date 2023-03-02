"""instatiate action and declare it's secrets"""
import kubiya
import os

action_store = kubiya.ActionStore(
    "gcp", "0"
)


#Todo - add container env var instead of gcp.yml secret
# action_store.uses_secrets(
#     [
#         "GOOGLE_APPLICATION_CREDENTIALS"
#     ]
# )
# os.environ['GOOGLE_APPLICATION_CREDENTIALS']=action_store.secrets.get("GOOGLE_APPLICATION_CREDENTIALS")