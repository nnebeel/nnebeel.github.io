import tkinter as tk
import random
import pygame
import requests
import io

# Initialize pygame for audio playback
pygame.init()

# Sound sources and animal data
sources = {
    "sb": "http://soundbible.com/grab.php?type=mp3&id=",
    "c": "https://download.ams.birds.cornell.edu/api/v1/asset/",
    "url": ""
}
original_deck = [
    {"name": "Gorilla", "sounds": [["sb", 1149, 0], ["c", 126334, 5]]},
    {"name": "Gorilla", "sounds": [ ["sb", 1149, 0], ["c", 126334, 5]]},
    {"name": "Elephant", "sounds": [ ["sb", 1136, 0], ["sb", 352, 0], ["c", 96337, 4]]},
    {"name": "Owl", "sounds": [ ["sb", 1851, 0], ["sb", 1342, 0], ["sb", 1331, 0], ["c", 138288, 13], ["c", 93570671, 0]]},
    {"name": "Horse", "sounds": [ ["sb", 427, 0], ["sb", 428, 0], ["sb", 429, 0]]},
    {"name": "Cuckoo", "sounds": [ ["c", 167547581, 0]]},
    {"name": "Cricket", "sounds": [ ["sb", 2083, 0], ["sb", 295, 0]]},
    {"name": "Duck", "sounds": [ ["sb", 1859, 0], ["sb", 1378, 0], ["sb", 1197, 0]]},
    {"name": "Cow", "sounds": [ ["sb", 1572, 0], ["sb", 1568, 0]]},
    {"name": "Hyena", "sounds": [ ["sb", 2191, 0]]},
    {"name": "Mouse", "sounds": [ ["url", "https://www.trutechinc.com/wp-content/uploads/2017/10/Mouse-Sound.mp3", 0], ["url", "https://averagehunter.com/mp3/mice-rats/mice%202.mp3", 0]]},
    {"name": "Dog", "sounds": [ ["sb", 2215, 0], ["sb", 2194, 0], ["sb", 2136, 0]]},
    {"name": "Pig", "sounds": [ ["sb", 736, 0]]},
    {"name": "Cat", "sounds": [ ["sb", 1687, 0], ["sb", 1684, 0], ["sb", 979, 0]]},
    {"name": "Pheasant", "sounds": [ ["c", 185044911, 0], ["c", 185770131, 0]]},
    {"name": "Goose", "sounds": [ ["sb", 1202, 0], ["sb", 1175, 0], ["sb", 952, 0]]},
    {"name": "Seagull", "sounds": [ ["sb", 2193, 0], ["sb", 1191, 0], ["sb", 192, 0]]},
    {"name": "Bee", "sounds": [ ["sb", 971, 0]]},
    {"name": "Lion", "sounds": [ ["sb", 1483, 0], ["sb", 156, 0]]},
    {"name": "Dove", "sounds": [ ["sb", 1231, 0], ["c", 104609081, 0], ["c", 166095431, 0]]},
    {"name": "Woodpecker", "sounds": [ ["sb", 20, 0], ["sb", 21, 0], ["c", 55656091, 0]]},
    {"name": "Rooster", "sounds": [ ["sb", 1134, 0], ["sb", 871, 0]]},
    {"name": "Sheep", "sounds": [ ["sb", 1012, 0], ["c", 126289, 5]]},
    {"name": "Seal", "sounds": [ ["sb", 549, 0], ["c", 125018, 4]]},
    {"name": "Frog", "sounds": [ ["sb", 2033, 0], ["sb", 1333, 0], ["sb", 1335, 0]]},
    {"name": "Donkey", "sounds": [ ["c", 201627, 0], ["c", 126394, 5]]},
    {"name": "Monkey", "sounds": [ ["sb", 2145, 0], ["sb", 356, 0]]},
    {"name": "Rattlesnake", "sounds": [ ["sb", 237, 0]]},
    {"name": "Dolphin", "sounds": [ ["sb", 863, 0], ["sb", 395, 0], ["sb", 231, 0]]},
    {"name": "Turkey", "sounds": [ ["sb", 1889, 0], ["sb", 1330, 0], ["sb", 1315, 0]]},
    {"name": "Wolf", "sounds": [ ["sb", 278, 0], ["sb", 2132, 0]]}
]

def play_sound_from_url(url, attempt):
    global current_sound_url
    try:
        response = requests.get(url)
        response.raise_for_status()
        file_like_object = io.BytesIO(response.content)
        pygame.mixer.music.load(file_like_object)
        pygame.mixer.music.play()
        current_sound_url = url
    except requests.exceptions.RequestException as e:
        print(f"Error playing sound: {e}")
        if attempt < len(current_animal["sounds"]) - 1:
            next_sound(attempt + 1)  # Try the next sound for the current animal
        else:
            remove_and_next_animal()  # All sounds failed; remove animal and move to next

def remove_and_next_animal():
    global current_animal, load_sound_retries
    if current_animal and current_animal in current_deck:
        current_deck.remove(current_animal)
    if current_animal and current_animal in original_deck:
        original_deck.remove(current_animal)
    load_sound_retries = 0  # Reset retries
    next_animal()

def next_animal():
    global current_animal, failed_attempts
    failed_attempts = 0
    if current_deck:
        current_animal = random.choice(current_deck)
        current_deck.remove(current_animal)
        next_sound()
    else:
        animal_name_var.set("All animals played. Reset to play again.")

def next_sound(attempt=0):
    if current_animal and current_animal["sounds"]:
        sound_info = current_animal["sounds"][attempt]
        sound_source = sources[sound_info[0]]
        sound_id = sound_info[1]
        sound_url = f"{sound_source}{sound_id}"
        if sound_info[0] == "url":
            sound_url = sound_id
        play_sound_from_url(sound_url, attempt)

def reveal_animal():
    if current_animal is not None:
        animal_name_var.set(current_animal["name"])
    else:
        animal_name_var.set("No animal selected yet")        

def replay_sound():
    if current_sound_url:
        play_sound_from_url(current_sound_url)

def reset_game():
    global current_deck
    current_deck = original_deck.copy()
    animal_name_var.set("")

# Initialization
def reset_game():
    global current_deck, current_animal, current_sound_url
    current_deck = original_deck.copy()
    current_animal = None
    current_sound_url = None
    animal_name_var.set("")

# GUI setup
root = tk.Tk()
root.title("Animal Sounds Game")

animal_name_var = tk.StringVar()
tk.Label(root, textvariable=animal_name_var, font=("Arial", 24)).pack(pady=20)

tk.Button(root, text="Next Animal", command=next_animal).pack(side=tk.LEFT, padx=10, pady=20)
tk.Button(root, text="Replay Sound", command=replay_sound).pack(side=tk.LEFT, padx=10, pady=20)
tk.Button(root, text="Next Sound", command=next_sound).pack(side=tk.LEFT, padx=10, pady=20)
tk.Button(root, text="Reveal", command=reveal_animal).pack(side=tk.LEFT, padx=10, pady=20)
tk.Button(root, text="Reset", command=reset_game).pack(side=tk.RIGHT, padx=10, pady=20)

# Initialize the game state
reset_game()

root.mainloop()
