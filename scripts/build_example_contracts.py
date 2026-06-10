from __future__ import annotations

from pathlib import Path
from textwrap import wrap


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "demo_contracts"

EXAMPLE_CONTRACTS = {
    "employment_offer_demo.pdf": {
        "title": "EMPLOYMENT AGREEMENT",
        "clauses": [
            "All intellectual property created outside work hours belongs to the employer.",
            "The employee agrees to a non-compete for 24 months after employment.",
            "The company may revise or reduce salary with seven days notice.",
            "Either party may terminate this agreement by giving 30 days notice.",
        ],
    },
    "freelancer_sow_demo.pdf": {
        "title": "FREELANCER STATEMENT OF WORK",
        "clauses": [
            "The client may request unlimited revisions until fully satisfied.",
            "Payment is due within 15 days of each approved milestone invoice.",
        ],
    },
    "rent_agreement_demo.pdf": {
        "title": "RESIDENTIAL RENT AGREEMENT",
        "clauses": [
            "This is an 11-month rent agreement for a residential apartment.",
            "The landlord may retain the security deposit at sole discretion for any reason.",
            "Early termination during lock-in requires the tenant to pay remaining rent for the entire term.",
            "The landlord may enter the premises without notice for inspection or repairs.",
        ],
    },
    "nda_demo.pdf": {
        "title": "NON-DISCLOSURE AGREEMENT",
        "clauses": [
            "The recipient shall not use general knowledge, skills, or experience learned during discussions.",
            "Only the recipient has confidentiality obligations to the disclosing party.",
            "Disclosure required by law or court order is permitted after notice.",
        ],
    },
    "loan_agreement_demo.pdf": {
        "title": "PERSONAL LOAN AGREEMENT",
        "clauses": [
            "The borrower shall provide a blank cheque as security.",
            "The lender may increase the interest rate at its sole discretion without consent.",
            "The entire outstanding amount is immediately due on any default without notice.",
            "The EMI schedule is attached and lists monthly instalments of principal and interest.",
        ],
    },
}


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    for filename, contract in EXAMPLE_CONTRACTS.items():
        pdf = build_pdf(contract["title"], contract["clauses"])
        (OUTPUT_DIR / filename).write_bytes(pdf)


def build_pdf(title: str, clauses: list[str]) -> bytes:
    stream = build_text_stream(title, clauses)
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        (
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>"
        ),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"\nendstream",
    ]

    parts = [b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n"]
    offsets = [0]
    for index, body in enumerate(objects, start=1):
        offsets.append(sum(len(part) for part in parts))
        parts.append(f"{index} 0 obj\n".encode("ascii"))
        parts.append(body)
        parts.append(b"\nendobj\n")

    xref_offset = sum(len(part) for part in parts)
    parts.append(b"xref\n")
    parts.append(f"0 {len(objects) + 1}\n".encode("ascii"))
    parts.append(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        parts.append(f"{offset:010d} 00000 n \n".encode("ascii"))
    parts.append(b"trailer\n")
    parts.append(f"<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode("ascii"))
    parts.append(b"startxref\n")
    parts.append(f"{xref_offset}\n".encode("ascii"))
    parts.append(b"%%EOF\n")
    return b"".join(parts)


def build_text_stream(title: str, clauses: list[str]) -> bytes:
    lines = [
        "BT",
        "/F1 18 Tf",
        "50 742 Td",
        f"({escape_pdf_text(title)}) Tj",
        "/F1 10 Tf",
        "0 -30 Td",
        "15 TL",
    ]
    for clause in clauses:
        for line in wrap(clause, width=88, break_long_words=False):
            lines.append(f"({escape_pdf_text(line)}) Tj")
            lines.append("T*")
        lines.append("T*")
    lines.append("ET")
    return "\n".join(lines).encode("ascii")


def escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


if __name__ == "__main__":
    main()
