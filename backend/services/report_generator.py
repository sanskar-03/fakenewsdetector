from io import BytesIO
from datetime import datetime
from xml.sax.saxutils import escape
from pathlib import Path
import os
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from backend.services.report_helpers import normalize_confidence, normalize_evidence, clean_reasoning, method_text, tr

FONT_CACHE = {}

def _font_for_language(language, bold=False):
    candidates = {
        "hi":["hi_merged_B.ttf" if bold else "hi_merged_R.ttf"],
        "bn":["bn_merged_B.ttf" if bold else "bn_merged_R.ttf"],
        "ta":["ta_merged_B.ttf" if bold else "ta_merged_R.ttf"],
        "te":["te_merged_B.ttf" if bold else "te_merged_R.ttf"],
        "mr":["hi_merged.ttf"],
        "gu":["gu_merged_B.ttf" if bold else "gu_merged_R.ttf"],
        "kn":["kn_merged_B.ttf" if bold else "kn_merged_R.ttf"],
        "ml":["ml_merged_B.ttf" if bold else "ml_merged_R.ttf"],
        "pa":["pa_merged_B.ttf" if bold else "pa_merged_R.ttf"],
    }.get(language, ["NotoSans-Bold.ttf" if bold else "NotoSans-Regular.ttf"])
    project_fonts = Path(__file__).resolve().parent.parent / "assets" / "fonts"
    roots=[project_fonts, Path("/usr/share/fonts/truetype/noto"),Path("/usr/share/fonts/truetype/dejavu"),Path("C:/Windows/Fonts"),Path(os.environ.get("WINDIR","C:/Windows"))/"Fonts"]
    windows_fallback = {
        "hi":"Nirmala.ttf","bn":"Nirmala.ttf","ta":"Nirmala.ttf","te":"Nirmala.ttf",
        "mr":"Nirmala.ttf","gu":"Nirmala.ttf","kn":"Nirmala.ttf","ml":"Nirmala.ttf",
        "pa":"Nirmala.ttf"
    }
    if language in windows_fallback:
        candidates = candidates + [windows_fallback[language]]
    for name in candidates:
        for root in roots:
            p=root/name
            if p.exists():
                key=f"{language}_{bold}"
                if key not in FONT_CACHE:
                    font_name=f"Aletheia_{language}_{'B' if bold else 'R'}"
                    pdfmetrics.registerFont(TTFont(font_name,str(p)))
                    FONT_CACHE[key]=font_name
                return FONT_CACHE[key]
    return "Helvetica-Bold" if bold else "Helvetica"

def _verdict_label(language, verdict):
    labels = {
        "hi":{"REAL":"वास्तविक","FAKE":"फर्जी","UNVERIFIED":"असत्यापित"},
        "ta":{"REAL":"உண்மை","FAKE":"போலி","UNVERIFIED":"சரிபார்க்கப்படவில்லை"},
        "bn":{"REAL":"বাস্তব","FAKE":"ভুয়া","UNVERIFIED":"যাচাই করা যায়নি"},
        "te":{"REAL":"వాస్తవం","FAKE":"నకిలీ","UNVERIFIED":"ధృవీకరించబడలేదు"},
        "mr":{"REAL":"वास्तविक","FAKE":"बनावट","UNVERIFIED":"असत्यापित"},
        "gu":{"REAL":"વાસ્તવિક","FAKE":"ખોટું","UNVERIFIED":"ચકાસાયેલ નથી"},
        "kn":{"REAL":"ನೈಜ","FAKE":"ನಕಲಿ","UNVERIFIED":"ಪರಿಶೀಲಿಸಲಾಗಿಲ್ಲ"},
        "ml":{"REAL":"യഥാർത്ഥം","FAKE":"വ്യാജം","UNVERIFIED":"സ്ഥിരീകരിക്കാനായില്ല"},
        "pa":{"REAL":"ਅਸਲ","FAKE":"ਜਾਅਲੀ","UNVERIFIED":"ਤਸਦੀਕ ਨਹੀਂ ਹੋਈ"},
    }
    return labels.get(language, {}).get(verdict, verdict)

def _tier_label(language, tier):
    labels = {
        "hi":{"primary":"प्राथमिक / आधिकारिक","fact_check":"तथ्य-जाँच","reputable_news":"प्रतिष्ठित समाचार","general":"अन्य संबंधित"},
        "ta":{"primary":"முதன்மை / அதிகாரப்பூர்வ","fact_check":"உண்மைச் சரிபார்ப்பு","reputable_news":"நம்பகமான செய்தி","general":"பிற தொடர்புடைய"},
        "bn":{"primary":"প্রাথমিক / সরকারি","fact_check":"ফ্যাক্ট-চেক","reputable_news":"বিশ্বস্ত সংবাদ","general":"অন্যান্য সম্পর্কিত"},
        "te":{"primary":"ప్రాథమిక / అధికారిక","fact_check":"వాస్తవ నిర్ధారణ","reputable_news":"ప్రతిష్ఠాత్మక వార్తలు","general":"ఇతర సంబంధిత"},
        "mr":{"primary":"प्राथमिक / अधिकृत","fact_check":"तथ्य-जांच","reputable_news":"प्रतिष्ठित बातम्या","general":"इतर संबंधित"},
        "gu":{"primary":"પ્રાથમિક / સત્તાવાર","fact_check":"ફેક્ટ-ચેક","reputable_news":"પ્રતિષ્ઠિત સમાચાર","general":"અન્ય સંબંધિત"},
        "kn":{"primary":"ಪ್ರಾಥಮಿಕ / ಅಧಿಕೃತ","fact_check":"ವಾಸ್ತವ ಪರಿಶೀಲನೆ","reputable_news":"ವಿಶ್ವಾಸಾರ್ಹ ಸುದ್ದಿ","general":"ಇತರೆ ಸಂಬಂಧಿತ"},
        "ml":{"primary":"പ്രാഥമിക / ഔദ്യോഗിക","fact_check":"വസ്തുതാ പരിശോധന","reputable_news":"വിശ്വസനീയ വാർത്ത","general":"മറ്റ് ബന്ധപ്പെട്ട"},
        "pa":{"primary":"ਮੁੱਖ / ਅਧਿਕਾਰਤ","fact_check":"ਤੱਥ-ਜਾਂਚ","reputable_news":"ਭਰੋਸੇਯੋਗ ਖ਼ਬਰ","general":"ਹੋਰ ਸੰਬੰਧਿਤ"},
    }
    return labels.get(language, {}).get(tier, tier or tr(language,"not_available"))

def build_pdf(case):
    case=case if isinstance(case,dict) else {}
    result=case.get("result") if isinstance(case.get("result"),dict) else case
    language=case.get("language") or result.get("language") or "en"
    case_id=case.get("case_id") or result.get("case_id") or case.get("_history",{}).get("case_id") or "UNKNOWN"
    verdict=str(result.get("verdict") or case.get("verdict") or "UNVERIFIED").upper()
    confidence=normalize_confidence(result.get("confidence",case.get("confidence",0)))
    claim=case.get("claim") or result.get("claim") or case.get("article") or case.get("text") or ""
    evidence=normalize_evidence(result.get("evidence") or result.get("sources") or case.get("evidence") or case.get("sources") or [])
    trusted=[x for x in evidence if x.get("tier") in {"primary","fact_check"} or (not x.get("tier") and x.get("source_quality",{}).get("category") in {"trusted","PRIMARY OFFICIAL","TRUSTED / FACT-CHECK"})]
    general=[x for x in evidence if x not in trusted and (x.get("tier") in {"reputable_news","general"} or x.get("source_quality",{}).get("category") in {"general","GENERAL","REPUTABLE NEWS"}) and x.get("source_quality",{}).get("category") not in {"unverified","UNVERIFIED"}]
    unverified=[x for x in evidence if x not in trusted and x not in general]
    summary=result.get("decision_summary") if isinstance(result.get("decision_summary"),dict) else {}
    support=int(summary.get("trusted_supporting", result.get("trusted_supporting_count", sum(1 for x in trusted if x.get("relation")=="SUPPORTS"))))
    contradict=int(summary.get("trusted_contradicting", result.get("trusted_contradicting_count", sum(1 for x in trusted if x.get("relation")=="CONTRADICTS"))))
    neutral=int(summary.get("trusted_neutral", result.get("trusted_neutral_count", sum(1 for x in trusted if x.get("relation")=="NEUTRAL"))))
    basis=result.get("decision_basis") or ("trusted_consensus" if verdict=="REAL" else "trusted_contradiction" if verdict=="FAKE" else "insufficient_trusted_evidence")
    basis_label=tr(language,"consensus") if basis=="trusted_consensus" else tr(language,"conflict") if basis=="trusted_conflict" else tr(language,"insufficient") if basis=="insufficient_trusted_evidence" else tr(language,"decision_basis")
    image=result.get("image_verification") or result.get("image") or {}
    image_status=str(image.get("status") if isinstance(image,dict) else image or "NOT_PROVIDED")
    statusmap={"NOT_PROVIDED":"image_not_provided","NO_REFERENCE_MATCH":"image_no_reference"}
    stream=BytesIO()
    doc=SimpleDocTemplate(stream,pagesize=A4,rightMargin=40,leftMargin=40,topMargin=40,bottomMargin=40,title=f"Aletheia {case_id}")
    styles=getSampleStyleSheet(); body_font=_font_for_language(language); bold_font=_font_for_language(language,True)
    title_style=ParagraphStyle("AletheiaTitle",parent=styles["Title"],alignment=TA_CENTER,fontName=bold_font,fontSize=20,leading=25,spaceAfter=14)
    h2=ParagraphStyle("AletheiaH2",parent=styles["Heading2"],fontName=bold_font)
    body=ParagraphStyle("AletheiaBody",parent=styles["BodyText"],fontName=body_font,fontSize=9.5,leading=13)
    small=ParagraphStyle("AletheiaSmall",parent=body,fontSize=8.5,leading=11)
    story=[Paragraph("ALETHEIA — CASE FILE",title_style),Paragraph(escape(tr(language,"report")),h2),Spacer(1,8)]
    computed_strength = ("STRONG" if (support >= 2 or contradict >= 1) else
                         "MODERATE" if (len(trusted) >= 1 or len(general) >= 2) else "WEAK")
    strength_labels = {"hi":{"STRONG":"मजबूत","MODERATE":"मध्यम","WEAK":"कमज़ोर"},
                       "ta":{"STRONG":"வலுவான","MODERATE":"மிதமான","WEAK":"பலவீனமான"},
                       "bn":{"STRONG":"শক্তিশালী","MODERATE":"মাঝারি","WEAK":"দুর্বল"},
                       "te":{"STRONG":"బలమైన","MODERATE":"మధ్యస్థ","WEAK":"బలహీనమైన"},
                       "mr":{"STRONG":"मजबूत","MODERATE":"मध्यम","WEAK":"कमकुवत"},
                       "gu":{"STRONG":"મજબૂત","MODERATE":"મધ્યમ","WEAK":"નબળું"},
                       "kn":{"STRONG":"ಬಲವಾದ","MODERATE":"ಮಧ್ಯಮ","WEAK":"ದುರ್ಬಲ"},
                       "ml":{"STRONG":"ശക്തമായ","MODERATE":"മിതമായ","WEAK":"ദുർബലമായ"},
                       "pa":{"STRONG":"ਮਜ਼ਬੂਤ","MODERATE":"ਦਰਮਿਆਨਾ","WEAK":"ਕਮਜ਼ੋਰ"}}
    strength_text = strength_labels.get(language, {}).get(computed_strength, computed_strength)
    meta=Table([[tr(language,"case_id"),str(case_id)],[tr(language,"result"),_verdict_label(language, verdict)],[tr(language,"confidence"),f"{confidence:.1f}%"],[tr(language,"generated"),datetime.now().strftime("%d %b %Y, %H:%M")],[tr(language,"evidence_strength"),strength_text]],colWidths=[180,300])
    meta.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.5,colors.grey),("FONTNAME",(0,0),(0,-1),bold_font),("FONTNAME",(1,0),(1,-1),body_font),("VALIGN",(0,0),(-1,-1),"TOP"),("PADDING",(0,0),(-1,-1),6)]))
    story += [meta,Spacer(1,14),Paragraph(escape(tr(language,"claim")),h2),Paragraph(escape(str(claim)),body),Spacer(1,12)]
    decision=Table([[tr(language,"decision_basis"),basis_label],[tr(language,"trusted_total"),str(len(trusted))],[tr(language,"trusted_supporting"),str(support)],[tr(language,"trusted_contradicting"),str(contradict)],[tr(language,"trusted_neutral"),str(neutral)],[tr(language,"related_total"),str(len(evidence))],[tr(language,"image_status"),tr(language,statusmap.get(image_status,"not_available")) if image_status in statusmap else image_status]],colWidths=[230,250])
    decision.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.5,colors.grey),("FONTNAME",(0,0),(0,-1),bold_font),("FONTNAME",(1,0),(1,-1),body_font),("VALIGN",(0,0),(-1,-1),"TOP"),("PADDING",(0,0),(-1,-1),6)]))
    story += [Paragraph(escape(tr(language,"decision_basis")),h2),decision,Spacer(1,12),Paragraph(escape(tr(language,"reasoning")),h2),Paragraph(escape(clean_reasoning(result,language)),body),Spacer(1,10),Paragraph(escape(tr(language,"method")),h2),Paragraph(escape(method_text(result,language)),body),Spacer(1,14),Paragraph(escape(tr(language,"evidence")),h2)]
    def add_group(title,rows):
        story.append(Paragraph(escape(title),h2))
        if not rows: story.append(Paragraph(escape(tr(language,"not_available")),body)); story.append(Spacer(1,6)); return
        for i,item in enumerate(rows,1):
            q=item.get("source_quality",{}); name=item.get("title") or item.get("source_name") or item.get("source") or item.get("name") or q.get("name") or "Source"; rel=item.get("relation","NEUTRAL"); reltxt=tr(language,"support") if rel=="SUPPORTS" else tr(language,"contradict") if rel=="CONTRADICTS" else tr(language,"neutral"); tier=item.get("tier") or q.get("quality","Unknown"); snippet=clean_reasoning({"reasoning":item.get("content") or item.get("snippet") or ""}, language) if (item.get("content") or item.get("snippet")) else ""; snippet=str(snippet)[:420]; line=f"{i}. {escape(str(name))}<br/>{escape(tr(language,'source_quality'))}: {escape(str(_tier_label(language, tier)))}<br/>{escape(tr(language,'relation'))}: {escape(reltxt)}"; url=item.get("url") or ""; line += f"<br/>{escape(str(url))}" if url else ""; line += f"<br/>{escape(snippet)}" if snippet else ""; story.extend([Paragraph(line,small),Spacer(1,7)])
    add_group(f"{tr(language,'trusted')} ({len(trusted)})",trusted); add_group(f"{tr(language,'general')} ({len(general)})",general); add_group(f"{tr(language,'unverified')} ({len(unverified)})",unverified)
    if image_status=="NO_REFERENCE_MATCH": story += [Spacer(1,8),Paragraph(escape(tr(language,"image_no_reference")),body)]
    story += [Spacer(1,12),Paragraph(escape(tr(language,"human_note")),body)]
    doc.build(story); stream.seek(0); return stream
