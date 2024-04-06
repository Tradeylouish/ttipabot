import os
from pathlib import Path
import random
import logging

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
import pygame
import pandas

MEDIA_FOLDER = Path.cwd() / "media"
logger = logging.getLogger(__name__)

def choose_line(patentAttorneys: pandas.DataFrame) -> tuple[Path, str]:
    if not patentAttorneys:
        # Select a random quote
        with open(MEDIA_FOLDER / 'quotes.txt', 'r') as file:
            lines = [line.rstrip() for line in file]
            text = [random.choice(lines)]
        sound_file = MEDIA_FOLDER / 'sardaukar-growl.mp3'
        logger.debug(f"No new patent attorneys found, random quote is: \"{text[0]}\"")
    else:
        text = [f"{patentAttorney.Name}." if patentAttorney.Firm == '' else f"{patentAttorney.Name} of {patentAttorney.Firm}." for patentAttorney in patentAttorneys]
        sound_file = MEDIA_FOLDER / 'sardaukar-chant.mp3'
        logger.debug(f"Found {len(text)} new patent attorneys.")
    
    return sound_file, text


def perform_chant(sound_file: str, text: str) -> None:
    """Uses pygame to perform chanting and display text."""
    pygame.init()
    screen = pygame.display.set_mode(flags=pygame.FULLSCREEN)
    pygame.mixer.music.load(sound_file)
    # Hacky way to ensure enough chant loops to cover everyone - based on approx ratio of chant length to number of lines to fade
    playcount = int(len(text) / 8) + 1
    try:
        pygame.mixer.music.play(playcount)
        logger.debug(f"Playing {sound_file} {playcount} time(s).")
    except Exception as ex:
        logger.error(f"Error attempting to play {sound_file}, check filepaths.", exc_info= ex)

    for line in text:
        fade_text(screen, line)
    logger.debug(f"Finished showing all text.")
    
    while pygame.mixer.music.get_busy(): 

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()

        screen.fill(pygame.Color('black'))
        pygame.display.flip()

def fade_text(screen: pygame.Surface, line: str) -> None:
    """Uses pygame to fade a line of text in and back out with a fixed timing."""
    clock = pygame.time.Clock()
    timer = 0
    # Constants for timing adjustment, based on Dune movie intro
    WAIT_TIME = 1500
    FADEOUT_TIME = 6000
    faded_in = False

    font = pygame.font.Font(MEDIA_FOLDER / 'Futura Medium.otf', 50)
    orig_surf = font.render(line, True, pygame.Color('white'))
    orig_surf_rect = orig_surf.get_rect(center = (screen.get_rect().centerx, screen.get_rect().centery * 1.5))
    txt_surf = orig_surf.copy()
    # This surface is used to adjust the alpha of the txt_surf.
    alpha_surf = pygame.Surface(txt_surf.get_size(), pygame.SRCALPHA)
    alpha = 0  # The current alpha value of the surface.

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                exit()

        if alpha < 255 and timer>= WAIT_TIME and not faded_in:
            # Increase alpha each frame, but make sure it doesn't go above 255.
            alpha = min(alpha+10, 255)
            if alpha == 255: faded_in=True 
        elif faded_in and timer>=FADEOUT_TIME and alpha > 0:
            # Decrease alpha each frame, but make sure it doesn't go below 0.
            alpha = max(alpha-10, 0)
            if alpha == 0: return

        txt_surf = orig_surf.copy()  # Don't modify the original text surf.
        # Fill alpha_surf with this color to set its alpha value.
        alpha_surf.fill((255, 255, 255, alpha))
        # To make the text surface transparent, blit the transparent
        # alpha_surf onto it with the BLEND_RGBA_MULT flag.
        txt_surf.blit(alpha_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)

        screen.fill(pygame.Color('black'))
        screen.blit(txt_surf, orig_surf_rect)
        pygame.display.flip()
        timer += clock.tick(24)