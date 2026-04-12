from dataclasses import dataclass

@dataclass
class ExtractedResponse:
    html: str
    text: str

def extract_response(response_html: str, response_text: str) -> ExtractedResponse:
    return ExtractedResponse(html=response_html, text=response_text)
