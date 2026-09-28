from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from backend.api.language import router as language_router
from backend.api.history import router as history_router
from backend.api.report import router as report_router
from backend.api.verify import router as verify_router
from backend.config.settings import get_settings
from backend.services.case_store import init_db
from backend.utils.logger import configure_logging

s=get_settings(); configure_logging(s.log_level)

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app=FastAPI(title=s.app_name,version=s.version,description='Evidence-assisted fake-news verification API.',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=s.cors_list,allow_credentials=False,allow_methods=['GET','POST','OPTIONS'],allow_headers=['*'])
app.include_router(language_router)
app.include_router(history_router)
app.include_router(report_router)
app.include_router(verify_router)

@app.get('/health')
async def health(): return {'status':'ok','version':s.version}

frontend=Path(__file__).resolve().parents[1]/'frontend'
if frontend.exists(): app.mount('/',StaticFiles(directory=frontend,html=True),name='frontend')
