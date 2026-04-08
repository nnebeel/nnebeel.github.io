import tkinter as tk
from PIL import Image, ImageTk

def create_rounded_rect(canvas, x1, y1, x2, y2, radius=25, **kwargs):
    points = [x1+radius, y1,
              x1+radius, y1,
              x2-radius, y1,
              x2-radius, y1,
              x2, y1,
              x2, y1+radius,
              x2, y1+radius,
              x2, y2-radius,
              x2, y2-radius,
              x2, y2,
              x2-radius, y2,
              x2-radius, y2,
              x1+radius, y2,
              x1+radius, y2,
              x1, y2,
              x1, y2-radius,
              x1, y2-radius,
              x1, y1+radius,
              x1, y1+radius,
              x1, y1]
    kwargs['smooth'] = True
    return canvas.create_polygon(points, **kwargs)

class AnimalSoundBingoApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Animal Sound Bingo")
        self.geometry("800x600")

        self.card_back_photo_path = "animalbingo2/images/card_back.png"
        self.card_face_photo_path = "animalbingo2/images/card_face.png"

        # Set the tabletop background image
        self.bg_image = Image.open("animalbingo2/images/tabletop_background.jpg")
        self.bg_photo = ImageTk.PhotoImage(self.bg_image)
        self.bg_label = tk.Label(self, image=self.bg_photo)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Create the Canvas widgets for the cards
        self.draw_deck_canvas = tk.Canvas(self)
        self.discard_pile_canvas = tk.Canvas(self)
        self.update_card_sizes()

        # Control Buttons
        self.pause_btn = tk.Button(self, text="Pause")
        self.pause_btn.place(x=350, y=500)

        self.replay_btn = tk.Button(self, text="Replay")
        self.replay_btn.place(x=400, y=500)

        self.reveal_btn = tk.Button(self, text="Reveal")
        self.reveal_btn.place(x=450, y=500)

        # Reset Game Button
        self.reset_btn = tk.Button(self, text="Reset Game")
        self.reset_btn.place(x=750, y=50)
        
        # Bind the resize event
        self.bind('<Configure>', self.on_resize)

        # Wait until the window is fully built before updating the card sizes
        self.after(100, self.update_card_sizes)

    def update_card_sizes(self):
        # Get the updated window size
        window_width = self.winfo_width()
        window_height = self.winfo_height()

        # If window dimensions are too small, don't update
        if window_width < 2 or window_height < 2:
            return

        # Define border and card width as a percentage of window width
        border_percent_width = 0.05  # 5% border width of the window width
        card_percent_width = 0.2  # 20% of the window width for the card width

        # Calculate the border width and card width
        border_width = int(window_width * border_percent_width)
        card_width = int(window_width * card_percent_width)
        
        # Calculate the card height maintaining the 1:1.4 aspect ratio
        card_height = int(card_width * 1.4)

        # Now calculate the y position so the card is vertically centered, accounting for the border
        card_y_pos = (window_height - card_height) // 2

        # Update the draw deck canvas size and position
        self.draw_deck_canvas.place(x=border_width, y=card_y_pos, width=card_width, height=card_height)
        self.create_card(self.draw_deck_canvas, card_width, card_height, self.card_back_photo_path)

        # Update the discard pile canvas size and position
        self.discard_pile_canvas.place(x=window_width - card_width - border_width, y=card_y_pos, width=card_width, height=card_height)
        self.create_card(self.discard_pile_canvas, card_width, card_height, self.card_face_photo_path)

    def create_card(self, canvas, width, height, image_path):
        # Load and resize the image to fit the card size
        image = Image.open(image_path)
        image = image.resize((width, height), Image.Resampling.LANCZOS)
        photo_image = ImageTk.PhotoImage(image)
        canvas.create_image(width // 2, height // 2, image=photo_image)
        canvas.image = photo_image  # Keep a reference to the image
    
    def on_resize(self, event):
        # Update the card sizes and positions
        self.update_card_sizes()

        # Update the background size
        self.bg_image_resized = self.bg_image.resize((event.width, event.height), Image.Resampling.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.bg_image_resized)
        self.bg_label.configure(image=self.bg_photo)
        self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)

        # Update button positions
        button_spacing = 50  # Adjust the spacing to your preference
        self.pause_btn.place(x=event.width / 2 - button_spacing, y=event.height - 100)
        self.replay_btn.place(x=event.width / 2, y=event.height - 100)
        self.reveal_btn.place(x=event.width / 2 + button_spacing, y=event.height - 100)
        self.reset_btn.place(x=event.width - 100, y=20)  # Keep the reset button at the top right

game_app = AnimalSoundBingoApp()
game_app.mainloop()
