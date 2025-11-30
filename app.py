import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import matplotlib.patheffects as path_effects
from matplotlib.patches import Circle
import mpl_toolkits.mplot3d.art3d as art3d
import imageio.v2 as imageio
import io
import platform

# --- Configuration & Style ---
STYLE = {
    'cam_path_front': '#37474F',  # Path in front of object
    'cam_path_back':  '#B0BEC5',  # Path behind object
    'cam_body':       '#263238',
    'view_cone':      '#00E5FF',
    'point_cloud':    '#039BE5',
    'final_mesh':     '#2962FF',
    'grid':           '#E0E0E0',
    'font_main':      '#1C2B33',
    'font_sub':       '#546E7A',
}

def configure_font():
    """Configure fonts to support Chinese characters across platforms."""
    sys_name = platform.system()
    if sys_name == 'Windows':
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'sans-serif']
    elif sys_name == 'Darwin': # Mac
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti TC', 'sans-serif']
    else:
        plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'sans-serif']
    plt.rcParams['axes.unicode_minus'] = False

# --- Geometry Helpers ---
def get_cube(center=(0,0,0), size=0.5):
    cx, cy, cz = center; r = size
    v = np.array([
        [cx-r, cy-r, cz-r], [cx+r, cy-r, cz-r], [cx+r, cy+r, cz-r], [cx-r, cy+r, cz-r],
        [cx-r, cy-r, cz+r], [cx+r, cy-r, cz+r], [cx+r, cy+r, cz+r], [cx-r, cy+r, cz+r]
    ])
    faces = [[v[0], v[1], v[5], v[4]], [v[1], v[2], v[6], v[5]], [v[2], v[3], v[7], v[6]], 
             [v[3], v[0], v[4], v[7]], [v[4], v[5], v[6], v[7]], [v[0], v[3], v[2], v[1]]]
    return faces

def get_point_cloud(num_points=150):
    points = []
    r = 0.5
    for _ in range(num_points):
        axis = np.random.choice([0, 1, 2])
        sign = np.random.choice([-1, 1])
        p = [np.random.uniform(-r, r), np.random.uniform(-r, r), np.random.uniform(-r, r)]
        p[axis] = r * sign 
        points.append(p)
    return np.array(points)

# --- Drawing Functions ---
def draw_camera(ax, pos, look_at=(0,0,0)):
    cx, cy, cz = pos
    # Camera body
    ax.scatter([cx], [cy], [cz], color=STYLE['cam_body'], s=60, marker='s', zorder=100, edgecolor='white', linewidth=1)
    # View cone
    ax.plot([cx, look_at[0]], [cy, look_at[1]], [cz, look_at[2]], 
            color=STYLE['view_cone'], alpha=0.6, linestyle='--', linewidth=1.5, zorder=99)

def draw_frame(fig, ax, t, target_text):
    ax.clear()
    ax.set_axis_off()
    ax.grid(False)
    ax.set_box_aspect((1, 1, 1))
    ax.set_xlim(-1.5, 1.5); ax.set_ylim(-1.5, 1.5); ax.set_zlim(-1.5, 1.5)
    
    # Draw simple floor
    for i in [-1.0, 0, 1.0]: 
        ax.plot([i, i], [-1.2, 1.2], [-1.2, -1.2], color=STYLE['grid'], alpha=0.5, lw=0.8)
        ax.plot([-1.2, 1.2], [i, i], [-1.2, -1.2], color=STYLE['grid'], alpha=0.5, lw=0.8)

    cube_data = get_cube()
    pts_data = get_point_cloud(150)
    
    ui_text = ""
    ui_sub = ""
    prompt_display = ""
    
    # Stages
    P1 = 0.60
    P2 = 0.80
    
    # === Phase 1: Orbit Scan (With Occlusion Handling) ===
    if t < P1:
        local_t = t / P1
        ui_text = "1. 多角度视频扫描"
        ui_sub = "环绕拍摄 (上/中/下)"
        prompt_display = target_text
        
        # Fixed view for static object illusion
        azim_val = -45
        elev_val = 15
        ax.view_init(elev=elev_val, azim=azim_val) 
        
        # Opaque cube for occlusion
        poly = Poly3DCollection(cube_data, linewidths=0.5)
        poly.set_facecolor('#ECEFF1')
        poly.set_edgecolor('#CFD8DC')
        poly.set_alpha(1.0)
        poly.set_zorder(10)
        ax.add_collection3d(poly)
        
        # Trajectory calculation
        total_angle = 6 * np.pi
        angle_offset = np.pi / 4
        current_angle = -local_t * total_angle + angle_offset
        radius = 1.45
        current_z = 0.8 - (local_t * 1.6)
        
        cam_x = radius * np.cos(current_angle)
        cam_y = radius * np.sin(current_angle)
        
        # View vector for occlusion check
        theta = np.radians(azim_val); phi = np.radians(elev_val)
        cam_vec_x = np.cos(phi) * np.cos(theta)
        cam_vec_y = np.cos(phi) * np.sin(theta)
        
        # Segmented path drawing
        sample_steps = int(local_t * 80) + 2
        prev_t = np.linspace(0, local_t, sample_steps)
        h_angle = -prev_t * total_angle + angle_offset
        h_z = 0.8 - (prev_t * 1.6)
        h_x = radius * np.cos(h_angle)
        h_y = radius * np.sin(h_angle)
        
        for k in range(len(h_x) - 1):
            mx = (h_x[k] + h_x[k+1]) / 2
            my = (h_y[k] + h_y[k+1]) / 2
            # Dot product to check depth relative to cube center
            proj_dist = mx * cam_vec_x + my * cam_vec_y
            
            if proj_dist > 0:
                z_ord = 20; col = STYLE['cam_path_front']; alp = 0.8; wid = 1.8
            else:
                z_ord = 5; col = STYLE['cam_path_back']; alp = 0.4; wid = 1.2
            
            ax.plot(h_x[k:k+2], h_y[k:k+2], h_z[k:k+2], 
                    color=col, alpha=alp, linewidth=wid, zorder=z_ord)
        
        draw_camera(ax, (cam_x, cam_y, current_z))

    # === Phase 2: Solving/PointCloud ===
    elif t < P2:
        local_t = (t - P1) / (P2 - P1)
        ui_text = "2. 解算 / 建模" 
        ui_sub = "稀疏点云 -> 稠密实体"
        prompt_display = target_text
        
        ax.view_init(elev=15, azim=-45 + local_t * 20)
        
        visible_indices = np.random.choice(len(pts_data), int(len(pts_data) * local_t), replace=False)
        if len(visible_indices) > 0:
            current_pts = pts_data[visible_indices]
            ax.scatter(current_pts[:,0], current_pts[:,1], current_pts[:,2], 
                       color=STYLE['point_cloud'], s=12, alpha=0.8, marker='.', depthshade=False, zorder=15)
        
        poly = Poly3DCollection(cube_data, linewidths=0.5)
        poly.set_facecolor((1,1,1,0))
        poly.set_edgecolor(STYLE['final_mesh'])
        poly.set_alpha(0.3 * local_t)
        poly.set_zorder(10)
        ax.add_collection3d(poly)

    # === Phase 3: Final Mesh ===
    else:
        local_t = (t - P2) / (1.0 - P2)
        ui_text = "3. 生成 3D 模型"
        ui_sub = "建模完成"
        prompt_display = target_text
        
        poly = Poly3DCollection(cube_data, linewidths=1.0)
        poly.set_facecolor(STYLE['final_mesh'])
        poly.set_edgecolor('white')
        poly.set_alpha(1.0)
        poly.set_zorder(10)
        ax.add_collection3d(poly)
        
        start_azim = -45 + 20
        ax.view_init(elev=15, azim=start_azim + local_t * 360)

    # UI Elements
    t_main = fig.text(0.5, 0.15, ui_text, ha='center', va='center', 
             fontsize=11, weight='bold', color=STYLE['font_main'])
    t_main.set_path_effects([path_effects.withStroke(linewidth=3, foreground='white')])
    
    t_sub = fig.text(0.5, 0.08, ui_sub, ha='center', va='center', 
             fontsize=8, weight='normal', color=STYLE['font_sub'])
    t_sub.set_path_effects([path_effects.withStroke(linewidth=2, foreground='white')])
    
    # Prompt Label
    if prompt_display:
        fig.text(0.5, 0.92, f"Target: {prompt_display}", ha='center', fontsize=9, color='#78909C', weight='bold')

def generate_gif_data(text, duration):
    configure_font()
    
    # Compressed settings: 12 FPS, small size
    FPS = 12
    TOTAL_FRAMES = int(duration * FPS)
    
    # 2.5 inch * 100 dpi = 250x250 pixels
    fig = plt.figure(figsize=(2.5, 2.5), dpi=100)
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    fig.patch.set_alpha(0.0) 
    ax = fig.add_subplot(111, projection='3d')
    
    frames = []
    
    # Progress bar in Streamlit
    bar = st.progress(0)
    
    for i in range(TOTAL_FRAMES):
        t_val = i / TOTAL_FRAMES
        draw_frame(fig, ax, t_val, text)
        
        # Save to memory buffer
        buf = io.BytesIO()
        fig.savefig(buf, format='png', transparent=True, facecolor='none')
        buf.seek(0)
        frames.append(imageio.imread(buf))
        buf.close()
        
        bar.progress((i + 1) / TOTAL_FRAMES)
        
    # Save GIF to memory
    output = io.BytesIO()
    imageio.mimsave(output, frames, format='gif', duration=1/FPS, disposal=2, loop=0, optimize=True)
    return output.getvalue()

# --- Streamlit App UI ---
st.set_page_config(page_title="AI 3D GIF Generator", layout="centered")

st.title("🧊 AI 3D 演示动图生成器")
st.markdown("生成 **环绕扫描 -> 点云 -> 建模** 的技术演示动图。")

col1, col2 = st.columns([2, 1])
with col1:
    text_input = st.text_input("建模目标名称", "智能音箱")
with col2:
    duration = st.slider("时长 (秒)", 3, 8, 6)

if st.button("🎬 开始生成 GIF", type="primary"):
    with st.spinner("正在逐帧渲染，请稍候..."):
        gif_bytes = generate_gif_data(text_input, duration)
    
    st.success("生成完成！")
    
    # Columns for preview and download
    c1, c2 = st.columns([1, 1])
    with c1:
        st.image(gif_bytes, caption="预览 (250x250)")
    with c2:
        st.download_button(
            label="💾 下载 GIF 文件",
            data=gif_bytes,
            file_name=f"3d_scan_{text_input}.gif",
            mime="image/gif"
        )