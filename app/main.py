# app/main.py
from fastapi import FastAPI, HTTPException, Header
import os, base64
from kubernetes import client, config
from kubernetes.client.rest import ApiException

app = FastAPI()

# Load in-cluster config (this runs inside OpenShift)
try:
    config.load_incluster_config()
    k8s = client.CoreV1Api()
except Exception as e:
    k8s = None
    # In dev you could also load kubeconfig: config.load_kube_config()

# AUTH_KEY is mounted from a k8s secret (see k8s manifests)
AUTH_KEY = os.environ.get("AUTH_KEY", "change-me")
NAMESPACE = os.environ.get("NAMESPACE", "my-namespace")

@app.get("/secret/{name}")
def get_secret(name: str, x_internal_api_key: str = Header(None)):
    # Basic API-key auth between API Connect and this bridge
    if not x_internal_api_key or x_internal_api_key != AUTH_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not k8s:
        raise HTTPException(status_code=500, detail="Kubernetes client not configured")

    try:
        sec = k8s.read_namespaced_secret(name, NAMESPACE)
        # expecting the key inside secret.data["api-key"]
        encoded = sec.data.get("api-key")
        if not encoded:
            raise HTTPException(status_code=404, detail="Key 'api-key' not found in secret")
        value = base64.b64decode(encoded).decode("utf-8")
        return {"apiKey": value}
    except ApiException as e:
        # forward status code for easier debugging
        raise HTTPException(status_code=e.status, detail=e.reason)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
