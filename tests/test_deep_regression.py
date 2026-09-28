from backend.services.retriever import relation, relevance, source_info
from backend.services.agent import _decision
from backend.services.report_generator import build_pdf

CLAIM='Suvendu Adhikari ate fish at the Kalighat temple and described himself as a Sanatani Hindu'


def test_unrelated_false_article_is_neutral():
    text='Fact Check: viral video of man dancing with alcohol is false. The man is not Ram Mandir Trust CEO Jitendra Mishra.'
    assert relation(CLAIM,text) == 'NEUTRAL'


def test_same_claim_confirmation_is_support():
    text='Suvendu Adhikari ate fish bhog at Kalighat temple and said he is a true Sanatani Hindu.'
    assert relation(CLAIM,text) == 'SUPPORTS'


def test_reputable_news_is_not_verdict_trusted():
    info=source_info('https://www.livehindustan.com/national/example.html')
    assert info['tier']=='reputable_news' and info['trusted'] is False


def test_single_support_is_not_real():
    ev=[{'tier':'fact_check','trusted':True,'relevance':.8,'relation':'SUPPORTS','source_domain':'a.com'}]
    assert _decision(ev)[0]=='UNVERIFIED'


def test_two_independent_supports_are_real():
    ev=[
        {'tier':'fact_check','trusted':True,'relevance':.8,'relation':'SUPPORTS','source_domain':'a.com'},
        {'tier':'primary','trusted':True,'relevance':.8,'relation':'SUPPORTS','source_domain':'b.gov.in'},
    ]
    assert _decision(ev)[0]=='REAL'


def test_conflict_is_unverified():
    ev=[
        {'tier':'fact_check','trusted':True,'relevance':.8,'relation':'SUPPORTS','source_domain':'a.com'},
        {'tier':'fact_check','trusted':True,'relevance':.8,'relation':'CONTRADICTS','source_domain':'b.com'},
    ]
    assert _decision(ev)[0]=='UNVERIFIED'


def test_pdf_contains_all_core_languages(tmp_path):
    claims={'hi':'सुवेंदु अधिकारी ने कालीघाट मंदिर में मछली का भोग खाया।','ta':'சுவேந்து அதிகாரி காளிகாட் கோவிலில் மீன் பிரசாதம் சாப்பிட்டார்.','bn':'সুবেন্দু অধিকারী কালীঘাট মন্দিরে মাছের প্রসাদ খেয়েছেন।','te':'సువేందు అధికారి కాళీఘాట్ ఆలయంలో చేప ప్రసాదం తిన్నారు.','mr':'सुवेंदु अधिकारी यांनी कालीघाट मंदिरात माशाचा प्रसाद खाल्ला.','gu':'સુવેન્દુ અધિકારીએ કાલીઘાટ મંદિરમાં માછલીનો પ્રસાદ ખાધો.','kn':'ಸುವೇಂದು ಅಧಿಕಾರಿ ಕಾಳಿಘಾಟ್ ದೇವಸ್ಥಾನದಲ್ಲಿ ಮೀನಿನ ಪ್ರಸಾದ ಸೇವಿಸಿದರು.','ml':'സുവേന്ദു അധികാരി കാളിഘട്ട് ക്ഷേത്രത്തിൽ മീൻ പ്രസാദം കഴിച്ചു.','pa':'ਸੁਵੇਂਦੂ ਅਧਿਕਾਰੀ ਨੇ ਕਾਲੀਘਾਟ ਮੰਦਰ ਵਿੱਚ ਮੱਛੀ ਦਾ ਪ੍ਰਸਾਦ ਖਾਧਾ.'}
    for lang,claim in claims.items():
        pdf=build_pdf({'case_id':'AF-TEST123','language':lang,'result':{'claim':claim,'verdict':'UNVERIFIED','confidence':25,'evidence':[],'reasoning':claim,'decision_basis':'insufficient_trusted_evidence','image_verification':{'status':'NOT_PROVIDED'}}})
        data=pdf.read(); assert len(data)>1000
