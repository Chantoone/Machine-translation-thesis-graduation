"""Spatial OCR and readable PDF replacement, independent of translation transport."""
import html
import logging
import re
from collections import Counter
from dataclasses import dataclass

import pymupdf
import pytesseract
from PIL import Image, ImageOps

LOGGER = logging.getLogger(__name__)


@dataclass
class Region:
    rect: pymupdf.Rect
    text: str
    lines: list
    size: float
    foreground: tuple
    background: tuple
    confidence: float
    bounds: object = None


def colors(image, box):
    crop = image.crop(box).convert('RGB')
    counts = Counter(crop.get_flattened_data() if hasattr(crop, "get_flattened_data") else crop.getdata())
    background = counts.most_common(1)[0][0]
    # Ignore antialiasing when selecting the text color.
    candidates = [(count, color) for color, count in counts.items()
                  if sum(abs(a-b) for a,b in zip(color, background)) > 180]
    foreground = max((item for item in candidates if item[0] >= 3),
                     key=lambda item: sum(abs(a-b) for a,b in zip(item[1],background)),
                     default=(0,(0,0,0)))[1]
    return tuple(c/255 for c in foreground), tuple(c/255 for c in background)


def join_lines(left, right):
    if left.endswith('-') and right[:1].islower():
        # Keep lexical hyphens: natural-language, cosine-similarity.
        return left + right
    return left + ' ' + right


def extract_regions(image, page_rect, language):
    image = ImageOps.exif_transpose(image).convert('RGB')
    # Keep detail for small print; cap only extreme image dimensions.
    image.thumbnail((5000, 5000))
    sx, sy = page_rect.width/image.width, page_rect.height/image.height
    data = pytesseract.image_to_data(image, lang=language, config='--psm 11',
                                    output_type=pytesseract.Output.DICT, timeout=60)
    groups = {}
    for i, text in enumerate(data['text']):
        if text.strip():
            groups.setdefault((data['block_num'][i], data['par_num'][i], data['line_num'][i]), []).append(i)
    regions = []
    for indices in groups.values():
        x0 = min(data['left'][i] for i in indices)
        y0 = min(data['top'][i] for i in indices)
        x1 = max(data['left'][i]+data['width'][i] for i in indices)
        y1 = max(data['top'][i]+data['height'][i] for i in indices)
        text = ' '.join(data['text'][i] for i in indices).strip()
        confidence = sum(float(data['conf'][i]) for i in indices)/len(indices)
        if x0 < 3 and y0 < 3 or (len(text) == 1 and not text.isdigit()):
            continue
        foreground, background = colors(image, (x0, y0, x1, y1))
        if confidence < 65:
            crop = image.crop((max(0,x0-8), max(0,y0-8), min(image.width,x1+8), min(image.height,y1+8)))
            gray = ImageOps.grayscale(crop)
            if sum(background) < 1.5:
                gray = ImageOps.invert(gray)
            gray = ImageOps.autocontrast(gray)
            retry = pytesseract.image_to_data(gray, lang=language, config='--psm 7',
                                              output_type=pytesseract.Output.DICT, timeout=30)
            words = [(t, float(c)) for t,c in zip(retry['text'],retry['conf']) if t.strip()]
            if words and sum(c for _,c in words)/len(words) > confidence:
                text = ' '.join(t for t,_ in words)
                confidence = sum(c for _,c in words)/len(words)
        rect = pymupdf.Rect(x0*sx, y0*sy, x1*sx, y1*sy)
        regions.append(Region(rect, text, [rect], rect.height, foreground, background, confidence))
    # Join only aligned, similarly styled lines with a small vertical gap.
    # Search geometrically, not in OCR's interleaved reading order.
    regions.sort(key=lambda r:(r.rect.y0, r.rect.x0))
    merged = []
    for region in regions:
        candidates = [r for r in merged
                      if abs(r.rect.x0-region.rect.x0) < 5
                      and 0 <= region.rect.y0-r.rect.y1 < max(7, r.size*1.2)
                      and .6 < r.size/region.size < 1.65
                      and (region.text[:1].islower() or r.text.endswith(("-", ","))
                           or (r.size > 25 and region.size > 25 and r.text.isupper() and region.text.isupper()))
                      and max(abs(a-b) for a,b in zip(r.background,region.background)) < .12]
        if candidates:
            previous = min(candidates, key=lambda r:region.rect.y0-r.rect.y1)
            previous.text = join_lines(previous.text, region.text)
            previous.rect |= region.rect
            previous.lines.extend(region.lines)
            previous.confidence = min(previous.confidence,region.confidence)
        else:
            merged.append(region)
    for region in merged:
        # Stop expansion at visible card/background borders, not only at text.
        rect = region.rect
        right = min(page_rect.width-2, rect.x1+16)
        bottom = min(page_rect.height-2, rect.y1+max(12,region.size*1.5))
        def matches(x, y):
            pixel = image.getpixel((max(0,min(image.width-1,int(x/sx))),
                                    max(0,min(image.height-1,int(y/sy)))))
            return max(abs(v/255-b) for v,b in zip(pixel,region.background)) < .06
        for step in range(2, int(bottom-rect.y1)+1):
            if not matches(rect.x0-2, rect.y1+step):
                bottom = rect.y1+step-1
                break
        for step in range(2, int(right-rect.x1)+1):
            if not matches(rect.x1+step, rect.y0-2):
                right = rect.x1+step-1
                break
        region.bounds = pymupdf.Rect(rect.x0,rect.y0,max(rect.x1,right),max(rect.y1,bottom))
    return merged


def css_color(color):
    return '#%02x%02x%02x' % tuple(round(c*255) for c in color)


def render_regions(page, regions, translations):
    if len(regions) != len(translations):
        raise ValueError('Số vùng dịch không khớp số vùng OCR.')
    changed = [(r,t) for r,t in zip(regions,translations) if r.text.strip() != t.strip()]
    for region,_ in changed:
        for line in region.lines:
            page.add_redact_annot(line + (-.7,-.7,.7,.7), fill=region.background)
    page.apply_redactions(images=0, graphics=0)
    for region, text in changed:
        rect = pymupdf.Rect(region.rect)
        # Grow into available space, stopping before adjacent columns/rows.
        right = min(page.rect.width-12, rect.x1+16)
        bottom = min(page.rect.height-12, rect.y1+max(12,region.size*1.5))
        if region.bounds is not None:
            right = min(right,region.bounds.x1)
            bottom = min(bottom,region.bounds.y1)
        for other in regions:
            if other is region:
                continue
            o = other.rect
            if o.y0 < rect.y1 and o.y1 > rect.y0 and o.x0 >= rect.x1:
                right = min(right,o.x0-4)
            if o.x0 < right and o.x1 > rect.x0 and o.y0 >= rect.y1:
                bottom = min(bottom,o.y0-3)
        rect.x1 = max(rect.x1,right)
        rect.y1 = max(rect.y1,bottom)
        size = max(8, min(36,region.size*1.1))
        css = (f'* {{font-family: sans-serif; font-size:{size}pt; '
               f'color:{css_color(region.foreground)}; line-height:1.15;}} '
               'body {margin:0;padding:0;}')
        safe = html.escape(text).replace('\n','<br>')
        spare, scale = page.insert_htmlbox(rect, safe, css=css, scale_low=0)
        if spare < 0:
            raise ValueError('Không thể đặt bản dịch vào một vùng chữ quá nhỏ.')
