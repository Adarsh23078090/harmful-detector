import streamlit as st
import requests
from PIL import Image
import matplotlib.pyplot as plt

# ---------------------------------------------------
# CONFIG & CSS
# ---------------------------------------------------
st.set_page_config(page_title="Harmful Content Detector", page_icon="🚨")

st.markdown("""
<style>
.result-bad { padding:12px; background:#ffcccc; border-left:5px solid #d10000; border-radius:8px; font-size:18px; }
.result-okay { padding:12px; background:#ccffcc; border-left:5px solid #008000; border-radius:8px; font-size:18px; }
.section-card { background:white; padding:15px; margin:15px 0; border-radius:12px; box-shadow:0 2px 10px rgba(0,0,0,.1); }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------
# OCR API
# ---------------------------------------------------
OCR_API_KEY = "helloworld"

def extract_text(img_path):
    url = "https://api.ocr.space/parse/image"
    with open(img_path, "rb") as f:
        files = {"file": f}
        data = {"apikey": OCR_API_KEY, "language": "eng"}
        try:
            res = requests.post(url, files=files, data=data).json()
            return res["ParsedResults"][0]["ParsedText"]
        except:
            return ""

# ---------------------------------------------------
# TEXT FILTERS (Profanity, Hate, Self-Harm, Sexual)
# ---------------------------------------------------
PROFANITY = [
    "fuck","f*ck","f**k","f***","f----","fuk","fk","fucc","fock","fekk","fkn",
    "shit","sh*t","sh**","sh1t","shiit","shyt","shiddy","shite",
    "bitch","b1tch","biatch","b!tch","btch","betch","bicth",
    "ass","a$$","azz","arse","arsehole","asshole","asshat","asstard","assclown",
    "bastard","bast*rd","bast@rd","bastid",
    "crap","cr*p","cr4p","crappy",
    "damn","damm","damnit","dammit","damnation",
    "bloody","bloodyhell","bloodyfool",
    "motherfucker","m0therfucker","mother f*cker","mf","mfer",
    "cunt","c*nt","cnt","kunt","cuntbag","cuntface",
    "dick","d1ck","d!ck","dik","dickhead","douche","douchebag","douch3",
    "pussy","p*ssy","pusy","pussi","puss","pushover",
    "slut","slutt","slutty","slutface",
    "whore","wh0re","ho","hoe","h0e","hore","thot",
    "bollocks","bullshit","bullsh*t","bullsh1t","bs","b.s.",
    "jerk","jackass","jack***","j3rk",
    "moron","idiot","imbecile","dumbass","dumb","dummy","dum dum",
    "prick","twat","tw@t","tw*t","twerp",
    "scumbag","scum","trash","garbage-person","waste","wasteman",
    "retard","r3tard","retarded","slow-brain","simpleton",
    "stupid","stup*d","st00pid","stupidhead","stoopid",
    "wanker","wank","tosser","git","dipshit","dipsh*t","freak","weirdo",
    "go to hell","to hell with you","hell no","hellhole",
    "loser","l0ser","losr","failure","failboy","failgirl",
    "snake","rat","rodent","parasite",
    "bootlicker","boot licker","brown noser",
    "coward","chicken","weakling","wimp","punk",
    "screw you","screw-off","screw this",
    "shut up","shut the hell up","shut it",
    "worthless","useless","good for nothing",
    "degenerate","degen","filth","dirty-minded","crook","thief",
    "liar","lying piece","fraud","hypocrite",
    "blockhead","bonehead","airhead","numbskull","meathead",
    "fool","foolish","goof","goofy","clown",
    "jerkwad","jerkface","butthead","buttface","buttbrain",
    "nonsense","bull","craphead",
    "annoying","pain in the neck","pain in the ass",
    "broke-ass","cheap-ass","lazy-ass","fake-ass",
    "poser","wannabe","tryhard","pathetic",
    "delusional","brain-dead","brainless",
    "idiotic","mindless","ignorant","dense",
    "gutter-trash","low-life","bottom-feeder",
    "psycho","lunatic","crazy","deranged",
    "creep","creepy","gross","disgusting",
    "buffoon","oaf","clownish",
    "half-wit","nitwit","twit"
]

HATE = [
    "kill you","kill yourself","kys","k.y.s","k y s","kys now",
    "i will kill you","i will kill","i'll kill you","i’ll kill you",
    "murder you","i will murder","i'll murder","murderous",
    "die","go die","drop dead","you should die","you deserve to die",
    "i hope you die","i hope you choke","choke and die",
    "hang yourself","go hang","hang him","hang her",
    "choke yourself","strangle you","strangle him",
    "terrorist","terrorism supporter","isis","extremist","radical","militant extremist",
    "racist","race hate","racial hate","ethnic hate","ethnic slur","racial slur",
    "nazi","neo-nazi","hitler","fascist","white power","white supremacist","supremacy",
    "slave","enslave you","you are a slave","slave mindset",
    "go back to your country","you don’t belong here","not welcome",
    "bomb you","i will bomb","bomb threat","i will attack","attack you",
    "threaten","threatening","harass","harassing",
    "harm you","hurt you","break you","beat you","beat you up","beat the hell out of you",
    "stab you","stab him","stab her","stabbing",
    "shoot you","gun you down","gunned down","i'll shoot you",
    "blow you up","explode you","explode his house",
    "lynch you","lynch him","lynch her","lynchers","lynching mob",
    "burn you","burn alive","burn your house","arson threat",
    "abuse you","abusive","violent toward you",
    "you’re a disease","you’re filth","subhuman","nonhuman","monster",
    "monkey (racial)","ape (racial)","animal (insult)","pig (insult)","vermin",
    "destroy you","ruin you","end you","i will end you",
    "hunt you","hunt him","hunt her",
    "execution","execute you","execute him","terminate you",
    "go to hell","rot in hell","burn in hell","damnation",
    "i’ll smash you","i’ll crush you","i’ll break your bones","break your neck",
    "die painfully","painful death","slow death","slow painful death",
    "ethnic cleansing","racial purge","purge you","cleanse you",
    "genocide supporter","hate speech supporter",
    "you people are trash","your race is trash","your kind is worthless",
    "you don’t deserve to live","your life is worthless",
    "we will find you","we will get you","we are coming for you",
    "you are the enemy","enemy of the state","enemy of people",
    "absolute scum","subspecies","worthless human",
    "violent threat","attack threat","harm threat",
    "destroy your family","destroy everything","destroy your life",
    "dox you","doxxing threat","expose you",
    "i’ll poison you","i’ll drug you","poison threat",
    "discriminate you","racially insult you"
]

SELF_HARM = [
    "i want to die","i wanna die","want to die","wish i was dead","should be dead",
    "i hate my life","hate my life","life is worthless","life is pointless","my life is pointless",
    "i am worthless","i am useless","i feel useless","feel empty","empty inside",
    "i want to kill myself","kill myself","killing myself","kms","k.m.s","k m s",
    "suicidal","suicide thought","suicide attempt","attempt suicide","commit suicide",
    "thinking of suicide","thinking of ending it",
    "cut myself","cutting myself","self harm","self-harm","selfharm","hurt myself",
    "i want to disappear","i should disappear","i wish i vanished","vanish forever",
    "no reason to live","don’t want to live","don’t wanna live",
    "end my life","ending my life","take my life","take my own life",
    "i am broken","i’m broken","i can’t go on","i can’t keep living","i can’t do this anymore",
    "want to bleed","want to cut","i should bleed","bleeding self","razor selfharm",
    "i deserve pain","i want pain","hurt me emotionally","make me hurt",
    "life is suffering","everything hurts","nothing matters",
    "nobody cares","nobody loves me","i’m alone","feel alone",
    "i’m done","i give up","i quit life","giving up life",
    "ending everything","ending it all","i'm finished","finished with life",
    "tired of living","tired of life","want escape life",
    "better if i die","better without me","people better without me",
    "i am a burden","i’m a burden","burden to all",
    "my existence is pain","my existence sucks",
    "i can’t survive","i am hopeless","feeling hopeless",
    "fear of living","don’t want tomorrow",
    "can’t breathe emotionally","emotionally dead",
    "i need help","crying inside","suffering mentally",
    "self-destruction","self destruct","self-destruction thoughts",
    "give up on everything","let me go","let me die",
    "escape this world","escape reality",
    "i feel dead","dead inside","emotionally dead",
    "i don’t matter","i’m nothing","am nothing","not worth living"
]

SEXUAL = [
    "sex","sexual","sex act","sex chat","sexual intent",
    "nude","nudes","send nudes","naked","nudity","nude photo","nude pic",
    "boobs","tits","breasts","cleavage","chest exposed",
    "porn","pornographic","adult content","adult video","adult photo",
    "xxx","nsfw","not safe for work","18+",
    "erotic","erotica","sensual","seductive",
    "fetish","kinky","kink","roleplay adult",
    "hot body","sexy body","sexy pic","sext","sexting",
    "kiss me","touch me","cuddle me sexually",
    "seduce","seducing","flirt","flirting sexually",
    "intimate","intimacy","sexual chat",
    "provocative","suggestive","suggestive pose",
    "strip","stripper","strip show","strip dance",
    "lapdance","lap dance","adult entertainer",
    "lingerie","underwear pic","bikini pic","revealing outfit",
    "humping","grinding","rubbing body",
    "arousing","arousal","turned on","feeling horny","horny",
    "adult star","adult model","camgirl","camboy",
    "hookup","hooking up","one night stand","casual encounter",
    "lust","lustful","lusting","sexual fantasy",
    "bedroom picture","bathroom selfie nude","mirror nude","provocative selfie",
    "explicit pic","explicit photo","explicit image",
    "fetish content","adult fetish",
    "dirty talk","dirty message","adult message",
    "spicy pic","spicy message",
    "threesome","group adult act","swinger",
    "romantic but adult","mature content","sexual tone",
    "seductive tone","seduction attempt",
    "intimate photo","private pic","private parts covered",
    "semi-nude","partial nudity","revealing clothing",
    "adult flirting","romantic flirting with adult intent",
    "body reveal","torso reveal","shirtless pic","scantily dressed",
    "adult-oriented","erotic pose","adult scenario",
    "provocative selfie","risqué photo",
    "for adults only","18 plus","adult-only zone"
]

# ---------------------------------------------------
# SIGHTENGINE IMAGE MODERATION
# ---------------------------------------------------
USER = "872379412"
SECRET = "BggWDfoR2MtExba7FVjwepaznrxWejv6"

def image_moderation(img_path):
    url = "https://api.sightengine.com/1.0/check.json"
    with open(img_path, 'rb') as f:
        files = {"media": f}
        params = {
            "models": "nudity,wad,offensive,gore,weapon,violence",
            "api_user": USER,
            "api_secret": SECRET,
        }
        try:
            return requests.post(url, data=params, files=files).json()
        except:
            return {}

# ---------------------------------------------------
# SAVE IMAGE
# ---------------------------------------------------
def save_uploaded_image(uploaded_file):
    img = Image.open(uploaded_file)
    if img.mode not in ("RGB","L"):
        img = img.convert("RGB")
    img.save("temp.png", "PNG")
    return "temp.png"

# ---------------------------------------------------
# TEXT SCORING
# ---------------------------------------------------
def analyze_text(raw_text):
    text = raw_text.lower()
    reasons = []

    if any(word in text for word in PROFANITY):
        reasons.append("Profanity detected.")

    if any(word in text for word in HATE):
        reasons.append("Hate or threatening language detected.")

    if any(word in text for word in SELF_HARM):
        reasons.append("Self-harm / suicidal expression detected.")

    if any(word in text for word in SEXUAL):
        reasons.append("Sexual/explicit text detected.")

    return reasons

# ---------------------------------------------------
# DECISION FUSION
# ---------------------------------------------------
def fuse(text_reasons, img_res):
    reasons = text_reasons.copy()

    nudity = img_res.get("nudity", {}) or {}
    if nudity.get("raw", 0) > 0.35:
        reasons.append("Nudity detected.")

    if nudity.get("sexual_activity", 0) > 0.25:
        reasons.append("Sexual activity in image.")

    if img_res.get("weapon", {}).get("prob", 0) > 0.4:
        reasons.append("Weapon detected.")

    if img_res.get("violence", {}).get("prob", 0) > 0.4:
        reasons.append("Violence detected.")

    if img_res.get("offensive", {}).get("prob", 0) > 0.4:
        reasons.append("Hate/offensive symbol detected.")

    if img_res.get("gore", {}).get("prob", 0) > 0.3:
        reasons.append("Gore detected.")

    final = "OKAY" if not reasons else "BAD"
    return final, reasons

# ---------------------------------------------------
# UI
# ---------------------------------------------------
st.title("🚨 Harmful Content Detection System")

uploaded = st.file_uploader("Upload image", type=["jpg","jpeg","png"])

if uploaded:
    temp_path = save_uploaded_image(uploaded)
    st.image(temp_path, width=350)

    # OCR
    text = extract_text(temp_path)

    st.markdown("<div class='section-card'>", unsafe_allow_html=True)
    st.subheader("🔍 Extracted Text")
    st.write(text if text.strip() else "*No text found*")
    st.markdown("</div>", unsafe_allow_html=True)

    # TEXT ANALYSIS
    text_reasons = analyze_text(text)

    # IMAGE ANALYSIS
    img_res = image_moderation(temp_path)

    # FUSION
    final, reasons = fuse(text_reasons, img_res)

    # ---------------------------------------------------
    # FINAL DASHBOARD
    # ---------------------------------------------------
    st.subheader("📊 Final Evaluation Dashboard")

    if final == "BAD":
        st.markdown("<div class='result-bad'>🚨 BAD</div>", unsafe_allow_html=True)
    else:
        st.markdown("<div class='result-okay'>✅ OKAY</div>", unsafe_allow_html=True)

    # --- SUMMARY CARDS ---
    st.write("### 🔎 Harmful Content Analysis Summary")

    col1, col2, col3, col4, col5 = st.columns(5)

    def score_box(col, title, value):
        with col:
            st.metric(label=title, value=f"{value:.2f}")

    nudity_score = img_res.get("nudity", {}).get("raw", 0)
    violence_score = img_res.get("violence", {}).get("prob", 0)
    weapon_score = img_res.get("weapon", {}).get("prob", 0)
    gore_score = img_res.get("gore", {}).get("prob", 0)
    offensive_score = img_res.get("offensive", {}).get("prob", 0)

    score_box(col1, "Nudity", nudity_score)
    score_box(col2, "Violence", violence_score)
    score_box(col3, "Weapon", weapon_score)
    score_box(col4, "Gore", gore_score)
    score_box(col5, "Offensive", offensive_score)

    # --- PIE CHART ---
    st.write("### 🥧 Trigger Contribution Chart")

    labels = []
    sizes = []

    if nudity_score > 0: labels.append("Nudity"); sizes.append(nudity_score)
    if violence_score > 0: labels.append("Violence"); sizes.append(violence_score)
    if weapon_score > 0: labels.append("Weapon"); sizes.append(weapon_score)
    if gore_score > 0: labels.append("Gore"); sizes.append(gore_score)
    if offensive_score > 0: labels.append("Offensive"); sizes.append(offensive_score)

    if not labels:
        labels = ["Safe"]
        sizes = [1]

    fig1, ax1 = plt.subplots()
    ax1.pie(sizes, labels=labels, autopct="%1.1f%%")
    ax1.axis('equal')
    st.pyplot(fig1)

    # --- BAR CHART ---
    st.write("### 📈 Probability Scores")

    fig2, ax2 = plt.subplots()
    categories = ["Nudity", "Violence", "Weapon", "Gore", "Offensive"]
    values = [nudity_score, violence_score, weapon_score, gore_score, offensive_score]

    ax2.bar(categories, values)
    st.pyplot(fig2)

    # --- TEXT REASONS ---
    st.write("### 🧾 Detected Issues")
    if reasons:
        for r in reasons:
            st.write("•", r)
    else:
        st.write("No harmful content detected.")

    # --- RAW JSON ---
    with st.expander("🧰 Raw OCR & API Debug Data"):
        st.write("**OCR Extracted Text:**")
        st.write(text)
        st.write("**SightEngine Raw Response:**")
        st.json(img_res)
