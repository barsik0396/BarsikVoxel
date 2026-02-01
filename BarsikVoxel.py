import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.arrays import vbo
import numpy as np
import math

# Константы
WORLD_WIDTH = 64
WORLD_HEIGHT = 16
WORLD_DEPTH = 64

# Типы блоков
AIR = 0
GRASS = 1
DIRT = 2

# Цвета блоков (R, G, B)
BLOCK_COLORS = {
    GRASS: (0.2, 0.8, 0.2),  # Зелёный
    DIRT: (0.6, 0.4, 0.2),    # Коричневый
}

# Вершины куба (относительные координаты)
CUBE_VERTICES = np.array([
    # Каждая грань - 4 вершины (2 треугольника)
    # Front
    [0, 0, 1], [1, 0, 1], [1, 1, 1], [0, 1, 1],
    # Back
    [1, 0, 0], [0, 0, 0], [0, 1, 0], [1, 1, 0],
    # Top
    [0, 1, 1], [1, 1, 1], [1, 1, 0], [0, 1, 0],
    # Bottom
    [0, 0, 0], [1, 0, 0], [1, 0, 1], [0, 0, 1],
    # Left
    [0, 0, 0], [0, 0, 1], [0, 1, 1], [0, 1, 0],
    # Right
    [1, 0, 1], [1, 0, 0], [1, 1, 0], [1, 1, 1],
], dtype=np.float32)

class Camera:
    def __init__(self):
        self.pos = [WORLD_WIDTH // 2, WORLD_HEIGHT + 5, WORLD_DEPTH // 2]
        self.rot = [0, 0]  # [pitch, yaw]
        self.speed = 0.1
        self.sensitivity = 0.2
        
    def update(self, keys, mouse_rel):
        # Обновление вращения камеры
        self.rot[1] -= mouse_rel[0] * self.sensitivity  # Инвертировали yaw
        self.rot[0] -= mouse_rel[1] * self.sensitivity
        
        # Ограничение pitch
        self.rot[0] = max(-89, min(89, self.rot[0]))
        
        # Вычисление направления движения
        yaw_rad = math.radians(self.rot[1])
        
        dx = 0
        dz = 0
        
        if keys[K_w]:
            dx -= math.sin(yaw_rad) * self.speed
            dz -= math.cos(yaw_rad) * self.speed
        if keys[K_s]:
            dx += math.sin(yaw_rad) * self.speed
            dz += math.cos(yaw_rad) * self.speed
        if keys[K_d]:
            dx += math.cos(yaw_rad) * self.speed
            dz -= math.sin(yaw_rad) * self.speed
        if keys[K_a]:
            dx -= math.cos(yaw_rad) * self.speed
            dz += math.sin(yaw_rad) * self.speed
        if keys[K_SPACE]:
            self.pos[1] += self.speed
        if keys[K_LSHIFT]:
            self.pos[1] -= self.speed
            
        self.pos[0] += dx
        self.pos[2] += dz
    
    def apply(self):
        glRotatef(-self.rot[0], 1, 0, 0)
        glRotatef(-self.rot[1], 0, 1, 0)
        glTranslatef(-self.pos[0], -self.pos[1], -self.pos[2])

class World:
    def __init__(self):
        self.blocks = np.zeros((WORLD_WIDTH, WORLD_HEIGHT, WORLD_DEPTH), dtype=np.uint8)
        self.generate()
        self.vbo = None
        self.vertex_count = 0
        self.build_mesh()
    
    def generate(self):
        # Простая генерация: нижние 8 блоков - земля, сверху дёрн
        for x in range(WORLD_WIDTH):
            for z in range(WORLD_DEPTH):
                # Земля
                for y in range(7):
                    self.blocks[x][y][z] = DIRT
                # Дёрн сверху
                self.blocks[x][7][z] = GRASS
    
    def get_block(self, x, y, z):
        if 0 <= x < WORLD_WIDTH and 0 <= y < WORLD_HEIGHT and 0 <= z < WORLD_DEPTH:
            return self.blocks[x][y][z]
        return AIR
    
    def is_face_visible(self, x, y, z, face_index):
        """Проверка видимости грани"""
        # Соседи для каждой грани: front, back, top, bottom, left, right
        neighbors = [
            (x, y, z+1),  # front
            (x, y, z-1),  # back
            (x, y+1, z),  # top
            (x, y-1, z),  # bottom
            (x-1, y, z),  # left
            (x+1, y, z),  # right
        ]
        nx, ny, nz = neighbors[face_index]
        return self.get_block(nx, ny, nz) == AIR
    
    def build_mesh(self):
        """Строим один большой меш для всего мира"""
        vertices = []
        colors = []
        
        for x in range(WORLD_WIDTH):
            for y in range(WORLD_HEIGHT):
                for z in range(WORLD_DEPTH):
                    block_type = self.get_block(x, y, z)
                    if block_type == AIR:
                        continue
                    
                    color = BLOCK_COLORS.get(block_type, (1, 1, 1))
                    
                    # Проверяем каждую грань
                    for face_idx in range(6):
                        if self.is_face_visible(x, y, z, face_idx):
                            # Добавляем 4 вершины грани
                            face_start = face_idx * 4
                            for i in range(4):
                                vertex = CUBE_VERTICES[face_start + i].copy()
                                vertex[0] += x
                                vertex[1] += y
                                vertex[2] += z
                                vertices.append(vertex)
                                colors.append(color)
        
        if len(vertices) == 0:
            return
        
        # Создаём массив вершин с цветами
        vertices = np.array(vertices, dtype=np.float32)
        colors = np.array(colors, dtype=np.float32)
        
        # Интерливим вершины и цвета: [x, y, z, r, g, b, x, y, z, r, g, b, ...]
        vertex_data = np.zeros((len(vertices), 6), dtype=np.float32)
        vertex_data[:, 0:3] = vertices
        vertex_data[:, 3:6] = colors
        vertex_data = vertex_data.flatten()
        
        # Создаём VBO
        self.vbo = vbo.VBO(vertex_data)
        self.vertex_count = len(vertices)
    
    def draw(self):
        """Рисуем весь мир одним вызовом"""
        if self.vbo is None or self.vertex_count == 0:
            return
        
        self.vbo.bind()
        
        glEnableClientState(GL_VERTEX_ARRAY)
        glEnableClientState(GL_COLOR_ARRAY)
        
        # Stride = 6 floats (x, y, z, r, g, b)
        stride = 6 * 4  # 6 floats * 4 bytes
        
        glVertexPointer(3, GL_FLOAT, stride, self.vbo)
        glColorPointer(3, GL_FLOAT, stride, self.vbo + 12)  # Смещение 3 floats = 12 bytes
        
        # Рисуем все квады
        glDrawArrays(GL_QUADS, 0, self.vertex_count)
        
        glDisableClientState(GL_VERTEX_ARRAY)
        glDisableClientState(GL_COLOR_ARRAY)
        
        self.vbo.unbind()

def main():
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    pygame.display.set_caption("BarsikVoxel")
    
    # Захват мыши
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)
    
    # Настройка OpenGL
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_CULL_FACE)  # Отсечение задних граней для оптимизации
    glCullFace(GL_BACK)
    
    # Цвет неба (голубой)
    glClearColor(0.5, 0.7, 1.0, 1.0)
    
    glMatrixMode(GL_PROJECTION)
    gluPerspective(70, (display[0] / display[1]), 0.1, 100.0)
    glMatrixMode(GL_MODELVIEW)
    
    # Создание мира и камеры
    print("Генерация мира...")
    world = World()
    print(f"Мир создан! Вершин для отрисовки: {world.vertex_count}")
    
    camera = Camera()
    
    clock = pygame.time.Clock()
    running = True
    
    print("\nУправление:")
    print("WASD - движение")
    print("Мышь - осмотр")
    print("Пробел - вверх")
    print("Shift - вниз")
    print("ESC - выход")
    
    while running:
        mouse_rel = (0, 0)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
            if event.type == pygame.MOUSEMOTION:
                mouse_rel = event.rel
        
        keys = pygame.key.get_pressed()
        camera.update(keys, mouse_rel)
        
        # Очистка экрана (небо)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # Применение камеры
        camera.apply()
        
        # Рисуем весь мир одним вызовом
        world.draw()
        
        pygame.display.flip()
        fps = clock.tick(60)
        
        # Показываем FPS в заголовке окна
        if pygame.time.get_ticks() % 500 < 20:  # Обновляем каждые ~500ms
            pygame.display.set_caption(f"BarsikVoxel - FPS: {int(clock.get_fps())}")
    
    pygame.quit()

if __name__ == "__main__":
    main()