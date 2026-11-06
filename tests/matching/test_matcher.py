from shopease.matching import Ambiguous, Customer, Matched, NoMatch, match_name


def test_matches_tamil_name_and_case_suffix():
    result = match_name("ரவிக்கு", (Customer(1, "Ravi Kumar"),))
    assert isinstance(result, Matched)


def test_ambiguous_first_name_is_question():
    result = match_name("Ravi", (Customer(1, "Ravi Kumar"), Customer(2, "Ravi Shankar")))
    assert isinstance(result, Ambiguous)


def test_alias_is_checked_before_phonetic_matching():
    result = match_name("Kutty", (Customer(1, "Karthik"),), {"kutty": 1})
    assert isinstance(result, Matched)


def test_unknown_name_is_not_silently_matched():
    assert isinstance(match_name("Suresh", (Customer(1, "Ravi Kumar"),)), NoMatch)
