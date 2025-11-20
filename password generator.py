import random
import string

def generate_password(min_length, numbers=True, special_chars=True):
    # 1. Initialize character sets (Correctly Indented)
    letters = string.ascii_letters
    digits = string.digits
    specials = string.punctuation
    
    characters = letters
    
    # 2. Build the pool of available characters
    if numbers:
        characters += digits
    if special_chars:
        characters += specials
    
    # 3. Initialize Password and Criteria Flags
    pwd = ""
    has_number = False
    has_special = False
    
    # Loop continues until the password meets both length AND inclusion criteria
    while True:
        # Check if length is met AND if all required character types are present
        meets_criteria = len(pwd) >= min_length
        if numbers:
            meets_criteria = meets_criteria and has_number
        if special_chars:
            meets_criteria = meets_criteria and has_special
            
        # Exit the loop if all criteria are met
        if meets_criteria:
            break
            
        # Add a new random character
        new_char = random.choice(characters)
        pwd += new_char

        # Update criteria flags based on the new character
        if new_char in digits:
            has_number = True
        elif new_char in specials:
            has_special = True

    return pwd

# --- Example Usage (Outside the function) ---
# This code MUST be outside the function definition
password_len_10 = generate_password(10)
print(f"Password (Length 10, all types): {password_len_10}")

password_simple = generate_password(8, numbers=False, special_chars=False)
print(f"Password (Length 8, letters only): {password_simple}")
