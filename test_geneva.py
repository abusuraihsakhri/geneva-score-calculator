import geneva as m
def test_score():
    r=m.calculate_score({'age':68,'sex':'M','cancer':1})
    assert 'score' in r and 'tier' in r
    r2=m.calculate_score({'age':30,'sex':'F'})
    assert r2['score']<=r['score']
