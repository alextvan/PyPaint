import re

f = open("Pictionary_Words.txt", "r")
reg = re.compile(r"^(\d+)\. ([A-Za-z ]+)$")

def find_word(index):
    f.seek(0)
    for l in f:
        if reg.match(l):
            match = reg.match(l)
            if match.group(1) == str(index):
                return match.group(2)
                
    return "Error"
