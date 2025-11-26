memory = {}

def set_name(name):
    #print(f"Set name function here, and I am saving : {name}")
    memory["user_name"] = name.title()
    return f"Got it, I'll remember your name is {name.title()}."

def get_name():
    #print(f"Get name function here, and I am returning : {memory}")
    name = memory.get("user_name")
    return name
