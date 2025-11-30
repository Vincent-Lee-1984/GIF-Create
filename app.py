import streamlit as st  # 导入 Streamlit 库，用于构建网页界面
import numpy as np  # 导入 NumPy 库，用于数值计算与随机数
import matplotlib.pyplot as plt  # 导入 Matplotlib 库，用于绘图
from mpl_toolkits.mplot3d.art3d import Poly3DCollection  # 导入 3D 多边形集合类
import matplotlib.patheffects as path_effects  # 导入路径效果模块，用于文本描边
from matplotlib.patches import Circle  # 导入圆形补丁，用于投影阴影
import mpl_toolkits.mplot3d.art3d as art3d  # 导入 3D 工具，用于将 2D 补丁转为 3D
import imageio.v2 as imageio  # 导入 ImageIO v2，用于保存 GIF
import io  # 导入 io，用于内存缓冲读写
import platform  # 导入 platform，用于判断操作系统以设置字体
import re  # 导入正则表达式模块，用于解析需求文本

# --- 全局样式（可根据主题色动态调整） ---
STYLE = {  # 定义默认样式颜色字典
    'cam_path_front': '#37474F',  # 相机路径（物体前方）颜色
    'cam_path_back':  '#B0BEC5',  # 相机路径（物体后方）颜色
    'cam_body':       '#263238',  # 相机机身颜色
    'view_cone':      '#00E5FF',  # 视线/视锥颜色
    'point_cloud':    '#039BE5',  # 点云颜色
    'final_mesh':     '#2962FF',  # 最终网格颜色
    'grid':           '#E0E0E0',  # 地面网格颜色
    'font_main':      '#1C2B33',  # 主标题字体颜色
    'font_sub':       '#546E7A',  # 副标题字体颜色
}

def configure_font():  # 配置跨平台中文字体
    sys_name = platform.system()  # 获取操作系统名称
    if sys_name == 'Windows':  # 若为 Windows
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'sans-serif']  # 设置中文字体列表
    elif sys_name == 'Darwin':  # 若为 macOS
        plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'PingFang SC', 'Heiti TC', 'sans-serif']  # 设置中文字体列表
    else:  # 其他 Linux 等系统
        plt.rcParams['font.sans-serif'] = ['WenQuanYi Micro Hei', 'sans-serif']  # 设置中文字体列表
    plt.rcParams['axes.unicode_minus'] = False  # 允许坐标轴显示负号

# --- 解析需求文本为配置 ---
def parse_requirements(text: str):  # 将用户需求文本解析为配置字典
    t = (text or '').lower()  # 将文本转为小写，便于匹配
    cfg = {  # 定义默认配置字典
        'shape': 'cube',  # 默认几何体为立方体
        'enable_scan': True,  # 启用环绕扫描阶段
        'enable_pointcloud': True,  # 启用点云阶段
        'enable_final': True,  # 启用最终网格阶段
        'rotation_final': True,  # 最终阶段是否旋转展示
        'transparent_bg': True,  # 是否使用透明背景
        'show_grid': True,  # 是否显示地面网格
        'fps': 12,  # 默认帧率
        'duration': 6,  # 默认时长（秒）
        'size_inch': 2.5,  # 画布英寸大小
        'dpi': 100,  # 画布 DPI
        'primary_color': '#2962FF',  # 主色（用于最终网格）
        'target_name': '目标物体',  # 默认目标名称
    }  # 结束默认配置

    if '金字塔' in text or 'pyramid' in t:  # 匹配金字塔关键词
        cfg['shape'] = 'pyramid'  # 设置几何体为金字塔
    if '棱柱' in text or 'prism' in t:  # 匹配棱柱关键词
        cfg['shape'] = 'prism'  # 设置几何体为棱柱
    if '立方' in text or 'cube' in t:  # 匹配立方关键词
        cfg['shape'] = 'cube'  # 设置几何体为立方体

    if '不透明' in text or 'opaque' in t:  # 匹配不透明背景需求
        cfg['transparent_bg'] = False  # 设置背景不透明
    if '无网格' in text or 'no grid' in t:  # 匹配不显示网格需求
        cfg['show_grid'] = False  # 不显示地面网格

    fps_match = re.search(r"fps\s*(\d+)", t)  # 正则提取 fps 参数
    if fps_match:  # 若匹配到
        cfg['fps'] = int(fps_match.group(1))  # 更新帧率
    dur_match = re.search(r"(sec|秒)\s*(\d+)", t)  # 正则提取时长参数
    if dur_match:  # 若匹配到
        cfg['duration'] = int(dur_match.group(2))  # 更新时长

    color_match = re.search(r"#([0-9a-f]{6})", t)  # 正则提取十六进制颜色
    if color_match:  # 若匹配到
        cfg['primary_color'] = f"#{color_match.group(1)}"  # 更新主色

    name_match = re.search(r"(目标|target)[:：]\s*(\S+)", text or '', re.IGNORECASE)  # 提取目标名称
    if name_match:  # 若匹配到
        cfg['target_name'] = name_match.group(2)  # 更新目标名称

    return cfg  # 返回配置字典

# --- 几何体生成 ---
def get_cube(center=(0, 0, 0), size=0.5):  # 生成立方体六个面的顶点集合
    cx, cy, cz = center; r = size  # 解包中心与尺寸半径
    v = np.array([  # 顶点列表
        [cx - r, cy - r, cz - r], [cx + r, cy - r, cz - r], [cx + r, cy + r, cz - r], [cx - r, cy + r, cz - r],  # 底面四点
        [cx - r, cy - r, cz + r], [cx + r, cy - r, cz + r], [cx + r, cy + r, cz + r], [cx - r, cy + r, cz + r]   # 顶面四点
    ])  # 顶点数组结束
    faces = [  # 面列表，每个面由四个顶点构成
        [v[0], v[1], v[5], v[4]], [v[1], v[2], v[6], v[5]], [v[2], v[3], v[7], v[6]],
        [v[3], v[0], v[4], v[7]], [v[4], v[5], v[6], v[7]], [v[0], v[3], v[2], v[1]]
    ]  # 面集合结束
    return faces  # 返回立方体面集合

def get_pyramid(center=(1.2, 0, -0.2), size=0.5):  # 生成金字塔面的顶点集合
    cx, cy, cz = center; r = size  # 解包中心与尺寸
    v = np.array([[cx - r, cy - r, cz], [cx + r, cy - r, cz], [cx + r, cy + r, cz], [cx - r, cy + r, cz], [cx, cy, cz + r * 1.5]])  # 底面四点和顶点
    faces = [[v[0], v[1], v[2], v[3]], [v[0], v[1], v[4]], [v[1], v[2], v[4]], [v[2], v[3], v[4]], [v[3], v[0], v[4]]]  # 构造各三角面
    return faces  # 返回金字塔面集合

def get_prism(center=(-1.2, 0, 0), size=0.4, height=0.8):  # 生成六边棱柱面的顶点集合
    cx, cy, cz = center; r = size; h = height / 2  # 解包中心、半径与半高
    angles = np.linspace(0, 2 * np.pi, 7)[:-1]  # 生成六边形角度序列
    bottom = [[cx + r * np.cos(a), cy + r * np.sin(a), cz - h] for a in angles]  # 底面六点
    top = [[cx + r * np.cos(a), cy + r * np.sin(a), cz + h] for a in angles]  # 顶面六点
    faces = [bottom, top]  # 先加入底面与顶面
    for i in range(6): faces.append([bottom[i], bottom[(i + 1) % 6], top[(i + 1) % 6], top[i]])  # 逐个加入侧面
    return faces  # 返回棱柱面集合

def get_point_cloud(num_points=150):  # 生成近似立方体表面的点云
    points = []  # 初始化点列表
    r = 0.5  # 立方体半径
    for _ in range(num_points):  # 遍历生成指定数量的点
        axis = np.random.choice([0, 1, 2])  # 随机选择一个轴
        sign = np.random.choice([-1, 1])  # 随机选择符号正负
        p = [np.random.uniform(-r, r), np.random.uniform(-r, r), np.random.uniform(-r, r)]  # 随机生成一个点
        p[axis] = r * sign  # 将选定轴固定在立方体表面
        points.append(p)  # 添加到列表
    return np.array(points)  # 返回点云数组

def draw_camera(ax, pos, look_at=(0, 0, 0)):  # 绘制相机与视线
    cx, cy, cz = pos  # 解包相机位置
    ax.scatter([cx], [cy], [cz], color=STYLE['cam_body'], s=60, marker='s', zorder=100, edgecolor='white', linewidth=1)  # 绘制相机机身
    ax.plot([cx, look_at[0]], [cy, look_at[1]], [cz, look_at[2]], color=STYLE['view_cone'], alpha=0.6, linestyle='--', linewidth=1.5, zorder=99)  # 绘制视线

# --- 帧绘制：根据配置组合三阶段 ---
def draw_frame(fig, ax, t, cfg):  # 绘制单帧图像
    ax.clear()  # 清除上一帧内容
    ax.set_axis_off()  # 关闭坐标轴
    ax.grid(False)  # 关闭网格线
    ax.set_box_aspect((1, 1, 1))  # 设置坐标轴比例
    ax.set_xlim(-1.5, 1.5); ax.set_ylim(-1.5, 1.5); ax.set_zlim(-1.5, 1.5)  # 设置范围

    if cfg.get('show_grid', True):  # 若配置要求显示网格
        for i in [-1.0, 0, 1.0]:  # 遍历三条网格线位置
            ax.plot([i, i], [-1.2, 1.2], [-1.2, -1.2], color=STYLE['grid'], alpha=0.5, lw=0.8)  # 绘制纵向网格线
            ax.plot([-1.2, 1.2], [i, i], [-1.2, -1.2], color=STYLE['grid'], alpha=0.5, lw=0.8)  # 绘制横向网格线

    # 根据形状生成几何体数据
    if cfg['shape'] == 'cube':  # 若为立方体
        mesh_data = get_cube()  # 生成立方体面集合
    elif cfg['shape'] == 'pyramid':  # 若为金字塔
        mesh_data = get_pyramid((0, 0, 0))  # 在原点生成金字塔
    else:  # 否则为棱柱
        mesh_data = get_prism((0, 0, 0))  # 在原点生成棱柱

    pts_data = get_point_cloud(180)  # 生成点云数据

    # 阶段时间占比（按启用与否自适应）
    s1 = 0.4 if cfg.get('enable_scan') else 0.0  # 扫描阶段占比
    s2 = 0.35 if cfg.get('enable_pointcloud') else 0.0  # 点云阶段占比
    s3 = 1.0 - (s1 + s2)  # 最终阶段占比
    p1 = s1  # 第一阶段结束时刻
    p2 = s1 + s2  # 第二阶段结束时刻

    ui_text = ''  # 初始化主标题文本
    ui_sub = ''  # 初始化副标题文本
    target_text = cfg.get('target_name', '目标物体')  # 目标文本

    if t < p1:  # 阶段 1：环绕扫描
        local_t = t / max(p1, 1e-6)  # 归一化局部时间，防止除零
        ui_text = '1. 多角度视频扫描'  # 设置主标题
        ui_sub = '环绕拍摄 (上/中/下)'  # 设置副标题
        azim_val = -45  # 固定方位角
        elev_val = 15  # 固定仰角
        ax.view_init(elev=elev_val, azim=azim_val)  # 设置视角

        poly = Poly3DCollection(mesh_data, linewidths=0.5)  # 创建面片集合对象
        poly.set_facecolor('#ECEFF1')  # 设置面片填充颜色
        poly.set_edgecolor('#CFD8DC')  # 设置边缘颜色
        poly.set_alpha(1.0)  # 设置不透明度
        poly.set_zorder(10)  # 设置图层顺序
        ax.add_collection3d(poly)  # 添加到 3D 轴

        total_angle = 6 * np.pi  # 总旋转角度
        angle_offset = np.pi / 4  # 初始偏移角度
        current_angle = -local_t * total_angle + angle_offset  # 当前角度
        radius = 1.45  # 相机环绕半径
        current_z = 0.8 - (local_t * 1.6)  # 相机高度变化
        cam_x = radius * np.cos(current_angle)  # 相机 X 坐标
        cam_y = radius * np.sin(current_angle)  # 相机 Y 坐标

        theta = np.radians(azim_val); phi = np.radians(elev_val)  # 将角度转为弧度
        cam_vec_x = np.cos(phi) * np.cos(theta)  # 视线向量 X 分量
        cam_vec_y = np.cos(phi) * np.sin(theta)  # 视线向量 Y 分量

        sample_steps = int(local_t * 80) + 2  # 路径采样步数
        prev_t = np.linspace(0, local_t, sample_steps)  # 历史时间采样
        h_angle = -prev_t * total_angle + angle_offset  # 历史角度序列
        h_z = 0.8 - (prev_t * 1.6)  # 历史高度序列
        h_x = radius * np.cos(h_angle)  # 历史 X 序列
        h_y = radius * np.sin(h_angle)  # 历史 Y 序列

        for k in range(len(h_x) - 1):  # 遍历绘制线段
            mx = (h_x[k] + h_x[k + 1]) / 2  # 线段中点 X
            my = (h_y[k] + h_y[k + 1]) / 2  # 线段中点 Y
            proj_dist = mx * cam_vec_x + my * cam_vec_y  # 与视线的点积判断前后
            if proj_dist > 0:  # 若在物体前方
                z_ord = 20; col = STYLE['cam_path_front']; alp = 0.8; wid = 1.8  # 设置前方路径样式
            else:  # 若在物体后方
                z_ord = 5; col = STYLE['cam_path_back']; alp = 0.4; wid = 1.2  # 设置后方路径样式
            ax.plot(h_x[k:k + 2], h_y[k:k + 2], h_z[k:k + 2], color=col, alpha=alp, linewidth=wid, zorder=z_ord)  # 绘制路径线段
        draw_camera(ax, (cam_x, cam_y, current_z))  # 绘制当前相机位置

    elif t < p2:  # 阶段 2：点云解算
        local_t = (t - p1) / max(p2 - p1, 1e-6)  # 归一化局部时间
        ui_text = '2. 解算 / 建模'  # 设置主标题
        ui_sub = '稀疏点云 → 稠密实体'  # 设置副标题
        ax.view_init(elev=15, azim=-45 + local_t * 20)  # 调整视角以增强动感

        visible_indices = np.random.choice(len(pts_data), max(1, int(len(pts_data) * local_t)), replace=False)  # 按时间逐步显示点云
        current_pts = pts_data[visible_indices]  # 当前可见点
        ax.scatter(current_pts[:, 0], current_pts[:, 1], current_pts[:, 2], color=STYLE['point_cloud'], s=12, alpha=0.8, marker='.', depthshade=False, zorder=15)  # 绘制点云

        poly = Poly3DCollection(mesh_data, linewidths=0.6)  # 创建面片集合
        poly.set_facecolor((1, 1, 1, 0))  # 设置透明面
        poly.set_edgecolor(cfg.get('primary_color', STYLE['final_mesh']))  # 使用主色作为边缘色
        poly.set_alpha(0.3 * local_t)  # 根据时间提高不透明度
        poly.set_zorder(10)  # 设置图层顺序
        ax.add_collection3d(poly)  # 添加到 3D 轴

    else:  # 阶段 3：最终网格与旋转
        local_t = (t - p2) / max(1.0 - p2, 1e-6)  # 归一化局部时间
        ui_text = '3. 生成 3D 模型'  # 设置主标题
        ui_sub = '建模完成'  # 设置副标题

        poly = Poly3DCollection(mesh_data, linewidths=1.0)  # 创建面片集合
        final_color = cfg.get('primary_color', STYLE['final_mesh'])  # 取最终主色
        poly.set_facecolor(final_color)  # 设置面颜色
        poly.set_edgecolor('white')  # 设置边缘颜色为白色
        poly.set_alpha(1.0)  # 设置不透明度
        poly.set_zorder(10)  # 设置图层顺序
        ax.add_collection3d(poly)  # 添加到 3D 轴

        base_azim = -25  # 初始方位角
        azim = base_azim + (local_t * 360 if cfg.get('rotation_final', True) else 0)  # 若启用旋转则进行 360° 旋转
        ax.view_init(elev=15, azim=azim)  # 设置视角

    # UI 文本叠加
    t_main = fig.text(0.5, 0.15, ui_text, ha='center', va='center', fontsize=11, weight='bold', color=STYLE['font_main'])  # 主标题文本
    t_main.set_path_effects([path_effects.withStroke(linewidth=3, foreground='white')])  # 主标题描边
    t_sub = fig.text(0.5, 0.08, ui_sub, ha='center', va='center', fontsize=8, weight='normal', color=STYLE['font_sub'])  # 副标题文本
    t_sub.set_path_effects([path_effects.withStroke(linewidth=2, foreground='white')])  # 副标题描边
    fig.text(0.5, 0.92, f"Target: {cfg.get('target_name', '目标物体')}", ha='center', fontsize=9, color='#78909C', weight='bold')  # 顶部目标标签

# --- 生成 GIF ---
def generate_gif_data(requirements_text: str, ui_overrides: dict):  # 根据需求文本与 UI 覆盖生成 GIF 字节
    configure_font()  # 配置中文字体
    cfg = parse_requirements(requirements_text or '')  # 解析需求文本得到基础配置
    cfg.update({k: v for k, v in ui_overrides.items() if v is not None})  # 使用 UI 参数覆盖默认配置

    # 根据配置调整全局样式主色
    STYLE['final_mesh'] = cfg.get('primary_color', STYLE['final_mesh'])  # 更新最终网格主色

    fps = int(cfg.get('fps', 12))  # 获取帧率
    total_frames = int(max(1, cfg.get('duration', 6)) * fps)  # 计算总帧数
    fig = plt.figure(figsize=(cfg.get('size_inch', 2.5), cfg.get('size_inch', 2.5)), dpi=cfg.get('dpi', 100))  # 创建画布
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)  # 去除边距
    fig.patch.set_alpha(0.0 if cfg.get('transparent_bg', True) else 1.0)  # 设置背景透明或不透明
    ax = fig.add_subplot(111, projection='3d')  # 创建 3D 子图

    frames = []  # 初始化帧列表
    bar = st.progress(0)  # 创建进度条

    for i in range(total_frames):  # 遍历生成每一帧
        t_val = i / total_frames  # 归一化时间值
        draw_frame(fig, ax, t_val, cfg)  # 绘制当前帧
        buf = io.BytesIO()  # 创建内存缓冲区
        fig.savefig(buf, format='png', transparent=cfg.get('transparent_bg', True), facecolor='none')  # 将当前帧保存为 PNG 至缓冲区
        buf.seek(0)  # 将缓冲区指针回到起始位置
        frames.append(imageio.imread(buf))  # 读取缓冲区图像并加入帧列表
        buf.close()  # 关闭缓冲区
        bar.progress((i + 1) / total_frames)  # 更新进度条

    output = io.BytesIO()  # 创建输出缓冲区
    imageio.mimsave(output, frames, format='gif', duration=1 / fps, disposal=2, loop=0, optimize=True)  # 保存为 GIF 到输出缓冲区
    return output.getvalue()  # 返回 GIF 字节数据

# --- Streamlit 应用界面 ---
st.set_page_config(page_title='需求驱动 GIF 生成器', layout='centered')  # 设置页面标题与布局

st.title('� 根据需求生成生动 GIF 动图')  # 页面主标题
st.markdown('输入需求描述或使用下方控件定制：支持形状、时长、帧率、主题色、透明背景与网格等。')  # 页面说明文字

with st.expander('需求描述（可选）'):  # 折叠区：需求文本输入
    req_text = st.text_area('请输入你的需求（示例：目标: 智能音箱，FPS 15，#FF6D00，透明，展示点云与旋转）', height=120)  # 文本区域输入需求说明

col1, col2, col3 = st.columns([2, 1, 1])  # 三列布局用于基本参数
with col1:  # 第一列
    target_name = st.text_input('目标名称', '智能音箱')  # 输入目标名称
    primary_color = st.color_picker('主题色（最终网格）', '#2962FF')  # 选择主题颜色
with col2:  # 第二列
    duration = st.slider('时长 (秒)', 3, 12, 6)  # 选择总时长
    fps = st.slider('帧率 (FPS)', 8, 30, 12)  # 选择帧率
with col3:  # 第三列
    size_inch = st.slider('画布英寸', 2.0, 4.0, 2.5)  # 选择画布英寸大小
    transparent_bg = st.checkbox('透明背景', True)  # 勾选是否透明背景

shape = st.selectbox('几何形状', ['立方体', '金字塔', '六边棱柱'])  # 选择几何形状
show_grid = st.checkbox('显示地面网格', True)  # 勾选是否显示地面网格
enable_scan = st.checkbox('显示“环绕扫描”阶段', True)  # 勾选是否显示扫描阶段
enable_pointcloud = st.checkbox('显示“点云解算”阶段', True)  # 勾选是否显示点云阶段
rotation_final = st.checkbox('最终阶段旋转展示', True)  # 勾选最终阶段是否旋转

if st.button('🎬 开始生成 GIF', type='primary'):  # 点击按钮开始生成
    with st.spinner('正在逐帧渲染，请稍候...'):  # 显示生成中提示
        ui_cfg = {  # 收集 UI 覆盖配置
            'target_name': target_name,  # 目标名称
            'primary_color': primary_color,  # 主题色
            'duration': duration,  # 时长
            'fps': fps,  # 帧率
            'size_inch': size_inch,  # 画布英寸
            'transparent_bg': transparent_bg,  # 背景透明
            'shape': 'cube' if shape == '立方体' else ('pyramid' if shape == '金字塔' else 'prism'),  # 形状映射
            'show_grid': show_grid,  # 显示网格
            'enable_scan': enable_scan,  # 启用扫描阶段
            'enable_pointcloud': enable_pointcloud,  # 启用点云阶段
            'enable_final': True,  # 始终启用最终阶段
            'rotation_final': rotation_final,  # Final 是否旋转
        }  # UI 配置结束
        gif_bytes = generate_gif_data(req_text, ui_cfg)  # 生成 GIF 字节数据

    st.success('生成完成！')  # 显示成功提示
    c1, c2 = st.columns([1, 1])  # 两列布局：预览与下载
    with c1:  # 左列
        st.image(gif_bytes, caption=f'预览 ({int(size_inch*100)}x{int(size_inch*100)})')  # 显示生成结果预览
    with c2:  # 右列
        st.download_button(label='💾 下载 GIF 文件', data=gif_bytes, file_name=f"3d_demo_{target_name}.gif", mime='image/gif')  # 下载生成的 GIF
