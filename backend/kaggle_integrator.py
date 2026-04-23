"""
EWI EasyPlay - Kaggle 數據集集成
從 Kaggle 下載和處理音頻數據集
"""

import os
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Optional
import json

logger = logging.getLogger(__name__)


class KaggleIntegrator:
    """Kaggle 數據集集成"""
    
    def __init__(self, cache_dir: Path = None):
        """
        初始化 Kaggle 集成
        
        Args:
            cache_dir: 緩存目錄（預設 ./data/kaggle）
        """
        self.cache_dir = cache_dir or Path("data") / "kaggle"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 檢查 Kaggle API 是否配置
        self.kaggle_config = Path.home() / ".kaggle" / "kaggle.json"
        self.api = None
        self._init_kaggle_api()
    
    def _init_kaggle_api(self):
        """初始化 Kaggle API 客戶端"""
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi
            
            if not self.kaggle_config.exists():
                logger.warning(f"Kaggle 配置未找到: {self.kaggle_config}")
                logger.info("請設置 Kaggle API 密鑰：")
                logger.info("1. 訪問 https://www.kaggle.com/settings/account")
                logger.info("2. 點擊 'Create New Token' 下載 kaggle.json")
                logger.info(f"3. 放置到 {self.kaggle_config}")
                return False
            
            self.api = KaggleApi()
            self.api.authenticate()
            logger.info("✓ Kaggle API 已認證")
            return True
        
        except ImportError:
            logger.error("kaggle 未安裝")
            return False
        except Exception as e:
            logger.error(f"Kaggle API 初始化失敗: {str(e)}")
            return False
    
    async def search_datasets(self, query: str, limit: int = 5) -> List[Dict]:
        """搜尋 Kaggle 數據集"""
        try:
            if not self.api:
                logger.warning("Kaggle API 未配置，返回演示數據")
                return self._get_demo_datasets(query, limit)
            
            logger.info(f"搜尋 Kaggle 數據集: {query}")
            
            # 在線程中運行 API 調用（非阻塞）
            loop = asyncio.get_event_loop()
            
            def search_impl():
                datasets = self.api.dataset_list(search=query, max_size=limit * 10)
                results = []
                for ds in list(datasets)[:limit]:
                    results.append({
                        'ref': ds.ref,
                        'title': ds.title,
                        'size': getattr(ds, 'size', 'Unknown'),
                        'downloads': getattr(ds, 'downloadCount', 0),
                        'score': getattr(ds, 'currentDatasetVersionNumber', 0),
                        'url': f'https://www.kaggle.com/datasets/{ds.ref}'
                    })
                return results
            
            datasets = await loop.run_in_executor(None, search_impl)
            logger.info(f"找到 {len(datasets)} 個數據集")
            return datasets
        
        except Exception as e:
            logger.error(f"搜尋數據集失敗: {str(e)}")
            return self._get_demo_datasets(query, limit)
    
    async def download_dataset(self, dataset_ref: str, task_manager=None, task_id: str = None) -> Optional[str]:
        """
        下載 Kaggle 數據集
        
        Args:
            dataset_ref: 數據集參考 (e.g., 'user/dataset-name')
            task_manager: 任務管理器（用於進度更新）
            task_id: 任務 ID
        
        Returns:
            下載的數據集路徑
        """
        try:
            if task_manager and task_id:
                task_manager.update_task(task_id, 
                    current_step=f"從 Kaggle 下載數據集: {dataset_ref}...", 
                    progress=10
                )
            
            if not self.api:
                logger.warning("Kaggle API 未配置")
                raise Exception("Kaggle API 未配置，請設置 ~/.kaggle/kaggle.json")
            
            # 檢查是否已緩存
            dataset_path = self.cache_dir / dataset_ref.replace('/', '_')
            if dataset_path.exists():
                logger.info(f"✓ 使用緩存的數據集: {dataset_path}")
                if task_manager and task_id:
                    task_manager.update_task(task_id, progress=50)
                return str(dataset_path)
            
            logger.info(f"下載數據集: {dataset_ref}")
            
            # 在線程中下載（非阻塞）
            loop = asyncio.get_event_loop()
            
            def download_impl():
                self.api.dataset_download_files(
                    dataset_ref,
                    path=str(self.cache_dir),
                    unzip=True
                )
                return dataset_path
            
            result = await loop.run_in_executor(None, download_impl)
            
            if task_manager and task_id:
                task_manager.update_task(task_id, progress=80)
            
            logger.info(f"✓ 數據集已下載: {result}")
            return str(result)
        
        except Exception as e:
            logger.error(f"下載數據集失敗: {str(e)}")
            if task_manager and task_id:
                task_manager.fail_task(task_id, f"下載失敗: {str(e)}")
            raise
    
    async def get_popular_music_datasets(self) -> List[Dict]:
        """獲取流行的音樂數據集"""
        try:
            popular_datasets = [
                'freemusictechstuff/free-music-archive',
                'titansong/free-music-archive-metadata',
                'insiyonu/musicfeatures',
                'mirnavakili/spotify-artists',
                'edumucelli/spotify-20k-songs'
            ]
            
            results = []
            if not self.api:
                logger.info("使用預定義的流行音樂數據集列表")
                for ds_ref in popular_datasets[:3]:
                    results.append({
                        'ref': ds_ref,
                        'title': ds_ref.split('/')[-1],
                        'score': 0,
                        'url': f'https://www.kaggle.com/datasets/{ds_ref}'
                    })
                return results
            
            for ds_ref in popular_datasets:
                try:
                    ds_info = await self.search_datasets(ds_ref.split('/')[-1], limit=1)
                    if ds_info:
                        results.append(ds_info[0])
                except:
                    pass
            
            return results if results else await self.search_datasets('music', limit=5)
        
        except Exception as e:
            logger.error(f"獲取流行音樂數據集失敗: {str(e)}")
            return self._get_demo_datasets('music', 5)
    
    @staticmethod
    def _get_demo_datasets(query: str, limit: int = 5) -> List[Dict]:
        """返回演示數據集"""
        demo_datasets = [
            {
                'ref': 'freemusictechstuff/free-music-archive',
                'title': 'Free Music Archive Metadata',
                'size': '1.2 GB',
                'downloads': 5000,
                'score': 9.2,
                'url': 'https://www.kaggle.com/datasets/freemusictechstuff/free-music-archive'
            },
            {
                'ref': 'insiyonu/musicfeatures',
                'title': 'Music Features Dataset',
                'size': '500 MB',
                'downloads': 2000,
                'score': 8.5,
                'url': 'https://www.kaggle.com/datasets/insiyonu/musicfeatures'
            },
            {
                'ref': 'edumucelli/spotify-20k-songs',
                'title': 'Spotify 20K Songs Dataset',
                'size': '800 MB',
                'downloads': 8000,
                'score': 9.1,
                'url': 'https://www.kaggle.com/datasets/edumucelli/spotify-20k-songs'
            },
            {
                'ref': 'mirnavakili/spotify-artists',
                'title': 'Spotify Artists Dataset',
                'size': '300 MB',
                'downloads': 3000,
                'score': 8.8,
                'url': 'https://www.kaggle.com/datasets/mirnavakili/spotify-artists'
            },
            {
                'ref': 'titansong/free-music-archive-metadata',
                'title': 'FMA Metadata Extended',
                'size': '1.5 GB',
                'downloads': 4000,
                'score': 9.0,
                'url': 'https://www.kaggle.com/datasets/titansong/free-music-archive-metadata'
            }
        ]
        
        # 過濾匹配查詢的數據集
        if query.lower() != 'all':
            filtered = [ds for ds in demo_datasets if query.lower() in ds['title'].lower()]
            return filtered[:limit] if filtered else demo_datasets[:limit]
        
        return demo_datasets[:limit]
