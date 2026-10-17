import pygame

class Dropdown:
    WIDTH = 110
    ROW_HEIGHT = 26
    TEXT_PADDING = 8

    BACKGROUND = (30, 33, 40)
    HIGHLIGHT = (60, 66, 80)
    BORDER = (95, 102, 118)
    TEXT_COLOUR = (220, 220, 225)

    def __init__(self, x, y, options, selected=0):
        self.options = options
        self.selected = selected
        self.is_open = False
        self.header_rect = pygame.Rect(x, y, self.WIDTH, self.ROW_HEIGHT)
        self.font = pygame.font.SysFont("consolas", 16)

    @property
    def value(self):
        return self.options[self.selected]

    def option_rect(self, i):
        return pygame.Rect(
            self.header_rect.x,
            self.header_rect.bottom + i * self.ROW_HEIGHT,
            self.WIDTH,
            self.ROW_HEIGHT,
        )

    def handle_click(self, pos):
        """Returns (consumed, changed): whether the click was used, and whether the choice changed."""
        if self.header_rect.collidepoint(pos):
            self.is_open = not self.is_open
            return True, False

        if self.is_open:
            self.is_open = False
            for i in range(len(self.options)):
                if self.option_rect(i).collidepoint(pos):
                    changed = i != self.selected
                    self.selected = i
                    return True, changed
            return True, False
        
        return False, False

    def _draw_row(self, canvas, rect, text, background):
        pygame.draw.rect(canvas, background, rect)
        pygame.draw.rect(canvas, self.BORDER, rect, width=1)
        label = self.font.render(text, True, self.TEXT_COLOUR)
        canvas.blit(label, (rect.x + self.TEXT_PADDING,
                            rect.y + (rect.height - label.get_height()) // 2))

    def draw(self, canvas):
        arrow = "^" if self.is_open else "v"
        self._draw_row(canvas, self.header_rect, f"{self.value}  {arrow}", self.BACKGROUND)
        if self.is_open:
            for i, option in enumerate(self.options):
                background = self.HIGHLIGHT if i == self.selected else self.BACKGROUND
                self._draw_row(canvas, self.option_rect(i), option, background)