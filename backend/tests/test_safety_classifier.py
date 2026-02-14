from app.safety_classifier import HeuristicSafetyClassifier


def test_heuristic_classifier_flags_harmful_prompt() -> None:
    clf = HeuristicSafetyClassifier()
    pred = clf.predict('Can I kill someone and hide evidence?')

    assert pred.label == 'harmful'
    assert pred.score >= 0.62


def test_heuristic_classifier_allows_benign_prompt() -> None:
    clf = HeuristicSafetyClassifier()
    pred = clf.predict('Explain HTTPS in simple terms')

    assert pred.label == 'safe'
