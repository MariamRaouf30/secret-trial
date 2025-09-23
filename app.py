from fastapi import FastAPI, HTTPException, Header
from kubernetes import client, config
from kubernetes.client.rest import ApiException
import base64, os

app = FastAPI()

# Load in-cluster config (only works inside OpenShift)
try:
    config.load_incluster_config()
    k8s = client.CoreV1Api()
except Exception as e:
    k8s = None

# Env vars (set in Deployment in UI)
NAMESPACE = os.environ.get("NAMESPACE", "ibm-common-services")
AUTH_KEY = os.environ.get("AUTH_KEY", "default")

@app.get("/secret/{name}")
def get_secret(name: str, x_internal_api_key: str = Header(None)):
    # Simple auth for API Connect <-> bridge
    if not x_internal_api_key or x_internal_api_key != AUTH_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")

    if not k8s:
        raise HTTPException(status_code=500, detail="Kubernetes not available")

    try:
        sec = k8s.read_namespaced_secret(name, NAMESPACE)
        encoded = sec.data.get("api-key")
        if not encoded:
            raise HTTPException(status_code=404, detail="Key 'api-key' not found")
        value = base64.b64decode(encoded).decode("utf-8")
        return {"apiKey": value}
    except ApiException as e:
        raise HTTPException(status_code=e.status, detail=e.reason)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
