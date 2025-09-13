def boolean_search(query_tokens, enriched_index, min_match=2):
    """
    Recherche booléenne souple : retourne les documents qui contiennent au moins `min_match` termes de la requête.
    """
    from collections import Counter

    doc_counter = Counter()

    for term in query_tokens:
        if term in enriched_index:
            doc_counter.update(enriched_index[term].keys())

    matching_docs = [doc for doc, count in doc_counter.items() if count >= min_match]
    return sorted(matching_docs)[:5]


def rank_by_tf(query_terms, matching_docs, index):
    scores = []
    for doc in matching_docs:
        score = sum(index[term][doc][0] for term in query_terms if doc in index.get(term, {}))
        scores.append((doc, score))
    return sorted(scores, key=lambda x: x[1], reverse=True)[:5]