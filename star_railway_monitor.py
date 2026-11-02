"""
主程序入口
"""

from i18n import t, normalize_language
from module_types import display_attr, display_module, display_category

import json
import logging
import time
import threading
import argparse
import os
import sys
import multiprocessing as mp
from typing import Dict, List, Optional, Any
from logging_config import setup_logging, get_logger
from module_parser import ModuleParser
from module_types import ModuleInfo, normalize_attribute_list, normalize_attribute_name, normalize_category
from packet_capture import PacketCapture
from network_interface_util import get_network_interfaces, select_network_interface
from BlueProtobuf_pb2 import CharSerialize

# 多进程保护
_is_main_process = mp.current_process().name == 'MainProcess'

# 获取日志器
logger = get_logger(__name__) if _is_main_process else None




def get_exec_base_dir() -> str:
    """获取可执行文件所在目录或源码所在目录"""
    try:
        if getattr(sys, 'frozen', False):
            return os.path.dirname(sys.executable)
    except Exception:
        pass
    return os.path.dirname(os.path.abspath(__file__))


class StarResonanceMonitor:
    """星痕共鸣监控器"""
    
    def __init__(self, interface_index: int = None, category: str = "全部", attributes: List[str] = None,
                 exclude_attributes: List[str] = None, match_count: int = 1, enumeration_mode: bool = False,
                 min_attr_sum: dict | None = None, combination_size: int = 4, lang: str = 'en'):
        """
        初始化监控器
        
        Args:
            interface_index: 网络接口索引
            category: 模组类型（攻击/守护/辅助/全部）
            attributes: 要筛选的属性词条列表
            exclude_attributes: 要排除的属性词条列表
            match_count: 模组需要包含的指定词条数量
            enumeration_mode: 是否启用枚举模式
            min_attr_sum: 强制某属性在组合中的总和≥VALUE的字典
        """
        self.interface_index = interface_index
        self.category = category
        self.attributes = attributes or []
        self.exclude_attributes = exclude_attributes or []
        self.match_count = match_count
        self.min_attr_sum = min_attr_sum or {}
        self.enumeration_mode = enumeration_mode
        self.combination_size = combination_size
        self.lang = normalize_language(lang)
        self.is_running = False
        
        # 获取网络接口信息
        self.interfaces = get_network_interfaces(lang=self.lang)
        if interface_index is not None and 0 <= interface_index < len(self.interfaces):
            self.selected_interface = self.interfaces[interface_index]
        else:
            self.selected_interface = None
            
        # 初始化组件
        interface_name = self.selected_interface['name'] if self.selected_interface else None
        self.packet_capture = PacketCapture(interface_name, lang=self.lang)
        self.module_parser = ModuleParser(lang=self.lang)
        
        # 统计数据
        self.stats = {
            'total_packets': 0,
            'sync_container_packets': 0,
            'parsed_modules': 0,
            'players_found': 0,
            'start_time': None
        }
        
        # 存储解析结果
        self.player_modules = {}  # 玩家UID -> 模组列表
        self.module_history = []  # 模组历史记录
        
    def start_monitoring(self):
        """开始监控"""
        self.is_running = True
        self.stats['start_time'] = time.time()
        
        logger.info(t(self.lang, '=== Star Resonance Monitor Started ===', zh='=== 星痕共鸣监控器启动 ==='))
        cat_disp = self.category if self.lang == 'zh' else display_category(self.category, lang=self.lang)
        logger.info(t(self.lang, 'Module Category: {p0}', zh=f'模组类型: {self.category}', p0=cat_disp))
        if self.attributes:
            attrs_disp = self.attributes if self.lang == 'zh' else [display_attr(a, lang=self.lang) for a in self.attributes]
            logger.info(t(self.lang, 'Attributes: {p0} (require {p1})', zh=f"属性筛选: {', '.join(self.attributes)} (需要包含{self.match_count}个)", p0=', '.join(attrs_disp), p1=self.match_count))
        else:
            logger.info(t(self.lang, 'Attributes: None (use all modules)', zh='属性筛选: 无 (使用所有模组)'))
        if self.exclude_attributes:
            ex_disp = self.exclude_attributes if self.lang == 'zh' else [display_attr(a, lang=self.lang) for a in self.exclude_attributes]
            logger.info(t(self.lang, 'Exclude Attributes: {p0}', zh=f"排除属性: {', '.join(self.exclude_attributes)}", p0=', '.join(ex_disp)))
        if self.selected_interface:
            logger.info(t(self.lang, 'Network Interface: {p0} - {p1}', zh=f"网络接口: {self.interface_index} - {self.selected_interface['description']}", p0=self.interface_index, p1=self.selected_interface['description']))
            logger.info(t(self.lang, 'Interface Name: {p0}', zh=f"接口名称: {self.selected_interface['name']}", p0=self.selected_interface['name']))
            addresses = [addr['addr'] for addr in self.selected_interface['addresses']]
            logger.info(t(self.lang, 'Interface Addresses: {p0}', zh=f"接口地址: {', '.join(addresses)}", p0=', '.join(addresses)))
        else:
            logger.info(t(self.lang, 'Network Interface: Auto', zh='网络接口: 自动'))
        
        # 启动抓包
        self.packet_capture.start_capture(self._on_sync_container_data)
        
        
        logger.info(t(self.lang, 'Monitoring started, waiting for module packets. Please relogin and select character... (Will exit after parsing)', zh='监控已启动，等待模组数据包, 请重新登录选择角色... (解析完成后将自动退出)'))
        
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        self.packet_capture.stop_capture()
        
        logger.info(t(self.lang, '=== Monitoring Stopped ===', zh='=== 监控已停止 ==='))
        
    def _on_sync_container_data(self, data: Dict[str, Any]):
        """处理SyncContainerData数据包"""
        self.stats['sync_container_packets'] += 1
        
        try:
            # 解析模组信息
            v_data = data.get('v_data')
            if v_data:
                # 捕获后立即保存为最新离线数据
                try:
                    base_dir = get_exec_base_dir()
                    vdata_path = os.path.join(base_dir, 'modules.vdata')
                    with open(vdata_path, 'wb') as f:
                        f.write(v_data.SerializeToString())
                    logger.info(t(self.lang, 'Saved module data to: {p0}', zh=f'已保存模组数据到: {vdata_path}', p0=vdata_path))
                except Exception as e:
                    logger.warning(t(self.lang, 'Failed to save module data: {p0}', zh=f'保存模组数据失败: {e}', p0=e))

                self.module_parser.parse_module_info(
                    v_data=v_data, 
                    category=self.category, 
                    attributes=self.attributes, 
                    exclude_attributes=self.exclude_attributes,
                    match_count=self.match_count,
                    enumeration_mode=self.enumeration_mode,
                    min_attr_sum=self.min_attr_sum,
                    combination_size=self.combination_size
                )
                    
        except Exception as e:
            logger.error(t(self.lang, 'Failed to process SyncContainerData packet: {p0}', zh=f'处理SyncContainerData数据包失败: {e}', p0=e))
            

            

def parse_args(argv=None):
    """Read the language before constructing help, independent of flag order."""
    language_parser = argparse.ArgumentParser(add_help=False, allow_abbrev=False)
    language_parser.add_argument('--lang', '-lang', default='en', type=str.lower,
                                 choices=('en', 'ja', 'zh'))
    language_args, _ = language_parser.parse_known_args(argv)
    lang = language_args.lang
    parser = argparse.ArgumentParser(
        description=t(lang, 'Star Resonance Module Filter', zh='星痕共鸣模组筛选器'),
        parents=[language_parser], allow_abbrev=False, add_help=False)
    parser.add_argument('-h', '--help', action='help', help=t(lang, 'Show this help message and exit', zh='显示帮助并退出'))
    parser.add_argument('--interface', '-i', type=int, help=t(lang, 'Network interface index', zh='网络接口索引'))
    parser.add_argument('--debug', '-d', action='store_true', help=t(lang, 'Enable debug logging', zh='启用调试模式'))
    parser.add_argument('--auto', '-a', action='store_true', help=t(lang, 'Auto-detect the default network interface', zh='自动检测默认网络接口'))
    parser.add_argument('--list', '-l', action='store_true', help=t(lang, 'List network interfaces', zh='列出所有网络接口'))
    parser.add_argument('--category', '-c', default='all', help=t(lang, 'Module category: attack/guardian/support/all (also accepts Japanese and Chinese)', zh='模组类型: 攻击/守护/辅助/全部'))
    parser.add_argument('--attributes', '-attr', nargs='+', help=t(lang, 'Target attributes (quote names containing spaces)', zh='指定要筛选的属性词条'))
    parser.add_argument('--exclude-attributes', '-exattr', nargs='+', help=t(lang, 'Attributes excluded from scoring', zh='指定计分时排除的属性词条'))
    parser.add_argument('--match-count', '-mc', type=int, default=1, help=t(lang, 'Minimum matching attributes per module (default: 1)', zh='模组需要包含的指定词条数量 (默认: 1)'))
    parser.add_argument('--combination-size', '-cs', type=int, default=4, choices=[4, 5], help=t(lang, 'Modules per combination (default: 4)', zh='组合模组数量 (默认: 4)'))
    parser.add_argument('--min-attr-sum', '-mas', nargs=2, action='append', metavar=('ATTR','VALUE'), help=t(lang, 'Require total attribute value >= VALUE; repeatable', zh='指定属性总和下限；可多次使用'))
    parser.add_argument('--enumeration-mode', '-enum', action='store_true', help=t(lang, 'Use enumeration search', zh='启用枚举模式'))
    parser.add_argument('--load-vdata', '-lv', action='store_true', help=t(lang, 'Load modules.vdata from the program directory without capturing packets', zh='从程序目录读取 modules.vdata，跳过抓包'))
    parser._option_string_actions['--lang'].help = t(lang, 'Output language: en/ja/zh (default: en)', zh='输出语言: en/ja/zh (默认: en)')
    return parser.parse_args(argv)


def main():
    """Run the command line application."""
    args = parse_args()
    lang = args.lang

    # 归一化输入
    category_cn = normalize_category(args.category)
    attributes_cn = normalize_attribute_list(args.attributes)
    exclude_attributes_cn = normalize_attribute_list(args.exclude_attributes)

    min_attr_sum = {}
    if args.min_attr_sum:
        for name, val in args.min_attr_sum:
            try:
                min_attr_sum[normalize_attribute_name(name)] = int(val)
            except Exception:
                if lang != 'zh':
                    print(t(lang, '[WARN] Invalid -mas threshold: {p0} {p1} (must be integer)', p0=name, p1=val))
                else:
                    print(f"[WARN] 无效的 -mas 阈值：{name} {val}（应为整数）")
    
    # 设置日志系统
    setup_logging(debug_mode=args.debug, lang=lang)

    # --load-vdata 分支
    if args.load_vdata:
        base_dir = get_exec_base_dir()
        vdata_path = os.path.join(base_dir, 'modules.vdata')
        if not os.path.exists(vdata_path):
            logger.error(t(lang, 'Offline data file not found: {p0}', zh=f'找不到离线数据文件: {vdata_path}', p0=vdata_path))
            sys.exit(1)
        try:
            with open(vdata_path, 'rb') as f:
                data_bytes = f.read()
            char_serialize = CharSerialize()
            char_serialize.ParseFromString(data_bytes)
        except Exception as e:
            logger.error(t(lang, 'Failed to read or parse offline data: {p0}', zh=f'读取或解析离线数据失败: {e}', p0=e))
            sys.exit(1)

        try:
            ModuleParser(lang=lang).parse_module_info(
                v_data=char_serialize,
                category=category_cn,
                attributes=attributes_cn,
                exclude_attributes=exclude_attributes_cn,
                match_count=args.match_count,
                enumeration_mode=args.enumeration_mode,
                min_attr_sum=min_attr_sum,
                combination_size=args.combination_size
            )
        except SystemExit:
            raise
        except Exception as e:
            logger.error(t(lang, 'Offline computation failed: {p0}', zh=f'离线计算失败: {e}', p0=e))
            sys.exit(1)

        sys.exit(0)
        
    # 获取网络接口列表
    interfaces = get_network_interfaces(lang=lang)
    
    if not interfaces:
        logger.error(t(lang, 'No available network interfaces found!', zh='未找到可用的网络接口!'))
        return
        
    # 列出网络接口
    if args.list:
        print(t(lang, '=== Available Network Interfaces ===', zh='=== 可用的网络接口 ==='))
        for i, interface in enumerate(interfaces):
            name = interface['name']
            description = interface.get('description', name)
            is_up = "✓" if interface.get('is_up', False) else "✗"
            addresses = [addr['addr'] for addr in interface['addresses']]
            addr_str = ", ".join(addresses) if addresses else t(lang, 'No IP addresses', zh='无IP地址')
            
            print(t(lang, '  {p0:2d}. {p1} {p2}', p0=i, p1=is_up, p2=description))
            print(t(lang, '      Addresses: {p0}', zh=f'      地址: {addr_str}', p0=addr_str))
            print(t(lang, '      Name: {p0}', zh=f'      名称: {name}', p0=name))
            print()
        return
        
    # 确定要使用的接口
    interface_index = None
    
    if args.auto:
        # 自动检测默认接口
        print(t(lang, 'Auto-detecting default network interface...', zh='自动检测默认网络接口...'))
        interface_index = select_network_interface(interfaces, auto_detect=True, lang=lang)
        if interface_index is None:
            logger.error(t(lang, 'Default network interface not found!', zh='未找到默认网络接口!'))
            return
    elif args.interface is not None:
        # 使用指定的接口索引
        if 0 <= args.interface < len(interfaces):
            interface_index = args.interface
        else:
            logger.error(t(lang, 'Invalid interface index: {p0}', zh=f'无效的接口索引: {args.interface}', p0=args.interface))
            return
    else:
        # 交互式选择
        print(t(lang, 'Star Resonance Module Filter!', zh='星痕共鸣模组筛选器!'))
        print(t(lang, 'Version: V1.7', zh='版本: V1.7'))
        print(t(lang, 'GitHub: https://github.com/fudiyangjin/StarResonanceAutoMod'))
        print()
        
        interface_index = select_network_interface(interfaces, lang=lang)
        if interface_index is None:
            logger.error(t(lang, 'No network interface selected!', zh='未选择网络接口!'))
            return
            
    # 创建监控器
    monitor = StarResonanceMonitor(
        interface_index=interface_index,
        category=category_cn,
        attributes=attributes_cn,
        exclude_attributes=exclude_attributes_cn,
        match_count=args.match_count,
        enumeration_mode=args.enumeration_mode,
        min_attr_sum=min_attr_sum,
        combination_size=args.combination_size,
        lang=lang
    )
    
    try:
        # 启动监控
        monitor.start_monitoring()
        
        # 等待模组解析完成
        logger.info(t(lang, 'Waiting for module packets... (Will exit after parsing)', zh='等待模组数据包... (解析完成后将自动退出)'))
        
        while monitor.is_running:
            time.sleep(0.1)  # 更频繁的检查，减少延迟
            
    except KeyboardInterrupt:
        logger.info(t(lang, 'Stop signal received', zh='收到停止信号'))
    finally:
        if monitor.is_running:
            monitor.stop_monitoring()


if __name__ == "__main__":
    # 多进程打包支持
    mp.freeze_support()
    main()
