# streamlit_app/app.py
import streamlit as st
import requests
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
import json

# --- Sayfa Yapılandırması ---
st.set_page_config(
    page_title="GlobalTrade RiskAnalyzer Pro",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://globaltraderisk.com/support',
        'Report a bug': 'https://github.com/yourrepo/issues',
        'About': 'GlobalTrade RiskAnalyzer v1.0 - Profesyonel Dış Ticaret Risk Platformu'
    }
)

# --- Dark Mode CSS (Finans Terminali Teması) ---
st.markdown("""
<style>
    /* Bloomberg/Refinitiv benzeri koyu tema */
    .stApp {
        background-color: #0a0e17;
    }
    .main .block-container {
        padding-top: 1rem;
    }
    .metric-card {
        background: linear-gradient(145deg, #1a1f2e, #151a26);
        border: 1px solid #2a3040;
        border-radius: 12px;
        padding: 20px;
        color: #ffffff;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        border-color: #3a8bff;
        box-shadow: 0 8px 25px rgba(58, 139, 255, 0.2);
        transform: translateY(-2px);
    }
    .risk-high { color: #ff4444; font-weight: bold; }
    .risk-medium { color: #ffaa00; font-weight: bold; }
    .risk-low { color: #00cc66; font-weight: bold; }
    .stMetric {
        background-color: #1a1f2e;
        border-radius: 8px;
        padding: 10px;
    }
    h1, h2, h3 { color: #e0e6f0 !important; }
    .stSelectbox label, .stTextInput label { color: #8899aa !important; }
</style>
""", unsafe_allow_html=True)

# --- API Yapılandırması ---
API_BASE_URL = st.secrets.get("API_BASE_URL", "http://localhost:8000")
API_TOKEN = st.secrets.get("API_TOKEN", "demo_token")

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

# --- Session State ---
if 'language' not in st.session_state:
    st.session_state.language = 'TR'

if 'selected_countries' not in st.session_state:
    st.session_state.selected_countries = ['TUR', 'USA', 'CHN', 'RUS', 'DEU']

# --- Çok Dilli Çeviriler ---
translations = {
    'TR': {
        'title': '🌍 GlobalTrade RiskAnalyzer',
        'subtitle': 'Profesyonel Dış Ticaret Risk Analiz Platformu',
        'risk_dashboard': '📊 Risk Panosu',
        'country_analysis': '🔍 Ülke Analizi',
        'shipment_optimizer': '🚢 Sevkiyat Optimizasyonu',
        'overall_risk': 'Genel Risk Puanı',
        'political_risk': 'Siyasi Risk',
        'economic_risk': 'Ekonomik Risk',
        'security_risk': 'Güvenlik Riski',
        'trade_risk': 'Ticaret Riski',
        'analyze': 'Analiz Et',
        'optimize': 'Rotayı Optimize Et',
        'origin': 'Çıkış Ülkesi',
        'destination': 'Varış Ülkesi',
        'cargo_value': 'Yük Değeri (USD)',
        'cargo_type': 'Yük Tipi',
        'results': 'Sonuçlar',
        'no_data': 'Veri bulunamadı. Lütfen API bağlantısını kontrol edin.',
        'loading': 'Veriler yükleniyor...',
        'error': 'Bir hata oluştu',
        'footer': '© 2024 GlobalTrade RiskAnalyzer | Tüm hakları saklıdır',
    },
    'EN': {
        'title': '🌍 GlobalTrade RiskAnalyzer',
        'subtitle': 'Professional Foreign Trade Risk Analysis Platform',
        'risk_dashboard': '📊 Risk Dashboard',
        'country_analysis': '🔍 Country Analysis',
        'shipment_optimizer': '🚢 Shipment Optimizer',
        'overall_risk': 'Overall Risk Score',
        'political_risk': 'Political Risk',
        'economic_risk': 'Economic Risk',
        'security_risk': 'Security Risk',
        'trade_risk': 'Trade Risk',
        'analyze': 'Analyze',
        'optimize': 'Optimize Route',
        'origin': 'Origin Country',
        'destination': 'Destination Country',
        'cargo_value': 'Cargo Value (USD)',
        'cargo_type': 'Cargo Type',
        'results': 'Results',
        'no_data': 'No data found. Please check API connection.',
        'loading': 'Loading data...',
        'error': 'An error occurred',
        'footer': '© 2024 GlobalTrade RiskAnalyzer | All rights reserved',
    },
    'AR': {
        'title': '🌍 محلل المخاطر العالمي للتجارة',
        'subtitle': 'منصة احترافية لتحليل مخاطر التجارة الخارجية',
        'risk_dashboard': '📊 لوحة المخاطر',
        'country_analysis': '🔍 تحليل الدولة',
        'shipment_optimizer': '🚢 محسن الشحن',
        'overall_risk': 'درجة المخاطر الإجمالية',
        'political_risk': 'المخاطر السياسية',
        'economic_risk': 'المخاطر الاقتصادية',
        'security_risk': 'مخاطر الأمن',
        'trade_risk': 'مخاطر التجارة',
        'analyze': 'تحليل',
        'optimize': 'تحسين المسار',
        'origin': 'بلد المنشأ',
        'destination': 'بلد الوجهة',
        'cargo_value': 'قيمة الشحنة (دولار)',
        'cargo_type': 'نوع الشحنة',
        'results': 'النتائج',
        'no_data': 'لم يتم العثور على بيانات. يرجى التحقق من اتصال API.',
        'loading': 'جاري تحميل البيانات...',
        'error': 'حدث خطأ',
        'footer': '© 2024 جميع الحقوق محفوظة',
    }
}

# --- Yardımcı Fonksiyonlar ---
def t(key):
    """Çeviri fonksiyonu"""
    lang = st.session_state.language
    return translations.get(lang, translations['EN']).get(key, key)

def get_risk_color(score):
    """Risk puanına göre renk döndürür"""
    if score >= 70:
        return "#ff4444"  # Kırmızı - Yüksek risk
    elif score >= 40:
        return "#ffaa00"  # Turuncu - Orta risk
    else:
        return "#00cc66"  # Yeşil - Düşük risk

def get_risk_level(score):
    if score >= 70:
        return "🔴 " + ("YÜKSEK" if st.session_state.language == 'TR' else "HIGH")
    elif score >= 40:
        return "🟡 " + ("ORTA" if st.session_state.language == 'TR' else "MEDIUM")
    else:
        return "🟢 " + ("DÜŞÜK" if st.session_state.language == 'TR' else "LOW")

def fetch_country_risk(country_code):
    """API'den ülke risk verisini çeker"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/api/v1/risk/{country_code}",
            headers=headers,
            timeout=30
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"API Hatası: {str(e)}")
        return None

@st.cache_data(ttl=300)  # 5 dakika önbellek
def fetch_batch_risks(country_codes):
    """Toplu risk verisi çeker"""
    try:
        codes_str = ",".join(country_codes)
        response = requests.get(
            f"{API_BASE_URL}/api/v1/risk/batch?codes={codes_str}",
            headers=headers,
            timeout=60
        )
        if response.status_code == 200:
            return response.json()
        return []
    except:
        return []

# --- Sidebar ---
with st.sidebar:
    st.markdown("## ⚙️ " + ("Ayarlar" if st.session_state.language == 'TR' else "Settings"))
    
    # Dil seçimi
    lang_options = {'🇹🇷 Türkçe': 'TR', '🇬🇧 English': 'EN', '🇸🇦 العربية': 'AR'}
    selected_lang = st.selectbox(
        "🌐 Language / Dil / اللغة",
        list(lang_options.keys()),
        index=0
    )
    st.session_state.language = lang_options[selected_lang]
    
    st.divider()
    
    # Navigasyon
    page = st.radio(
        "📋 " + ("Menü" if st.session_state.language == 'TR' else "Menu"),
        [t('risk_dashboard'), t('country_analysis'), t('shipment_optimizer')]
    )
    
    st.divider()
    
    # SaaS Abonelik Bilgisi
    st.markdown("### 💎 " + ("Abonelik" if st.session_state.language == 'TR' else "Subscription"))
    st.markdown("**PRO Plan** - " + ("Aylık" if st.session_state.language == 'TR' else "Monthly"))
    st.progress(65, text=f"13/20 " + ("gün kaldı" if st.session_state.language == 'TR' else "days left"))
    
    st.divider()
    st.caption(t('footer'))

# --- Ana Sayfa ---
st.title(t('title'))
st.caption(t('subtitle'))

# ==================== RİSK PANOSU ====================
if t('risk_dashboard') in page:
    st.markdown(f"## {t('risk_dashboard')}")
    
    # Ülke seçimi
    all_countries = ['TUR', 'USA', 'CHN', 'RUS', 'GBR', 'DEU', 'ARE', 'SAU', 'IRN', 'JPN', 'KOR', 'FRA', 'EGY']
    country_names = {
        'TUR': '🇹🇷 Türkiye', 'USA': '🇺🇸 ABD', 'CHN': '🇨🇳 Çin', 'RUS': '🇷🇺 Rusya',
        'GBR': '🇬🇧 İngiltere', 'DEU': '🇩🇪 Almanya', 'ARE': '🇦🇪 BAE', 'SAU': '🇸🇦 S.Arabistan',
        'IRN': '🇮🇷 İran', 'JPN': '🇯🇵 Japonya', 'KOR': '🇰🇷 G.Kore', 'FRA': '🇫🇷 Fransa',
        'EGY': '🇪🇬 Mısır'
    }
    
    st.session_state.selected_countries = st.multiselect(
        "İzlenecek Ülkeler",
        all_countries,
        default=st.session_state.selected_countries,
        format_func=lambda x: country_names.get(x, x)
    )
    
    if st.button("🔄 " + ("Riskleri Güncelle" if st.session_state.language == 'TR' else "Refresh Risks"), type="primary"):
        st.cache_data.clear()
        st.rerun()
    
    # Verileri çek
    with st.spinner(t('loading')):
        risks = fetch_batch_risks(st.session_state.selected_countries)
    
    if risks:
        # Isı Haritası
        st.markdown("### 🗺️ " + ("Küresel Risk Isı Haritası" if st.session_state.language == 'TR' else "Global Risk Heatmap"))
        
        df_map = pd.DataFrame(risks)
        fig = go.Figure(data=go.Choropleth(
            locations=df_map['country_code'],
            z=df_map['overall_score'],
            text=df_map['country_name'],
            colorscale=[[0, '#00cc66'], [0.4, '#ffaa00'], [0.7, '#ff4444'], [1, '#990000']],
            colorbar_title="Risk Puanı",
            marker_line_color='darkgray',
            marker_line_width=0.5,
        ))
        fig.update_layout(
            geo=dict(
                showframe=False,
                showcoastlines=True,
                projection_type='natural earth',
                bgcolor='#0a0e17'
            ),
            paper_bgcolor='#0a0e17',
            plot_bgcolor='#0a0e17',
            font=dict(color='#ffffff'),
            margin=dict(l=0, r=0, t=0, b=0),
            height=400,
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Risk Kartları
        st.markdown("### 📈 " + ("Ülke Risk Profilleri" if st.session_state.language == 'TR' else "Country Risk Profiles"))
        
        for risk in risks:
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1.5, 1.5, 1.5])
                
                with col1:
                    flag = country_names.get(risk['country_code'], '').split(' ')[0]
                    st.markdown(f"### {flag} {risk['country_name']}")
                    st.caption(risk.get('ai_summary', '')[:120] + '...')
                
                with col2:
                    score = risk['overall_score']
                    st.metric(
                        t('overall_risk'),
                        f"{score:.0f}/100",
                        delta=get_risk_level(score),
                        delta_color="off"
                    )
                
                with col3:
                    score = risk['political_score']
                    st.metric(t('political_risk'), f"{score:.0f}", 
                             delta="⚠️" if score > 60 else "✅")
                
                with col4:
                    score = risk['economic_score']
                    st.metric(t('economic_risk'), f"{score:.0f}",
                             delta="⚠️" if score > 60 else "✅")
                
                with col5:
                    score = risk['security_score']
                    st.metric(t('security_risk'), f"{score:.0f}",
                             delta="⚠️" if score > 60 else "✅")
                
                # Radar Chart
                categories = ['Siyasi', 'Ekonomik', 'Güvenlik', 'Ticaret']
                values = [risk['political_score'], risk['economic_score'], 
                         risk['security_score'], risk['trade_score']]
                
                fig_radar = go.Figure(data=go.Scatterpolar(
                    r=values,
                    theta=categories,
                    fill='toself',
                    fillcolor='rgba(58, 139, 255, 0.3)',
                    line=dict(color='#3a8bff', width=2),
                    name=risk['country_name']
                ))
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(visible=True, range=[0, 100], color='#8899aa'),
                        bgcolor='#1a1f2e'
                    ),
                    paper_bgcolor='#0a0e17',
                    plot_bgcolor='#0a0e17',
                    font=dict(color='#ffffff'),
                    height=250,
                    margin=dict(l=20, r=20, t=20, b=20),
                    showlegend=False
                )
                
                col_radar, col_findings = st.columns([1, 1])
                with col_radar:
                    st.plotly_chart(fig_radar, use_container_width=True)
                
                with col_findings:
                    st.markdown("**🔑 " + ("Önemli Bulgular" if st.session_state.language == 'TR' else "Key Findings") + "**")
                    for finding in risk.get('key_findings', [])[:3]:
                        st.markdown(f"- {finding}")
                    st.caption(f"🕐 {risk.get('calculated_at', '')[:19]}")
                
                st.divider()

# ==================== ÜLKE ANALİZİ ====================
elif t('country_analysis') in page:
    st.markdown(f"## {t('country_analysis')}")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        selected_country = st.selectbox(
            "Ülke Seçin",
            all_countries,
            format_func=lambda x: country_names.get(x, x)
        )
        
        if st.button("🔍 " + t('analyze'), type="primary", use_container_width=True):
            st.session_state.analyze_country = selected_country
    
    if 'analyze_country' in st.session_state:
        with st.spinner(t('loading')):
            risk = fetch_country_risk(st.session_state.analyze_country)
        
        if risk:
            with col2:
                # Büyük risk göstergesi
                st.markdown(f"""
                <div style="text-align:center; padding:20px;">
                    <h1 style="font-size:72px; color:{get_risk_color(risk['overall_score'])}; margin:0;">
                        {risk['overall_score']:.0f}<span style="font-size:24px;">/100</span>
                    </h1>
                    <p style="color:#8899aa; font-size:18px;">{get_risk_level(risk['overall_score'])}</p>
                </div>
                """, unsafe_allow_html=True)
            
            # Detaylı metrikler
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            
            metrics = [
                (t('political_risk'), risk['political_score']),
                (t('economic_risk'), risk['economic_score']),
                (t('security_risk'), risk['security_score']),
                (t('trade_risk'), risk['trade_score']),
            ]
            
            for col, (label, value) in zip([col_m1, col_m2, col_m3, col_m4], metrics):
                with col:
                    st.markdown(f"""
                    <div class="metric-card" style="text-align:center;">
                        <p style="color:#8899aa; margin:0; font-size:12px;">{label}</p>
                        <p style="color:{get_risk_color(value)}; font-size:36px; margin:5px 0;">{value:.0f}</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            # AI Özeti
            st.markdown("### 🤖 AI Analiz Özeti")
            st.info(risk.get('ai_summary', 'No summary available'))
            
            # Kaynaklar
            st.markdown("### 📚 Kaynaklar")
            for url in risk.get('source_urls', []):
                st.markdown(f"- [{url}]({url})")

# ==================== SEVKİYAT OPTİMİZASYONU ====================
elif t('shipment_optimizer') in page:
    st.markdown(f"## {t('shipment_optimizer')}")
    
    col1, col2 = st.columns(2)
    
    with col1:
        origin = st.selectbox(t('origin'), all_countries, format_func=lambda x: country_names.get(x, x))
        cargo_type = st.selectbox(t('cargo_type'), ['Genel Kargo', 'Tehlikeli Madde', 'Gıda', 'Elektronik', 'Tekstil', 'Makine'])
        cargo_value = st.number_input(t('cargo_value'), min_value=1000, value=50000, step=1000)
    
    with col2:
        destination = st.selectbox(t('destination'), all_countries, format_func=lambda x: country_names.get(x, x), index=2)
        incoterms = st.selectbox("Incoterms", ['FOB', 'CIF', 'EXW', 'DAP', 'DDP'], index=1)
    
    if st.button("🚀 " + t('optimize'), type="primary", use_container_width=True):
        with st.spinner("🔄 Rota optimize ediliyor..."):
            try:
                payload = {
                    "origin_country": origin,
                    "destination_country": destination,
                    "cargo_type": cargo_type,
                    "cargo_value": cargo_value,
                    "currency": "USD",
                    "incoterms": incoterms
                }
                response = requests.post(
                    f"{API_BASE_URL}/api/v1/shipment/optimize",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.shipment_result = result
                else:
                    st.error(f"API Hatası: {response.status_code}")
            except Exception as e:
                st.error(f"Bağlantı hatası: {str(e)}")
    
    if 'shipment_result' in st.session_state:
        result = st.session_state.shipment_result
        
        st.markdown("---")
        st.markdown(f"### 📋 {t('results')}")
        
        col_r1, col_r2, col_r3, col_r4 = st.columns(4)
        
        with col_r1:
            st.metric("🛡️ " + ("Rota Risk Puanı" if st.session_state.language == 'TR' else "Route Risk Score"),
                     f"{result['risk_assessment']['overall_route_risk']:.0f}/100")
        
        with col_r2:
            risk_level = result['optimized_route']['risk_level']
            emoji = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(risk_level, "⚪")
            st.metric("⚠️ " + ("Risk Seviyesi" if st.session_state.language == 'TR' else "Risk Level"),
                     f"{emoji} {risk_level}")
        
        with col_r3:
            st.metric("💰 " + ("Tahmini Maliyet" if st.session_state.language == 'TR' else "Est. Cost"),
                     f"${result['estimated_cost']:,.2f}")
        
        with col_r4:
            st.metric("📅 " + ("Tahmini Süre" if st.session_state.language == 'TR' else "Est. Days"),
                     f"{result['estimated_days']} gün")
        
        st.markdown("### 📜 " + ("Mevzuat Önerileri" if st.session_state.language == 'TR' else "Compliance Notes"))
        for note in result['compliance_notes']:
            st.markdown(f"- ✅ {note}")
        
        if not result['compliance_notes']:
            st.success("✅ " + ("Bu rota için ek mevzuat gerekliliği bulunmamaktadır." if st.session_state.language == 'TR' else "No additional compliance requirements for this route."))

# --- Footer ---
st.markdown("---")
st.caption(t('footer'))
