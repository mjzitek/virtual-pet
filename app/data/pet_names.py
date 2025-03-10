"""
Pet name lists for the Virtual Pet Application.

This module provides lists of pet names for each pet type.
"""

# Cat names
CAT_NAMES = [
    "Whiskers", "Mittens", "Luna", "Oliver", "Leo", "Bella", "Charlie", "Lucy",
    "Max", "Lily", "Simba", "Cleo", "Felix", "Nala", "Oscar", "Milo", "Sophie",
    "Jack", "Kitty", "Tiger", "Shadow", "Smokey", "Misty", "Oreo", "Pepper",
    "Ginger", "Sasha", "Pumpkin", "Jasper", "Ruby"
]

# Dog names
DOG_NAMES = [
    "Buddy", "Max", "Bailey", "Cooper", "Daisy", "Sadie", "Molly", "Lola",
    "Rocky", "Maggie", "Charlie", "Sophie", "Jack", "Stella", "Toby", "Lucy",
    "Duke", "Zoe", "Teddy", "Lily", "Bentley", "Mia", "Rusty", "Coco",
    "Murphy", "Gracie", "Bear", "Penny", "Tucker", "Rosie"
]

# Rabbit names
RABBIT_NAMES = [
    "Thumper", "Hoppy", "Flopsy", "Mopsy", "Cottontail", "Bun-Bun", "Clover",
    "Daisy", "Oreo", "Cinnamon", "Snowball", "Pepper", "Nibbles", "Toffee",
    "Caramel", "Peanut", "Hazel", "Cocoa", "Marshmallow", "Nutmeg", "Ginger",
    "Honey", "Vanilla", "Mocha", "Licorice", "Butterscotch", "Cookie", "Maple",
    "Pumpkin", "Willow"
]

# Bird names
BIRD_NAMES = [
    "Tweety", "Sunny", "Sky", "Blueberry", "Kiwi", "Mango", "Peaches", "Rio",
    "Skye", "Zephyr", "Feather", "Piper", "Sparky", "Chirpy", "Phoenix", "Polly",
    "Robin", "Finch", "Falcon", "Eagle", "Hawk", "Raven", "Dove", "Sparrow",
    "Jay", "Oriole", "Cardinal", "Hummingbird", "Parrot", "Cockatiel"
]

# Fish names
FISH_NAMES = [
    "Bubbles", "Splash", "Nemo", "Dory", "Finn", "Goldie", "Coral", "Marlin",
    "Flounder", "Ariel", "Guppy", "Flipper", "Ripple", "Wave", "Pearl", "Shimmer",
    "Aqua", "Neptune", "Poseidon", "Marina", "Triton", "Oceana", "Tide", "Sailor",
    "Captain", "Shelly", "Scales", "Gill", "Finley", "Nessie"
]

# Hamster names
HAMSTER_NAMES = [
    "Peanut", "Nibbles", "Squeaky", "Hammy", "Biscuit", "Cookie", "Nugget", "Tiny",
    "Gizmo", "Cinnamon", "Honey", "Oreo", "Marshmallow", "Buttercup", "Snickers",
    "Chewy", "Popcorn", "Pumpkin", "Muffin", "Cupcake", "Waffle", "Pancake",
    "Scooter", "Whiskers", "Fuzzy", "Teddy", "Pepper", "Ginger", "Nutmeg", "Cocoa"
]

# Dictionary mapping pet types to name lists
PET_NAMES = {
    "cat": CAT_NAMES,
    "dog": DOG_NAMES,
    "rabbit": RABBIT_NAMES,
    "bird": BIRD_NAMES,
    "fish": FISH_NAMES,
    "hamster": HAMSTER_NAMES
}

def get_random_name(pet_type: str) -> str:
    """
    Get a random name for the specified pet type.
    
    Args:
        pet_type: The type of pet (e.g., "cat", "dog")
        
    Returns:
        A random name appropriate for the pet type
    """
    import random
    
    # Get the name list for the pet type, or use cat names as default
    name_list = PET_NAMES.get(pet_type.lower(), CAT_NAMES)
    
    # Return a random name from the list
    return random.choice(name_list) 