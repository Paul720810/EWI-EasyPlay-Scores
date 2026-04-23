"""
EWI EasyPlay Services Package
導出所有服務類和實例
"""

# 由於存在 services.py 模塊，Python 會優先使用 services/ 包
# 因此需要在這裡导入並重新導出所有服務

try:
    # 嘗試從根目錄的 services.py 導入
    import sys
    from pathlib import Path
    parent_dir = Path(__file__).parent.parent
    sys.path.insert(0, str(parent_dir))
    
    from importlib.util import spec_from_file_location, module_from_spec
    spec = spec_from_file_location("_services_module", str(parent_dir / "services.py"))
    services_module = module_from_spec(spec)
    spec.loader.exec_module(services_module)
    
    TaskManager = services_module.TaskManager
    YouTubeDownloader = services_module.YouTubeDownloader
    AudioAnalyzer = services_module.AudioAnalyzer
    JianguGenerator = services_module.JianguGenerator
    EWIFingeringAlgorithm = services_module.EWIFingeringAlgorithm
    MIDIGenerator = services_module.MIDIGenerator
    SpotifyIntegrator = services_module.SpotifyIntegrator
    
except Exception as e:
    # 如果無法導入，定義占位符
    import logging
    logging.warning(f"無法導入服務: {e}")

__all__ = [
    'TaskManager',
    'YouTubeDownloader',
    'AudioAnalyzer',
    'JianguGenerator',
    'EWIFingeringAlgorithm',
    'MIDIGenerator',
    'SpotifyIntegrator',
]
