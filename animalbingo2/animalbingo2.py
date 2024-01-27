import tkinter as tk
from PIL import Image, ImageTk

def setup_gui():
    # Create the main window
    root = tk.Tk()
    root.title("Animal Sound Bingo")

    # Set the size of the window
    root.geometry("800x600")

    # Load and set the tabletop background image
    bg_image = Image.open("images/tabletop_background.jpg")  # Replace with your actual image file
    bg_photo = ImageTk.PhotoImage(bg_image)
    bg_label = tk.Label(root, image=bg_photo)
    bg_label.place(x=0, y=0, relwidth=1, relheight=1)

    # Draw Deck Button (Placeholder for now)
    draw_deck_btn = tk.Button(root, text="Draw Deck")
    draw_deck_btn.place(x=50, y=250)

    # Discard Pile Button (Placeholder for now)
    discard_pile_btn = tk.Button(root, text="Discard Pile")
    discard_pile_btn.place(x=700, y=250)

    # Control Buttons
    pause_btn = tk.Button(root, text="Pause")
    pause_btn.place(x=350, y=500)

    replay_btn = tk.Button(root, text="Replay")
    replay_btn.place(x=400, y=500)

    reveal_btn = tk.Button(root, text="Reveal")
    reveal_btn.place(x=450, y=500)

    # Reset Game Button
    reset_btn = tk.Button(root, text="Reset Game")
    reset_btn.place(x=750, y=50)

    root.mainloop()

# Run the setup
setup_gui()
