#-------------------------------------------------------------------------------
# Name:        LavalampParticles.py
# Purpose: pretty visualizer
#
# Author:      The Schim
#
# Created:     16/03/2023
# Copyright:   (c) The Schim 2023
# Licence:     CC0
#-------------------------------------------------------------------------------
import pygame
import random
import math
from colorsys import hsv_to_rgb, rgb_to_hsv
import uuid

# Constants
WIDTH, HEIGHT = 800, 600
BG_COLOR = (0, 0, 0)
FPS = 60
MIN_RADIUS = 33.3
MAX_RADIUS = 99.9
SPLIT_PROB = 0.29
DEPTH = 700
cooldown = random.randint(314, 6400)
INITIAL_GLOBS = 50
MAX_NUMBER_GLOBS = 230
SPEED_DIVISOR = 2.0+(1/math.pi)
AGE_FACTOR = 0.1
TRANSFER = 0.00075

def random_point_on_ellipsoid(a, b, c):
    while True:
        u = random.uniform(-1, 1)
        v = random.uniform(-1, 1)
        w = random.uniform(-1, 1)
        d = u**2/a**2 + v**2/b**2 + w**2/c**2

        if d <= 1:
            break

    x = (WIDTH / 2) + a * u
    y = (HEIGHT / 2) + b * v
    z = (DEPTH / 2) + c * w

    x = max(MIN_RADIUS, min(WIDTH - MIN_RADIUS, x))
    y = max(MIN_RADIUS, min(HEIGHT - MIN_RADIUS, y))
    z = max(MIN_RADIUS, min(DEPTH - MIN_RADIUS, z))

    return x, y, z

def wild_color_mutation(parent_color):
    mutation_range = 128  # Adjust this value to control the mutation range
    mutated_color = tuple(
        max(64, min(255, parent_color[i] + random.randint(-mutation_range, mutation_range)))
        for i in range(3)
    )
    return mutated_color



class Glob:
    def __init__(self, x, y, z, radius, color, set_id=None, glob_sets=None):
        self.x = x
        self.y = y
        self.z = z
        self.radius = radius
        self.color = color
        self.glob_sets = glob_sets if glob_sets is not None else {}  # set default value
        self.creation_time = pygame.time.get_ticks()

        if set_id is None:
            set_id = str(uuid.uuid4())

        self.set_id = set_id

        if self.set_id not in self.glob_sets:
            self.glob_sets[self.set_id] = set()
        self.glob_sets[self.set_id].add(self)

        speed_multiplier = 28.88 / self.radius
        self.vx = (random.uniform(-1, 1) / speed_multiplier) / SPEED_DIVISOR
        self.vy = (random.uniform(-1, 1) / speed_multiplier) / SPEED_DIVISOR
        self.vz = (random.uniform(-1, 1) / speed_multiplier) / SPEED_DIVISOR

        if self.radius == MAX_RADIUS:
            self.num_globs = len(INITIAL_GLOBS)
        else:
            self.num_globs = round(self.radius / (MAX_RADIUS / INITIAL_GLOBS))

        self.split_prob = SPLIT_PROB

    def split(self, globs):
        if len(globs) < MAX_NUMBER_GLOBS and random.random() < self.split_prob:
            new_globs = []
            num_new_globs = random.randint(round(2*((self.radius/MAX_RADIUS*0.5)+1)), round(5*((self.radius/MAX_RADIUS*0.5)+1)))
            for _ in range(num_new_globs):
                new_x = self.x + random.uniform(-self.radius, self.radius)
                new_y = self.y + random.uniform(-self.radius, self.radius)
                new_z = self.z + random.uniform(-self.radius, self.radius)
                new_radius = self.radius / num_new_globs

                # Use wild color mutation for offspring
                new_color = wild_color_mutation(self.color)

                new_glob = Glob(new_x, new_y, new_z, new_radius, new_color, self.set_id, self.glob_sets)
                new_glob.split_prob = self.split_prob
                new_globs.append(new_glob)
            return new_globs
        else:

            return None

    def draw(self, screen, bg_color):
        # Calculate the coordinate ratios of the glob's position relative to the room's center
        x_ratio = (self.x - WIDTH / 2) / (WIDTH / 2)
        y_ratio = (self.y - HEIGHT / 2) / (HEIGHT / 2)
        z_ratio = (self.z - DEPTH / 2) / (DEPTH / 2)

        # Calculate the amount by which to push in the glob's coordinate
        distance_from_center = math.sqrt(x_ratio ** 2 + y_ratio ** 2 + z_ratio ** 2)
        if distance_from_center == 0:
            push_in = 0
        else:
            a = 1.5  # Semi-major axis
            b = a / 2  # Semi-minor axis
            c = math.sqrt(a ** 2 - b ** 2)  # Distance from center to foci
            distance_from_focus = math.sqrt((x_ratio * a) ** 2 + (y_ratio * a) ** 2 + (z_ratio * b) ** 2)
            push_in = (distance_from_focus - c) / distance_from_center

        # Transform the glob's position based on the push-in value
        x_transformed = self.x + (WIDTH / 2 - self.x) * push_in
        y_transformed = self.y + (HEIGHT / 2 - self.y) * push_in
        z_transformed = self.z + (DEPTH / 2 - self.z) * push_in

        # Scale the transformed position based on the z-coordinate
        scale_factor = get_scale_factor(z_transformed, DEPTH)
        x_scaled = x_transformed * scale_factor + (1 - scale_factor) * (WIDTH / 2)
        y_scaled = y_transformed * scale_factor + (1 - scale_factor) * (HEIGHT / 2)

        # Calculate the scaled radius and fade color
        scaled_radius = int(self.radius * scale_factor)
        r = int(self.color[0] * scale_factor + bg_color[0] * (1 - scale_factor))
        g = int(self.color[1] * scale_factor + bg_color[1] * (1 - scale_factor))
        b = int(self.color[2] * scale_factor + bg_color[2] * (1 - scale_factor))
        fade_color = (r, g, b)

        # Ensure fade_color is a valid RGB tuple
        fade_color = tuple(max(0, min(c, 255)) for c in fade_color)

        # Draw the glob on the screen
        pygame.draw.circle(screen, fade_color, (int(x_scaled), int(y_scaled)), scaled_radius)



    def update(self, globs, glob_sets):
        global TRANSFER
        removed = False
        # Move glob according to its speed
        self.x += self.vx
        self.y += self.vy
        self.z += self.vz

        # Apply boundary conditions
        self.x %= WIDTH
        self.y %= HEIGHT
        self.z %= DEPTH

        # Move globs out of sibling set if they are far enough apart
        siblings = [g for g in self.glob_sets[self.set_id] if g != self]
        for sibling in siblings:
            distance = math.sqrt((self.x - sibling.x)**2 + (self.y - sibling.y)**2 + (self.z - sibling.z)**2)
            if distance > 2 * self.radius:
                self.glob_sets[self.set_id].remove(self)
                new_set_id = str(uuid.uuid4())
                self.set_id = new_set_id
                self.glob_sets[new_set_id] = {self}
                break

        # Handle glob collision and color blending
        for other in globs:
            if other != self:
                distance = math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2 + (self.z - other.z)**2)
                if distance <= self.radius + other.radius:
                    if self.radius > other.radius:
                        larger, smaller = self, other
                    else:
                        larger, smaller = other, self

                    transfer_rate = TRANSFER  # Adjust this value to control the transfer rate
                    transferred_radius = smaller.radius * transfer_rate
                    larger.radius += transferred_radius
                    smaller.radius -= transferred_radius

                    # Color blending
                    larger_area = math.pi * larger.radius**2
                    smaller_area = math.pi * smaller.radius**2
                    total_area = larger_area + smaller_area
                    new_color = tuple(int((larger_area * larger.color[i] + smaller_area * smaller.color[i]) / total_area) for i in range(3))
                    larger.color = new_color

                    # Remove smaller glob if its radius becomes zero
                    if smaller.radius <= 0:
                        globs.remove(smaller)
                        if smaller.set_id in glob_sets and smaller in glob_sets[smaller.set_id]:
                            glob_sets[smaller.set_id].remove(smaller)
                            self.num_globs -= 1 # decrement the num_globs of the parent glob
                        removed = True
                        break

        # Check if the glob should split, outside the loop
        if self.radius > MAX_RADIUS:
            new_globs = self.split(globs)
            if new_globs:
                globs.extend(new_globs)
                if not removed and self in globs:
                    globs.remove(self)
                    self.num_globs -= 1 # decrement the num_globs of the parent glob

def attract_smaller_globs(globs, min_radius):
    force = 0.3/4.6
    for glob1 in globs:
        if glob1.radius < min_radius:
            nearest_larger_glob = None
            nearest_distance = float('inf')
            for glob2 in globs:
                if glob2.radius >= min_radius and glob2 != glob1:
                    distance = math.sqrt((glob1.x - glob2.x) ** 2 + (glob1.y - glob2.y) ** 2 + (glob1.z - glob2.z) ** 2)
                    if distance < nearest_distance:
                        nearest_larger_glob = glob2
                        nearest_distance = distance
            if nearest_larger_glob is not None:
                attraction_force = force * (min_radius / nearest_distance)
                dx = nearest_larger_glob.x - glob1.x
                dy = nearest_larger_glob.y - glob1.y
                dz = nearest_larger_glob.z - glob1.z
                norm = math.sqrt(dx**2 + dy**2 + dz**2)
                glob1.vx += dx / norm * attraction_force
                glob1.vy += dy / norm * attraction_force
                glob1.vz += dz / norm * attraction_force

def get_attraction_force(color1, color2):
    h1, s1, v1 = rgb_to_hsv(*(c / 255 for c in color1))
    h2, s2, v2 = rgb_to_hsv(*(c / 255 for c in color2))

    hue_diff = abs(h1 - h2)
    saturation_diff = abs(s1 - s2)

    attraction_strength = (1 - hue_diff) * (1 - saturation_diff)
    attraction_force = 0.0002 * attraction_strength

    return attraction_force

def get_scale_factor(z, depth):
    return 1 - (z / depth)

def average_glob_hsv(globs):
    if len(globs) == 0:
        return (0, 0, 0)  # default background color if there are no globs

    num_globs = len(globs)
    total_h, total_s, total_v = 0, 0, 0
    for glob in globs:
        h, s, v = rgb_to_hsv(*(c / 255 for c in glob.color))
        total_h += h
        total_s += s
        total_v += v

    avg_h = total_h / num_globs
    avg_s = total_s / num_globs
    avg_v = total_v / num_globs

    return avg_h, avg_s, avg_v

def get_random_color():
    r = random.randint(100, 255)
    g = random.randint(100, 255)
    b = random.randint(100, 255)
    return (r, g, b)

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Nia.S & ChatGPT's Lavalamp")
    clock = pygame.time.Clock()

    a, b, c = WIDTH / 2, HEIGHT / 2, DEPTH / 2

    globs = [Glob(*random_point_on_ellipsoid(a, b, c),
                  random.uniform(MIN_RADIUS, MAX_RADIUS),
                  get_random_color(),
                  str(uuid.uuid4())) for _ in range(INITIAL_GLOBS)]

    # Initialize the glob sets with the initial globs
    glob_sets = {i: {glob} for i, glob in enumerate(globs)}

    running = True
    while running:

        # Calculate the background color
        avg_h, avg_s, avg_v = average_glob_hsv(globs)
        bg_color = tuple(int(c * 255) for c in hsv_to_rgb(1 - avg_h, 1 - avg_s, 1 - avg_v))
        screen.fill(bg_color)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_f:
                    if screen.get_flags() & pygame.FULLSCREEN:
                        pygame.display.set_mode((WIDTH, HEIGHT))
                    else:
                        pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)


        new_globs = []

        # Sort globs based on z-axis
        sorted_globs = sorted(globs, key=lambda g: g.z, reverse=True)

        # Attract smaller globs to the nearest larger glob
        attract_smaller_globs(globs, MIN_RADIUS)

        # Draw globs in order of z-axis
        for glob in sorted_globs:
            result = glob.update(globs, glob_sets)  # Call update method with 2 arguments instead of 3
            if result:
                new_globs.extend(result)

            glob.draw(screen, bg_color)

        # Update the display and tick the clock
        pygame.display.flip()
        clock.tick(FPS)

        # Add new globs to the list
        globs.extend(new_globs)

        # Remove globs that have radius less than 1
        globs = [glob for glob in globs if glob.radius >= 1]

        # Update the num_globs attribute of all globs
        num_globs = len(globs)
        for glob in globs:
            glob.num_globs = num_globs

    pygame.quit()
if __name__ == "__main__":
    main()