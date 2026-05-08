"""
Batch render + upload 10 stock market Shorts.
Run: py batch_10_videos.py
Runs all 10 without stopping. Logs failures and continues.
"""

import os, sys, re, pickle, time, traceback
sys.path.insert(0, r"C:\Users\user\Desktop\dashboard")

from moviepy import AudioFileClip
from config       import OUTPUT_DIR, CACHE_DIR
from news_fetcher import fetch_section_images
from script_gen   import make_timed_segments
from audio_gen    import generate_audio, get_best_voice
from video_gen    import create_video

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(CACHE_DIR,  exist_ok=True)

CHANNEL_SLUG = "stock_wizard"

# ── YouTube credentials ────────────────────────────────────────────────────────
def get_yt():
    tf = os.path.join(r"C:\Users\user\Desktop\dashboard\channels\youtube",
                      f"{CHANNEL_SLUG}_token.pickle")
    creds = pickle.load(open(tf, "rb"))
    if isinstance(creds, Credentials):
        return build("youtube", "v3", credentials=creds)
    c = Credentials(token=creds.get("token"), refresh_token=creds.get("refresh_token"),
                    token_uri=creds.get("token_uri","https://oauth2.googleapis.com/token"),
                    client_id=creds.get("client_id"), client_secret=creds.get("client_secret"))
    return build("youtube", "v3", credentials=c)

def sanitize_tags(tags):
    clean, total = [], 0
    for t in tags:
        t = re.sub(r'[^\w\s\-\']', '', t, flags=re.UNICODE).strip()
        if not t or total + len(t) + 1 > 500: continue
        clean.append(t); total += len(t) + 1
    return clean

def upload(video_path, title, summary, tags):
    clean = sanitize_tags(tags)
    htags = " ".join(f"#{t}" for t in clean)
    desc  = (f"{title}\n\n{summary}\n\n"
             f"Bullish ya Bearish? Comment mein batao!\n"
             f"Daily stock updates ke liye Subscribe karo!\n"
             f"Bell icon dabao - koi update miss mat karo!\n\n"
             f"{'='*32}\n{htags}\n{'='*32}\n"
             f"#Shorts #YouTubeShorts #StockMarket #IndianStocks #ShareMarket")
    yt  = get_yt()
    req = yt.videos().insert(
        part="snippet,status",
        body={"snippet": {"title": title[:100], "description": desc, "tags": clean,
                          "categoryId": "25", "defaultLanguage": "hi",
                          "defaultAudioLanguage": "hi"},
              "status":  {"privacyStatus": "public", "selfDeclaredMadeForKids": False,
                          "madeForKids": False}},
        media_body=MediaFileUpload(video_path, mimetype="video/mp4",
                                   chunksize=1024*1024, resumable=True)
    )
    resp = None
    while resp is None:
        st, resp = req.next_chunk()
        if st: print(f"  Uploading... {int(st.progress()*100)}%", end="\r")
    url = f"https://www.youtube.com/shorts/{resp['id']}"
    print(f"\n  UPLOADED -> {url}")
    return url

# ── 10 Video configs ────────────────────────────────────────────────────────────

VIDEOS = [

# ─── 1. Reliance Industries ───────────────────────────────────────────────────
{
  "slug": "reliance",
  "seed": 10,
  "company_query": "reliance industries india jio AI data centre technology",
  "story": {"title": "Reliance AI + Data Centre Play! India Ka Digital Backbone Kaun Banega?", "src": "ET Markets / RIL"},
  "audio": (
    "Reliance ko log ab sirf oil aur Jio se nahi, "
    "data centre aur AI infra se bhi judge kar rahe hain. "
    "Jio ke 5G rollout, edge data centres, "
    "aur AI partnerships ka combo "
    "RIL ko next decade ke digital backbone ke roop mein position kar raha hai. "
    "Sawal simple hai, "
    "agar India ka data game yahin se chalega, "
    "to kya aaj ka Reliance price us future ko poora reflect karta hai? "
    "Aapko kya lagta hai? Comment mein batao. "
    "Aisi hi daily stock updates ke liye channel subscribe karo "
    "aur yeh Short like aur share karo."
  ),
  "sections": [
    {"image_type": "breaking", "time_weight": 18, "lines": ["Reliance - NEXT LEVEL!", "Oil Nahi, AI + Data!"]},
    {"image_type": "company",  "time_weight": 28, "lines": ["Jio 5G + Data Centres", "AI Partnerships STRONG!", "India Ka Digital Backbone?"]},
    {"image_type": "market",   "time_weight": 20, "lines": ["Kya Price Reflect Karta Hai?", "Next Decade Ka Big Bet!"]},
    {"image_type": "cta",      "time_weight": 18, "lines": ["Bullish Ya Bearish? Comment!", "Subscribe - Daily Updates!", "LIKE  |  SHARE  |  SUBSCRIBE"]},
  ],
  "title": "Reliance AI + Data Centre Play! India Ka Digital Backbone - Kya Price Reflect Karta Hai?",
  "summary": "Reliance ab sirf oil+Jio nahi - data centres aur AI infra se bhi judge ho raha hai. Jio 5G + edge data centres + AI partnerships = next decade ka digital backbone. Kya aaj ka price us future ko fully reflect karta hai?",
  "tags": ["Reliance","Jio","DataCentre","AIInfra","TelecomStocks","RelianceRetail","Nifty50","LargeCap","IndianStocks","ShareMarketIndia","RIL","JioAI","5GIndia","TechStocks","GrowthStocks","Bluechip","NSE","MarketToday","Shorts","YouTubeShorts"],
},

# ─── 2. HDFC Bank ────────────────────────────────────────────────────────────
{
  "slug": "hdfc_bank",
  "seed": 11,
  "company_query": "HDFC bank india private banking finance headquarters",
  "story": {"title": "HDFC Bank - Dip Ya Danger? Merger Ke Baad Kya Sochein?", "src": "ET Markets / HDFC Bank"},
  "audio": (
    "HDFC Bank, jo kabhi no brainer compounder tha, "
    "ab merger ke baad growth slowdown aur valuation debate mein phas gaya hai. "
    "Loan growth normalise ho raha hai, NIM pe pressure hai, "
    "lekin franchise ab bhi India ki sabse powerful hai. "
    "Ye jo correction chal raha hai, "
    "yeh agle das saal ka best entry zone hai, "
    "ya structure hi change ho gaya hai, "
    "yeh hi aaj ka biggest question hai. "
    "Aapko kya lagta hai, dip pe buy karein ya wait? "
    "Comment mein batao aur channel subscribe karo."
  ),
  "sections": [
    {"image_type": "breaking", "time_weight": 20, "lines": ["HDFC Bank - DIP YA DANGER?", "Merger Ke Baad Big Question!"]},
    {"image_type": "company",  "time_weight": 28, "lines": ["Loan Growth NORMALISING", "NIM Pe Pressure!", "Franchise Still POWERFUL!"]},
    {"image_type": "market",   "time_weight": 22, "lines": ["Best Entry Zone Ya...", "Structure Change Ho Gaya?", "Biggest Debate Right Now!"]},
    {"image_type": "cta",      "time_weight": 14, "lines": ["Buy Ya Wait? Comment!", "Subscribe - Daily Updates!", "LIKE  |  SHARE  |  SUBSCRIBE"]},
  ],
  "title": "HDFC Bank - Dip Ya Danger? Merger Ke Baad Best Entry Zone Hai Ya Structure Change Ho Gaya?",
  "summary": "HDFC Bank merger ke baad growth slowdown aur valuation debate mein hai. Loan growth normalise, NIM pressure. Lekin franchise India ki sabse powerful. Kya yeh correction next 10 saal ka best entry zone hai?",
  "tags": ["HDFCBank","BankingStocks","NiftyBank","Bluechip","Valuation","LongTermInvesting","DIIHolding","RetailInvestors","StockMarketNews","HDFCMerger","NIM","LoanGrowth","PrivateBanks","NSE","IndianStocks","ShareMarketIndia","Nifty50","StockAlert","Shorts","YouTubeShorts"],
},

# ─── 3. ICICI Bank ───────────────────────────────────────────────────────────
{
  "slug": "icici_bank",
  "seed": 12,
  "company_query": "ICICI bank india private banking digital finance",
  "story": {"title": "ICICI Bank - Silent Leader! High ROE + Clean Assets = Nifty Bank Ka Poster Boy?", "src": "ET Markets / ICICI Bank"},
  "audio": (
    "Jab sab HDFC Bank ki tension mein busy the, "
    "ICICI Bank quietly high ROE aur clean asset quality ke saath "
    "naya market favourite ban chuka hai. "
    "Retail aur corporate dono side se growth, "
    "digital stack strong, "
    "aur valuations abhi bhi peers se reasonable hain. "
    "Kya agle paanch saal mein Nifty Bank ka asli poster boy "
    "ICICI Bank hi hone wala hai? "
    "Aapko kya lagta hai? Comment mein batao. "
    "Channel subscribe karo aur yeh Short like karo."
  ),
  "sections": [
    {"image_type": "breaking", "time_weight": 16, "lines": ["ICICI Bank - SILENT LEADER!", "Market Ka New Favourite!"]},
    {"image_type": "company",  "time_weight": 30, "lines": ["High ROE + Clean Assets!", "Retail + Corporate Growth", "Digital Stack STRONG!", "Valuations - Reasonable!"]},
    {"image_type": "market",   "time_weight": 18, "lines": ["Nifty Bank Ka Poster Boy?", "Next 5 Saal Ka Big Bet!"]},
    {"image_type": "cta",      "time_weight": 14, "lines": ["Bullish Ya Bearish? Comment!", "Subscribe - Daily Updates!", "LIKE  |  SHARE  |  SUBSCRIBE"]},
  ],
  "title": "ICICI Bank Silent Leader! High ROE + Clean Assets - Kya Nifty Bank Ka Asli Poster Boy Yahi Hai?",
  "summary": "Jab sab HDFC ki tension mein the, ICICI Bank quietly high ROE aur clean assets ke saath market favourite ban gaya. Retail + corporate growth, strong digital stack, reasonable valuations. Kya agle 5 saal mein Nifty Bank ka asli leader ICICI hoga?",
  "tags": ["ICICIBank","PrivateBank","NiftyBank","ROE","Financials","Bluechip","IndianStocks","ShareMarketIndia","BankingStocks","ICICI","CleanAssets","DigitalBanking","NSE","MarketToday","Nifty50","StockAlert","LongTermInvesting","StockMarket","Shorts","YouTubeShorts"],
},

# ─── 4. Tata Motors ──────────────────────────────────────────────────────────
{
  "slug": "tata_motors_ev",
  "seed": 13,
  "company_query": "tata motors india electric vehicle EV nexon automobile",
  "story": {"title": "Tata Motors EV + JLR Combo! Value Unlocking Ka Potential Kitna Bada Hai?", "src": "ET Markets / Tata Motors"},
  "audio": (
    "Tata Motors sirf Nexon EV wali story nahi hai. "
    "India mein EV, buses, commercial vehicles ka growth, "
    "aur global level pe JLR ke premium SUVs "
    "mila ke ek powerful combo ban chuke hain. "
    "Agar Tata Motors apna EV business alag list karta hai, "
    "to value unlocking ka potential kitna bada ho sakta hai? "
    "Car company ka PE lagana sahi hai, "
    "ya isko full EV aur luxury play samajhna chahiye? "
    "Aapko kya lagta hai? Comment mein batao. "
    "Channel subscribe karo daily updates ke liye."
  ),
  "sections": [
    {"image_type": "breaking", "time_weight": 14, "lines": ["Tata Motors - FULL COMBO!", "Sirf Nexon EV Nahi!"]},
    {"image_type": "company",  "time_weight": 28, "lines": ["India EV + Bus + CV Growth", "JLR Premium SUVs - Global!", "Powerful Combo BANA!"]},
    {"image_type": "market",   "time_weight": 26, "lines": ["EV Business Alag List?", "Value Unlocking MASSIVE!", "Car PE Sahi Hai Ya EV Play?"]},
    {"image_type": "cta",      "time_weight": 14, "lines": ["Bullish Ya Bearish? Comment!", "Subscribe - Daily Updates!", "LIKE  |  SHARE  |  SUBSCRIBE"]},
  ],
  "title": "Tata Motors EV + JLR Combo! EV Business Alag List Hua To Value Unlocking Kitni Badi Hogi?",
  "summary": "Tata Motors sirf Nexon EV nahi - India EV+buses+CV growth aur JLR premium SUVs mila ke powerful combo. Agar EV business alag list ho, value unlocking massive ho sakti hai. Car company ka PE sahi hai ya full EV+luxury play?",
  "tags": ["TataMotors","EVStocks","JLR","AutoSector","Nifty50","Turnaround","GrowthStory","IndianStocks","LongTermInvesting","NexonEV","ElectricVehicle","TataEV","ValueUnlocking","LuxuryCar","NSE","MarketToday","StockAlert","ShareMarketIndia","Shorts","YouTubeShorts"],
},

# ─── 5. Adani Group ──────────────────────────────────────────────────────────
{
  "slug": "adani_comeback",
  "seed": 14,
  "company_query": "adani ports india sea port infrastructure capex",
  "story": {"title": "Adani Group Comeback! Short Seller Ke Baad Phir Highs Pe - Real Ya Sentiment?", "src": "ET Markets / Adani Group"},
  "audio": (
    "Short seller reports ke baad "
    "Adani group ko logon ne almost khatam maan liya tha. "
    "Aaj same stocks phir se highs ke aas paas dikh rahe hain, "
    "ports, power, renewables mein massive capex announcements ke saath. "
    "Yeh comeback actual earnings pe based hai, "
    "ya sirf liquidity aur sentiment ka game hai? "
    "Risk reward yahan pe sabse zyada polarising hai. "
    "Aapko kya lagta hai? Comment mein batao. "
    "Aisi hi daily market updates ke liye channel subscribe karo."
  ),
  "sections": [
    {"image_type": "breaking", "time_weight": 18, "lines": ["Adani - MASSIVE COMEBACK!", "Short Seller Ke Baad Highs!"]},
    {"image_type": "company",  "time_weight": 28, "lines": ["Ports + Power + Renewables", "Massive Capex ANNOUNCED!", "Back Near HIGHS!"]},
    {"image_type": "market",   "time_weight": 20, "lines": ["Real Earnings Ya Sentiment?", "Most POLARISING Stock!", "Risk Reward - High Beta!"]},
    {"image_type": "cta",      "time_weight": 14, "lines": ["Bullish Ya Bearish? Comment!", "Subscribe - Daily Updates!", "LIKE  |  SHARE  |  SUBSCRIBE"]},
  ],
  "title": "Adani Group Comeback! Short Seller Ke Baad Phir Highs Pe - Real Earnings Ya Sirf Sentiment?",
  "summary": "Short seller reports ke baad Adani group almost khatam maan liya gaya tha. Aaj same stocks phir highs ke paas - ports, power, renewables mein massive capex. Real earnings based hai ya sirf sentiment+liquidity ka game?",
  "tags": ["AdaniPorts","AdaniPower","AdaniGroup","InfraStocks","PowerStocks","HighBeta","Volatility","IndianMarkets","RetailFavourite","AdaniComeback","AdaniRenewables","Capex","NSE","MarketToday","ShareMarketIndia","IndianStocks","StockAlert","HighRiskHighReward","Shorts","YouTubeShorts"],
},

# ─── 6. Vedanta ──────────────────────────────────────────────────────────────
{
  "slug": "vedanta",
  "seed": 15,
  "company_query": "vedanta india metals mining zinc aluminium factory",
  "story": {"title": "Vedanta Demerger + High Dividend! Debt Vs Value Unlocking - Kya Sochein?", "src": "ET Markets / Vedanta"},
  "audio": (
    "Vedanta ek side se "
    "high dividend, demerger aur value unlocking ki kahani suna raha hai, "
    "aur doosri side se market ko "
    "uska debt aur commodity cyclicality yaad aa raha hai. "
    "Metals, oil, zinc, aluminium, "
    "sab businesses alag alag list honge to "
    "kya actual value unlock hogi, "
    "ya sirf structure complex ho jayega? "
    "Retail ke liye yeh stock thrill bhi hai, risk bhi. "
    "Aapko kya lagta hai? Comment mein batao. "
    "Channel subscribe karo aur yeh Short like karo."
  ),
  "sections": [
    {"image_type": "breaking", "time_weight": 18, "lines": ["Vedanta - THRILL + RISK!", "Dividend + Demerger Story!"]},
    {"image_type": "company",  "time_weight": 24, "lines": ["High Dividend DECLARED!", "Demerger - Value Unlock?", "Metals + Oil + Zinc + Aluminium"]},
    {"image_type": "market",   "time_weight": 26, "lines": ["Debt Problem REAL!", "Commodity Cycle RISK!", "Alag List = Real Value?"]},
    {"image_type": "cta",      "time_weight": 16, "lines": ["Bullish Ya Bearish? Comment!", "Subscribe - Daily Updates!", "LIKE  |  SHARE  |  SUBSCRIBE"]},
  ],
  "title": "Vedanta Demerger + High Dividend! Debt Vs Value Unlocking - Retail Ke Liye Thrill Bhi Risk Bhi!",
  "summary": "Vedanta ek side se high dividend, demerger aur value unlocking ki kahani, doosri side se debt aur commodity cyclicality ka dar. Metals, oil, zinc, aluminium alag list honge - kya actual value unlock hogi ya structure sirf complex hoga?",
  "tags": ["Vedanta","MetalStocks","Dividend","Demerger","CommodityCycle","Nifty500","HighRiskHighReward","RetailFavourite","VedantaDemerger","Zinc","Aluminium","Mining","Debt","IndianStocks","ShareMarketIndia","NSE","MarketToday","StockAlert","Shorts","YouTubeShorts"],
},

# ─── 7. Paytm ────────────────────────────────────────────────────────────────
{
  "slug": "paytm",
  "seed": 16,
  "company_query": "paytm india fintech digital payments mobile app",
  "story": {"title": "Paytm Next Chapter - Comeback Ya Slow Fade? RBI Actions Ke Baad Kya Hua?", "src": "ET Markets / Paytm"},
  "audio": (
    "Paytm par ek waqt India ka biggest fintech future likha ja raha tha. "
    "Aaj same stock regulator actions, licence issues "
    "aur business restructuring ke beech struggle kar raha hai. "
    "Company cash burn control kar rahi hai, "
    "lending partnerships aur soundbox jaisi products pe focus hai, "
    "lekin trust wapas aayega ya nahi, "
    "yeh hi million dollar question hai. "
    "Paytm ka next chapter comeback hoga ya slow fade out? "
    "Aapko kya lagta hai? Comment mein batao. "
    "Channel subscribe karo daily updates ke liye."
  ),
  "sections": [
    {"image_type": "breaking", "time_weight": 16, "lines": ["Paytm - NEXT CHAPTER?", "India Ka Biggest Fintech!"]},
    {"image_type": "company",  "time_weight": 30, "lines": ["RBI Action + Licence Issues", "Cash Burn CONTROL Ho Raha!", "Soundbox + Lending Focus"]},
    {"image_type": "market",   "time_weight": 24, "lines": ["Trust Wapas Aayega?", "Comeback Ya Slow Fade?", "Million Dollar Question!"]},
    {"image_type": "cta",      "time_weight": 14, "lines": ["Bullish Ya Bearish? Comment!", "Subscribe - Daily Updates!", "LIKE  |  SHARE  |  SUBSCRIBE"]},
  ],
  "title": "Paytm Next Chapter! RBI Actions + Licence Issues Ke Baad Comeback Hoga Ya Slow Fade Out?",
  "summary": "Paytm par kabhi India ka biggest fintech future likha ja raha tha. Aaj regulator actions, licence issues aur restructuring ke beech struggle. Cash burn control, soundbox+lending focus, lekin trust wapas? Comeback ya slow fade?",
  "tags": ["Paytm","Fintech","RBIAction","HighRiskStock","TurnaroundStory","StartupIPO","NewAgeStocks","IndianStocks","PaytmCrash","DigitalPayments","Soundbox","Lending","ShareMarketIndia","NSE","MarketToday","StockAlert","HighBeta","Volatility","Shorts","YouTubeShorts"],
},

# ─── 8. Zomato ───────────────────────────────────────────────────────────────
{
  "slug": "zomato",
  "seed": 17,
  "company_query": "zomato india food delivery app restaurant blinkit",
  "story": {"title": "Zomato Profit Ke Baad Valuation! Overvalued Tech Ya Long-Term Compounder?", "src": "ET Markets / Zomato"},
  "audio": (
    "Zomato ne finally multiple quarters mein "
    "consistent profit dikha diya hai. "
    "Food delivery, Blinkit quick commerce, "
    "aur ad revenue milke business ko strong bana rahe hain. "
    "Ab debate yeh hai, "
    "yeh stock abhi bhi overvalued tech fancy hai, "
    "ya India ka long term consumer tech compounder? "
    "Growth aur profit dono jab saath chalte hain, "
    "story aur interesting ho jati hai. "
    "Aapko kya lagta hai? Comment mein batao. "
    "Channel subscribe karo aur yeh Short like karo."
  ),
  "sections": [
    {"image_type": "breaking", "time_weight": 16, "lines": ["Zomato - FINALLY PROFIT!", "Multiple Quarters Consistent!"]},
    {"image_type": "company",  "time_weight": 26, "lines": ["Food Delivery STRONG!", "Blinkit Quick Commerce!", "Ad Revenue ADD Ho Raha!"]},
    {"image_type": "market",   "time_weight": 24, "lines": ["Overvalued Ya Compounder?", "Growth + Profit = Story!", "Long Term Big Bet?"]},
    {"image_type": "cta",      "time_weight": 14, "lines": ["Bullish Ya Bearish? Comment!", "Subscribe - Daily Updates!", "LIKE  |  SHARE  |  SUBSCRIBE"]},
  ],
  "title": "Zomato Consistent Profit! Overvalued Tech Fancy Hai Ya India Ka Long Term Consumer Compounder?",
  "summary": "Zomato ne multiple quarters mein consistent profit dikha diya. Food delivery + Blinkit quick commerce + ad revenue milke strong business. Ab debate: overvalued tech fancy ya India ka long-term consumer tech compounder?",
  "tags": ["Zomato","NewAgeStocks","Profitability","FoodDelivery","Blinkit","GrowthStocks","TechStocks","IndianStockMarket","ZomatoProfit","QuickCommerce","ConsumerTech","AdRevenue","NSE","MarketToday","IndianStocks","ShareMarketIndia","StockAlert","Nifty500","Shorts","YouTubeShorts"],
},

# ─── 9. Vodafone Idea (analysis angle) ───────────────────────────────────────
{
  "slug": "vi_analysis",
  "seed": 18,
  "company_query": "vodafone idea india telecom Vi 5G network tower",
  "story": {"title": "Vodafone Idea AGR Cut - Hope Ka Trade Ya Real Turnaround? Time Hi Batayega!", "src": "ET Telecom / Vi"},
  "audio": (
    "Vodafone Idea ka Adjusted Gross Revenue bill "
    "officially cut ho chuka hai, "
    "amount ab kam hai aur do hazaar tees ke baad spread ho gaya hai. "
    "Short term mein yeh ek clear relief hai, "
    "lekin network quality, 5G capex "
    "aur fresh capital raise ke bina "
    "story complete nahi hogi. "
    "Yeh stock hope ka trade hai "
    "ya real turnaround? "
    "Time hi batayega. "
    "Aapko kya lagta hai? Comment mein batao. "
    "Channel subscribe karo aur yeh Short like karo."
  ),
  "sections": [
    {"image_type": "breaking", "time_weight": 16, "lines": ["Vodafone Idea - AGR CUT!", "Official Relief Aaya!"]},
    {"image_type": "company",  "time_weight": 22, "lines": ["AGR Bill OFFICIALLY KAM!", "Amount Spread - 2030s Tak", "Short Term RELIEF!"]},
    {"image_type": "market",   "time_weight": 26, "lines": ["5G Capex - STILL NEEDED!", "Capital Raise ZARURI!", "Hope Ka Trade Ya Real?"]},
    {"image_type": "cta",      "time_weight": 14, "lines": ["Bullish Ya Bearish? Comment!", "Subscribe - Daily Updates!", "LIKE  |  SHARE  |  SUBSCRIBE"]},
  ],
  "title": "Vodafone Idea AGR Cut! Hope Ka Trade Hai Ya Real Turnaround? 5G Capex Aur Capital Raise Ka Kya?",
  "summary": "Vi ka AGR bill officially cut, amount kam aur 2030s tak spread. Short term relief clear hai, lekin 5G capex aur fresh capital raise ke bina story complete nahi hogi. Hope ka trade hai ya real turnaround? Time hi batayega.",
  "tags": ["VodafoneIdea","Telecom","AGRDues","Debt","Turnaround","PennyStock","HighBeta","RetailFavourite","IndianStocks","Vi","5GIndia","TelecomStocks","CapitalRaise","NetworkQuality","NSE","MarketToday","StockAlert","ShareMarketIndia","Shorts","YouTubeShorts"],
},

# ─── 10. Netweb + Tata Elxsi ─────────────────────────────────────────────────
{
  "slug": "ai_infra_plays",
  "seed": 19,
  "company_query": "tata elxsi india AI technology software engineering embedded",
  "story": {"title": "India Ke Hidden AI Infra Plays! Netweb Technologies + Tata Elxsi - Next 10 Saal Ka Bet?", "src": "ET Markets / NSE"},
  "audio": (
    "Aaj jo bhi AI tools, models, data centres chal rahe hain, "
    "unke peeche kisi na kisi ne "
    "servers, chips, networking aur software infra banaya hai. "
    "India mein Netweb Technologies "
    "GPU servers aur HPC systems bana raha hai, "
    "aur Tata Elxsi "
    "embedded AI solutions, auto ADAS, aur OTT tech mein leader hai. "
    "Agar AI agle das saal ka biggest theme hai, "
    "to kya yeh dono stocks "
    "India ke hidden AI infra plays ho sakte hain? "
    "Aapko kya lagta hai? Comment mein batao. "
    "Channel subscribe karo aur yeh Short like karo."
  ),
  "sections": [
    {"image_type": "breaking", "time_weight": 18, "lines": ["India Ka HIDDEN AI PLAY!", "Netweb + Tata Elxsi!"]},
    {"image_type": "company",  "time_weight": 28, "lines": ["Netweb - GPU + HPC Systems!", "Tata Elxsi - Auto ADAS AI", "OTT + Embedded Tech Leader!"]},
    {"image_type": "market",   "time_weight": 24, "lines": ["AI - Next 10 Saal Ka Theme!", "Hidden Infra Plays?", "Thematic Investing!"]},
    {"image_type": "cta",      "time_weight": 14, "lines": ["Bullish Ya Bearish? Comment!", "Subscribe - Daily Updates!", "LIKE  |  SHARE  |  SUBSCRIBE"]},
  ],
  "title": "India Ke Hidden AI Infra Plays! Netweb Technologies + Tata Elxsi - Next 10 Saal Ka Biggest Bet?",
  "summary": "AI tools, models aur data centres ke peeche servers+infra banane wale kaun? Netweb Technologies GPU servers+HPC systems bana raha hai. Tata Elxsi embedded AI, auto ADAS, OTT tech mein leader. Kya yeh India ke hidden AI infra plays hain?",
  "tags": ["NetwebTechnologies","TataElxsi","AIStocks","AIInfra","ITStocks","HighGrowth","ThematicInvesting","IndianEquity","TechStocks","AIIndia","GPU","HPC","EmbeddedAI","AutoADAS","OTTTech","NSE","MarketToday","ShareMarketIndia","Shorts","YouTubeShorts"],
},

]

# ── Main runner ────────────────────────────────────────────────────────────────

def run_video(v, idx, total):
    slug         = v["slug"]
    audio_path   = os.path.join(CACHE_DIR,  f"{slug}_audio.mp3")
    output_path  = os.path.join(OUTPUT_DIR, f"{slug}_short.mp4")

    print(f"\n{'='*60}")
    print(f"  [{idx}/{total}] {slug.upper()}")
    print(f"{'='*60}")

    # Remove old output
    if os.path.exists(output_path):
        os.remove(output_path)

    # 1. AI Images
    print("\n[1/4] AI section images (Stability AI)...")
    section_images = fetch_section_images(v["company_query"], seed=v["seed"])

    # 2. Audio
    print("\n[2/4] Audio (ElevenLabs)...")
    if os.path.exists(audio_path):
        print(f"  Cached: {os.path.getsize(audio_path)//1024} KB")
    else:
        voice_id = get_best_voice()
        generate_audio(v["audio"], audio_path, voice_id)

    dur = AudioFileClip(audio_path).duration
    print(f"  Duration: {dur:.1f}s")

    # 3. Segments
    segments = make_timed_segments(v["sections"], dur)
    print(f"\n[3/4] Segments ({len(segments)}):")
    for seg in segments:
        txt = seg['text'].encode('ascii', 'replace').decode()
        print(f"  [{seg['image_type']:8s}] {seg['start']:5.1f}s-{seg['end']:5.1f}s  \"{txt}\"")

    # 4. Render
    print("\n[4/4] Rendering...")
    create_video(v["story"], v["audio"], segments, audio_path, output_path,
                 section_images=section_images, target_duration=60)

    size_mb = os.path.getsize(output_path) / 1024 / 1024
    print(f"  Done -> {output_path} ({size_mb:.1f} MB)")

    # 5. Upload
    print("\n[5/5] Uploading to YouTube...")
    url = upload(output_path, v["title"], v["summary"], v["tags"])
    return url


def main():
    results = []
    voice_id = get_best_voice()   # warm up voice selection once

    for i, v in enumerate(VIDEOS, 1):
        try:
            url = run_video(v, i, len(VIDEOS))
            results.append((v["slug"], "OK", url))
        except Exception as e:
            print(f"\n  ERROR on {v['slug']}: {e}")
            traceback.print_exc()
            results.append((v["slug"], "FAILED", str(e)[:80]))
        time.sleep(2)   # brief pause between videos

    print(f"\n\n{'='*60}")
    print(f"  BATCH COMPLETE — {len(VIDEOS)} videos")
    print(f"{'='*60}")
    for slug, status, info in results:
        mark = "OK" if status == "OK" else "XX"
        print(f"  [{mark}] {slug:20s} -> {info}")


if __name__ == "__main__":
    main()
