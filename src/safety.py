BLOCKLIST=[
    "how to self-prescribe","overdose","suicide","euthanasia","diagnose me exactly","dose for child without doctor","replace doctor","illegal drug making"
    ]

def is_dangerous(q:str) -> bool:
    ql=q.lower()
    return any(x in ql for x in BLOCKLIST)

def disclaimer():
    return("Not medical advice. For emergencies, call local emergency services."
           "Consult a qualified clinician before acting on this information")
