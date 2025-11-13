from flask import Flask, render_template, request, jsonify
import json
import os
import sys
from flask_cors import CORS
import logging
from dotenv import load_dotenv
from datetime import datetime

# 加载环境变量
load_dotenv()

# 创建Flask应用实例
app = Flask(__name__)

# 配置CORS，允许跨域请求 - 线上部署增强版
# 在生产环境中，根据环境变量配置允许的源
allowed_origins = os.environ.get('ALLOWED_ORIGINS', 'http://localhost:8080,http://127.0.0.1:8080,http://localhost:3000,http://127.0.0.1:3000,http://localhost:5000,http://127.0.0.1:5000').split(',')

# 检查是否在生产环境中
is_production = os.environ.get('PRODUCTION', 'False').lower() == 'true'

# 生产环境安全配置
CORS(app, resources={r"/api/*": {
    "origins": allowed_origins,
    "methods": ["GET", "POST", "OPTIONS"],
    "allow_headers": ["Content-Type", "Authorization"],
    "expose_headers": ["Content-Length"],
    "allow_credentials": True,
    "max_age": 3600
}})

# 应用配置
app.config['DEBUG'] = os.environ.get('DEBUG', 'False').lower() == 'true'
app.config['JSON_AS_ASCII'] = False  # 确保中文正常显示
app.config['JSON_SORT_KEYS'] = False  # 保持返回数据的原始顺序
app.config['PREFERRED_URL_SCHEME'] = 'https'  # 生产环境推荐使用HTTPS

# 配置日志 - 增强版配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("app.log"),  # 写入文件
        logging.StreamHandler()  # 输出到控制台
    ]
)
logger = logging.getLogger(__name__)

# 全局变量存储数据
antibiotic_data = None

# 加载JSON数据
def load_data():
    global antibiotic_data
    # 支持从环境变量指定数据文件路径
    json_path = os.environ.get('ANTIBIOTIC_DATA_PATH', 'antibiotic_data.json')
    
    # 获取应用根目录，确保路径正确
    app_root = os.path.dirname(os.path.abspath(__file__))
    json_full_path = os.path.join(app_root, json_path)
    
    logger.info(f"尝试加载数据文件: {json_full_path}")
    if os.path.exists(json_full_path):
        try:
            with open(json_full_path, 'r', encoding='utf-8') as f:
                antibiotic_data = json.load(f)
            logger.info(f"数据加载成功，包含 {len(antibiotic_data.get('data', []))} 条记录")
            return True
        except Exception as e:
            logger.error(f"加载数据文件时出错: {str(e)}")
            antibiotic_data = None
            return False
    else:
        logger.error(f"警告：JSON数据文件不存在: {json_full_path}")
        antibiotic_data = None
        return False

# 主页路由
@app.route('/')
def index():
    return render_template('index.html')

# 新的细菌列表API端点（支持分页）
@app.route('/api/bacteria', methods=['GET'])
def get_bacteria():
    try:
        if antibiotic_data is None:
            logger.error("细菌列表API: 数据未加载")
            return jsonify({'success': False, 'error': '数据未加载'}), 500
        
        bacteria_list = [record.get('bacteria', '') for record in antibiotic_data.get('data', [])]
        
        logger.info(f"细菌列表API: 返回 {len(bacteria_list)} 种细菌")
        return jsonify({
            'success': True,
            'bacteria': bacteria_list,
            'total': len(bacteria_list)
        })
    except Exception as e:
        logger.error(f"细菌列表API出错: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '获取细菌列表时发生错误',
            'details': str(e) if app.config['DEBUG'] else None
        }), 500

# 单个药物详情API（适配前端需求）
@app.route('/api/drug/<int:drug_id>', methods=['GET'])
def get_drug_detail(drug_id):
    """获取单个药物的详细信息，包括对各种细菌的敏感性数据"""
    try:
        logger.info(f"获取药物详情API: ID={drug_id}")
        
        if antibiotic_data is None:
            logger.error("药物详情API: 数据未加载")
            return jsonify({'success': False, 'error': '数据未加载'}), 500
        
        # 获取所有药物列表并排序
        drug_set = set()
        for record in antibiotic_data.get('data', []):
            for drug in record.get('antibiotics', {}).keys():
                drug_set.add(drug)
        
        drug_list = list(drug_set)
        drug_list.sort()
        
        # 检查ID是否有效
        if drug_id < 1 or drug_id > len(drug_list):
            logger.warning(f"药物详情API: 无效的药物ID={drug_id}")
            return jsonify({'success': False, 'error': '药物不存在'}), 404
        
        # 获取对应ID的药物名称
        drug_name = drug_list[drug_id - 1]  # ID从1开始
        
        # 查找该药物的所有细菌敏感性数据
        bacteria_results = []
        for record in antibiotic_data.get('data', []):
            if drug_name in record.get('antibiotics', {}):
                bacteria_results.append({
                    'bacteria': record.get('bacteria'),
                    'sensitivity': record['antibiotics'][drug_name]
                })
        
        logger.info(f"药物详情API: 找到药物 '{drug_name}' 的 {len(bacteria_results)} 条数据")
        return jsonify({
            'success': True,
            'id': drug_id,
            'name': drug_name,
            'bacteria_results': bacteria_results
        })
    except Exception as e:
        logger.error(f"药物详情API出错: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '获取药物详情时发生错误',
            'details': str(e) if app.config['DEBUG'] else None
        }), 500

# 单个细菌详情API（适配前端需求）
@app.route('/api/bacteria/<int:bacteria_id>', methods=['GET'])
def get_bacteria_detail(bacteria_id):
    """获取单个细菌的详细信息，包括对各种抗生素的敏感性数据"""
    try:
        logger.info(f"获取细菌详情API: ID={bacteria_id}")
        
        if antibiotic_data is None:
            logger.error("细菌详情API: 数据未加载")
            return jsonify({'success': False, 'error': '数据未加载'}), 500
        
        data_records = antibiotic_data.get('data', [])
        
        # 检查ID是否有效
        if bacteria_id < 1 or bacteria_id > len(data_records):
            logger.warning(f"细菌详情API: 无效的细菌ID={bacteria_id}")
            return jsonify({'success': False, 'error': '细菌不存在'}), 404
        
        # 获取对应ID的细菌记录
        record = data_records[bacteria_id - 1]  # ID从1开始
        
        logger.info(f"细菌详情API: 找到细菌 '{record.get('bacteria')}' 的数据")
        return jsonify({
            'success': True,
            'id': bacteria_id,
            'bacteria': record.get('bacteria'),
            'antibiotics': record.get('antibiotics', {})
        })
    except Exception as e:
        logger.error(f"细菌详情API出错: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '获取细菌详情时发生错误',
            'details': str(e) if app.config['DEBUG'] else None
        }), 500

# 新的药物列表API端点（支持分页）
@app.route('/api/drugs', methods=['GET'])
def get_drugs():
    try:
        if antibiotic_data is None:
            logger.error("药物列表API: 数据未加载")
            return jsonify({'success': False, 'error': '数据未加载'}), 500
        
        # 统计所有药物种类
        drug_set = set()
        for record in antibiotic_data.get('data', []):
            for drug in record.get('antibiotics', {}).keys():
                drug_set.add(drug)
        
        drug_list = list(drug_set)
        drug_list.sort()  # 排序以便稳定输出
        
        # 简单实现，返回所有药物
        logger.info(f"药物列表API: 返回 {len(drug_list)} 种药物")
        return jsonify({
            'success': True,
            'drugs': drug_list,
            'total': len(drug_list)
        })
    except Exception as e:
        logger.error(f"药物列表API出错: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '获取药物列表时发生错误',
            'details': str(e) if app.config['DEBUG'] else None
        }), 500

# 按细菌搜索API
@app.route('/api/search/bacteria', methods=['GET'])
def search_by_bacteria():
    try:
        bacteria_name = request.args.get('name', '').strip()
        logger.info(f"接收到细菌搜索请求，搜索词: '{bacteria_name}'")
        
        if not bacteria_name:
            logger.warning("细菌搜索请求参数为空")
            return jsonify({'success': False, 'error': '请提供细菌名称'}), 400
        
        if antibiotic_data is None:
            logger.error("细菌搜索时数据未加载")
            return jsonify({'success': False, 'error': '数据未加载'}), 500
        
        # 转换搜索词为小写用于模糊匹配
        search_term_lower = bacteria_name.lower()
        
        # 在数据中查找对应的细菌，支持模糊匹配
        for record in antibiotic_data.get('data', []):
            record_bacteria = record.get('bacteria', '')
            # 去除换行符并转换为小写进行比较
            normalized_bacteria = record_bacteria.replace('\n', ' ').lower()
            search_term_normalized = search_term_lower.replace('\n', ' ')
            
            # 如果记录中的细菌名称包含搜索词，或者搜索词包含记录中的细菌名称（去除拉丁名部分）
            if search_term_normalized in normalized_bacteria or normalized_bacteria.split(' ')[0] in search_term_normalized:
                result = {
                    'success': True,
                    'bacteria': record_bacteria,
                    'antibiotics': record.get('antibiotics', {})
                }
                logger.info(f"找到细菌: '{record_bacteria}'，包含 {len(result['antibiotics'])} 条药敏数据")
                return jsonify(result)
        
        logger.info(f"未找到匹配的细菌: '{bacteria_name}'")
        return jsonify({'success': False, 'error': '未找到该细菌的记录'}), 404
    except Exception as e:
        logger.error(f"细菌搜索过程中出错: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '搜索过程中发生错误',
            'details': str(e) if app.config['DEBUG'] else None
        }), 500

# 按药物搜索API
@app.route('/api/search/drug', methods=['GET'])
def search_by_drug():
    try:
        drug_name = request.args.get('name', '').strip()
        logger.info(f"接收到药物搜索请求，搜索词: '{drug_name}'")
        
        if not drug_name:
            logger.warning("药物搜索请求参数为空")
            return jsonify({'success': False, 'error': '请提供药物名称'}), 400
        
        if antibiotic_data is None:
            logger.error("药物搜索时数据未加载")
            return jsonify({'success': False, 'error': '数据未加载'}), 500
        
        # 使用药物索引查找数据，确保按原始Excel从上到下的顺序返回结果
        if 'drug_indexed' in antibiotic_data and drug_name in antibiotic_data['drug_indexed']:
            # drug_indexed中的结果已经按照原始Excel中的细菌顺序存储
            results = antibiotic_data['drug_indexed'][drug_name]
            logger.info(f"通过索引找到药物: '{drug_name}'，包含 {len(results)} 条细菌敏感性数据")
            return jsonify({
                'success': True,
                'drug': drug_name,
                'bacteria_results': results
            })
        
        # 如果药物索引不存在，使用替代方法查找
        alternative_results = []
        for record in antibiotic_data.get('data', []):
            if drug_name in record.get('antibiotics', {}):
                alternative_results.append({
                    'bacteria': record.get('bacteria'),
                    'sensitivity': record['antibiotics'][drug_name]
                })
        
        if alternative_results:
            logger.info(f"通过替代方法找到药物: '{drug_name}'，包含 {len(alternative_results)} 条细菌敏感性数据")
            return jsonify({
                'success': True,
                'drug': drug_name,
                'bacteria_results': alternative_results
            })
        
        logger.info(f"未找到匹配的药物: '{drug_name}'")
        return jsonify({'success': False, 'error': '未找到该药物的记录'}), 404
    except Exception as e:
        logger.error(f"药物搜索过程中出错: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '搜索过程中发生错误',
            'details': str(e) if app.config['DEBUG'] else None
        }), 500

# 获取统计信息API
@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    try:
        if antibiotic_data is None:
            logger.error("统计信息API: 数据未加载")
            return jsonify({'success': False, 'error': '数据未加载'}), 500
        
        total_bacteria = len(antibiotic_data.get('data', []))
        bacteria_list = [record.get('bacteria', '') for record in antibiotic_data.get('data', [])]
        
        # 统计所有药物种类
        drug_set = set()
        for record in antibiotic_data.get('data', []):
            for drug in record.get('antibiotics', {}).keys():
                drug_set.add(drug)
        
        total_drugs = len(drug_set)
        drug_list = list(drug_set)
        
        logger.info(f"统计信息: {total_bacteria} 种细菌, {total_drugs} 种药物")
        return jsonify({
            'success': True,
            'total_bacteria': total_bacteria,
            'total_drugs': total_drugs,
            'bacteria_list': bacteria_list,
            'drug_list': drug_list
        })
    except Exception as e:
        logger.error(f"统计信息API出错: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': '获取统计信息时发生错误',
            'details': str(e) if app.config['DEBUG'] else None
        }), 500

# 兼容旧的统计信息API
@app.route('/api/stats', methods=['GET'])
def get_stats():
    if antibiotic_data:
        return jsonify({
            'success': True,
            'bacteria_count': len(antibiotic_data.get('bacteria_list', [])),
            'drug_count': len(antibiotic_data.get('drug_list', [])),
            'record_count': len(antibiotic_data.get('data', []))
        })
    else:
        return jsonify({'success': False, 'error': '数据未加载'})

# 比较多个细菌的API
@app.route('/api/compare/bacteria', methods=['GET'])
def compare_bacteria():
    # 获取查询参数中的细菌名称列表
    bacteria_names = request.args.getlist('name')
    
    if not bacteria_names or len(bacteria_names) < 2:
        return jsonify({'success': False, 'error': '请至少提供两个细菌名称'})
    
    if not antibiotic_data:
        return jsonify({'success': False, 'error': '数据未加载'})
    
    results = {
        'success': True,
        'bacteria': [],  # 将在下面填充找到的实际细菌名称
        'comparison_data': []
    }
    
    # 收集所有涉及的药物
    all_drugs = set()
    bacteria_data = {}
    found_bacteria_names = []  # 存储找到的实际细菌名称
    
    # 为每个细菌获取数据
    for bacteria_name in bacteria_names:
        search_term_lower = bacteria_name.lower()
        found = False
        
        for record in antibiotic_data.get('data', []):
            record_bacteria = record.get('bacteria', '')
            normalized_bacteria = record_bacteria.replace('\n', ' ').lower()
            
            if search_term_lower in normalized_bacteria or normalized_bacteria.split(' ')[0] in search_term_lower:
                bacteria_data[record_bacteria] = record.get('antibiotics', {})
                found_bacteria_names.append(record_bacteria)  # 添加找到的实际细菌名称
                # 添加所有药物到集合
                for drug in record.get('antibiotics', {}).keys():
                    all_drugs.add(drug)
                found = True
                break
        
        if not found:
            # 如果找不到某个细菌，返回错误信息
            return jsonify({'success': False, 'error': f'未找到细菌 "{bacteria_name}" 的记录'})
    
    # 更新results中的细菌名称列表为找到的实际名称
    results['bacteria'] = found_bacteria_names
    
    # 构建比较数据
    # 按照原始药物列表顺序
    for drug in antibiotic_data.get('drug_list', []):
        if drug in all_drugs:
            drug_data = {'drug': drug, 'bacteria_results': {}}
            for bacteria in found_bacteria_names:  # 使用找到的实际细菌名称
                if bacteria in bacteria_data and drug in bacteria_data[bacteria]:
                    drug_data['bacteria_results'][bacteria] = bacteria_data[bacteria][drug]
                else:
                    drug_data['bacteria_results'][bacteria] = '未知'
            results['comparison_data'].append(drug_data)
    
    return jsonify(results)

# 比较多个药物的API
@app.route('/api/compare/drug', methods=['GET'])
def compare_drugs():
    # 获取查询参数中的药物名称列表
    drug_names = request.args.getlist('name')
    
    if not drug_names or len(drug_names) < 2:
        return jsonify({'success': False, 'error': '请至少提供两个药物名称'})
    
    if not antibiotic_data:
        return jsonify({'success': False, 'error': '数据未加载'})
    
    results = {
        'success': True,
        'drugs': drug_names,
        'comparison_data': []
    }
    
    # 收集所有涉及的细菌
    all_bacteria = set()
    
    # 为每个药物获取数据
    for drug_name in drug_names:
        if 'drug_indexed' in antibiotic_data and drug_name in antibiotic_data['drug_indexed']:
            for record in antibiotic_data['drug_indexed'][drug_name]:
                all_bacteria.add(record['bacteria'])
    
    # 构建比较数据
    for bacteria in antibiotic_data.get('bacteria_list', []):
        if bacteria in all_bacteria:
            bacteria_data = {'bacteria': bacteria, 'drug_results': {}}
            
            # 为每个药物查找对该细菌的敏感性
            for drug in drug_names:
                bacteria_data['drug_results'][drug] = '未知'
                
                # 在drug_indexed中查找
                if 'drug_indexed' in antibiotic_data and drug in antibiotic_data['drug_indexed']:
                    for record in antibiotic_data['drug_indexed'][drug]:
                        if record['bacteria'] == bacteria:
                            bacteria_data['drug_results'][drug] = record['sensitivity']
                            break
                
                # 如果在drug_indexed中找不到，在原始数据中查找
                if bacteria_data['drug_results'][drug] == '未知':
                    for record in antibiotic_data.get('data', []):
                        if record.get('bacteria') == bacteria and drug in record.get('antibiotics', {}):
                            bacteria_data['drug_results'][drug] = record['antibiotics'][drug]
                            break
            
            results['comparison_data'].append(bacteria_data)
    
    return jsonify(results)

# API端点已在文件前面部分定义，此处不再重复定义

# 全局错误处理
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"未捕获的异常: {str(e)}", exc_info=True)
    return jsonify({
        'success': False,
        'error': '服务器内部错误',
        'details': str(e) if app.config['DEBUG'] else None
    }), 500

# 健康检查端点
@app.route('/api/health', methods=['GET'])
def health_check():
    """应用健康检查端点，用于监控系统状态"""
    try:
        data_loaded = antibiotic_data is not None
        status = 'healthy' if data_loaded else 'degraded'
        
        return jsonify({
            'status': status,
            'data_loaded': data_loaded,
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        }), 200 if data_loaded else 503
    except Exception as e:
        logger.error(f"健康检查失败: {str(e)}")
        return jsonify({
            'status': 'unhealthy',
            'error': '服务不可用'
        }), 503

# 全局404错误处理
@app.errorhandler(404)
def not_found(error):
    """处理所有未找到的路由请求"""
    logger.warning(f"未找到的API端点: {request.path}")
    return jsonify({
        'success': False,
        'error': '请求的资源不存在',
        'endpoint': request.path,
        'method': request.method
    }), 404

# 全局400错误处理
@app.errorhandler(400)
def bad_request(error):
    """处理请求参数错误"""
    logger.warning(f"请求参数错误: {str(error)}")
    return jsonify({
        'success': False,
        'error': '请求参数错误',
        'details': str(error) if app.config['DEBUG'] else None
    }), 400

# 全局500错误处理
@app.errorhandler(Exception)
def internal_error(error):
    """处理所有服务器内部错误"""
    logger.error(f"服务器内部错误: {str(error)}", exc_info=True)
    return jsonify({
        'success': False,
        'error': '服务器内部错误',
        'details': str(error) if app.config['DEBUG'] else None
    }), 500

# 请求前处理
@app.before_request
def log_request_info():
    """记录每个API请求的详细信息"""
    logger.info(f"接收到请求: {request.method} {request.path}")
    logger.debug(f"请求参数: {dict(request.args)}")

# 响应后处理
@app.after_request
def after_request(response):
    """在每个API响应后添加必要的头信息并记录响应状态"""
    # 添加安全相关的头信息
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    
    # 记录响应状态
    if response.status_code >= 400:
        logger.warning(f"请求响应: {request.path} {response.status_code}")
    else:
        logger.debug(f"请求响应: {request.path} {response.status_code}")
        
    return response

# 已在前面定义了before_request，这里省略重复的定义
def before_request():
    logger.info(f"接收到请求: {request.method} {request.path}")
    # 检查数据是否已加载，如果未加载则尝试加载
    global antibiotic_data
    if antibiotic_data is None:
        load_data()

# 应用启动时加载数据
# 支持通过WSGI服务器启动（如Gunicorn、uWSGI等）
# 初始化时加载数据
load_data()

# WSGI入口点 - 用于生产环境部署
gunicorn_app = app

# 直接运行时的配置
if __name__ == '__main__':
    try:
        # 启动前加载数据
        load_data()
        
        # 获取环境变量中的配置
        port = int(os.environ.get('PORT', 5000))
        debug_mode = os.environ.get('DEBUG', 'False').lower() == 'true'
        
        logger.info(f"启动抗生素查询服务，端口: {port}, 调试模式: {debug_mode}")
        logger.info(f"数据加载完成，共 {len(antibiotic_data.get('data', [])) if antibiotic_data else 0} 种细菌")
        
        # 启动Flask应用 - 生产环境配置增强
        app.run(
            debug=debug_mode,
            host='0.0.0.0',
            port=port,
            threaded=True,
            processes=1,
            use_reloader=debug_mode
        )
    except Exception as e:
        logger.critical(f"应用启动失败: {str(e)}", exc_info=True)
        raise
