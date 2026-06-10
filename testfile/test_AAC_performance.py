# test_AAC_performance.py - AAC 性能对比测试
# 测试原版 AAC.py 与优化版 AACOps.py 的性能差距
#
# 运行方式：
#   MicroPython: import test_AAC_performance
#   CPython:     python test_AAC_performance.py

import time
import math
import sys
import os

# MicroPython 兼容性处理
try:
    # 标准 Python
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except (AttributeError, TypeError):
    # MicroPython - 添加项目根目录到路径
    # 目录结构: / -> domain/, testfile/
    sys.path.insert(0, '/')

# 导入原版和优化版
import domain.AAC as AAC_original
import domain.AACOps as AAC_optimized


def get_time_ms():
    """获取当前时间（毫秒）"""
    return time.time() * 1000


def test_correctness():
    """测试正确性：对比两个版本的输出结果"""
    print("\n" + "=" * 60)
    print("正确性测试")
    print("=" * 60)
    
    aac_orig = AAC_original.AAC()
    aac_opt = AAC_optimized.AACOptimized()
    
    # 测试用例：(干球温度, 相对湿度)
    test_cases = [
        (25.0, 0.50),   # 常温中等湿度
        (30.0, 0.60),   # 较高温
        (20.0, 0.80),   # 较低温高湿度
        (35.0, 0.30),   # 高温低湿度
        (15.0, 0.90),   # 低温高湿度
        (28.0, 0.45),   # 常温较低湿度
        (40.0, 0.20),   # 高温干燥
        (10.0, 0.95),   # 低温接近饱和
        (22.5, 0.55),   # 常规工况
        (32.0, 0.70),   # 夏季典型
    ]
    
    diff_threshold = 0.1  # 允许误差 0.1℃
    all_passed = True
    
    print(f"{'干球温度':^10} {'相对湿度':^10} {'原版结果':^12} {'优化版结果':^12} {'误差':^10} {'状态':^8}")
    print("-" * 60)
    
    for tg, rh in test_cases:
        ts_orig = aac_orig.ts(tg, rh, 0.1)
        ts_opt = aac_opt.ts(tg, rh, 0.1)
        
        error = abs(ts_orig - ts_opt)
        passed = error < diff_threshold
        status = "[PASS]" if passed else "[FAIL]"
        
        if not passed:
            all_passed = False
        
        print(f"{tg:^10.1f} {rh:^10.2f} {ts_orig:^12.2f} {ts_opt:^12.2f} {error:^10.3f} {status:^8}")
    
    print("-" * 60)
    print(f"总体结果: {'全部通过' if all_passed else '存在失败'}")
    
    return all_passed


def test_performance():
    """测试性能：对比两个版本的执行时间"""
    print("\n" + "=" * 60)
    print("性能测试")
    print("=" * 60)
    
    aac_orig = AAC_original.AAC()
    aac_opt = AAC_optimized.AACOptimized()
    
    # 测试参数
    test_temps = [20.0, 25.0, 30.0, 35.0]
    test_rhs = [0.3, 0.5, 0.7, 0.9]
    
    # 总测试次数为500次
    total_tests = 500
    iterations = total_tests // (len(test_temps) * len(test_rhs))
    
    print(f"测试点数量: {len(test_temps)} × {len(test_rhs)} = {len(test_temps) * len(test_rhs)}")
    print(f"每点重复次数: {iterations}")
    print(f"总计算次数: {total_tests}")
    print()
    
    # 测试原版
    print("测试原版 AAC.ts()...")
    start_time = get_time_ms()
    
    for _ in range(iterations):
        for tg in test_temps:
            for rh in test_rhs:
                aac_orig.ts(tg, rh, 0.1)
    
    time_orig = get_time_ms() - start_time
    
    # 测试优化版（二分法）
    print("测试优化版 AACOps.ts() [二分法]...")
    start_time = get_time_ms()
    
    for _ in range(iterations):
        for tg in test_temps:
            for rh in test_rhs:
                aac_opt.ts(tg, rh, 0.1)
    
    time_opt_bisect = get_time_ms() - start_time
    
    # 测试优化版（牛顿法）
    print("测试优化版 AACOps.ts_newton() [牛顿法]...")
    start_time = get_time_ms()
    
    for _ in range(iterations):
        for tg in test_temps:
            for rh in test_rhs:
                aac_opt.ts_newton(tg, rh)
    
    time_opt_newton = get_time_ms() - start_time
    
    # 输出结果
    print("\n" + "-" * 60)
    print(f"{'版本':^25} {'耗时(ms)':^15} {'平均(μs/次)':^15} {'加速比':^10}")
    print("-" * 60)
    
    avg_orig = time_orig / total_tests * 1000
    avg_bisect = time_opt_bisect / total_tests * 1000
    avg_newton = time_opt_newton / total_tests * 1000
    
    speedup_bisect = time_orig / time_opt_bisect if time_opt_bisect > 0 else float('inf')
    speedup_newton = time_orig / time_opt_newton if time_opt_newton > 0 else float('inf')
    
    print(f"{'原版 AAC.ts()':^25} {time_orig:^15.1f} {avg_orig:^15.2f} {'1.0x':^10}")
    print(f"{'优化版 [二分法]':^25} {time_opt_bisect:^15.1f} {avg_bisect:^15.2f} {f'{speedup_bisect:.1f}x':^10}")
    print(f"{'优化版 [牛顿法]':^25} {time_opt_newton:^15.1f} {avg_newton:^15.2f} {f'{speedup_newton:.1f}x':^10}")
    print("-" * 60)
    
    return {
        'time_orig': time_orig,
        'time_bisect': time_opt_bisect,
        'time_newton': time_opt_newton,
        'speedup_bisect': speedup_bisect,
        'speedup_newton': speedup_newton
    }


def test_edge_cases():
    """测试边界情况"""
    print("\n" + "=" * 60)
    print("边界情况测试")
    print("=" * 60)
    
    aac_opt = AAC_optimized.AACOptimized()
    
    edge_cases = [
        ("无效输入 (-9999)", -9999, 0.5),
        ("无效湿度", 25.0, -99.99),
        ("RH = 0%", 25.0, 0.0),
        ("RH = 100%", 25.0, 1.0),
        ("极低温度", -10.0, 0.5),
        ("极高温度", 50.0, 0.5),
        ("极低湿度", 30.0, 0.01),
    ]
    
    print(f"{'测试用例':^20} {'干球温度':^10} {'相对湿度':^10} {'结果':^12}")
    print("-" * 60)
    
    for name, tg, rh in edge_cases:
        result = aac_opt.ts(tg, rh, 0.1)
        print(f"{name:^20} {tg:^10.2f} {rh:^10.2f} {result:^12.2f}")
    
    print("-" * 60)


def test_monotonicity():
    """测试单调性：验证 rh 是 ts 的单调递增函数"""
    print("\n" + "=" * 60)
    print("单调性验证")
    print("=" * 60)
    
    aac_opt = AAC_optimized.AACOptimized()
    
    tg = 30.0  # 固定干球温度
    ts_values = [tg - i for i in range(0, 21, 2)]  # ts 从 tg 递减到 tg-20
    
    print(f"固定干球温度: {tg}℃")
    print(f"{'湿球温度 ts':^15} {'相对湿度 rh':^15} {'单调性':^10}")
    print("-" * 45)
    
    prev_rh = None
    is_monotonic = True
    
    for ts in ts_values:
        rh = aac_opt.rh(tg, ts)
        
        if prev_rh is not None:
            # rh 应该随 ts 递减而递减（单调递增函数）
            if rh > prev_rh:
                is_monotonic = False
                status = "[FAIL]"
            else:
                status = "[OK]"
        else:
            status = "-"
        
        print(f"{ts:^15.1f} {rh:^15.4f} {status:^10}")
        prev_rh = rh
    
    print("-" * 45)
    print(f"单调性验证: {'通过' if is_monotonic else '失败'}")


def run_all_tests():
    """运行所有测试"""
    print("\n")
    print("=" * 60)
    print(" " * 15 + "AAC 性能对比测试报告" + " " * 15)
    print("=" * 60)
    
    # 正确性测试
    correctness_passed = test_correctness()
    
    # 性能测试
    perf_results = test_performance()
    
    # 边界情况测试
    test_edge_cases()
    
    # 单调性验证
    test_monotonicity()
    
    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"正确性测试: {'通过' if correctness_passed else '失败'}")
    print(f"性能提升 [二分法]: {perf_results['speedup_bisect']:.1f}x")
    print(f"性能提升 [牛顿法]: {perf_results['speedup_newton']:.1f}x")
    print("=" * 60)
    
    return correctness_passed and perf_results['speedup_bisect'] > 1


# 自动运行测试
if __name__ == "__main__":
    run_all_tests()
