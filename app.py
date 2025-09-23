from fastapi import FastAPI, HTTPException
from kubernetes import client, config
import base64

app = FastAPI()

config.load_incluster_config()
k8s = client.CoreV1Api()

NAMESPACE = "ibm-common-services"

@app.get("/secret/{name}")
def get_secret(name: str):
    try:
        sec = k8s.read_namespaced_secret(name, NAMESPACE)
        encoded = sec.data.get("api-key")
        if not encoded:
            raise HTTPException(status_code=404, detail="Key 'api-key' not found in secret")
        value = base64.b64decode(encoded).decode("utf-8")
        return {"apiKey": value}
    except client.exceptions.ApiException as e:
        raise HTTPException(status_code=e.status, detail=e.reason)
