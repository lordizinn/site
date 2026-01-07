from fastapi import FastAPI, APIRouter, Depends, HTTPException, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import asyncio
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import bcrypt
import jwt
import hmac
import hashlib
import mercadopago
import random
import resend

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

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

app = FastAPI(title="Aviator Analytics Pro API")
api_router = APIRouter(prefix="/api")
security = HTTPBearer()

# Models
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

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    payload = verify_jwt_token(token)
    user = await db.users.find_one({"id": payload['user_id']}, {"_id": 0})
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
async def register(user: UserRegister):
    existing = await db.users.find_one({"email": user.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "email": user.email,
        "name": user.name,
        "password_hash": hash_password(user.password),
        "subscription_status": "inactive",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(user_doc)
    token = create_jwt_token(user_id, user.email)
    
    return {"token": token, "user_id": user_id, "email": user.email, "name": user.name}

@api_router.post("/auth/login")
async def login(credentials: UserLogin):
    user = await db.users.find_one({"email": credentials.email}, {"_id": 0})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not verify_password(credentials.password, user['password_hash']):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if user.get('subscription_status') != 'active':
        raise HTTPException(status_code=403, detail="Subscription inactive. Please subscribe to access.")
    
    token = create_jwt_token(user['id'], user['email'])
    
    return {
        "token": token,
        "user_id": user['id'],
        "email": user['email'],
        "name": user['name'],
        "subscription_status": user.get('subscription_status')
    }

@api_router.post("/subscription/create-preference")
async def create_preference(sub: SubscriptionCreate):
    existing = await db.users.find_one({"email": sub.email}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    external_reference = str(uuid.uuid4())
    
    # Store pending preference
    await db.pending_preferences.insert_one({
        "external_reference": external_reference,
        "email": sub.email,
        "name": sub.name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    })
    
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
async def handle_webhook(request: Request):
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
            pending = await db.pending_preferences.find_one(
                {"external_reference": external_reference},
                {"_id": 0}
            )
            
            if pending:
                user_id = str(uuid.uuid4())
                password = str(uuid.uuid4())[:8]
                
                user_doc = {
                    "id": user_id,
                    "email": pending["email"],
                    "name": pending["name"],
                    "password_hash": hash_password(password),
                    "subscription_status": "active",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                await db.users.insert_one(user_doc)
                
                next_billing = datetime.now(timezone.utc) + timedelta(days=30)
                subscription_doc = {
                    "user_id": user_id,
                    "status": "active",
                    "plan_id": "MONTHLY_100",
                    "payment_id": payment_id,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "next_billing_date": next_billing.isoformat()
                }
                
                await db.subscriptions.insert_one(subscription_doc)
                await db.pending_preferences.delete_one({"external_reference": external_reference})
                
                # Send confirmation email
                email_html = f"""
                <h2>Bem-vindo ao Aviator Analytics Pro</h2>
                <p>Olá {pending['name']},</p>
                <p>Sua assinatura foi confirmada com sucesso!</p>
                <p><strong>Email:</strong> {pending['email']}<br>
                <strong>Senha temporária:</strong> {password}</p>
                <p>Acesse o dashboard: <a href="{FRONTEND_URL}/login">{FRONTEND_URL}/login</a></p>
                <p>Por favor, altere sua senha após o primeiro acesso.</p>
                """
                await send_email_async(pending["email"], "Assinatura Confirmada - Aviator Analytics Pro", email_html)
    
    return {"status": "received"}

@api_router.get("/subscription/check-status/{external_reference}")
async def check_subscription_status(external_reference: str):
    user = await db.users.find_one(
        {"subscription_status": "active"},
        {"_id": 0}
    )
    
    if user:
        subscription = await db.subscriptions.find_one({"user_id": user["id"]}, {"_id": 0})
        if subscription:
            return {"status": "active", "user": user}
    
    pending = await db.pending_preferences.find_one(
        {"external_reference": external_reference},
        {"_id": 0}
    )
    
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

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()