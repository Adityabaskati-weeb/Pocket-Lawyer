from __future__ import annotations

from dataclasses import dataclass

from pocket_lawyer.models import RiskLevel


SUPPORTED_CONTRACT_TYPES = {
    "employment": "Employment contract",
    "freelancer": "Freelancer/client contract",
    "rent": "Rent agreement",
    "nda": "NDA",
    "vendor": "Vendor/service agreement",
    "loan": "Loan agreement",
}

CONTRACT_TYPE_ALIASES = {
    "employment_contract": "employment",
    "job_offer": "employment",
    "offer_letter": "employment",
    "freelance": "freelancer",
    "freelancer_contract": "freelancer",
    "client_contract": "freelancer",
    "rent_agreement": "rent",
    "rental": "rent",
    "lease": "rent",
    "lease_agreement": "rent",
    "non_disclosure": "nda",
    "non_disclosure_agreement": "nda",
    "confidentiality_agreement": "nda",
    "service_agreement": "vendor",
    "vendor_agreement": "vendor",
    "msa": "vendor",
    "loan_agreement": "loan",
    "personal_loan": "loan",
}


def normalize_contract_type(value: str) -> str:
    normalized = value.strip().lower().replace("-", "_").replace(" ", "_")
    candidate = CONTRACT_TYPE_ALIASES.get(normalized, normalized)
    if candidate in SUPPORTED_CONTRACT_TYPES:
        return candidate
    return "employment"


@dataclass(frozen=True)
class ClauseRule:
    title: str
    category: str
    risk_level: RiskLevel
    risk_score: int
    patterns: tuple[str, ...]
    plain_language_summary: str
    why_it_matters: str
    suggested_replacement: str
    negotiation_tip: str
    contract_types: tuple[str, ...] = ("employment",)


CLAUSE_RULES: tuple[ClauseRule, ...] = (
    ClauseRule(
        title="Broad IP ownership",
        category="ip_ownership",
        risk_level="red",
        risk_score=88,
        patterns=(
            r"all intellectual property.*(?:outside work hours|personal time|side project)",
            r"(?:side projects?|freelance work).*belongs to (?:the )?(?:company|employer)",
            r"all inventions.*whether or not.*company resources",
        ),
        plain_language_summary=(
            "The employer may be claiming ownership over personal projects or "
            "work created outside the job."
        ),
        why_it_matters=(
            "This can put your apps, freelance work, open-source work, or side "
            "business at risk."
        ),
        suggested_replacement=(
            "IP created within assigned duties or using company confidential "
            "information belongs to the company. Pre-existing work and personal "
            "projects created outside work without company resources remain yours."
        ),
        negotiation_tip=(
            "Ask to limit IP assignment to work created for the company using "
            "company resources or confidential information."
        ),
    ),
    ClauseRule(
        title="Post-employment non-compete",
        category="non_compete",
        risk_level="red",
        risk_score=84,
        patterns=(
            r"non[- ]?compete.*(?:12|18|24|36)\s*months?",
            r"shall not (?:work|engage|be employed).*competitor.*(?:after|post).*employment",
            r"cannot work.*(?:same|similar).*(?:industry|sector).*(?:after|post)",
        ),
        plain_language_summary=(
            "The contract may restrict where you can work after leaving the company."
        ),
        why_it_matters=(
            "A broad non-compete can limit future job options and bargaining power."
        ),
        suggested_replacement=(
            "Replace broad non-compete language with a narrow non-solicitation "
            "clause limited to direct clients or employees for a reasonable period."
        ),
        negotiation_tip=(
            "Ask to remove the non-compete or narrow it to non-solicitation of "
            "specific clients for a limited time."
        ),
    ),
    ClauseRule(
        title="Unilateral salary reduction",
        category="compensation",
        risk_level="red",
        risk_score=82,
        patterns=(
            r"(?:company|employer).*may.*(?:reduce|revise|change).*(?:salary|compensation).*notice",
            r"(?:salary|compensation).*may be.*(?:reduced|changed|revised).*sole discretion",
        ),
        plain_language_summary=(
            "The employer may be able to change your pay without meaningful consent."
        ),
        why_it_matters=(
            "Compensation should not be reduced unilaterally after you accept the role."
        ),
        suggested_replacement=(
            "Any change to compensation must be agreed in writing by both parties "
            "and cannot reduce fixed salary already earned."
        ),
        negotiation_tip=(
            "Ask for salary changes to require your written consent and to apply "
            "only prospectively."
        ),
    ),
    ClauseRule(
        title="Employment bond or training repayment",
        category="bond",
        risk_level="red",
        risk_score=78,
        patterns=(
            r"(?:bond|service agreement).*?(?:lakh|lakhs|rs\.?|inr|rupees)",
            r"(?:training|joining).*?(?:repay|reimburse|liquidated damages)",
            r"employee.*pay.*(?:liquidated damages|penalty).*leav",
        ),
        plain_language_summary=(
            "The contract may require you to pay money if you leave before a fixed period."
        ),
        why_it_matters=(
            "Large bond amounts can trap employees or create disputes when changing jobs."
        ),
        suggested_replacement=(
            "Any repayment should be limited to documented training costs, reduce "
            "monthly over time, and exclude normal onboarding or salary."
        ),
        negotiation_tip=(
            "Ask for the bond amount to be itemized, reduced over time, and limited "
            "to actual documented training costs."
        ),
    ),
    ClauseRule(
        title="Termination without cause",
        category="termination",
        risk_level="yellow",
        risk_score=58,
        patterns=(
            r"(?:company|employer).*terminate.*(?:without cause|without assigning any reason)",
            r"services.*may be terminated.*sole discretion",
        ),
        plain_language_summary=(
            "The employer may be able to end employment without explaining the reason."
        ),
        why_it_matters=(
            "This is common in some contracts, but it should be balanced with notice "
            "or pay in lieu of notice."
        ),
        suggested_replacement=(
            "Termination without cause should require the agreed notice period or "
            "salary in lieu of notice."
        ),
        negotiation_tip=(
            "Ask them to confirm notice pay applies if employment is terminated "
            "without cause."
        ),
    ),
    ClauseRule(
        title="Indefinite confidentiality",
        category="confidentiality",
        risk_level="yellow",
        risk_score=50,
        patterns=(
            r"confidential(?:ity)? obligations?.*(?:forever|perpetual|indefinite)",
            r"confidential information.*survive.*indefinitely",
        ),
        plain_language_summary=(
            "The confidentiality duty may continue forever without limits."
        ),
        why_it_matters=(
            "Some confidentiality survives employment, but the clause should exclude "
            "public knowledge and your general skills."
        ),
        suggested_replacement=(
            "Confidentiality should apply to non-public company information and "
            "exclude public information, independently developed knowledge, and "
            "general skills."
        ),
        negotiation_tip=(
            "Ask to add exclusions for public information, independently developed "
            "knowledge, and general professional skills."
        ),
    ),
    ClauseRule(
        title="One-sided arbitration location",
        category="dispute_resolution",
        risk_level="yellow",
        risk_score=46,
        patterns=(
            r"exclusive jurisdiction.*(?:company|employer).*choice",
            r"arbitration.*(?:sole arbitrator).*appointed by (?:the )?(?:company|employer)",
        ),
        plain_language_summary=(
            "The dispute process may be controlled too heavily by the employer."
        ),
        why_it_matters=(
            "A fair dispute process should not let one side choose the decision-maker alone."
        ),
        suggested_replacement=(
            "Use a mutually appointed arbitrator and a neutral or employment-location venue."
        ),
        negotiation_tip=(
            "Ask for a mutually appointed arbitrator and a reasonable venue."
        ),
    ),
    ClauseRule(
        title="Mutual 30-day notice period",
        category="notice_period",
        risk_level="green",
        risk_score=12,
        patterns=(
            r"(?:both parties|either party).*30 days'? notice",
            r"30 days'? notice.*(?:both parties|either party)",
        ),
        plain_language_summary=(
            "A mutual 30-day notice period is generally standard for many roles."
        ),
        why_it_matters=(
            "Mutual notice gives both sides a predictable exit period."
        ),
        suggested_replacement="No change needed if this matches the offer discussion.",
        negotiation_tip="Confirm that salary is paid during the full notice period.",
    ),
    ClauseRule(
        title="Company property return",
        category="exit_obligations",
        risk_level="green",
        risk_score=8,
        patterns=(
            r"return.*(?:company property|laptop|documents).*termination",
            r"upon termination.*return.*(?:property|equipment|documents)",
        ),
        plain_language_summary=(
            "Returning company property at exit is a standard employment obligation."
        ),
        why_it_matters="This is usually expected and not a major risk by itself.",
        suggested_replacement="No change usually needed.",
        negotiation_tip="Ask for a written handover acknowledgment when returning assets.",
    ),
    ClauseRule(
        title="Client owns work before payment",
        category="ip_payment",
        risk_level="red",
        risk_score=82,
        patterns=(
            r"(?:client|company).*own(?:s|ership)?.*(?:all work|deliverables|intellectual property).*(?:before|regardless of).*payment",
            r"(?:all rights|ip).*transfer.*(?:upon creation|immediately).*(?:payment|paid)",
            r"freelancer.*assigns.*(?:all rights|intellectual property).*before.*payment",
        ),
        plain_language_summary=(
            "The client may get ownership of your work even if they have not paid you."
        ),
        why_it_matters=(
            "For freelancers, ownership should usually transfer only after full payment."
        ),
        suggested_replacement=(
            "Ownership of final deliverables transfers only after full and cleared payment. "
            "Drafts, tools, templates, and pre-existing IP remain with the freelancer."
        ),
        negotiation_tip=(
            "Ask to tie IP transfer to full payment and carve out your reusable templates, "
            "tools, and pre-existing work."
        ),
        contract_types=("freelancer",),
    ),
    ClauseRule(
        title="Unlimited revisions",
        category="scope_creep",
        risk_level="yellow",
        risk_score=55,
        patterns=(
            r"unlimited revisions?",
            r"revise.*until.*(?:client|customer).*satisfied",
            r"changes.*without additional (?:fee|cost|charges)",
        ),
        plain_language_summary=(
            "The client may be able to keep asking for changes without paying more."
        ),
        why_it_matters=(
            "Unlimited revision language can turn a fixed-fee project into open-ended work."
        ),
        suggested_replacement=(
            "Include a fixed number of revision rounds and charge separately for extra scope."
        ),
        negotiation_tip=(
            "Ask to cap revisions and define what counts as a new request or change in scope."
        ),
        contract_types=("freelancer",),
    ),
    ClauseRule(
        title="Payment depends on sole approval",
        category="payment_terms",
        risk_level="red",
        risk_score=76,
        patterns=(
            r"payment.*(?:sole satisfaction|sole discretion|final approval)",
            r"no payment.*until.*(?:client|company).*accepts",
            r"(?:client|customer).*may reject.*without.*payment",
        ),
        plain_language_summary=(
            "The client may delay or deny payment based on vague approval language."
        ),
        why_it_matters=(
            "Payment terms need objective milestones so completed work cannot be withheld unfairly."
        ),
        suggested_replacement=(
            "Payment is due on objective milestone completion, with written feedback required "
            "within a fixed review period."
        ),
        negotiation_tip=(
            "Ask for milestone-based payment and deemed acceptance if feedback is not given on time."
        ),
        contract_types=("freelancer",),
    ),
    ClauseRule(
        title="Milestone payment within 15 days",
        category="payment_terms",
        risk_level="green",
        risk_score=10,
        patterns=(
            r"payment.*(?:within|in)\s*15 days.*(?:invoice|milestone)",
            r"milestone.*payment.*15 days",
        ),
        plain_language_summary=(
            "A clear milestone payment deadline is generally freelancer-friendly."
        ),
        why_it_matters="Clear deadlines reduce payment disputes.",
        suggested_replacement="No change needed if the milestones are also clearly defined.",
        negotiation_tip="Confirm invoice details and late-payment handling in writing.",
        contract_types=("freelancer",),
    ),
    ClauseRule(
        title="Deposit can be forfeited for any reason",
        category="security_deposit",
        risk_level="red",
        risk_score=80,
        patterns=(
            r"(?:security )?deposit.*(?:forfeit|forfeited).*any reason",
            r"landlord.*retain.*deposit.*sole discretion",
            r"deposit.*non[- ]?refundable",
        ),
        plain_language_summary=(
            "The landlord may be able to keep your deposit without proving actual damage or dues."
        ),
        why_it_matters=(
            "Security deposit deductions should be limited to unpaid rent, bills, or documented damage."
        ),
        suggested_replacement=(
            "Deposit deductions must be limited to documented unpaid dues or damage beyond normal wear."
        ),
        negotiation_tip=(
            "Ask for itemized deductions and a fixed refund timeline after move-out."
        ),
        contract_types=("rent",),
    ),
    ClauseRule(
        title="Heavy lock-in penalty",
        category="lock_in",
        risk_level="red",
        risk_score=74,
        patterns=(
            r"lock[- ]?in.*(?:entire|remaining).*rent",
            r"tenant.*pay.*remaining.*(?:lock[- ]?in|term)",
            r"early termination.*(?:six|6|twelve|12).*months.*rent",
        ),
        plain_language_summary=(
            "Leaving early may trigger a very large penalty."
        ),
        why_it_matters=(
            "A lock-in should be proportionate and should not trap the tenant unfairly."
        ),
        suggested_replacement=(
            "Early exit should require reasonable notice and, at most, a limited agreed charge."
        ),
        negotiation_tip=(
            "Ask to cap early-exit charges and allow exit for job transfer, safety, or serious defects."
        ),
        contract_types=("rent",),
    ),
    ClauseRule(
        title="Landlord entry without notice",
        category="privacy",
        risk_level="yellow",
        risk_score=52,
        patterns=(
            r"landlord.*enter.*(?:any time|without notice)",
            r"owner.*access.*premises.*without.*notice",
        ),
        plain_language_summary=(
            "The landlord may be able to enter the home without reasonable notice."
        ),
        why_it_matters=(
            "Tenants should have privacy, except for emergencies or agreed inspections."
        ),
        suggested_replacement=(
            "Landlord entry should require prior notice, except in emergencies."
        ),
        negotiation_tip="Ask for at least 24 hours notice before non-emergency visits.",
        contract_types=("rent",),
    ),
    ClauseRule(
        title="11-month rent term",
        category="term",
        risk_level="green",
        risk_score=8,
        patterns=(
            r"(?:eleven|11)[ -]?month.*(?:rent|lease|tenancy)",
            r"term.*(?:eleven|11)\s*months",
        ),
        plain_language_summary=(
            "An 11-month rent agreement is common in many Indian residential rentals."
        ),
        why_it_matters="The term itself is usually not risky by itself.",
        suggested_replacement="No change needed if renewal and notice terms are clear.",
        negotiation_tip="Confirm renewal, deposit refund, and notice terms separately.",
        contract_types=("rent",),
    ),
    ClauseRule(
        title="Perpetual confidentiality with no exclusions",
        category="confidentiality",
        risk_level="red",
        risk_score=78,
        patterns=(
            r"confidential.*(?:forever|perpetual|indefinite).*no exceptions",
            r"all information.*confidential.*(?:forever|perpetual|indefinite)",
            r"confidentiality.*survive.*forever",
        ),
        plain_language_summary=(
            "The NDA may treat too much information as confidential forever."
        ),
        why_it_matters=(
            "NDAs should exclude public information, prior knowledge, independently developed work, "
            "and legally required disclosures."
        ),
        suggested_replacement=(
            "Confidentiality should be limited to non-public information and include standard exclusions."
        ),
        negotiation_tip=(
            "Ask to add exclusions for public information, prior knowledge, independent development, "
            "and legally compelled disclosure."
        ),
        contract_types=("nda",),
    ),
    ClauseRule(
        title="No residual knowledge carve-out",
        category="career_restriction",
        risk_level="yellow",
        risk_score=54,
        patterns=(
            r"recipient.*shall not use.*(?:skills|experience|general knowledge)",
            r"no use.*(?:memory|residual|general knowledge)",
        ),
        plain_language_summary=(
            "The NDA may restrict your general skills or memory, not just confidential information."
        ),
        why_it_matters=(
            "You should still be able to use your general experience after the NDA."
        ),
        suggested_replacement=(
            "The NDA should not restrict general skills, experience, or unaided memory."
        ),
        negotiation_tip="Ask for a residual knowledge or general skills carve-out.",
        contract_types=("nda",),
    ),
    ClauseRule(
        title="One-way NDA for mutual sharing",
        category="mutuality",
        risk_level="yellow",
        risk_score=44,
        patterns=(
            r"recipient.*obligations.*disclosing party",
            r"one[- ]?way.*nda",
            r"only (?:recipient|you).*confidentiality",
        ),
        plain_language_summary=(
            "Only one side may be protected even if both sides share confidential information."
        ),
        why_it_matters=(
            "If both sides share sensitive information, confidentiality duties should be mutual."
        ),
        suggested_replacement="Use mutual confidentiality obligations where both parties share information.",
        negotiation_tip="Ask to make the NDA mutual if you will share your own confidential information.",
        contract_types=("nda",),
    ),
    ClauseRule(
        title="Standard compelled disclosure carve-out",
        category="disclosure_exception",
        risk_level="green",
        risk_score=8,
        patterns=(
            r"disclosure.*required by law",
            r"court order.*(?:disclose|disclosure)",
            r"government authority.*required.*disclosure",
        ),
        plain_language_summary=(
            "The NDA allows legally required disclosure, which is a normal exception."
        ),
        why_it_matters="This prevents conflict with court orders or legal duties.",
        suggested_replacement="No change needed if notice to the other party is reasonable.",
        negotiation_tip="Confirm notice requirements are practical and lawful.",
        contract_types=("nda",),
    ),
    ClauseRule(
        title="Unlimited vendor liability",
        category="liability",
        risk_level="red",
        risk_score=82,
        patterns=(
            r"(?:vendor|service provider).*unlimited liability",
            r"liability.*uncapped",
            r"liable for.*all losses.*(?:indirect|consequential|special)",
        ),
        plain_language_summary=(
            "The vendor may be exposed to unlimited financial liability."
        ),
        why_it_matters=(
            "Uncapped liability can exceed the contract value and threaten the business."
        ),
        suggested_replacement=(
            "Cap liability to fees paid under the contract, with narrow exceptions for fraud or willful misconduct."
        ),
        negotiation_tip="Ask for a liability cap and exclusion of indirect or consequential losses.",
        contract_types=("vendor",),
    ),
    ClauseRule(
        title="Payment after complete client discretion",
        category="payment_terms",
        risk_level="red",
        risk_score=76,
        patterns=(
            r"payment.*sole discretion.*(?:client|customer)",
            r"(?:client|customer).*withhold.*payment.*any reason",
            r"payment.*only after.*complete satisfaction",
        ),
        plain_language_summary=(
            "The customer may be able to withhold vendor payment for vague reasons."
        ),
        why_it_matters=(
            "Vendor contracts need objective acceptance and payment timelines."
        ),
        suggested_replacement=(
            "Payment should be due after delivery or objective acceptance, with written reasons required for rejection."
        ),
        negotiation_tip="Ask for deemed acceptance and a fixed invoice payment timeline.",
        contract_types=("vendor",),
    ),
    ClauseRule(
        title="Unilateral scope changes",
        category="scope",
        risk_level="yellow",
        risk_score=56,
        patterns=(
            r"(?:client|customer).*may change.*scope.*without.*additional",
            r"services.*modified.*sole discretion",
            r"vendor.*perform.*additional services.*no extra",
        ),
        plain_language_summary=(
            "The customer may be able to add work without extra fees or timeline changes."
        ),
        why_it_matters=(
            "Scope creep hurts margins and delivery quality."
        ),
        suggested_replacement=(
            "Any material scope change should require a written change order covering fees and timeline."
        ),
        negotiation_tip="Ask for a written change-order process.",
        contract_types=("vendor",),
    ),
    ClauseRule(
        title="Net 30 invoice payment",
        category="payment_terms",
        risk_level="green",
        risk_score=10,
        patterns=(
            r"(?:invoice|invoices).*paid.*(?:within|in)\s*30 days",
            r"net\s*30",
        ),
        plain_language_summary=(
            "A 30-day invoice payment cycle is common for vendor contracts."
        ),
        why_it_matters="Clear payment timing reduces collection risk.",
        suggested_replacement="No change needed if taxes, invoice format, and acceptance are clear.",
        negotiation_tip="Confirm late payment interest and dispute process.",
        contract_types=("vendor",),
    ),
    ClauseRule(
        title="Blank cheque or security cheque risk",
        category="security",
        risk_level="red",
        risk_score=84,
        patterns=(
            r"blank cheque",
            r"security cheque.*(?:undated|blank)",
            r"borrower.*issue.*cheque.*without.*amount",
        ),
        plain_language_summary=(
            "The lender may ask for a blank or undated security cheque."
        ),
        why_it_matters=(
            "Blank cheques can be misused and create serious repayment disputes."
        ),
        suggested_replacement=(
            "Avoid blank instruments. Any security cheque should have clear amount, date, purpose, and return conditions."
        ),
        negotiation_tip="Ask to remove blank cheque language or make every instrument fully filled and documented.",
        contract_types=("loan",),
    ),
    ClauseRule(
        title="Unilateral interest rate change",
        category="interest",
        risk_level="red",
        risk_score=78,
        patterns=(
            r"lender.*may.*(?:change|increase|revise).*interest.*sole discretion",
            r"interest rate.*may be.*changed.*without.*consent",
            r"floating.*interest.*sole discretion",
        ),
        plain_language_summary=(
            "The lender may be able to increase interest without clear limits."
        ),
        why_it_matters=(
            "Uncontrolled interest changes can make repayment unaffordable."
        ),
        suggested_replacement=(
            "Interest changes should follow a disclosed benchmark or require written consent."
        ),
        negotiation_tip="Ask for a fixed rate or a transparent benchmark-based floating rate.",
        contract_types=("loan",),
    ),
    ClauseRule(
        title="Immediate default for minor breach",
        category="default",
        risk_level="yellow",
        risk_score=58,
        patterns=(
            r"any breach.*event of default",
            r"default.*immediately.*(?:without notice|no notice)",
            r"entire outstanding.*immediately due.*any default",
        ),
        plain_language_summary=(
            "A small or fixable issue may trigger immediate full repayment."
        ),
        why_it_matters=(
            "Borrowers should usually get notice and time to cure non-payment or paperwork defaults."
        ),
        suggested_replacement=(
            "Default should require written notice and a reasonable cure period, except for serious non-payment or fraud."
        ),
        negotiation_tip="Ask for notice and cure periods before acceleration.",
        contract_types=("loan",),
    ),
    ClauseRule(
        title="Clear EMI schedule",
        category="repayment",
        risk_level="green",
        risk_score=8,
        patterns=(
            r"emi schedule",
            r"repayment schedule.*(?:annexure|attached)",
            r"monthly instalments?.*(?:principal|interest)",
        ),
        plain_language_summary=(
            "A clear repayment schedule is a good sign."
        ),
        why_it_matters="Borrowers need exact due dates and amounts.",
        suggested_replacement="No change needed if prepayment and late fees are also clear.",
        negotiation_tip="Confirm prepayment charges, grace period, and late fee limits.",
        contract_types=("loan",),
    ),
)
