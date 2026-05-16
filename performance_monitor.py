"""
性能监控工具
用于查看 API 调用和 AI 决策的优化效果
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any
from ai_client_optimized import get_optimized_client
from ai_priority_manager_optimized import OptimizedAIPriorityManager


class PerformanceMonitor:
    """性能监控器"""
    
    def __init__(self):
        self.client = get_optimized_client()
        self.start_time = time.time()
    
    def get_api_stats(self) -> Dict[str, Any]:
        """获取 API 调用统计"""
        stats = self.client.get_performance_stats()
        
        return {
            "连接池统计": stats["connection_pool"],
            "请求队列状态": stats["request_queue"],
            "运行时间": f"{time.time() - self.start_time:.2f} 秒"
        }
    
    def get_priority_stats(self, priority_manager: OptimizedAIPriorityManager) -> Dict[str, Any]:
        """获取优先级管理器统计"""
        return priority_manager.get_stats()
    
    def print_report(self, priority_manager: OptimizedAIPriorityManager = None):
        """打印性能报告"""
        print("\n" + "="*60)
        print("🚀 性能监控报告")
        print("="*60)
        
        # API 统计
        api_stats = self.get_api_stats()
        print("\n📊 API 调用统计:")
        print(f"  总请求数: {api_stats['连接池统计']['total_requests']}")
        print(f"  成功请求: {api_stats['连接池统计']['successful_requests']}")
        print(f"  失败请求: {api_stats['连接池统计']['failed_requests']}")
        print(f"  平均响应时间: {api_stats['连接池统计']['avg_time']:.2f} 秒")
        print(f"  活跃请求数: {api_stats['请求队列状态']['active_requests']}")
        
        # 优先级管理器统计
        if priority_manager:
            priority_stats = self.get_priority_stats(priority_manager)
            print("\n🎯 AI 决策统计:")
            print(f"  总请求数: {priority_stats['total_requests']}")
            print(f"  缓存命中: {priority_stats['cache_hits']}")
            print(f"  缓存命中率: {priority_stats['cache_hit_rate']:.1f}%")
            print(f"  AI 调用次数: {priority_stats['ai_calls']}")
            print(f"  平均响应时间: {priority_stats['avg_response_time']:.2f} 秒")
            print(f"  节省 Token 数: {priority_stats['total_tokens_saved']}")
        
        print("\n" + "="*60)
    
    def export_report(self, priority_manager: OptimizedAIPriorityManager = None) -> Dict:
        """导出报告为 JSON"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "api_stats": self.get_api_stats()
        }
        
        if priority_manager:
            report["priority_stats"] = self.get_priority_stats(priority_manager)
        
        return report


def compare_performance():
    """对比优化前后的性能"""
    from ai_client import call_ai as call_ai_old
    from ai_client_optimized import call_ai_optimized
    import time
    
    test_messages = [
        {"role": "user", "content": "测试消息 1"}
    ]
    
    print("\n🔬 性能对比测试")
    print("="*60)
    
    # 测试旧版
    print("\n测试旧版 API 调用...")
    start_old = time.time()
    result_old = call_ai_old(test_messages)
    time_old = time.time() - start_old
    
    # 测试新版
    print("测试优化版 API 调用...")
    start_new = time.time()
    result_new = call_ai_optimized(test_messages)
    time_new = time.time() - start_new
    
    print("\n📈 对比结果:")
    print(f"  旧版耗时: {time_old:.2f} 秒")
    print(f"  优化版耗时: {time_new:.2f} 秒")
    print(f"  性能提升: {((time_old - time_new) / time_old * 100):.1f}%")
    print("="*60)


if __name__ == "__main__":
    # 示例用法
    monitor = PerformanceMonitor()
    
    # 模拟一些请求
    print("正在进行测试请求...")
    client = get_optimized_client()
    
    for i in range(3):
        result = client.call_ai([{"role": "user", "content": f"测试消息 {i+1}"}])
        if result:
            print(f"  请求 {i+1} 成功")
        time.sleep(0.5)
    
    # 打印报告
    monitor.print_report()
    
    # 导出报告
    report = monitor.export_report()
    print("\n📄 导出的 JSON 报告:")
    print(json.dumps(report, indent=2, ensure_ascii=False))
