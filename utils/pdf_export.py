"""Minimal text-based PDF export for tailored resumes."""


def _pdf_text(value):
    return str(value or "").replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").encode("latin-1", "replace").decode("latin-1")


def resume_to_pdf(tailored):
    lines = []
    if tailored.get("summary"):
        lines.extend(["SUMMARY", tailored["summary"], ""])
    for heading, key in (("SKILLS", "skills"), ("EXPERIENCE", "experience"), ("PROJECTS", "projects"), ("CERTIFICATIONS", "certifications")):
        values = tailored.get(key, [])
        if not values:
            continue
        lines.extend([heading, ""])
        for value in values:
            if isinstance(value, dict):
                title = value.get("title") or value.get("name") or value.get("company") or ""
                if title:
                    lines.append(title)
                lines.extend(f"- {item}" for item in value.get("bullets", []))
            else:
                lines.append(f"- {value}")
        lines.append("")
    lines = lines or ["TAILORED RESUME"]
    stream_lines = ["BT", "/F1 10 Tf", "50 750 Td"]
    for line in lines[:55]:
        stream_lines.append(f"({_pdf_text(line[:110])}) Tj")
        stream_lines.append("0 -14 Td")
    stream_lines.append("ET")
    stream = "\n".join(stream_lines).encode("latin-1", "replace")
    objects = [b"<< /Type /Catalog /Pages 2 0 R >>", b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>", b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>", b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream", b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for index, obj in enumerate(objects, 1):
        offsets.append(len(output))
        output.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    output.extend(b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:]))
    output.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
    return bytes(output)
