

def number2text(x):
    if int(x / 1000) > 0:
        return f"{x/1000:.1f} mi"
    else:
        return f"{x}"