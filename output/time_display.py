from datetime import datetime

class TimeDisplay:
    def __init__(self):
        pass
    
    def current_time(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    def display_time(self):
        print(f"現在の時刻: {self.current_time()}")

if __name__ == "__main__":
    time_display = TimeDisplay()
    time_display.display_time()