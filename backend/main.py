from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fathom.routers import tasks
from fathom.routers import playground as playground_router
import os
from dotenv import load_dotenv
import asyncio

# LUSID SDK (async factory) and aiohttp client session
import lusid
from lusid.extensions.configuration_loaders import SecretsFileConfigurationLoader
import aiohttp

# Load environment variables (backend/.env, repo-root .env.local fallback)
load_dotenv()
repo_root_env = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
repo_root_env_local = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env.local"))
if os.path.exists(repo_root_env):
    load_dotenv(repo_root_env, override=True)
if os.path.exists(repo_root_env_local):
    load_dotenv(repo_root_env_local, override=True)

async def lifespan(app: FastAPI):
    # Resolve secrets path (absolute)
    env_secrets = os.getenv("FBN_SECRETS_PATH") or os.getenv("LUSID_SECRETS_PATH")
    if not env_secrets:
        # Default to repo-root secrets.json
        env_secrets = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "secrets.json"))
    secrets_path = os.path.abspath(env_secrets)

    # Ensure file exists early for clearer errors
    if not os.path.exists(secrets_path):
        print(f"[Fathom] LUSID secrets not found at: {secrets_path}")
    else:
        print(f"[Fathom] Using LUSID secrets: {secrets_path}")

    # Create shared aiohttp session and ApiClientFactory
    session = aiohttp.ClientSession()
    try:
        loader = SecretsFileConfigurationLoader(secrets_path)
        app.state.lusid_factory = lusid.ApiClientFactory(
            config_loaders=[loader],
            app_name="Fathom",
            client_session=session
        )
        print("[Fathom] LUSID ApiClientFactory initialised")
    except Exception as e:
        print(f"[Fathom] Failed to initialise LUSID ApiClientFactory: {e}")
        app.state.lusid_factory = None

    yield

    # Teardown
    try:
        await session.close()
    except Exception:
        pass


app = FastAPI(
    title="Fathom Backend",
    description="LUSID Workflow Task Investigation API",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(tasks.router, prefix="/fathom", tags=["tasks"])
app.include_router(playground_router.router, prefix="/v1/playground", tags=["playground"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "fathom-backend"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
