from datetime import datetime

def display_current_time():
    """Display the current time in a readable format"""
    current_time = datetime.now()
    return current_time.strftime("%Y-%m-%d %H:%M:%S")

if __name__ == "__main__":
    print(f"Current time: {display_current_time()}")