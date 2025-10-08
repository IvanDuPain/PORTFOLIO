import json
import re
from pathlib import Path

try:
    from pdfminer.high_level import extract_text
except Exception:
    extract_text = None

try:
    import fitz  # PyMuPDF
except Exception:
    fitz = None


PDF_NAME = "Portfolio Iwan Mertil (1).pdf"


def naive_parse(text: str) -> dict:
    # Normalize whitespace
    text = re.sub(r"\r", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    lines = [l.strip() for l in text.splitlines()]
    non_empty = [l for l in lines if l]
    blob = "\n".join(non_empty)

    # Basic sections via French keywords commonly found in portfolios/CV
    sections = {
        "about": "",
        "experiences": [],
        "projects": [],
        "skills": [],
        "contact": {"email": "", "phone": "", "location": "", "linkedin": "", "github": ""},
        "images": {"portrait": "", "gallery": []},
        "raw_text": "",
    }

    # Contact extraction
    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", blob)
    if email_match:
        sections["contact"]["email"] = email_match.group(0)
    phone_match = re.search(r"(?:\+?\d{1,3}[\s.-]?)?(?:\(\d+\)[\s.-]?)?\d[\d\s.-]{7,}\d", blob)
    if phone_match:
        sections["contact"]["phone"] = phone_match.group(0)
    # Simple linkedin/github
    m = re.search(r"https?://(www\.)?linkedin\.com/[^\s]+", blob)
    if m: sections["contact"]["linkedin"] = m.group(0)
    m = re.search(r"https?://(www\.)?github\.com/[^\s]+", blob)
    if m: sections["contact"]["github"] = m.group(0)

    # Try to split by headings
    split_patterns = [
        ("experiences", r"(?i)exp[ée]riences?|parcours professionnel|exp pro"),
        ("projects", r"(?i)projets?|r[ée]alisations?|portfolio"),
        ("skills", r"(?i)comp[ée]tences?|skills|technologies"),
        ("about", r"(?i)[àa] propos|profil|summary|pr[ée]sentation"),
    ]

    # Build simple index of sections by searching markers
    indices = []
    for name, pat in split_patterns:
        for m in re.finditer(pat, blob):
            indices.append((m.start(), name))
    indices.sort()

    chunks = {}
    for i, (start, name) in enumerate(indices):
        end = indices[i + 1][0] if i + 1 < len(indices) else len(blob)
        chunks[name] = blob[start:end].strip()

    sections["raw_text"] = blob

    # About: take first paragraph if present
    if chunks.get("about"):
        about_text = re.sub(r"(?i)^[^\n]*?propos[^\n]*\n", "", chunks["about"]).strip()
        sections["about"] = about_text[:800]
    else:
        # fallback: first 800 chars
        sections["about"] = blob[:800]

    # Experiences: split into entries by common separators (dates, bullets)
    if chunks.get("experiences"):
        body = re.sub(r"(?i)^.*?exp[ée]riences?.*\n", "", chunks["experiences"]).strip()
        entries = re.split(r"\n\s*[-•]\s+|\n\n+", body)
        for e in entries:
            if len(e) < 15: 
                continue
            title = e.split("\n")[0][:120]
            period = "" 
            m = re.search(r"(\d{4}\s*[-–]\s*(?:\d{4}|pr[ée]sent|aujourd'hui))", e, re.IGNORECASE)
            if m: period = m.group(1)
            sections["experiences"].append({"title": title, "company": "", "period": period, "location": "", "description": e[:400]})

    # Projects
    if chunks.get("projects"):
        body = re.sub(r"(?i)^.*?projets?.*\n", "", chunks["projects"]).strip()
        entries = re.split(r"\n\s*[-•]\s+|\n\n+", body)
        for e in entries:
            if len(e) < 10:
                continue
            name = e.split("\n")[0][:80]
            link = ""
            m = re.search(r"https?://[^\s]+", e)
            if m: link = m.group(0)
            sections["projects"].append({"name": name, "summary": e[:220], "link": link})

    # Skills: comma or line separated
    if chunks.get("skills"):
        body = re.sub(r"(?i)^.*?comp[ée]tences?.*\n", "", chunks["skills"]).strip()
        tokens = re.split(r",|\n|\u2022|•|\s{2,}", body)
        skills = [t.strip(" -•\t") for t in tokens if 1 < len(t.strip()) <= 40]
        # dedupe preserve order
        seen = set()
        ordered = []
        for s in skills:
            k = s.lower()
            if k in seen:
                continue
            seen.add(k)
            ordered.append(s)
        sections["skills"] = ordered[:40]

    return sections


def main():
    pdf_path = Path(PDF_NAME)
    if not pdf_path.exists():
        raise SystemExit(f"PDF introuvable: {pdf_path}")
    if extract_text is None:
        raise SystemExit("pdfminer.six n'est pas installé.")

    text = extract_text(str(pdf_path))
    data = naive_parse(text)

    # Extract images if PyMuPDF available
    assets_dir = Path("assets")
    assets_dir.mkdir(exist_ok=True)
    if fitz is not None:
        try:
            doc = fitz.open(str(pdf_path))
            saved = []
            for page_index in range(len(doc)):
                page = doc[page_index]
                for img_index, img in enumerate(page.get_images(full=True)):
                    xref = img[0]
                    pix = fitz.Pixmap(doc, xref)
                    if pix.n > 4:  # CMYK
                        pix = fitz.Pixmap(fitz.csRGB, pix)
                    ext = "png" if pix.alpha else "jpg"
                    out_path = assets_dir / f"img_{page_index+1}_{img_index+1}.{ext}"
                    pix.save(str(out_path))
                    saved.append(str(out_path).replace('\\', '/'))
            if saved:
                data["images"]["gallery"] = saved
                data["images"]["portrait"] = saved[0]
        except Exception:
            pass

    out = Path("site_content.json")
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Écrit: {out.resolve()}")


if __name__ == "__main__":
    main()


