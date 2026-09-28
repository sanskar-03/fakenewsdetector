from backend.services.source_registry import source_info

def source_credibility(url):
    return source_info(url)

# Compatibility exports for older LangGraph imports.
def text_verifier_node(state):
    return state

def image_verifier_node(state):
    return state

def fact_check_retriever_node(state):
    return state

def source_credibility_node(state):
    return state
