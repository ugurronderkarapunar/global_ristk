# backend/main.py
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime, timedelta
import asyncio
import os

from agents.risk_analyst_agent import get_risk_agent
from agents.compliance_agent import ComplianceAgent
from agents.logistics_agent import LogisticsOptimizer

# --- FastAPI App ---
app = FastAPI(
    title="GlobalTrade RiskAnalyzer API",
    description="Küresel Ticaret Risk Analizi ve Lojistik Optimizasyon SaaS Platformu",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# --- CORS Middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8501", "https://*.streamlit.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Security ---
security = HTTPBearer()

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """JWT token doğrulama - Gerçek uygulamada PyJWT kullanılır"""
    token = credentials.credentials
    # TODO: Gerçek JWT doğrulama
    if token == "demo_token" or token.startswith("sk-"):
        return {"user_id": "demo-user", "tier": "PRO"}
    raise HTTPException(status_code=401, detail="Geçersiz token")


# --- Pydantic Modeller ---
class RiskScoreResponse(BaseModel):
    country_code: str
    country_name: str
    overall_score: float = Field(..., ge=0, le=100)
    political_score: float = Field(..., ge=0, le=100)
    economic_score: float = Field(..., ge=0, le=100)
    security_score: float = Field(..., ge=0, le=100)
    trade_score: float = Field(..., ge=0, le=100)
    ai_summary: str
    source_urls: List[str]
    key_findings: List[str]
    calculated_at: datetime
    trend: Optional[str] = "STABLE"  # UP, DOWN, STABLE

class ShipmentRequest(BaseModel):
    origin_country: str = Field(..., min_length=3, max_length=3)
    destination_country: str = Field(..., min_length=3, max_length=3)
    cargo_type: str
    cargo_value: float = Field(..., gt=0)
    currency: str = "USD"
    incoterms: Optional[str] = "FOB"

class ShipmentResponse(BaseModel):
    shipment_id: str
    origin: str
    destination: str
    risk_assessment: Dict
    optimized_route: Dict
    compliance_notes: List[str]
    estimated_cost: float
    estimated_days: int

class HealthResponse(BaseModel):
    status: str
    version: str
    agents_ready: bool
    uptime: str


# --- Endpoints ---
@app.get("/api/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Sistem sağlık kontrolü"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "agents_ready": True,
        "uptime": "24/7"
    }

@app.get("/api/v1/risk/{country_code}", response_model=RiskScoreResponse, tags=["Risk Analysis"])
async def get_country_risk(
    country_code: str,
    force_refresh: bool = Query(False, description="Önbelleği atla ve yeniden analiz et"),
    user: dict = Depends(verify_token)
):
    """
    Belirli bir ülke için canlı risk puanı döndürür.
    
    - **country_code**: ISO 3166-1 alpha-3 (örn: TUR, USA, CHN)
    - **force_refresh**: true ise AI ajanı yeniden çalıştırır
    """
    # Ülke kodu doğrulama
    if len(country_code) != 3:
        raise HTTPException(status_code=400, detail="Geçersiz ülke kodu. 3 haneli ISO kodu girin.")
    
    country_code = country_code.upper()
    
    # Gerçek uygulamada Redis'ten önbellek kontrolü yapılır
    # Şimdilik direkt ajanı çağıralım
    agent = get_risk_agent()
    
    # Ülke adı mapping'i (normalde DB'den gelir)
    country_names = {
        "TUR": "Turkey", "USA": "United States", "CHN": "China",
        "RUS": "Russia", "GBR": "United Kingdom", "DEU": "Germany",
        "ARE": "United Arab Emirates", "EGY": "Egypt", "SAU": "Saudi Arabia",
        "IRN": "Iran", "FRA": "France", "JPN": "Japan", "KOR": "South Korea"
    }
    
    country_name = country_names.get(country_code, country_code)
    
    # AI analizi (asenkron değilse thread'de çalıştır)
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(agent.analyze_country, country_name, country_code)
        risk_data = future.result(timeout=60)
    
    return RiskScoreResponse(
        country_code=country_code,
        country_name=country_name,
        **risk_data,
        trend="STABLE"  # Gerçekte önceki puanla karşılaştırılır
    )

@app.get("/api/v1/risk/batch", response_model=List[RiskScoreResponse], tags=["Risk Analysis"])
async def get_multiple_countries_risk(
    codes: str = Query(..., description="Virgülle ayrılmış ülke kodları: TUR,USA,CHN"),
    user: dict = Depends(verify_token)
):
    """Birden fazla ülke için risk puanlarını toplu getirir"""
    country_codes = [c.strip().upper() for c in codes.split(",") if len(c.strip()) == 3]
    
    if len(country_codes) > 10:
        raise HTTPException(status_code=400, detail="Tek seferde en fazla 10 ülke sorgulanabilir")
    
    agent = get_risk_agent()
    country_names = {
        "TUR": "Turkey", "USA": "United States", "CHN": "China",
        "RUS": "Russia", "GBR": "United Kingdom", "DEU": "Germany",
        "ARE": "United Arab Emirates", "EGY": "Egypt", "SAU": "Saudi Arabia",
        "IRN": "Iran", "FRA": "France", "JPN": "Japan", "KOR": "South Korea"
    }
    
    results = []
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {}
        for code in country_codes:
            name = country_names.get(code, code)
            futures[executor.submit(agent.analyze_country, name, code)] = code
        
        for future in concurrent.futures.as_completed(futures, timeout=120):
            code = futures[future]
            try:
                risk_data = future.result()
                results.append(RiskScoreResponse(
                    country_code=code,
                    country_name=country_names.get(code, code),
                    **risk_data,
                    trend="STABLE"
                ))
            except Exception as e:
                results.append(RiskScoreResponse(
                    country_code=code,
                    country_name=country_names.get(code, code),
                    overall_score=50, political_score=50, economic_score=50,
                    security_score=50, trade_score=50,
                    ai_summary=f"Hata: {str(e)[:100]}",
                    source_urls=[], key_findings=["Analiz başarısız"],
                    calculated_at=datetime.utcnow(), trend="STABLE"
                ))
    
    return results

@app.post("/api/v1/shipment/optimize", response_model=ShipmentResponse, tags=["Logistics"])
async def optimize_shipment(
    shipment: ShipmentRequest,
    user: dict = Depends(verify_token)
):
    """Sevkiyat için rota optimizasyonu ve risk değerlendirmesi"""
    # Gerçek uygulamada LogisticsOptimizer ve ComplianceAgent çalışır
    agent = get_risk_agent()
    
    # Origin ve destination risklerini al
    origin_risk = agent.analyze_country(shipment.origin_country, shipment.origin_country)
    dest_risk = agent.analyze_country(shipment.destination_country, shipment.destination_country)
    
    # Basitleştirilmiş optimizasyon
    avg_risk = (origin_risk["overall_score"] + dest_risk["overall_score"]) / 2
    
    route = {
        "waypoints": [shipment.origin_country, shipment.destination_country],
        "alternative_ports": [],
        "risk_level": "HIGH" if avg_risk > 70 else "MEDIUM" if avg_risk > 40 else "LOW",
        "suggested_insurance": avg_risk > 60
    }
    
    compliance = []
    if avg_risk > 70:
        compliance.append("Akreditif (L/C) ile ödeme önerilir")
        compliance.append("Ek sigorta poliçesi zorunlu")
    if avg_risk > 50:
        compliance.append("Ön ödeme oranı en az %30 olmalı")
    
    return ShipmentResponse(
        shipment_id=f"SHP-{datetime.utcnow().strftime('%Y%m%d')}-{shipment.origin_country}{shipment.destination_country}",
        origin=shipment.origin_country,
        destination=shipment.destination_country,
        risk_assessment={
            "overall_route_risk": round(avg_risk, 1),
            "origin_risk": origin_risk["overall_score"],
            "destination_risk": dest_risk["overall_score"]
        },
        optimized_route=route,
        compliance_notes=compliance,
        estimated_cost=round(5000 * (1 + avg_risk/200), 2),
        estimated_days=14 + int(avg_risk / 10)
    )

@app.get("/api/v1/countries", tags=["Reference Data"])
async def get_countries_list():
    """Sistemdeki tüm ülkelerin listesini döndürür"""
    return {
        "countries": [
            {"code": "TUR", "name_tr": "Türkiye", "name_en": "Turkey", "name_ar": "تركيا", "name_zh": "土耳其"},
            {"code": "USA", "name_tr": "Amerika Birleşik Devletleri", "name_en": "United States", "name_ar": "الولايات المتحدة", "name_zh": "美国"},
            {"code": "CHN", "name_tr": "Çin", "name_en": "China", "name_ar": "الصين", "name_zh": "中国"},
            {"code": "RUS", "name_tr": "Rusya", "name_en": "Russia", "name_ar": "روسيا", "name_zh": "俄罗斯"},
            {"code": "GBR", "name_tr": "Birleşik Krallık", "name_en": "United Kingdom", "name_ar": "المملكة المتحدة", "name_zh": "英国"},
            {"code": "DEU", "name_tr": "Almanya", "name_en": "Germany", "name_ar": "ألمانيا", "name_zh": "德国"},
            {"code": "ARE", "name_tr": "Birleşik Arap Emirlikleri", "name_en": "UAE", "name_ar": "الإمارات", "name_zh": "阿联酋"},
            {"code": "SAU", "name_tr": "Suudi Arabistan", "name_en": "Saudi Arabia", "name_ar": "السعودية", "name_zh": "沙特阿拉伯"},
            {"code": "IRN", "name_tr": "İran", "name_en": "Iran", "name_ar": "إيران", "name_zh": "伊朗"},
            {"code": "JPN", "name_tr": "Japonya", "name_en": "Japan", "name_ar": "اليابان", "name_zh": "日本"},
        ]
    }


# --- Startup Event ---
@app.on_event("startup")
async def startup_event():
    """Uygulama başlangıcında ajanları initialize et"""
    print("🚀 GlobalTrade RiskAnalyzer başlatılıyor...")
    print("✅ FastAPI hazır")
    print("🤖 AI Ajanları yükleniyor...")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
