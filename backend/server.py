from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from sqlmodel import SQLModel, Field, create_engine, select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
import os
import logging
import asyncio
from pathlib import Path
from pydantic import BaseModel, EmailStr
from typing import Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import mercadopago
import random
import resend

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Database Configuration
# Default to absolute path for SQLite database
_default_db_path = ROOT_DIR / 'data' / 'app.db'
_default_db_url = f'sqlite+aiosqlite:///{_default_db_path}'
DATABASE_URL = os.environ.get('DATABASE_URL', _default_db_url)

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)

# Create session maker
async_session_maker = async_sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# JWT config
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'

# Mercado Pago SDK
mp_access_token = os.environ.get('MERCADO_PAGO_ACCESS_TOKEN', '')
if mp_access_token:
    mp = mercadopago.SDK(mp_access_token)
else:
    mp = None

# Resend
resend_api_key = os.environ.get('RESEND_API_KEY', '')
if resend_api_key:
    resend.api_key = resend_api_key

SENDER_EMAIL = os.environ.get('SENDER_EMAIL', 'onboarding@resend.dev')
FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:3000')

# Initialize database on startup
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    # Ensure data directory exists for SQLite
    if 'sqlite' in DATABASE_URL.lower():
        # Extract path from DATABASE_URL (format: sqlite+aiosqlite:///path/to/db.db)
        if ':///' in DATABASE_URL:
            db_path = Path(DATABASE_URL.split(':///', 1)[1])
            db_dir = db_path.parent
            db_dir.mkdir(parents=True, exist_ok=True)
            logging.info(f"Ensured database directory exists: {db_dir}")
    
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    logging.info("Database initialized")
    yield
    # Shutdown
    await engine.dispose()
    logging.info("Database connection closed")

app = FastAPI(title="Aviator Analytics Pro API", lifespan=lifespan)
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Setup static files and frontend serving
FRONTEND_BUILD_DIR = ROOT_DIR.parent / 'frontend' / 'build'

# Health check endpoint (no auth required) - must be before static files
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Mount static files if frontend build exists
if FRONTEND_BUILD_DIR.exists():
    # Mount static directory for assets
    static_dir = FRONTEND_BUILD_DIR / 'static'
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    
    # Serve index.html for root
    @app.get("/")
    async def serve_frontend_root():
        return FileResponse(str(FRONTEND_BUILD_DIR / 'index.html'))
else:
    # Fallback if frontend not built - show API info
    @app.get("/")
    @app.head("/")
    async def root():
        return {
            "service": "Aviator Analytics Pro API",
            "status": "healthy",
            "version": "1.0.0",
            "endpoints": {
                "health": "/health",
                "api": "/api",
                "docs": "/docs"
            },
            "note": "Frontend not built. Run 'cd frontend && npm run build' to enable frontend serving."
        }

# SQLModel Models
class User(SQLModel, table=True):
    __tablename__ = "users"
    
    id: str = Field(primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
    password_hash: str
    subscription_status: str = Field(default="inactive")
    created_at: str

class PendingPreference(SQLModel, table=True):
    __tablename__ = "pending_preferences"
    
    external_reference: str = Field(primary_key=True)
    email: str
    name: str
    created_at: str
    expires_at: str

class Subscription(SQLModel, table=True):
    __tablename__ = "subscriptions"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(index=True)
    status: str
    plan_id: str
    payment_id: str
    created_at: str
    next_billing_date: str

# Pydantic Models for API
class UserRegister(BaseModel):
    email: EmailStr
    name: str
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class SubscriptionCreate(BaseModel):
    email: EmailStr
    name: str

class AlertCreate(BaseModel):
    type: str
    multiplier_threshold: float
    probability: float
    risk_level: str

class AlertValidation(BaseModel):
    alert_id: str
    confirmed: bool

# Database session dependency
async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

# Auth helpers
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_jwt_token(user_id: str, email: str) -> str:
    payload = {
        'user_id': user_id,
        'email': email,
        'exp': datetime.now(timezone.utc) + timedelta(days=30)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    session: AsyncSession = Depends(get_session)
):
    token = credentials.credentials
    payload = verify_jwt_token(token)
    
    result = await session.execute(
        select(User).where(User.id == payload['user_id'])
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Email helper
async def send_email_async(recipient: str, subject: str, html: str):
    if not resend_api_key:
        logging.warning("Resend API key not configured, skipping email")
        return
    
    try:
        params = {
            "from": SENDER_EMAIL,
            "to": [recipient],
            "subject": subject,
            "html": html
        }
        await asyncio.to_thread(resend.Emails.send, params)
        logging.info(f"Email sent to {recipient}")
    except Exception as e:
        logging.error(f"Failed to send email: {str(e)}")

# Mock Aviator data generator
def generate_mock_multiplier():
    """Generate realistic Aviator multiplier"""
    rand = random.random()
    if rand < 0.5:
        return round(random.uniform(1.0, 2.0), 2)
    elif rand < 0.8:
        return round(random.uniform(2.0, 5.0), 2)
    elif rand < 0.95:
        return round(random.uniform(5.0, 10.0), 2)
    elif rand < 0.99:
        return round(random.uniform(10.0, 50.0), 2)
    else:
        return round(random.uniform(50.0, 100.0), 2)

# Routes
@api_router.post("/auth/register")
async def register(user: UserRegister, session: AsyncSession = Depends(get_session)):
    # Check if user exists
    result = await session.execute(
        select(User).where(User.email == user.email)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user_doc = User(
        id=user_id,
        email=user.email,
        name=user.name,
        password_hash=hash_password(user.password),
        subscription_status="inactive",
        created_at=datetime.now(timezone.utc).isoformat()
    )
    
    try:
        session.add(user_doc)
        await session.commit()
    except Exception as e:
        await session.rollback()
        logging.error(f"Failed to register user: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to register user")
    
    token = create_jwt_token(user_id, user.email)
    
    return {"token": token, "user_id": user_id, "email": user.email, "name": user.name}

@api_router.post("/auth/login")
async def login(credentials: UserLogin, session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(User).where(User.email == credentials.email)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(credentials.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if user.subscription_status != 'active':
        raise HTTPException(status_code=403, detail="Subscription inactive. Please subscribe to access.")
    
    token = create_jwt_token(user.id, user.email)
    
    return {
        "token": token,
        "user_id": user.id,
        "email": user.email,
        "name": user.name,
        "subscription_status": user.subscription_status
    }

@api_router.post("/subscription/create-preference")
async def create_preference(sub: SubscriptionCreate, session: AsyncSession = Depends(get_session)):
    # Check if user exists
    result = await session.execute(
        select(User).where(User.email == sub.email)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    external_reference = str(uuid.uuid4())
    
    # Store pending preference
    pending_pref = PendingPreference(
        external_reference=external_reference,
        email=sub.email,
        name=sub.name,
        created_at=datetime.now(timezone.utc).isoformat(),
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    )
    
    try:
        session.add(pending_pref)
        await session.commit()
    except Exception as e:
        await session.rollback()
        logging.error(f"Failed to create pending preference: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create subscription preference")
    
    if mp:
        preference_data = {
            "items": [
                {
                    "id": "MONTHLY_100",
                    "title": "Assinatura Mensal Aviator Analytics Pro",
                    "description": "Análise estatística profissional do jogo Aviator",
                    "quantity": 1,
                    "unit_price": 100.0
                }
            ],
            "payer": {
                "email": sub.email,
                "name": sub.name
            },
            "auto_return": "approved",
            "back_urls": {
                "success": f"{FRONTEND_URL}/subscription/success?ref={external_reference}",
                "failure": f"{FRONTEND_URL}/subscription/failure",
                "pending": f"{FRONTEND_URL}/subscription/pending"
            },
            "external_reference": external_reference,
            "metadata": {
                "user_email": sub.email,
                "user_name": sub.name
            }
        }
        
        try:
            result = mp.preference().create(preference_data)
            if result.get("status") == 201 and "response" in result:
                preference_id = result["response"]["id"]
            else:
                logging.error(f"Mercado Pago error: {result}")
                raise HTTPException(status_code=500, detail="Erro ao criar preferência no Mercado Pago")
        except Exception as e:
            logging.error(f"Mercado Pago exception: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Erro ao processar pagamento: {str(e)}")
    else:
        # Mock preference for testing without Mercado Pago credentials
        preference_id = f"mock_{external_reference}"
    
    return {"preference_id": preference_id, "external_reference": external_reference}

@api_router.post("/webhooks/mercado-pago")
async def handle_webhook(request: Request, session: AsyncSession = Depends(get_session)):
    body = await request.body()
    data = await request.json()
    
    # In production, verify signature here
    # signature = request.headers.get("x-signature")
    
    if data.get("type") == "payment":
        payment_id = data.get("data", {}).get("id")
        
        if mp:
            payment_info = mp.payment().get(payment_id)
            payment_status = payment_info["response"]["status"]
            external_reference = payment_info["response"].get("external_reference")
        else:
            # Mock for testing
            payment_status = "approved"
            external_reference = data.get("external_reference")
        
        if payment_status == "approved":
            result = await session.execute(
                select(PendingPreference).where(
                    PendingPreference.external_reference == external_reference
                )
            )
            pending = result.scalar_one_or_none()
            
            if pending:
                user_id = str(uuid.uuid4())
                password = str(uuid.uuid4())[:8]
                
                user_doc = User(
                    id=user_id,
                    email=pending.email,
                    name=pending.name,
                    password_hash=hash_password(password),
                    subscription_status="active",
                    created_at=datetime.now(timezone.utc).isoformat()
                )
                
                session.add(user_doc)
                
                next_billing = datetime.now(timezone.utc) + timedelta(days=30)
                subscription_doc = Subscription(
                    user_id=user_id,
                    status="active",
                    plan_id="MONTHLY_100",
                    payment_id=payment_id,
                    created_at=datetime.now(timezone.utc).isoformat(),
                    next_billing_date=next_billing.isoformat()
                )
                
                session.add(subscription_doc)
                
                # Delete pending preference
                await session.delete(pending)
                
                try:
                    await session.commit()
                except Exception as e:
                    await session.rollback()
                    logging.error(f"Failed to process webhook payment: {str(e)}")
                    return {"status": "error", "message": "Failed to process payment"}
                
                # Send confirmation email
                email_html = f"""
                <h2>Bem-vindo ao Aviator Analytics Pro</h2>
                <p>Olá {pending.name},</p>
                <p>Sua assinatura foi confirmada com sucesso!</p>
                <p><strong>Email:</strong> {pending.email}<br>
                <strong>Senha temporária:</strong> {password}</p>
                <p>Acesse o dashboard: <a href="{FRONTEND_URL}/login">{FRONTEND_URL}/login</a></p>
                <p>Por favor, altere sua senha após o primeiro acesso.</p>
                """
                await send_email_async(pending.email, "Assinatura Confirmada - Aviator Analytics Pro", email_html)
    
    return {"status": "received"}

@api_router.get("/subscription/check-status/{external_reference}")
async def check_subscription_status(external_reference: str, session: AsyncSession = Depends(get_session)):
    # Check for active user with subscription
    result = await session.execute(
        select(User).where(User.subscription_status == "active")
    )
    user = result.scalar_one_or_none()
    
    if user:
        sub_result = await session.execute(
            select(Subscription).where(Subscription.user_id == user.id)
        )
        subscription = sub_result.scalar_one_or_none()
        if subscription:
            return {
                "status": "active",
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "name": user.name,
                    "subscription_status": user.subscription_status,
                    "created_at": user.created_at
                }
            }
    
    # Check for pending preference
    pend_result = await session.execute(
        select(PendingPreference).where(
            PendingPreference.external_reference == external_reference
        )
    )
    pending = pend_result.scalar_one_or_none()
    
    if pending:
        return {"status": "pending"}
    
    return {"status": "not_found"}

@api_router.get("/dashboard/stats")
async def get_dashboard_stats(user = Depends(get_current_user)):
    # Generate mock statistics
    total_alerts = random.randint(150, 300)
    confirmed = random.randint(int(total_alerts * 0.6), int(total_alerts * 0.8))
    
    return {
        "total_alerts_issued": total_alerts,
        "confirmed_scenarios": confirmed,
        "confirmation_rate": round((confirmed / total_alerts) * 100, 1),
        "high_multipliers_today": random.randint(5, 15),
        "avg_multiplier": round(random.uniform(2.5, 4.5), 2)
    }

@api_router.get("/aviator/history")
async def get_aviator_history(user = Depends(get_current_user)):
    # Generate mock history
    history = []
    now = datetime.now(timezone.utc)
    
    for i in range(50):
        timestamp = now - timedelta(minutes=i*3)
        history.append({
            "timestamp": timestamp.isoformat(),
            "multiplier": generate_mock_multiplier()
        })
    
    return {"history": history}

@api_router.get("/alerts/recent")
async def get_recent_alerts(user = Depends(get_current_user)):
    # Generate mock alerts
    alert_types = [
        "Padrão de alta detectado",
        "Sequência de multiplicadores baixos",
        "Probabilidade elevada próximo round",
        "Ciclo histórico identificado"
    ]
    
    alerts = []
    now = datetime.now(timezone.utc)
    
    for i in range(10):
        timestamp = now - timedelta(minutes=random.randint(1, 120))
        alerts.append({
            "id": str(uuid.uuid4()),
            "type": random.choice(alert_types),
            "timestamp": timestamp.isoformat(),
            "multiplier_threshold": round(random.uniform(2.0, 10.0), 2),
            "probability": round(random.uniform(60, 85), 1),
            "risk_level": random.choice(["low", "medium", "high"])
        })
    
    return {"alerts": alerts}

@api_router.get("/alerts/validated")
async def get_validated_alerts(user = Depends(get_current_user)):
    # Generate mock validated alerts
    alerts = []
    
    for i in range(20):
        created = datetime.now(timezone.utc) - timedelta(hours=random.randint(1, 72))
        confirmed = random.random() > 0.3
        
        alerts.append({
            "id": str(uuid.uuid4()),
            "created_at": created.isoformat(),
            "predicted_multiplier": round(random.uniform(2.0, 15.0), 2),
            "actual_multiplier": round(random.uniform(1.5, 20.0), 2),
            "confirmed": confirmed,
            "status": "Cenário confirmado" if confirmed else "Cenário não confirmado"
        })
    
    return {"validated_alerts": alerts}

@api_router.get("/metrics/period")
async def get_period_metrics(period: str = "day", user = Depends(get_current_user)):
    # Generate mock period metrics
    data_points = 7 if period == "week" else (30 if period == "month" else 24)
    
    metrics = []
    for i in range(data_points):
        metrics.append({
            "period": i,
            "alerts_issued": random.randint(5, 20),
            "confirmed": random.randint(3, 15),
            "high_multipliers": random.randint(1, 5)
        })
    
    return {"period": period, "metrics": metrics}

app.include_router(api_router)

# SPA catch-all route - MUST be after API router to not intercept API routes
if FRONTEND_BUILD_DIR.exists():
    @app.get("/{full_path:path}")
    async def serve_frontend_spa(full_path: str):
        """Catch-all route for SPA - serves files or index.html for client-side routing"""
        # Check if it's a file in the build directory
        file_path = FRONTEND_BUILD_DIR / full_path
        if file_path.is_file():
            return FileResponse(str(file_path))
        
        # For all other paths (SPA routes), serve index.html
        return FileResponse(str(FRONTEND_BUILD_DIR / 'index.html'))

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
