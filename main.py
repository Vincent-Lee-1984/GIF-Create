import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.patheffects as path_effects
from matplotlib.patches import Circle
import mpl_toolkits.mplot3d.art3d as art3d
import imageio.v2 as imageio
import io
import platform

# --- 0. 字体配置 ---
def configure_font():
    sys = platform.system()
    if sys == 'Windows':
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'sans-serif']
    elif sys == 'Darwin': 
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti TC', 'sans-serif']
    else:
        plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False
configure_font()

# --- 1. 几何体数据 ---
def get_cube(center=(0,0,0), size=0.5):
    cx, cy, cz = center; r = size
    v = np.array([
        [cx-r, cy-r, cz-r], [cx+r, cy-r, cz-r], [cx+r, cy+r, cz-r], [cx-r, cy+r, cz-r],
        [cx-r, cy-r, cz+r], [cx+r, cy-r, cz+r], [cx+r, cy+r, cz+r], [cx-r, cy+r, cz+r]
    ])
    faces = [[v[0], v[1], v[5], v[4]], [v[1], v[2], v[6], v[5]], [v[2], v[3], v[7], v[6]], 
             [v[3], v[0], v[4], v[7]], [v[4], v[5], v[6], v[7]], [v[0], v[3], v[2], v[1]]]
    return faces

def get_pyramid(center=(1.2, 0, -0.2), size=0.5):
    cx, cy, cz = center; r = size
    v = np.array([[cx-r, cy-r, cz], [cx+r, cy-r, cz], [cx+r, cy+r, cz], [cx-r, cy+r, cz], [cx, cy, cz+r*1.5]])
    faces = [[v[0], v[1], v[2], v[3]], [v[0], v[1], v[4]], [v[1], v[2], v[4]], [v[2], v[3], v[4]], [v[3], v[0], v[4]]]
    return faces

def get_prism(center=(-1.2, 0, 0), size=0.4, height=0.8):
    cx, cy, cz = center; r = size; h = height / 2
    angles = np.linspace(0, 2*np.pi, 7)[:-1]
    bottom = [[cx + r*np.cos(a), cy + r*np.sin(a), cz-h] for a in angles]
    top = [[cx + r*np.cos(a), cy + r*np.sin(a), cz+h] for a in angles]
    faces = [bottom, top]
    for i in range(6): faces.append([bottom[i], bottom[(i+1)%6], top[(i+1)%6], top[i]])
    return faces

# --- 2. 绘图函数 ---
def draw_scene(fig, ax, t, frame_idx):
    # 彻底清理
    ax.clear()
    fig.texts.clear()
    fig.lines.clear()
    fig.patches.clear()
    
    # 设置 3D 环境
    ax.set_axis_off()
    ax.grid(False)
    ax.set_box_aspect((1, 1, 1))
    ax.set_xlim(-1.5, 1.5); ax.set_ylim(-1.5, 1.5); ax.set_zlim(-1, 1)
    
    # 颜色
    INIT_COLOR, INIT_EDGE = '#CFD8DC', '#78909C'
    ACTIVE_COLOR, ACTIVE_EDGE = '#2979FF', '#FFFFFF'
    TARGET_STR = "立方体"
    
    # 阴影
    shadow = Circle((0, 0), 0.8, facecolor='black', alpha=0.15, edgecolor='none')
    ax.add_patch(shadow)
    art3d.pathpatch_2d_to_3d(shadow, z=-0.6, zdir="z")
    
    cube_d = get_cube(); pyr_d = get_pyramid(); prism_d = get_prism()
    base_azim = -60
    
    # === 阶段控制 (使用修正后的正确数学逻辑) ===
    # Phase 1: 0 - 0.35
    # Phase 2: 0.35 - 0.55
    # Phase 3: 0.55 - 1.0
    
    if t < 0.35: # Phase 1
        local_t = t / 0.35
        
        phase_txt = "1. 上传图片、给定目标"
        prompt_txt = TARGET_STR[:int(local_t * (len(TARGET_STR) + 1))]
        cursor = "|" if (frame_idx % 6 < 3) else "" # 调整闪烁频率适应低帧率
        
        for d in [cube_d, pyr_d, prism_d]:
            poly = Poly3DCollection(d, linewidths=0.8) # 线条变细适应小图
            poly.set_facecolor(INIT_COLOR); poly.set_edgecolor(INIT_EDGE); poly.set_alpha(1.0)
            ax.add_collection3d(poly)
        ax.view_init(elev=25, azim=base_azim)
        
    elif t < 0.55: # Phase 2
        local_t = (t - 0.35) / 0.2
        
        phase_txt = "2. 识别目标与分割..."
        prompt_txt = TARGET_STR; cursor = ""
        
        cube_p = Poly3DCollection(cube_d, linewidths=0.8)
        cube_p.set_facecolor(ACTIVE_COLOR); cube_p.set_edgecolor(ACTIVE_EDGE); cube_p.set_alpha(1.0)
        ax.add_collection3d(cube_p)
        
        alpha = max(0, 1.0 - local_t)
        if alpha > 0.05:
            for d in [pyr_d, prism_d]:
                p = Poly3DCollection(d, linewidths=0.8)
                p.set_facecolor(INIT_COLOR); p.set_edgecolor((0.5, 0.6, 0.6, alpha)); p.set_alpha(alpha)
                ax.add_collection3d(p)
        ax.view_init(elev=25, azim=base_azim)
        
    else: # Phase 3
        local_t = (t - 0.55) / 0.45
        
        phase_txt = "3. 生成 3D 模型"
        prompt_txt = TARGET_STR; cursor = ""
        
        cube_p = Poly3DCollection(cube_d, linewidths=0.8)
        cube_p.set_facecolor(ACTIVE_COLOR); cube_p.set_edgecolor(ACTIVE_EDGE); cube_p.set_alpha(1.0)
        ax.add_collection3d(cube_p)
        
        curr_azim = base_azim + (local_t * 360)
        ax.view_init(elev=25, azim=curr_azim)
        
    # === UI 绘制 (适配小尺寸画布) ===
    # 字体改小：14->10, 15->11
    def add_ui(x, y, txt, sz, col, weight='bold'):
        t_obj = fig.text(x, y, txt, ha='left', fontsize=sz, color=col, weight=weight)
        t_obj.set_path_effects([path_effects.withStroke(linewidth=2, foreground='white')]) # 描边变细

    st = fig.text(0.5, 0.85, phase_txt, ha='center', fontsize=10, weight='bold', color='#37474F')
    st.set_path_effects([path_effects.withStroke(linewidth=2, foreground='white')])
    
    fig.lines.append(plt.Line2D([0.1, 0.9], [0.15, 0.15], transform=fig.transFigure, color='#546E7A', linewidth=1.5))
    add_ui(0.1, 0.18, "建模目标:", 8, '#546E7A')
    add_ui(0.28, 0.16, prompt_txt, 11, '#263238')
    if cursor: add_ui(0.28 + len(prompt_txt)*0.06, 0.16, cursor, 11, '#2979FF')


# --- 3. 压缩渲染 ---
# 目标：4秒时长, 15 FPS -> 60 帧
TOTAL_FRAMES = 60
frames = []

print("正在生成压缩版 GIF (sam3d_fixed_compressed.gif)...")
# 缩小画布：3x3英寸 @ 100dpi = 300x300像素
fig = plt.figure(figsize=(3, 3), dpi=100) 
# 去除白边，最大化利用像素
plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)

fig.patch.set_alpha(0.0) 
ax = fig.add_subplot(111, projection='3d')

for i in range(TOTAL_FRAMES):
    t_val = i / TOTAL_FRAMES
    
    draw_scene(fig, ax, t_val, i)
    
    # 内存截图 (无残影)
    buf = io.BytesIO()
    # 关键：不使用 bbox_inches='tight'，避免尺寸跳动，手动 layout 已铺满
    fig.savefig(buf, format='png', transparent=True, facecolor='none')
    buf.seek(0)
    
    frames.append(imageio.imread(buf))
    buf.close()
    
    if i % 10 == 0:
        print(f"  进度: {i}/{TOTAL_FRAMES}")

# 保存：15 FPS, LZW 压缩
imageio.mimsave(
    'sam3d_fixed_compressed.gif', 
    frames, 
    duration=4.0 / TOTAL_FRAMES, # 约 0.066s (15fps)
    disposal=2, 
    loop=0,
    optimize=True
)

print("完成！文件: sam3d_fixed_compressed.gif")
