from typing import TypedDict,Optional,Any
class VerificationState(TypedDict, total=False):
    article:str; image_url:Optional[str]; claim:str; classification:Any; trusted_evidence:list; live_evidence:list; image:Any; verdict:str; confidence:float; reasoning:str
