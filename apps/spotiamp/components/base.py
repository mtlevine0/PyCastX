import pygame
from components.text import Text, Marquee
from components.time import Time
from components.visualizer import Visualizer
import math

class Base(pygame.sprite.Sprite):
    skin = "base"
    def __init__(self, display_width, display_height, now_playing_title):
        super().__init__()
        self.display_width = display_width
        self.display_height = display_height
        self.base_surface = pygame.Surface((274, 115))
        
        ## Main
        self.main = self.Main(self.skin)
        self.main.draw(self.base_surface)

        ## Logo
        self.logo = self.Logo(self.skin)
        self.logo.draw(self.base_surface)

        ## Title
        self.title = self.Title(self.skin)
        self.title.draw(self.base_surface)

        ## Cuttle
        self.cuttle = self.Cuttle(self.skin)
        self.cuttle.draw(self.base_surface)

        ## Cbuttons
        self.cbuttons = self.Cbuttons(self.skin)
        self.cbuttons.draw(self.base_surface)

        ## Shufrep
        self.shufrep = self.ShufRep(self.skin)
        self.shufrep.draw(self.base_surface)

        ## Volume
        self.volume = self.Volume(self.skin)
        self.volume.move(0)
        self.volume.draw(self.base_surface)

        ## Balance
        self.balance = self.Balance(self.skin)
        self.balance.draw(self.base_surface)

        ## Monoster
        self.monoster = self.Monoster(self.skin)
        self.monoster.draw(self.base_surface)

        ## PlayerState
        self.playerstate = self.PlayerState(self.skin)
        self.playerstate.draw(self.base_surface)
        self.playerstate.move('stopped')

        ## Posbar
        self.posbar = self.Posbar(self.skin)
        self.posbar.move(0)

        self.posbar.draw(self.base_surface)

        ## BitRate
        self.bitrate = self.BitRate(self.skin)
        self.bitrate.draw(self.base_surface)

        ## SampleRate
        self.samplerate = self.SampleRate(self.skin)
        self.samplerate.draw(self.base_surface)

        ## Text
        self.text = Text(self.skin, 5, 6)
        text_image = self.text.draw(now_playing_title, self.base_surface)

        self.marquee = Marquee(text_image, 0.1, 156, 6)

        ## Time
        self.time = Time(self.skin)
        self.time.draw("00:00", self.base_surface)

        ## Visualizer
        self.visualizer = Visualizer(self.skin, width=76, height=16, num_bands=19)
        self.visualizer.draw(self.base_surface)


    def move(self, position, time, volume, state, spectrum_data=None):
        self.posbar.move(position)
        self.posbar.draw(self.base_surface)
        self.marquee.move()
        self.marquee.draw(self.base_surface)
        self.volume.move(volume)
        self.volume.draw(self.base_surface)
        self.playerstate.move(state)
        self.playerstate.draw(self.base_surface)
        self.time.draw(time, self.base_surface)
        self.visualizer.move(spectrum_data)
        self.visualizer.draw(self.base_surface)

    def draw(self, surface):
        scaled_base_surface = self.base_surface
        scaled_base_surface = pygame.transform.scale(self.base_surface, (self.display_width, self.display_height))
        surface.blit(scaled_base_surface, scaled_base_surface.get_rect())

    class Main(pygame.sprite.Sprite):
        def __init__(self, skin):
            super().__init__()
            # TODO: this needs to be made case insensitive
            # self.image = pygame.image.load("skins/{}/MAIN.BMP".format(skin))
            self.image = pygame.image.load("skins/{}/MAIN_no_logo.png".format(skin))


        def draw(self, surface):
            surface.blit(self.image, self.image.get_rect())

    class Logo(pygame.sprite.Sprite):
        def __init__(self, skin):
            super().__init__()
            self.monoster_surface = pygame.Surface((50, 50))
            self.logo = pygame.image.load("skins/base/tux_logo.png")
            self.logo = pygame.transform.scale(self.logo, (28, 28))

        def draw(self, surface):
            surface.blit(self.logo, (240, 83))

    class Title(pygame.sprite.Sprite):
        def __init__(self, skin):
            super().__init__()
            sprite_sheet = pygame.image.load("skins/{}/TITLEBAR.BMP".format(skin))
            # self.image = sprite_sheet.subsurface(pygame.Rect(27, 0, 275, 14))
            self.image = sprite_sheet.subsurface(pygame.Rect(27, 57, 275, 14))
            self.rect = self.image.get_rect()

        def draw(self, surface):
            surface.blit(self.image, (0, 0))

    class Cuttle(pygame.sprite.Sprite):
        def __init__(self, skin):
            super().__init__()
            sprite_sheet = pygame.image.load("skins/{}/TITLEBAR.BMP".format(skin))
            self.image = sprite_sheet.subsurface(pygame.Rect(304, 1, 8, 42))
            self.rect = self.image.get_rect()

        def draw(self, surface):
            surface.blit(self.image, (12, 23))

    class Cbuttons(pygame.sprite.Sprite):
        def __init__(self, skin):
            super().__init__()
            self.cbuttons_surface = pygame.Surface((145, 16))
            self.cbuttons_surface.set_colorkey((0, 0, 0))
            sprite_sheet = pygame.image.load("skins/{}/CBUTTONS.BMP".format(skin))
            self.play_pause_image = sprite_sheet.subsurface(pygame.Rect(0, 0, 113, 16))
            self.load_image = sprite_sheet.subsurface(pygame.Rect(114, 0, 21, 15))

        def draw(self, surface):
            self.cbuttons_surface.blit(self.play_pause_image, (0, 0))
            self.cbuttons_surface.blit(self.load_image, (120, 1))
            surface.blit(self.cbuttons_surface, (16, 89))

    class ShufRep(pygame.sprite.Sprite):
        def __init__(self, skin):
            super().__init__()
            self.shufrep_surface = pygame.Surface((74, 13))
            self.eqpl_surface = pygame.Surface((67, 13))
            self.eqpl_surface.set_colorkey((0, 0, 0))

            sprite_sheet = pygame.image.load("skins/{}/SHUFREP.BMP".format(skin))
            self.shufrep_image = sprite_sheet.subsurface(pygame.Rect(0, 0, 74, 14))
            self.eq_image = sprite_sheet.subsurface(pygame.Rect(0, 61, 21, 10))
            self.pl_image = sprite_sheet.subsurface(pygame.Rect(23, 61, 21, 10))

        def draw(self, surface):
            self.eqpl_surface.blit(self.eq_image, (0, 0))
            self.eqpl_surface.blit(self.pl_image, (23, 0))
            self.shufrep_surface.blit(self.shufrep_image, (0, 0))
            surface.blit(self.eqpl_surface, (220, 59))
            surface.blit(self.shufrep_surface, (163, 90))

    class Volume(pygame.sprite.Sprite):
        def __init__(self, skin):
            super().__init__()
            self.volume_surface = pygame.Surface((67, 13))
            sprite_sheet = pygame.image.load("skins/{}/VOLUME.BMP".format(skin)) # 28 color options, 14px tall
            self.sprite_sheet = sprite_sheet
            self.volume_image = sprite_sheet.subsurface(pygame.Rect(0, 330, 67, 15))
            self.slider_image = sprite_sheet.subsurface(pygame.Rect(15, 422, 13, 10))
            self.slider_rect = self.slider_image.get_rect()

        def move(self, percentage):
            x_pos = percentage / 100 * (self.volume_surface.get_rect().width - self.slider_rect.width) 
            self.slider_rect.x = x_pos

            # Calculate the colored slider background to use
            sprite_y_pos = self.percentage_to_bin(percentage) * 15
            self.volume_image = self.sprite_sheet.subsurface(pygame.Rect(0, sprite_y_pos, 67, 15)) # left, top, width, height

        def draw(self, surface):
            self.volume_surface.blit(self.volume_image, (0, 0))
            self.volume_surface.blit(self.slider_image, self.slider_rect)
            surface.blit(self.volume_surface, (108, 58))

        def percentage_to_bin(self, percent, num_bins=28):
            """
            Map a percentage (0–100) to one of `num_bins` bins.

            Returns an integer bin index from 0 to num_bins-1.
            """
            # Clamp input to [0, 100]
            percent = max(0.0, min(100.0, percent))

            bin_width = 100.0 / num_bins
            bin_index = int(percent // bin_width)

            # Handle the edge case where percent == 100
            return min(bin_index, num_bins - 1)

    class Balance(pygame.sprite.Sprite):
        def __init__(self, skin):
            super().__init__()
            self.balance_surface = pygame.Surface((37, 13))
            sprite_sheet = pygame.image.load("skins/{}/BALANCE.BMP".format(skin))
            self.balance_image = sprite_sheet.subsurface(pygame.Rect(9, 0, 43, 13))
            self.slider_image = sprite_sheet.subsurface(pygame.Rect(15, 422, 13, 10))

        def draw(self, surface):
            self.balance_surface.blit(self.balance_image, (0, 0))
            self.balance_surface.blit(self.slider_image, (13, 1))
            surface.blit(self.balance_surface, (178, 58))

    class Monoster(pygame.sprite.Sprite):
        def __init__(self, skin):
            super().__init__()
            self.monoster_surface = pygame.Surface((54, 11))
            sprite_sheet = pygame.image.load("skins/{}/MONOSTER.BMP".format(skin))
            self.mono_image = sprite_sheet.subsurface(pygame.Rect(29, 12, 28, 11))
            self.stereo_image = sprite_sheet.subsurface(pygame.Rect(0, 0, 28, 11))

        def draw(self, surface):
            self.monoster_surface.blit(self.mono_image, (0, 0))
            self.monoster_surface.blit(self.stereo_image, (26, 0))
            surface.blit(self.monoster_surface, (213, 41))

    class PlayerState(pygame.sprite.Sprite):
        def __init__(self, skin):
            super().__init__()
            self.playerstate_surface = pygame.Surface((9, 9))
            sprite_sheet = pygame.image.load("skins/{}/PLAYPAUS.BMP".format(skin))
            self.play_image = sprite_sheet.subsurface(pygame.Rect(0, 0, 9, 9)) # left, top, width, height
            self.pause_image = sprite_sheet.subsurface(pygame.Rect(9, 0, 9, 9))
            self.stop_image = sprite_sheet.subsurface(pygame.Rect(20, 0, 9, 9))
            self.state = None

        def draw(self, surface):
            if self.state == "playing":
                self.playerstate_surface.blit(self.play_image, (0, 0))
            elif self.state == "paused":
                self.playerstate_surface.blit(self.pause_image, (0, 0))
            else:
                self.playerstate_surface.blit(self.stop_image, (0, 0))
            surface.blit(self.playerstate_surface, (27, 27))

        def move(self, state):
            self.state = state.lower()

    class BitRate(pygame.sprite.Sprite):
        def __init__(self, skin):
            self.skin = skin
            self.surface = pygame.Surface((12, 10))
            self.bitrate = "192"
            self.text = Text(self.skin, 5, 6)
            self.text_image = self.text.draw(self.bitrate, self.surface)

        def draw(self, surface):
            surface.blit(self.text_image, (110, 43))

    class SampleRate(pygame.sprite.Sprite):
        def __init__(self, skin):
            self.skin = skin
            self.surface = pygame.Surface((12, 10))
            self.sampleRate = "44"
            self.text = Text(self.skin, 5, 6)
            self.text_image = self.text.draw(self.sampleRate, self.surface)

        def draw(self, surface):
            surface.blit(self.text_image, (156, 43))

    class Posbar(pygame.sprite.Sprite):
        def __init__(self, skin):
            super().__init__()
            self.posbar_surface = pygame.Surface((248, 10))
            sprite_sheet = pygame.image.load("skins/{}/POSBAR.BMP".format(skin))
            self.posbar_image = sprite_sheet.subsurface(pygame.Rect(0, 0, 248, 10))
            self.slider_image = sprite_sheet.subsurface(pygame.Rect(249, 0, 27, 10))
            self.slider_rect = self.slider_image.get_rect()
        def move(self, percentage):
            x_pos = percentage / 100 * (self.posbar_surface.get_rect().width - self.slider_rect.width) 
            self.slider_rect.x = x_pos

        def draw(self, surface):
            self.posbar_surface.blit(self.posbar_image, (0, 0))
            self.posbar_surface.blit(self.slider_image, self.slider_rect)
            surface.blit(self.posbar_surface, (16, 72))

