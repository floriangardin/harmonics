

from harmonics.parser import HarmonicsParser
test_file_with_errors = """
Time Sginature: 3/4
m1 T1.v1 b1 C5
m2 T1.a1 b1 D5{~}
"""

parser = HarmonicsParser()
errors = parser.syntax_error_report(test_file_with_errors)
print(errors)


test_file_without_errors = """
Time Signature: 3/4
m1 T1.v1 b1 C5
m2 T1.v1 b1 D5[~]
"""

errors = parser.syntax_error_report(test_file_without_errors)
print(errors)