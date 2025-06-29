from datetime import date

def display_today():
    today = date.today()
    return today.strftime("%Y-%m-%d")

if __name__ == "__main__":
    print(display_today())