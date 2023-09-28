from tenma.tenmaDcLib import findSubclassesRecursively

class Base(object):
    MATCH_STR = ['']
    pass

class Test1(Base):
    MATCH_STR = ['Test 1']

class Test2(Base):
    MATCH_STR = ['Test 2', 'Test 2.5']

class Test3(Test2):
    MATCH_STR = ['Test 3']

def test_findSubclassesRecursively():
    expected_classes = [['Test 1'], ['Test 2', 'Test 2.5'], ['Test 3']]
    actual_classes = []
    for cls in findSubclassesRecursively(Base):
        actual_classes.append(cls.MATCH_STR)
    actual_classes.sort()
    assert actual_classes == expected_classes