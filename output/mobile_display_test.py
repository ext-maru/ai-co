def mobile_display_test(text, width=40):
    """Mobile display test function - formats text for mobile screen width"""
    if not text:
        return ""
    
    lines = []
    words = text.split()
    current_line = ""
    
    for word in words:
        if len(current_line + " " + word) <= width:
            current_line += " " + word if current_line else word
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    
    if current_line:
        lines.append(current_line)
    
    return "\n".join(lines)

def test_mobile_display():
    """Test the mobile display function"""
    test_text = "This is a sample text that should be formatted for mobile display with proper line breaks and word wrapping."
    result = mobile_display_test(test_text)
    print("Mobile Display Test:")
    print("-" * 40)
    print(result)
    print("-" * 40)

if __name__ == "__main__":
    test_mobile_display()