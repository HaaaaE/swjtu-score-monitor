from PIL import Image, ImageDraw

from pathlib import Path
import sys, os
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import PROJECT_ROOT
# --- 准备工作：创建用于存放调试结果的文件夹 ---
DEBUG_FOLDER = os.path.join(PROJECT_ROOT, "utils" , "debug_output")

if not os.path.exists(DEBUG_FOLDER):
    os.makedirs(DEBUG_FOLDER)

# --- 1. 预处理 ---
def preprocess_image(image_path, threshold=128, noise_reduction_strength=2):
    """
    对图像进行预处理，并保存中间步骤以便调试。
    """
    img = Image.open(image_path)
    
    # 步骤 1.1: 灰度化
    img_gray = img.convert('L')
    
    # 步骤 1.2: 二值化
    table = []
    for i in range(256):
        if i < threshold:
            table.append(0)  # 黑色
        else:
            table.append(1)  # 白色
    img_bin = img_gray.point(table, '1')
    width, height = img_bin.size
    img_data = img_bin.load()
    for x in range(width):
        for y in range(height):
            if x == 0 or y == 0:
                img_data[x, y] = 1
                
    # 【调试】保存二值化结果
    #img_bin.convert('RGB').save(os.path.join(DEBUG_FOLDER, "debug_1_binarized.png"))
    print("✅ 步骤1: 二值化完成。请检查 'utils/debug_output/debug_1_binarized.png'")
    
    return img_bin

# --- 2. 字符分割 ---
def segment_characters(img):
    """
    分割字符，并可视化垂直投影，保存每个切割出的字符。
    """
    width, height = img.size
    pixels = img.load()
    
    # 步骤 2.1: 计算垂直投影
    vertical_projection = [0] * width
    for x in range(width):
        for y in range(height):
            if pixels[x, y] == 0:
                vertical_projection[x] += 1
                
    # 【调试】可视化垂直投影图
    proj_img = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(proj_img)
    for x, val in enumerate(vertical_projection):
        draw.line([(x, height), (x, height - val)], fill=(0, 0, 0))
    #proj_img.save(os.path.join(DEBUG_FOLDER, "debug_3_vertical_projection.png"))
    print("✅ 步骤3: 垂直投影计算完成。'")

    # 步骤 2.2: 寻找边界并切割
    in_char = False
    char_boundaries = []
    start_x = 0
    for x, val in enumerate(vertical_projection):
        # 从背景进入字符区域：检测到黑色像素(val > 1)
        if val > 1 and not in_char:
            in_char = True
            start_x = x  # 记录字符起始位置
        # 从字符区域回到背景：检测到空白列(val <= 1)
        elif val <= 1 and in_char:
            in_char = False
            end_x = x
            char_boundaries.append((start_x, end_x))  # 保存字符边界
    # 处理边界情况：如果图像末尾还在字符内
    if in_char:
        char_boundaries.append((start_x, width))

    char_images = []
    for i, (start, end) in enumerate(char_boundaries):
        box = (start, 0, end, height)
        char_img = img.crop(box)
        
        # 使用水平投影消除上下位置差异
        char_width, char_height = char_img.size
        char_pixels = char_img.load()
        
        # 计算水平投影(每一行的黑色像素数量)
        horizontal_projection = [0] * char_height
        for y in range(char_height):
            for x in range(char_width):
                if char_pixels[x, y] == 0:  # 黑色像素
                    horizontal_projection[y] += 1
        
        # 找到字符的上下边界
        top_boundary = 0
        bottom_boundary = char_height - 1
        
        # 从上往下找第一个有内容的行
        for y in range(char_height):
            if horizontal_projection[y] > 1:
                top_boundary = y
                break
        
        # 从下往上找最后一个有内容的行
        for y in range(char_height - 1, -1, -1):
            if horizontal_projection[y] > 1:
                bottom_boundary = y
                break
        
        # 裁剪掉上下空白区域
        if bottom_boundary > top_boundary:
            char_img = char_img.crop((0, top_boundary, char_width, bottom_boundary + 1))
        
        char_images.append(char_img)
        # 【调试】保存每个切割出的字符（保持二值模式）
        #char_img.save(os.path.join(DEBUG_FOLDER, f"char_{i}.png"))
        #print(f"  - 保存 'debug_output/char_{i}.png'")
        
    print("✅ 步骤4: 字符分割完成。")
    return char_images

# --- 3. 字符识别 (增加详细log) ---
def load_templates(template_dir=os.path.join(PROJECT_ROOT, 'utils', 'templates')):
    """加载模板字符库"""
    # 初始化空字典，用于存储模板图像
    templates = {}
    # 检查模板目录是否存在，如果不存在则返回 None
    if not os.path.exists(template_dir): return None
    # 遍历模板目录中的所有文件
    for filename in os.listdir(template_dir):
        # 只处理 PNG 格式的图像文件
        if filename.endswith('.png'):
            # 提取文件名（去掉扩展名）作为字符名称
            char_name = os.path.splitext(filename)[0]
            # 打开图像并转换为二值模式
            img = Image.open(os.path.join(template_dir, filename))
            # 转换为灰度后二值化，确保模式统一
            if img.mode != '1':
                img = img.convert('L').point(lambda x: 0 if x < 128 else 1, '1')
            templates[char_name] = img
    # 返回包含所有模板的字典
    return templates

def recognize_character(char_img, templates, offset_range=3):
    """
    识别单个字符图像，通过滑动窗口与模板库中的字符进行像素级比较
    
    参数:
        char_img: 待识别的字符图像(PIL Image对象)
        templates: 模板字符库字典，键为字符名，值为模板图像
        offset_range: 允许的上下左右偏移范围，默认为3像素
    
    返回:
        best_match: 最匹配的字符名称(字符串)
    """
    # 获取待识别字符的尺寸和像素数据
    char_width, char_height = char_img.size
    char_pixels = char_img.load()
    
    # 初始化最大相似度为0，用于记录最佳匹配的相似度
    max_similarity = 0.0
    # 初始化最佳匹配字符为'?'，表示未识别或无匹配结果
    best_match = '?'
    
    # 【调试】打印分隔线，标记开始新一轮字符匹配过程
    print("-" * 20)
    
    # 遍历模板库中的每个字符模板
    for char_name, template_img in templates.items():
        # 获取模板图像的尺寸和像素数据
        template_width, template_height = template_img.size
        template_pixels = template_img.load()
        
        # 对当前模板尝试不同的偏移位置
        best_offset_similarity = 0.0
        best_offset = (0, 0)
        
        # 计算模板的黑色像素总数
        template_black_count = 0
        for x in range(template_width):
            for y in range(template_height):
                if template_pixels[x, y] == 0:  # 黑色像素
                    template_black_count += 1
        
        # 计算待识别字符的黑色像素总数
        char_black_count = 0
        for x in range(char_width):
            for y in range(char_height):
                if char_pixels[x, y] == 0:  # 黑色像素
                    char_black_count += 1
        
        # 遍历所有可能的偏移量
        for offset_x in range(-offset_range, offset_range + 1):
            for offset_y in range(-offset_range, offset_range + 1):
                # 计算黑色部分重合的像素数量
                overlap_black_count = 0
                
                # 遍历模板的每个像素
                for template_x in range(template_width):
                    for template_y in range(template_height):
                        # 如果模板这个位置是黑色像素
                        if template_pixels[template_x, template_y] == 0:
                            # 计算对应在待识别字符上的位置
                            char_x = template_x + offset_x
                            char_y = template_y + offset_y
                            
                            # 检查是否在待识别字符的范围内
                            if 0 <= char_x < char_width and 0 <= char_y < char_height:
                                # 如果待识别字符这个位置也是黑色，则重合
                                if char_pixels[char_x, char_y] == 0:
                                    overlap_black_count += 1
                
                # 计算相似度：黑色重合像素占模板黑色像素的比例
                if template_black_count > 0:
                    template_ratio = overlap_black_count / template_black_count
                else:
                    template_ratio = 0.0
                
                # 计算相似度：黑色重合像素占待识别字符黑色像素的比例
                if char_black_count > 0:
                    char_ratio = overlap_black_count / char_black_count
                else:
                    char_ratio = 0.0
                
                # 使用调和平均数作为相似度（比算术平均更严格）
                if template_ratio + char_ratio > 0:
                    similarity = 2 * template_ratio * char_ratio / (template_ratio + char_ratio)
                else:
                    similarity = 0.0
                
                # 更新该模板的最佳偏移
                if similarity > best_offset_similarity:
                    best_offset_similarity = similarity
                    best_offset = (offset_x, offset_y)
        
        # 【调试】输出当前模板的最佳匹配结果
        print(f"  与模板 '{char_name}' 比较，最佳相似度: {best_offset_similarity:.3f} (偏移: {best_offset})")
        
        # 如果当前模板的相似度大于全局最大相似度，则更新最佳匹配
        if best_offset_similarity > max_similarity:
            max_similarity = best_offset_similarity
            best_match = char_name
    
    # 【调试】输出最终选定的最佳匹配字符及其相似度
    print(f"  ==> 最佳匹配: '{best_match}' (相似度: {max_similarity:.3f})")
    # 返回识别结果
    return best_match

# --- 4. 对外接口 ---
def classify(image_bytes):
    """
    识别验证码图片（从字节流输入）
    
    参数:
        image_bytes: 图片字节流（可以是从网络请求获取的内容）
        binary_threshold: 二值化阈值，默认94
        offset_range: 滑动窗口偏移范围，默认3
        silent: 是否静默模式（不打印调试信息），默认False
    
    返回:
        识别出的验证码字符串
    """
    import io
    

    print("--- 开始识别验证码 ---")
    
    # 0. 加载模板
    templates = load_templates()
    if not templates:
        print("错误：模板文件夹 'templates' 为空或不存在。请先创建模板。")
        return

    # 1. 预处理
    BINARY_THRESHOLD = 94
        # 1. 从字节流加载图像
    img = Image.open(io.BytesIO(image_bytes))
    # 步骤 1.1: 灰度化
    img_gray = img.convert('L')

    # 步骤 1.2: 二值化
    table = []
    for i in range(256):
        if i < BINARY_THRESHOLD:
            table.append(0)  # 黑色
        else:
            table.append(1)  # 白色
    img_bin = img_gray.point(table, '1')
    width, height = img_bin.size
    img_data = img_bin.load()
    for x in range(width):
        for y in range(height):
            if x == 0 or y == 0:
                img_data[x, y] = 1
                
    # 【调试】保存二值化结果
    #img_bin.convert('RGB').save(os.path.join(DEBUG_FOLDER, "debug_1_binarized.png"))
    print("✅ 步骤1: 二值化完成。'")    
    # 2. 分割字符
    char_images = segment_characters(img_bin)
    
    # 3. 识别字符
    print("\n✅ 步骤5: 开始逐个识别字符...")
    result = ""
    for i, char_img in enumerate(char_images):
        print(f"\n--- 正在识别第 {i+1} 个字符 (char_{i}.png) ---")
        recognized_char = recognize_character(char_img, templates)
        result += recognized_char
        
    return result

# --- 主流程 ---
def main(captcha_path):
    print("--- 开始识别验证码 ---")
    
    # 0. 加载模板
    templates = load_templates()
    if not templates:
        print("错误：模板文件夹 'templates' 为空或不存在。请先创建模板。")
        return

    # 1. 预处理
    BINARY_THRESHOLD = 94
    NOISE_STRENGTH = 4
    processed_img = preprocess_image(captcha_path, threshold=BINARY_THRESHOLD, noise_reduction_strength=NOISE_STRENGTH)
    
    # 2. 分割字符
    char_images = segment_characters(processed_img)
    
    # 3. 识别字符
    print("\n✅ 步骤5: 开始逐个识别字符...")
    result = ""
    for i, char_img in enumerate(char_images):
        print(f"\n--- 正在识别第 {i+1} 个字符 (char_{i}.png) ---")
        recognized_char = recognize_character(char_img, templates)
        result += recognized_char
        
    return result

if __name__ == '__main__':
    captcha_file = "image.png"
    if not os.path.exists(captcha_file):
        print(f"错误: 验证码文件 '{captcha_file}' 不存在。")
    else:
        captcha_text = main(captcha_file)
        print("\n" + "="*30)
        print(f"最终识别结果: {captcha_text}")
        print("="*30)