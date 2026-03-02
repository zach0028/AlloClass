from pydantic import BaseModel


class AlternativeClassification(BaseModel):
    category: str
    confidence: float


class AxisClassification(BaseModel):
    axis_name: str
    category: str
    confidence: float
    reasoning: str
    alternative: AlternativeClassification | None = None


class ClassifierOutput(BaseModel):
    results: list[AxisClassification]


class ChallengerChallenge(BaseModel):
    axis_name: str
    alternative_category: str
    argument: str
    agrees_with_original: bool


class ChallengerOutput(BaseModel):
    challenges: list[ChallengerChallenge]


class FeedbackParserOutput(BaseModel):
    axis_name: str
    corrected_category: str
    reasoning: str


class AxisFilter(BaseModel):
    axis_name: str
    categories: list[str]


class TicketQueryFilters(BaseModel):
    axes: list[AxisFilter] = []
    date_range: str | None = None
    confidence_min: float | None = None
    confidence_max: float | None = None
    was_challenged: bool | None = None
    has_feedback: bool | None = None
    text_search: str | None = None


class TicketQueryOutput(BaseModel):
    filters: TicketQueryFilters
    sort: str = "created_at_desc"
    limit: int = 20
    aggregation: str | None = None


class SemanticQueryOutput(BaseModel):
    search_text: str
    limit: int = 20


class TicketEvaluation(BaseModel):
    classification_id: str
    meaning_preserved: bool
    confidence_analysis: str


class RuleModification(BaseModel):
    index: int
    new_rule: str


class JudgeOutput(BaseModel):
    ticket_evaluations: list[TicketEvaluation]
    rules_to_add: list[str]
    rules_to_remove: list[int]
    rules_to_modify: list[RuleModification]
    global_diagnosis: str


class Reformulation(BaseModel):
    id: str
    reformulated_text: str


class ReformulationsOutput(BaseModel):
    reformulations: list[Reformulation]


class ErrorPattern(BaseModel):
    pattern_type: str
    from_category: str
    to_category: str
    axis_name: str
    trigger_description: str
    occurrence_count: int
    proposed_rule: str


class ErrorPatternsOutput(BaseModel):
    patterns: list[ErrorPattern]


class ExpectedResult(BaseModel):
    axis_name: str
    expected_category: str


class AdversarialCase(BaseModel):
    text: str
    expected_results: list[ExpectedResult]
    difficulty: str


class AdversarialCasesOutput(BaseModel):
    cases: list[AdversarialCase]
