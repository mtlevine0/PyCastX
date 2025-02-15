import pygame

class Time(pygame.sprite.Sprite):
    def __init__(self, skin):
        super().__init__()
        self.sprite_sheet = pygame.image.load("skins/{}/NUMBERS.BMP".format(skin))
        self.char_width = 9
        self.char_height = 13

    def draw(self, time_string, surface):
        m = int(time_string[0])
        mm = int(time_string[1])
        s = int(time_string[3])
        ss = int(time_string[4])
        time_surface = pygame.Surface((47, 14), pygame.SRCALPHA, 32)
        time_surface = time_surface.convert_alpha()
        m_image = self.sprite_sheet.subsurface(pygame.Rect(9 * m, 0, self.char_width, self.char_height))
        mm_image = self.sprite_sheet.subsurface(pygame.Rect(9 * mm, 0, self.char_width, self.char_height))
        s_image = self.sprite_sheet.subsurface(pygame.Rect(9 * s, 0, self.char_width, self.char_height))
        ss_image = self.sprite_sheet.subsurface(pygame.Rect(9 * ss, 0, self.char_width, self.char_height))

        time_surface.blit(m_image, (0, 0))
        time_surface.blit(mm_image, (11, 0))
        time_surface.blit(s_image, (27, 0))
        time_surface.blit(ss_image, (37, 0))

        surface.blit(time_surface, (50, 26))
