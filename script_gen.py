"""
Clean script generator — no headers, no markdown, no timestamps.
Returns 4 sections with Hinglish lines + image theme per section.
Audio script is full Hindi Devanagari for ElevenLabs.
"""

import re, random

# ─── Helpers ─────────────────────────────────────────────────────────────────

def _nums(text):
    pcts   = re.findall(r"(\d+\.?\d*)\s*%", text)
    crores = re.findall(r"([\d,]+(?:\.\d+)?)\s*(?:crore|cr)\b", text, re.I)
    pts    = re.findall(r"([\d,]+)\s*(?:points?|pts)\b", text, re.I)
    return {
        "pct":    pcts[0]   if pcts   else None,
        "crore":  crores[0] if crores else None,
        "points": pts[0]    if pts    else None,
    }

def _stocks(text):
    known = ["Nifty 50", "Sensex", "Bank Nifty", "Adani", "Reliance", "TCS",
             "Infosys", "HDFC", "Bajaj", "Tata", "Wipro", "SBI", "ICICI",
             "Kotak", "Zomato", "Paytm", "LIC", "ONGC", "ITC", "HUL",
             "Maruti", "Titan", "Tata Motors", "Tata Steel", "JSW"]
    return [s for s in known if s.lower() in text.lower()][:2]

def _scenario(title, desc):
    t = (title + " " + desc).lower()
    if any(w in t for w in ["crash","collapse","circuit","meltdown","bloodbath","plunge","tank","rout","sell-off"]):
        return "crash"
    if any(w in t for w in ["record high","all-time high","ath","52-week high","rally","surge","soar","bull run","breakout"]):
        return "rally"
    if any(w in t for w in ["fii","foreign investor","foreign institutional","dii"]):
        return "fii"
    if any(w in t for w in ["ipo","listing","debut","grey market","gmp"]):
        return "ipo"
    if any(w in t for w in ["profit","earnings","results","quarterly","q1","q2","q3","q4","revenue","pat","ebitda"]):
        return "earnings"
    if any(w in t for w in ["rbi","repo rate","interest rate","monetary policy","inflation","gdp","budget"]):
        return "macro"
    if any(w in t for w in ["sebi","fraud","scam","ban","penalty","investigation","insider"]):
        return "sebi"
    if any(w in t for w in ["us market","global","federal reserve","fed","china","oil","dollar","rupee"]):
        return "global"
    if any(w in t for w in ["fall","falls","drop","decline","down","loss","slump"]):
        return "fall"
    return "general"

def _is_loss(title, desc):
    t = (title + " " + desc).lower()
    return any(w in t for w in ["fall","falls","decline","miss","loss","down","drop","slump","weak","poor","below","negative"])

def _company_sector(title, desc):
    """Return a Pexels search term for the company/sector."""
    t = (title + " " + desc).lower()
    if any(w in t for w in ["tata motors","maruti","mahindra","bajaj auto","tvs","automobile","auto","ev","electric vehicle"]):
        return "automobile india tata motors car"
    if any(w in t for w in ["tcs","infosys","wipro","hcl","tech mahindra","software","it company","technology"]):
        return "india software technology coding"
    if any(w in t for w in ["sbi","hdfc","icici","kotak","axis","bank","banking","nbfc","loan"]):
        return "india bank finance money"
    if any(w in t for w in ["reliance","ongc","oil","petroleum","energy","gas","power","ntpc"]):
        return "india energy oil power"
    if any(w in t for w in ["adani","ambani","infrastructure","port","airport"]):
        return "india infrastructure construction"
    if any(w in t for w in ["pharma","cipla","sun pharma","dr reddy","medicine","healthcare"]):
        return "india pharmaceutical medicine"
    if any(w in t for w in ["fmcg","itc","hul","dabur","nestle","consumer"]):
        return "india consumer goods market"
    return "india business corporate company office"

# ─── AUDIO scripts (Hindi Devanagari for ElevenLabs) ─────────────────────────

def _audio(scenario, title, n, stocks, loss):
    s   = stocks[0] if stocks else "यह stock"
    s2  = stocks[1] if len(stocks) > 1 else s
    p   = f"{n['pct']}%" if n["pct"] else "बड़ा"
    c   = f"₹{n['crore']} करोड़" if n["crore"] else "करोड़ों रुपए"
    pts = f"{n['points']} अंक" if n["points"] else "अंक"
    t   = title.strip()

    templates = {
        "crash": (
            f"BREAKING! बाज़ार में भारी भूचाल आ गया! {s} में {p} की तबाही मच गई! "
            f"{pts} एक ही झटके में टूट गए! {c} रुपए स्वाहा हो गए! "
            f"निवेशकों के होश उड़ गए! सपोर्ट लेवल टूट रहा है! "
            f"{t}. "
            f"क्या अभी और गिरेगा बाज़ार? एक्सपर्ट्स चेतावनी दे रहे हैं! "
            f"यह सिर्फ correction है या असली crash शुरू हो गया? "
            f"क्या आपको अभी बेचना चाहिए या होल्ड करना चाहिए? "
            f"stop-loss कहाँ लगाएं? पूरी analysis और market update सबसे पहले पाने के लिए "
            f"अभी Like करें और Subscribe करें!"
        ),
        "rally": (
            f"BREAKING! बाज़ार ने आज इतिहास रच दिया! {s} में जबरदस्त तेज़ी आई! "
            f"{p} की शानदार उड़ान! {pts} की धमाकेदार छलांग — एक ही दिन में! "
            f"{c} का ज़बरदस्त फायदा! {t}. "
            f"Bull Run रुकने का नाम नहीं ले रहा! "
            f"आज का यह उछाल कोई संयोग नहीं — fundamentals मज़बूत हैं! "
            f"अगला target price कहाँ है? क्या अभी BUY करना सही रहेगा? "
            f"एक्सपर्ट्स की राय है — यह stock अभी और ऊपर जाएगा! "
            f"लेकिन risk management भी ज़रूरी है! अपना portfolio मज़बूत करें! "
            f"रोज़ ऐसे market updates सबसे पहले पाने के लिए अभी Like करें और Subscribe करें!"
        ),
        "fii": (
            f"BREAKING! {'FII ने भारत को छोड़ा!' if loss else 'FII को भारत पर भरोसा आया!'} "
            f"विदेशी निवेशकों ने {c} के shares {'एक ही दिन में बेच दिए!' if loss else 'एक ही दिन में खरीद लिए!'} "
            f"{'यह बाज़ार के लिए बड़ा झटका है!' if loss else 'यह बुलिश संकेत है!'} "
            f"{t}. "
            f"{'DII खरीद रहे हैं, लेकिन क्या वो बाज़ार को संभाल पाएंगे?' if loss else 'Nifty को बड़ा boost मिलने वाला है!'} "
            f"कौन से sectors में सबसे ज़्यादा {'बिकवाली' if loss else 'खरीदारी'} हो रही है? "
            f"IT, Banking, Auto — किस sector पर सबसे ज़्यादा असर? "
            f"अगले हफ्ते बाज़ार किस तरफ जाएगा? "
            f"पूरा FII analysis जानने के लिए Like करें और Subscribe करें!"
        ),
        "ipo": (
            f"BREAKING! {s} का IPO आ गया! {c} का धमाकेदार offer! "
            f"Grey Market Premium में ज़बरदस्त उछाल देखा जा रहा है! "
            f"{t}. "
            f"क्या listing gain मिलेगा? Subscription कितनी बार भर गया? "
            f"एक्सपर्ट्स का कहना है — यह IPO आपको मालामाल कर सकता है! "
            f"company के fundamentals क्या हैं? Valuations सही हैं? "
            f"लेकिन risks भी हैं जो आपको जाननी चाहिए! "
            f"क्या आपको apply करना चाहिए? पूरी details और expert analysis के लिए "
            f"Like करें और Subscribe करें!"
        ),
        "earnings": (
            (
                f"ALERT! {s} के quarterly results ने निराश कर दिया! "
                f"PAT में {p} की गिरावट! सिर्फ {c} का मुनाफा — analysts की उम्मीदों से बहुत कम! "
                f"{t}. "
                f"Revenue miss, margin pressure — दोनों तरफ से झटका! "
                f"कल बाज़ार खुलते ही stock गिरेगा? "
                f"क्या यह exit करने का सही समय है या और गिरने का इंतज़ार करें? "
                f"support level कहाँ है? क्या यह stock फिर उठेगा? "
                f"एक्सपर्ट्स की पूरी राय जानने के लिए Like करें और Subscribe करें!"
            ) if loss else (
                f"BREAKING! {s} ने quarterly results में धमाका किया! "
                f"Net profit में {p} की शानदार growth! {c} का record मुनाफा! "
                f"{t}. "
                f"Revenue और margins दोनों ने analysts को हैरान कर दिया! "
                f"कल stock rocket बनेगा? अगला target price क्या होगा? "
                f"क्या अभी BUY करना सही है या थोड़ा इंतज़ार करें? "
                f"इस stock को long-term hold करना चाहिए? "
                f"एक्सपर्ट की पूरी analysis के लिए Like करें और Subscribe करें!"
            )
        ),
        "macro": (
            f"BREAKING! RBI ने बड़ा फ़ैसला सुना दिया! "
            f"Repo rate में {p} का बदलाव! पूरा बाज़ार हिल गया! "
            f"{t}. "
            f"आपका Home Loan, Car Loan और EMI — सब कुछ बदलने वाला है! "
            f"यह फ़ैसला आम आदमी की जेब पर सीधा असर डालेगा! "
            f"Banking stocks पर क्या होगा असर? Real Estate, Bond market क्या करें? "
            f"Sensex Nifty किस तरफ जाएगा अगले महीने? "
            f"Inflation और GDP पर क्या असर होगा? "
            f"इस फ़ैसले का पूरा असर समझने के लिए Like करें और Subscribe करें!"
        ),
        "sebi": (
            f"BREAKING! SEBI ने बड़ी कार्रवाई की! {s} पर भारी जुर्माना लगाया! "
            f"{t}. "
            f"निवेशकों के पैरों तले ज़मीन खिसक गई! क्या आपका पैसा सुरक्षित है? "
            f"इस stock पर trading रोकी जाएगी? "
            f"क्या यह insider trading का मामला है? "
            f"SEBI के इस फ़ैसले का पूरा मतलब क्या है? "
            f"कंपनी का management क्या कह रहा है? "
            f"क्या अभी इस stock को बेच देना चाहिए? "
            f"Expert की पूरी analysis के लिए Like करें और Subscribe करें!"
        ),
        "global": (
            f"BREAKING! Global markets में भारी उथल-पुथल! भारत पर बड़ा असर पड़ने वाला है! "
            f"US Fed का बड़ा फ़ैसला, China की मुश्किलें, और Oil prices में उछाल — "
            f"तीनों एक साथ आ गए! {t}. "
            f"Nifty पर {p} गिरावट की आशंका! Dollar vs Rupee में बड़ा बदलाव! "
            f"FII बेचेंगे या खरीदेंगे? IT और pharma exports पर क्या होगा असर? "
            f"कौन से stocks safe हैं इस turbulence में? "
            f"पूरी global market analysis और India strategy के लिए Like करें और Subscribe करें!"
        ),
        "fall": (
            f"ALERT! {s} में अचानक बड़ी गिरावट आ गई! {p} नीचे! {pts} टूटे! "
            f"{t}. "
            f"निवेशक घबराए हुए हैं! बाज़ार क्यों गिरा? असली वजह क्या है? "
            f"क्या यह temporary dip है या और गिरेगा? "
            f"क्या यह खरीदारी का golden मौका है? "
            f"support level कहाँ है और stop-loss कहाँ लगाएं? "
            f"एक्सपर्ट क्या कह रहे हैं? पूरी analysis और BUY-SELL strategy के लिए "
            f"Like करें और Subscribe करें!"
        ),
        "general": (
            f"BREAKING! {s} की बड़ी खबर आई! {t}. "
            f"{c} का {p} बदलाव — बाज़ार में हलचल मच गई! "
            f"यह खबर आपके portfolio को कैसे affect करेगी? "
            f"Short-term में क्या होगा? Long-term outlook क्या है? "
            f"Experts का कहना है — BUY करें, SELL करें या HOLD करें? "
            f"किन investors को सबसे ज़्यादा फायदा होगा? "
            f"पूरी analysis और market updates सबसे पहले पाने के लिए "
            f"Like करें और Subscribe करें!"
        ),
    }
    return templates.get(scenario, templates["general"])

# ─── DISPLAY sections (Hinglish — 4 sections, clean text for video) ──────────
# Each section: {"lines": [...], "image_type": "breaking"|"company"|"market"|"cta"}

def _sections_crash(title, n, stocks):
    s   = stocks[0] if stocks else "Market"
    p   = f"{n['pct']}%" if n["pct"] else "Badi Giraawat"
    pts = f"{n['points']} Points" if n["points"] else "Points"
    c   = f"Rs {n['crore']} Crore" if n["crore"] else "Hazaron Crore"
    return [
        {"image_type": "breaking", "lines": [
            "BREAKING!",
            "Market Mein BHUUCHAL!",
            f"{s} — {p} Ki TABAAHI!",
        ]},
        {"image_type": "company", "lines": [
            f"{pts} Gire!",
            f"{c} — Ek Jhatke Mein SWAHA!",
            "Investors Ke Hosh Ude!",
        ]},
        {"image_type": "market", "lines": [
            "Kya Aur GIREGA?",
            "Support Level Toot Raha Hai!",
            "Experts Ki Chhetaawni — Savdhan!",
        ]},
        {"image_type": "cta", "lines": [
            "Aise Hi Alerts Sabse Pehle?",
            "Subscribe KARO ABHI!",
            "LIKE  |  SHARE  |  SUBSCRIBE",
        ]},
    ]

def _sections_rally(title, n, stocks):
    s   = stocks[0] if stocks else "Market"
    p   = f"{n['pct']}%" if n["pct"] else "Jabardast"
    pts = f"{n['points']} Points" if n["points"] else "Points"
    c   = f"Rs {n['crore']} Crore" if n["crore"] else "Hazaron Crore"
    return [
        {"image_type": "breaking", "lines": [
            "BREAKING!",
            f"{s} Ne Raccha ITIHAAS!",
            "Record High — Sabne Dekha!",
        ]},
        {"image_type": "company", "lines": [
            f"{p} Ki UDAAN!",
            f"{pts} Ki Chhalaang!",
            f"{c} Ka FAYDA — Ek Din Mein!",
        ]},
        {"image_type": "market", "lines": [
            "Bull Run JAARI HAI!",
            "Next Target Kahan Hai?",
            "Kya Abhi BUY Karna Chahiye?",
        ]},
        {"image_type": "cta", "lines": [
            "Expert Analysis Chahiye?",
            "Subscribe Karo — FREE Updates!",
            "LIKE  |  SHARE  |  SUBSCRIBE",
        ]},
    ]

def _sections_fii(title, n, sell):
    c = f"Rs {n['crore']} Crore" if n["crore"] else "Hazaron Crore"
    if sell:
        return [
            {"image_type": "breaking", "lines": [
                "BREAKING!",
                "FII Ne CHHODA India!",
                f"{c} Ke Shares BECH Diye!",
            ]},
            {"image_type": "market", "lines": [
                "Ek Hi Din Mein!",
                "Jab FII Bechte Hain...",
                "Nifty DOOBT Hai!",
            ]},
            {"image_type": "company", "lines": [
                "DII Kya Bacha Payenge?",
                "Domestic Buyers Active Hain",
                "Lekin Kab Tak?",
            ]},
            {"image_type": "cta", "lines": [
                "Market Ka Agle Step?",
                "Subscribe Karo — Daily Alerts!",
                "LIKE  |  SHARE  |  SUBSCRIBE",
            ]},
        ]
    return [
        {"image_type": "breaking", "lines": [
            "BREAKING!",
            "FII Ko India Par BHAROSA!",
            f"{c} Ke Shares KHARIDE!",
        ]},
        {"image_type": "market", "lines": [
            "Yeh BULLISH Signal Hai!",
            "Foreign Money Aa Raha Hai!",
            "Nifty Ko Milega Boost?",
        ]},
        {"image_type": "company", "lines": [
            "Kaunse Sectors Mein Khareedaari?",
            "IT, Banking, Auto — Sab Mein!",
            "Bull Run Shuru Hone Wala Hai?",
        ]},
        {"image_type": "cta", "lines": [
            "Pura Analysis Chahiye?",
            "Subscribe Karo ABHI!",
            "LIKE  |  SHARE  |  SUBSCRIBE",
        ]},
    ]

def _sections_ipo(title, n, stocks):
    co = stocks[0] if stocks else "Yeh Company"
    c  = f"Rs {n['crore']} Crore" if n["crore"] else "Hazaron Crore"
    return [
        {"image_type": "breaking", "lines": [
            "BREAKING!",
            f"{co} IPO AAYA!",
            f"{c} Ka Dhamaakedaar Offer!",
        ]},
        {"image_type": "company", "lines": [
            "Grey Market Premium Kya Hai?",
            "Subscription Kitni Baar Bhara?",
            "Listing Gain Milega?",
        ]},
        {"image_type": "market", "lines": [
            "Apply Karein Ya Nahi?",
            "Expert Bol Rahe Hain...",
            "Yeh MAUKA Chookna Mat!",
        ]},
        {"image_type": "cta", "lines": [
            "IPO Updates Sabse Pehle?",
            "Subscribe Karo ABHI!",
            "LIKE  |  SHARE  |  SUBSCRIBE",
        ]},
    ]

def _sections_earnings(title, n, stocks, loss):
    co  = stocks[0] if stocks else "Company"
    p   = f"{n['pct']}%" if n["pct"] else "Bada"
    c   = f"Rs {n['crore']} Crore" if n["crore"] else "Crore"
    if loss:
        return [
            {"image_type": "breaking", "lines": [
                "ALERT!",
                f"{co} Results — NIRASH Kiya!",
                "Quarterly Numbers Aaye!",
            ]},
            {"image_type": "company", "lines": [
                f"PAT {p} GIRA!",
                f"Sirf {c} Ka Munafa!",
                "Analysts Ki Ummidon Par Paani!",
            ]},
            {"image_type": "market", "lines": [
                "Kal Stock GIREGA?",
                "Support Level Kahan Hai?",
                "Kya EXIT Karna Chahiye?",
            ]},
            {"image_type": "cta", "lines": [
                "Expert Ki Raay Chahiye?",
                "Subscribe Karo — FREE Analysis!",
                "LIKE  |  SHARE  |  SUBSCRIBE",
            ]},
        ]
    return [
        {"image_type": "breaking", "lines": [
            "BREAKING!",
            f"{co} Ne Toda RECORD!",
            "Quarterly Results Dhamaakedaar!",
        ]},
        {"image_type": "company", "lines": [
            f"{p} Ki Growth!",
            f"{c} Ka Munafa!",
            "Analysts Hairan Reh Gaye!",
        ]},
        {"image_type": "market", "lines": [
            "Kal Stock UPAR JAYEGA?",
            "Target Price Kya Hai?",
            "BUY Karna Chahiye?",
        ]},
        {"image_type": "cta", "lines": [
            "Stock Tips Chahiye?",
            "Subscribe Karo ABHI!",
            "LIKE  |  SHARE  |  SUBSCRIBE",
        ]},
    ]

def _sections_macro(title, n):
    p = f"{n['pct']}%" if n["pct"] else "Bada"
    return [
        {"image_type": "breaking", "lines": [
            "BREAKING!",
            "RBI Ka BADA Faisla!",
            "Poora Market HILA!",
        ]},
        {"image_type": "company", "lines": [
            f"Repo Rate — {p} Ka Badlaaw!",
            "Home Loan, Car Loan, EMI...",
            "Sab Kuch BADLEGA!",
        ]},
        {"image_type": "market", "lines": [
            "Sensex Nifty Par ASAR!",
            "Banking Stocks — Kaisi Reaction?",
            "Real Estate Kya Hoga?",
        ]},
        {"image_type": "cta", "lines": [
            "Aapki EMI Badlegi?",
            "Subscribe — Sabse Pehle Jaano!",
            "LIKE  |  SHARE  |  SUBSCRIBE",
        ]},
    ]

def _sections_sebi(title, stocks):
    co = stocks[0] if stocks else "Company"
    return [
        {"image_type": "breaking", "lines": [
            "BREAKING!",
            "SEBI Ka BADA ACTION!",
            f"{co} Par Badi Karwaai!",
        ]},
        {"image_type": "company", "lines": [
            "Investors Ke Pairon Tale",
            "Zameen Khisak Gayi!",
            "Paisa Surakshit Hai?",
        ]},
        {"image_type": "market", "lines": [
            "Stock Par Kya Hoga Asar?",
            "SEBI Ke Faisle Ka Matlab?",
            "Kya Abhi Bechna Chahiye?",
        ]},
        {"image_type": "cta", "lines": [
            "Aise Alerts Missed Mat Karo!",
            "Subscribe Karo ABHI!",
            "LIKE  |  SHARE  |  SUBSCRIBE",
        ]},
    ]

def _sections_global(title, n):
    p = f"{n['pct']}%" if n["pct"] else "Bada"
    return [
        {"image_type": "breaking", "lines": [
            "BREAKING!",
            "Global Market Ka JHATKA!",
            "India Par Pada Asar!",
        ]},
        {"image_type": "company", "lines": [
            "US Fed + China + Oil —",
            "TEEN DUSHMAN EK SAATH!",
            f"Nifty Par {p} Asar Ki Aashanka!",
        ]},
        {"image_type": "market", "lines": [
            "Dollar Rs Mein Aayi Girawat?",
            "FII Bechenge Ya Khareedenge?",
            "Kaunse Stocks Safe Hain?",
        ]},
        {"image_type": "cta", "lines": [
            "Market Update Chahiye Roz?",
            "Subscribe Karo ABHI!",
            "LIKE  |  SHARE  |  SUBSCRIBE",
        ]},
    ]

def _sections_fall(title, n, stocks):
    s   = stocks[0] if stocks else "Market"
    p   = f"{n['pct']}%" if n["pct"] else "Kaafi"
    pts = f"{n['points']} Points" if n["points"] else "Points"
    return [
        {"image_type": "breaking", "lines": [
            "ALERT!",
            f"{s} Mein BADI GIRAAWAT!",
            f"{p} NEECHE!",
        ]},
        {"image_type": "company", "lines": [
            f"{pts} Toot Gaye!",
            "Kyon Gira Market?",
            "Asali Wajah Kya Hai?",
        ]},
        {"image_type": "market", "lines": [
            "Kya Yeh KHAREEDAARI Ka Mauka?",
            "Ya Aur Girega?",
            "Support Level Kahan Hai?",
        ]},
        {"image_type": "cta", "lines": [
            "Expert Ki Salaah Chahiye?",
            "Subscribe Karo — FREE!",
            "LIKE  |  SHARE  |  SUBSCRIBE",
        ]},
    ]

def _sections_general(title, n, stocks):
    s = stocks[0] if stocks else "Indian Market"
    p = f"{n['pct']}%" if n["pct"] else None
    c = f"Rs {n['crore']} Crore" if n["crore"] else None
    stat = f"{c} — {p} Badlaaw!" if c and p else (c or p or "Badi Khabar!")
    return [
        {"image_type": "breaking", "lines": [
            "BREAKING!",
            f"{s} — IMPORTANT UPDATE!",
            "Yeh Khabar Miss Mat Karo!",
        ]},
        {"image_type": "company", "lines": [
            stat,
            "Asar Padega Tumhare Portfolio Par!",
            "Kya Hai Poori Khabar?",
        ]},
        {"image_type": "market", "lines": [
            "Experts Kya Bol Rahe Hain?",
            "BUY? SELL? HOLD?",
            "Puri Analysis Yahan Hai!",
        ]},
        {"image_type": "cta", "lines": [
            "Roz Aisi Khabren Chahiye?",
            "Subscribe Karo ABHI!",
            "LIKE  |  SHARE  |  SUBSCRIBE",
        ]},
    ]

# ─── Public API ───────────────────────────────────────────────────────────────

_SECTIONS_MAP = {
    "crash":    lambda t, n, st, loss: _sections_crash(t, n, st),
    "rally":    lambda t, n, st, loss: _sections_rally(t, n, st),
    "fii":      lambda t, n, st, loss: _sections_fii(t, n, loss),
    "ipo":      lambda t, n, st, loss: _sections_ipo(t, n, st),
    "earnings": lambda t, n, st, loss: _sections_earnings(t, n, st, loss),
    "macro":    lambda t, n, st, loss: _sections_macro(t, n),
    "sebi":     lambda t, n, st, loss: _sections_sebi(t, st),
    "global":   lambda t, n, st, loss: _sections_global(t, n),
    "fall":     lambda t, n, st, loss: _sections_fall(t, n, st),
    "general":  lambda t, n, st, loss: _sections_general(t, n, st),
}

def generate_script(title, desc, category=None):
    """
    Returns:
      audio_script  → Hindi Devanagari string for ElevenLabs
      sections      → list of 4 dicts: {image_type, lines}
      scenario      → detected scenario string
      company_query → Pexels search term for company background
    """
    sc   = _scenario(title, desc)
    n    = _nums(title + " " + desc)
    st   = _stocks(title + " " + desc)
    loss = _is_loss(title, desc)

    audio   = _audio(sc, title, n, st, loss)
    sec_fn  = _SECTIONS_MAP.get(sc, _SECTIONS_MAP["general"])
    sections = sec_fn(title, n, st, loss)

    print(f"  Scenario: {sc} | loss={loss} | stocks={st} | pct={n['pct']} crore={n['crore']}")
    return {
        "audio_script":  audio,
        "sections":      sections,
        "scenario":      sc,
        "company_query": _company_sector(title, desc),
    }

def make_timed_segments(sections, audio_duration):
    """
    Assign start/end times to each section and return a flat segment list
    for FrameBuilder: [{text, start, end, image_type}, ...]

    Time per section is determined by (in priority order):
      1. section["time_weight"]  — explicit word/time weight you set manually
      2. len(section["lines"])   — fallback: proportional to line count
    """
    weights = [s.get("time_weight", len(s["lines"])) for s in sections]
    total_w = sum(weights)
    seg_list = []
    elapsed  = 0.0
    for sec, w in zip(sections, weights):
        sec_dur  = (w / total_w) * audio_duration
        line_dur = sec_dur / len(sec["lines"])
        for line in sec["lines"]:
            seg_list.append({
                "text":       line,
                "start":      elapsed,
                "end":        elapsed + line_dur,
                "image_type": sec["image_type"],
            })
            elapsed += line_dur
    return seg_list
