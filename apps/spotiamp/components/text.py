import pygame
import math
# char_map = {
#     '"': (130, 0),
#     '@': (136, 0),
#     '_': (55, 6),
#     '=': (59, 6),
#     '(': (65, 6),
#     ')': (70, 6),
#     '-': (75, 6),
#     '\'': (80, 6),
#     '!': (85, 6),
#     ''
# }

char_map = {
    "\"@": (0, 130),
    ".:()-\'!_+\\/[]^&%,=$#": (1, 55),
    "?* ": (2, 15)
}

class Text(pygame.sprite.Sprite):
    def __init__(self, skin, char_width, char_height):
        super().__init__()
        self.sprite_sheet = pygame.image.load("skins/{}/TEXT.BMP".format(skin))
        self.char_width = char_width
        self.char_height = char_height


    # TODO: Consolidate this method
    def draw(self, text, surface):
        surface_width = len(text) * self.char_width
        text_surface = pygame.Surface((surface_width, self.char_height))
        text = text.upper()

        for index, char in enumerate(text):
            if char >= 'A' and char <= 'Z':
                loc = (ord(char) - ord('A')) * self.char_width
                char_image = self.sprite_sheet.subsurface(pygame.Rect(loc, 0, self.char_width, self.char_height))
                text_surface.blit(char_image, (self.char_width * index, 0))
            elif char >= '0' and char <= '9':
                loc = (ord(char) - ord('0')) * self.char_width
                char_image = self.sprite_sheet.subsurface(pygame.Rect(loc, 6, self.char_width, self.char_height))
                text_surface.blit(char_image, (self.char_width * index, 0))
            else:
                char_coords = self.is_char_mapped(char)
                loc_x = (char_coords[0] * self.char_width) + char_coords[1][1][1]
                loc_y = char_coords[1][1][0] * self.char_height
                char_image = self.sprite_sheet.subsurface(pygame.Rect(loc_x, loc_y, self.char_width, self.char_height))
                text_surface.blit(char_image, (self.char_width * index, 0))

        # surface.blit(text_surface, (109, 28))
        return text_surface

    def is_char_mapped(self, char):
        for char_row in char_map.items():
            if char in char_row[0]:
                return (char_row[0].find(char), char_row)
            
class Marquee:
    def __init__(self, text_surface, marquee_speed, marquee_width, marquee_height):
        self.marquee_position = 0
        self.marquee_speed = marquee_speed
        self.marquee_width = marquee_width
        self.marquee_height = marquee_height
        self.text_surface = text_surface
        self.text_rect = self.text_surface.get_rect()
        self.marquee_surface = pygame.Surface((self.marquee_width, self.marquee_height))
        self.i = 0
        self.tiles = math.ceil(self.marquee_width / self.text_rect.width) + 1
        print(self.tiles)
        self.frame = 0

    def move(self):

        if self.frame > 15:
            self.i = 0

            while (self.i < self.tiles):
                self.marquee_surface.blit(self.text_surface, (self.text_rect.width * self.i + self.marquee_position, 0))
                self.i += 1

            self.marquee_position -= 5

            if abs(self.marquee_position) > self.text_rect.width:
                self.marquee_position = 0
            self.frame = 0

        self.frame += 1

    def draw(self, surface):
        surface.blit(self.marquee_surface, (109, 27))

