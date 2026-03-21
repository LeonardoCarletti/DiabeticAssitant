import requests
import httpx
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# Requests Patch
old_request = requests.Session.request
def new_request(self, method, url, **kwargs):
    kwargs['verify'] = False
    return old_request(self, method, url, **kwargs)
requests.Session.request = new_request

# HTTPX Patch (OpenAI client uses HTTPX)
old_httpx_send = httpx.Client.send
def new_httpx_send(self, request, **kwargs):
    self._verify = False 
    return old_httpx_send(self, request, **kwargs)
httpx.Client.send = new_httpx_send

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Diabetics Assistant API",
    description="API for the Personal Diabetics Assistant (RAG, Exames, Perfil, Predict)",
    version="1.0.0"
)

# Configurando CORS para permitir que o frontend acesse a API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Em produção, defina o domínio do frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from backend.api import rag_routes
from backend.api import profile_routes
from backend.api import predict_routes
from backend.api import exam_routes
from backend.api import nutrition_routes
from backend.api import workout_routes
from backend.api import logs_routes
from backend.api import autonomous_routes
from backend.api import recovery_routes
from backend.api import automation_routes
from backend.api import experiment_routes
from backend.api import report_routes
from backend.api import auth_routes
from backend.api import sync_routes

app.include_router(rag_routes.router)
app.include_router(profile_routes.router)
app.include_router(predict_routes.router)
app.include_router(exam_routes.router)
app.include_router(nutrition_routes.router)
app.include_router(workout_routes.router)
app.include_router(logs_routes.router)
app.include_router(autonomous_routes.router)
app.include_router(recovery_routes.router)
app.include_router(automation_routes.router)
app.include_router(experiment_routes.router)
app.include_router(report_routes.router)
app.include_router(auth_routes.router)
app.include_router(sync_routes.router)

@app.get("/")
def read_root():
    return {"message": "Diabetics Assistant API is running!"}
