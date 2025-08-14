from odoo import http
from odoo.http import request
import json
import logging
import requests
from bs4 import BeautifulSoup, NavigableString, Tag

_logger = logging.getLogger(__name__)

def html_to_escpos(html: str) -> bytes:
    ESC_INIT = b'\x1b@'
    ESC_ALIGN_LEFT = b'\x1ba\x00'
    ESC_ALIGN_CENTER = b'\x1ba\x01'
    ESC_BOLD_ON = b'\x1bE\x01'
    ESC_BOLD_OFF = b'\x1bE\x00'
    ESC_FONT_DOUBLE = b'\x1b!\x38'
    ESC_FONT_NORMAL = b'\x1b!\x00'
    ESC_CUT = b'\x1dV\x00'

    soup = BeautifulSoup(html, "html.parser")
    result = ESC_INIT

    def apply_style(text: str, style: dict) -> bytes:
        output = b""
        output += ESC_ALIGN_CENTER if style.get("center") else ESC_ALIGN_LEFT
        output += ESC_FONT_NORMAL if style.get("double") else ESC_FONT_NORMAL
        output += ESC_BOLD_ON if style.get("bold") else ESC_BOLD_OFF
        output += text.encode("ascii", "ignore") + b"\n"
        return output

    def parse_element(el, style=None):
        nonlocal result
        style = style or {"bold": False, "double": False, "center": False}

        if isinstance(el, NavigableString):
            text = el.strip()
            if text:
                result += apply_style(text, style)

        elif isinstance(el, Tag):
            tag = el.name.lower()
            classes = el.get("class", [])
            inline_style = el.get("style", "")

            new_style = style.copy()
            if tag in ["b", "strong"]:
                new_style["bold"] = True
            if "text-center" in classes:
                new_style["center"] = True
            if "pos-receipt-title" in classes or "receipt-header" in classes:
                new_style["bold"] = True
            if tag == "hr":
                result += b"-" * 32 + b"\n"
                return

            # Handle quantity + product line
            if "d-flex" in classes:
                parts = [child.get_text(strip=True) for child in el.find_all("span")]
                line = " ".join(parts)
                result += apply_style(line[:32], new_style)
                return

            # Handle span that contains a mixed inline sentence (e.g., Table 1 # 004)
            if tag == "span":
                text_parts = []
                for child in el.children:
                    if isinstance(child, NavigableString):
                        text_parts.append(child.strip())
                    elif isinstance(child, Tag) and child.name.lower() in ["strong", "b"]:
                        text_parts.append(child.get_text(strip=True))
                if text_parts:
                    line = " ".join(text_parts).replace("  ", " ")
                    result += apply_style(line.strip(), new_style)
                    return

            for child in el.children:
                parse_element(child, new_style)

            if tag in ["div", "p"]:
                result += b"\n"

    for child in soup.children:
        parse_element(child)

    result += ESC_CUT
    return result

    
class KotPrintController(http.Controller):
    @http.route('/pos/parse_data', type='json', auth='public')
    def parse_data(self, data):
        try:
            escpos_data = html_to_escpos(data)
            return {'result': True, 'data': escpos_data}

        except Exception as e:
            _logger.exception("Error in KOT printing")
            return {'result': False, 'message': str(e)}
        
    @http.route('/pos/flask_url', type='json', auth='public')
    def get_flask_url(self, config_id):
        config = request.env['pos.config'].sudo().browse([config_id])
        return {
            'url': config.flask_endpoint_url,
        }

    @http.route('/pos/print_kot', type='json', auth='public')
    def print_kot(self, receipt, printer):
        """Send KOT data to the Flask endpoint"""
        try:
            escpos_data = html_to_escpos(receipt)

            # Encode to base64 for JSON transport
            escpos_b64 = escpos_data

            # Get endpoint URL from POS config
            pos_config = request.env['pos.config'].sudo().search([], limit=1)

            flask_url = pos_config.flask_endpoint_url
            payload = {'content': escpos_b64, 'printer': printer}

            response = requests.post(
                flask_url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            if response.status_code == 200:
                return {'result': True}
            else:
                return {'result': False, 'message': f"Printer error: {response.text}"}
                
        except Exception as e:
            _logger.exception("Error in KOT printing")
            return {'result': False, 'message': str(e)}
    
