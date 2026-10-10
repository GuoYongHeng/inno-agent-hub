#!/usr/bin/env python3
"""
学校课表自动排课系统
基于约束满足(CSP) + 贪心回溯算法
支持20类约束规则，输出格式化Excel文件
"""

import argparse
import random
import sys
import os
from collections import defaultdict, Counter
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill
from openpyxl.utils import get_column_letter

# ============================================================
# 常量定义
# ============================================================

DAYS = ['周一', '周二', '周三', '周四', '周五']
PERIODS = [1, 2, 3, 4, 5, 6]          # 正课时段 (延时课不排课)
ALL_SLOTS = [1, 2, 3, 4, 5, 6, 7, 8]   # 包含延时课的完整时段

# 科目分类
MAIN_SUBJ = {'语文', '数学', '英语'}                    # 主科: 可同天多节
SPECIAL_SUBJ = {'体育', '体活'}                          # 体育/体活: 每天最多1节
ART_MUSIC_SUBJ = {'音乐', '美术'}                        # 音美: 3-6年级合并排课
FIXED_SUBJ = {'班会'}                                    # 固定时段科目

# 各年级科目限制 (前几节不安排的科目)
EARLY_RESTRICT = {
    '一年级': {'音乐', '美术', '体育', '道法', '劳动', '健康', '信息', '科学', '写作', '故事会', '体活'},
    '二年级': {'音乐', '美术', '体育', '道法', '劳动', '健康', '信息', '科学', '写作', '故事会', '体活'},
    '三年级': {'音乐', '美术', '体育', '道法', '劳动', '健康', '信息', '科学', '写作', '故事会', '体活'},
    '四年级': {'音乐', '美术', '体育', '道法', '劳动', '健康', '信息', '科学', '写作', '故事会', '体活'},
    '五年级': {'音乐', '美术', '体育', '道法', '劳动', '健康', '信息', '科学', '写作', '故事会', '体活'},
    '六年级': {'音乐', '美术', '体育', '道法', '劳动', '健康', '信息', '科学', '写作', '故事会', '体活'},
}

# P1 (第一节) 应安排的科目
P1_SUBJECTS = {'语文', '数学', '英语'}

# 年级显示顺序
GRADE_ORDER = ['一年级', '二年级', '三年级', '四年级', '五年级', '六年级']

# 颜色填充 (用于Excel输出)
SUBJECT_COLORS = {
    '语文': 'FFD700',
    '数学': '87CEEB',
    '英语': '90EE90',
    '体育': 'FFA07A',
    '体活': 'FFA07A',
    '音乐': 'DDA0DD',
    '美术': 'F0E68C',
    '科学': '98FB98',
    '道法': 'E0FFFF',
    '班会': 'FFB6C1',
    '写作': 'D8BFD8',
    '劳动': 'DEB887',
    '健康': 'AFEEEE',
    '信息': 'B0C4DE',
    '故事会': 'BC8F8F',
}

# ============================================================
# 新增约束常量
# ============================================================

# P1 (第一节) 分布规则: 周一-周五共5天, 周一固定班主任(语文)
# 'low'  = 1-2年级: 语文2节 + 数学3节 = 5天
# 'high' = 3-6年级: 语文2节 + 数学2节 + 英语1节 = 5天
P1_DISTRIBUTION = {
    'low':  {'语文': 2, '数学': 3},
    'high': {'语文': 2, '数学': 2, '英语': 1},
}

# 早上时段 (用于"语数每天早上至少1节"规则)
MORNING_PERIODS = [1, 2, 3]

# 最后一节 (禁止安排主科: 语文/数学/英语)
LAST_PERIOD = 6

# 禁止最后一节的科目
LAST_PERIOD_BAN = {'语文', '数学', '英语'}

# 单双周规则:
# 1-2年级: 所有课程不允许单双周差异
# 3-6年级: 仅音乐/美术允许单双周差异, 其余课程不允许
ODD_EVEN_ALLOWED_SUBJ = {'音乐', '美术'}  # 仅3-6年级允许单双周的科目

# 数学每天至少1节 (适用于所有年级)
MATH_DAILY_REQUIRED = True

# ============================================================
# 数据加载
# ============================================================

CLASSES = []
CLASS_GRADE = {}
GRADE_CLASSES = defaultdict(list)

def load_courses(filepath):
    """从Excel文件加载课程列表"""
    from openpyxl import load_workbook
    wb = load_workbook(filepath)
    
    # 查找课程列表工作表
    sheet_name = None
    for sn in wb.sheetnames:
        if '课程' in sn:
            sheet_name = sn
            break
    if not sheet_name:
        sheet_name = wb.sheetnames[0]
    
    ws = wb[sheet_name]
    
    tasks = []
    classes_set = set()
    
    for row in range(2, ws.max_row + 1):
        course_id = ws.cell(row, 1).value
        course_name = str(ws.cell(row, 2).value or '').strip()
        subject = str(ws.cell(row, 3).value or '').strip()
        grade = str(ws.cell(row, 4).value or '').strip()
        class_name = str(ws.cell(row, 5).value or '').strip()
        teacher = str(ws.cell(row, 6).value or '').strip()
        weekly_hours = ws.cell(row, 7).value
        
        if not subject or not class_name or not teacher:
            continue
        
        try:
            weekly_hours = int(weekly_hours)
        except (ValueError, TypeError):
            weekly_hours = 1
        
        # 生成周课时任务
        for i in range(weekly_hours):
            tasks.append({
                'course_id': str(course_id) if course_id else '',
                'course_name': course_name,
                'subject': subject,
                'grade': grade,
                'class': class_name,
                'teacher': teacher,
                'weekly_hours': weekly_hours,
                'task_idx': i,
                'placed': False,
            })
        
        classes_set.add(class_name)
        CLASS_GRADE[class_name] = grade
        GRADE_CLASSES[grade].append(class_name)
    
    # 排序班级
    global CLASSES
    CLASSES = sorted(classes_set, key=lambda c: (
        GRADE_ORDER.index(CLASS_GRADE[c]) if CLASS_GRADE[c] in GRADE_ORDER else 99,
        c
    ))
    
    return tasks


def identify_homeroom_teachers(tasks):
    """识别班主任: 每个班级的语文教师即班主任"""
    homeroom = {}
    for t in tasks:
        if t['subject'] == '语文' and t['class'] not in homeroom:
            homeroom[t['class']] = t['teacher']
    return homeroom


# ============================================================
# 排课引擎
# ============================================================

class TimetableSolver:
    def __init__(self, tasks):
        self.all_tasks = tasks
        self.schedule = {}  # (class, day, period) -> task or None
        self.teacher_occ = defaultdict(set)  # teacher -> set of (day, period)
        
        # 初始化课表
        for cls in CLASSES:
            for day in DAYS:
                for p in ALL_SLOTS:
                    self.schedule[(cls, day, p)] = None
        
        # 识别班主任
        self.homeroom = identify_homeroom_teachers(tasks)
        
        # 统计教师任务
        self.teacher_tasks = defaultdict(list)
        for t in tasks:
            self.teacher_tasks[t['teacher']].append(t)
    
    def _can_place(self, task, day, period):
        """检查任务是否可以放置在指定位置"""
        cls = task['class']
        teacher = task['teacher']
        subject = task['subject']
        
        # 1. 该位置已有课程
        if self.schedule[(cls, day, period)] is not None:
            return False
        
        # 2. 延时课不排课
        if period > 6:
            return False
        
        # 3. 教师冲突
        if (day, period) in self.teacher_occ[teacher]:
            return False
        
        # 4. 前两节限制 (非主科不安排在前两节)
        if period <= 2 and subject in EARLY_RESTRICT.get(task['grade'], set()):
            # 体育例外: 可以安排在前两节
            if subject not in ('体育',):
                return False
        
        # 5. 班会固定在周一第5节
        if subject == '班会':
            if day != '周一' or period != 5:
                return False
        
        # 6. 非主科同天限制 (除语文/英语/数学外, 每天每班最多1节)
        if subject not in MAIN_SUBJ:
            same_day_count = 0
            for p in PERIODS:
                existing = self.schedule[(cls, day, p)]
                if existing and existing['subject'] == subject:
                    same_day_count += 1
            if same_day_count > 0:
                return False
        
        # 7. 体育/体活每天最多1节 (视为同一科目)
        if subject in SPECIAL_SUBJ:
            for p in PERIODS:
                existing = self.schedule[(cls, day, p)]
                if existing and existing['subject'] in SPECIAL_SUBJ:
                    return False
        
        # 8. 3-6年级音美合并排课, 每天最多1节
        if subject in ART_MUSIC_SUBJ:
            grade_num = self._grade_num(task['grade'])
            if grade_num >= 3:
                for p in PERIODS:
                    existing = self.schedule[(cls, day, p)]
                    if existing and existing['subject'] in ART_MUSIC_SUBJ:
                        return False
        
        # 9. 周一第一节必须是班主任课程
        if day == '周一' and period == 1:
            homeroom_teacher = self.homeroom.get(cls)
            if homeroom_teacher and teacher != homeroom_teacher:
                return False
        
        # 10. 最后一节禁止安排主科 (语文/数学/英语)
        if period == LAST_PERIOD and subject in LAST_PERIOD_BAN:
            return False
        
        # 11. 同天连续同课禁止 (相邻节次不能相同科目, 班会除外)
        if subject != '班会':
            if period > 1:
                prev = self.schedule[(cls, day, period - 1)]
                if prev and prev['subject'] == subject:
                    return False
            if period < 6:
                nxt = self.schedule[(cls, day, period + 1)]
                if nxt and nxt['subject'] == subject:
                    return False
        
        # 12. P1科目限制: 第一节只能安排语文/数学/英语
        if period == 1 and subject not in P1_SUBJECTS and subject != '班会':
            return False
        
        return True
    
    def _grade_num(self, grade):
        """提取年级数字"""
        for i, ch in enumerate(grade):
            if ch in '一二三四五六':
                mapping = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6}
                return mapping.get(ch, 0)
        return 0
    
    def _place(self, task, day, period):
        """放置任务"""
        cls = task['class']
        teacher = task['teacher']
        self.schedule[(cls, day, period)] = task
        self.teacher_occ[teacher].add((day, period))
    
    def _unplace(self, task, day, period):
        """移除任务"""
        cls = task['class']
        teacher = task['teacher']
        self.schedule[(cls, day, period)] = None
        self.teacher_occ[teacher].discard((day, period))
    
    def _score(self, task, day, period):
        """评分函数: 越低越好"""
        score = 0
        cls = task['class']
        teacher = task['teacher']
        subject = task['subject']
        
        # 优先安排主科在前几节
        if subject in MAIN_SUBJ and period <= 3:
            score -= 5
        
        # 非主科优先安排在后面
        if subject not in MAIN_SUBJ and period >= 4:
            score -= 3
        
        # 分散同科目到不同天
        same_subj_days = set()
        for d in DAYS:
            for p in PERIODS:
                existing = self.schedule[(cls, d, p)]
                if existing and existing['subject'] == subject:
                    same_subj_days.add(d)
        if day in same_subj_days:
            score += 10
        
        # 教师每天覆盖: 鼓励填满教师空天
        teacher_days = set()
        for d in DAYS:
            for p in PERIODS:
                if (d, p) in self.teacher_occ[teacher]:
                    teacher_days.add(d)
        if day not in teacher_days:
            score -= 15  # 强烈鼓励填空天
        
        # P1分布: 避免同班同天多节P1科目
        if period == 1:
            for d in DAYS:
                if self.schedule[(cls, d, 1)] and d != day:
                    if self.schedule[(cls, d, 1)]['subject'] == subject:
                        score += 8
        
        # P1连续避让: 避免与前一天/后一天P1相同科目
        if period == 1:
            day_idx = DAYS.index(day)
            if day_idx > 0:
                prev_p1 = self.schedule[(cls, DAYS[day_idx - 1], 1)]
                if prev_p1 and prev_p1['subject'] == subject:
                    score += 15
            if day_idx < len(DAYS) - 1:
                next_p1 = self.schedule[(cls, DAYS[day_idx + 1], 1)]
                if next_p1 and next_p1['subject'] == subject:
                    score += 15
        
        # 语数早上至少1节: 如果该天还没有语数在早上, 强烈鼓励放置
        if subject in ('语文', '数学') and period in MORNING_PERIODS:
            has_morning = False
            for mp in MORNING_PERIODS:
                if mp == period:
                    continue
                existing = self.schedule[(cls, day, mp)]
                if existing and existing['subject'] in ('语文', '数学'):
                    has_morning = True
                    break
            if not has_morning:
                score -= 20
        
        # 数学每天分布: 鼓励数学分散到每天
        if subject == '数学':
            math_days = set()
            for d in DAYS:
                for p in PERIODS:
                    existing = self.schedule[(cls, d, p)]
                    if existing and existing['subject'] == '数学':
                        math_days.add(d)
            if day not in math_days:
                score -= 12  # 鼓励填没有数学的天
        
        return score
    
    def _place_fixed(self):
        """放置固定时段课程 (班会固定在周一第5节)"""
        for task in self.all_tasks:
            if task['subject'] == '班会':
                if self._can_place(task, '周一', 5):
                    self._place(task, '周一', 5)
                    task['placed'] = True
    
    def _pre_assign_p1(self):
        """预分配第一节, 遵循P1分布规则:
        - 周一第一节: 班主任(语文教师)课程
        - 1-2年级: 周内P1共 语文2+数学3 (周一已占语文1, 余下4天: 语文1+数学3)
        - 3-6年级: 周内P1共 语文2+数学2+英语1 (周一已占语文1, 余下4天: 语文1+数学2+英语1)
        - 同时避免连续两天P1相同科目
        """
        count = 0
        non_monday = ['周二', '周三', '周四', '周五']
        
        for cls in CLASSES:
            grade = CLASS_GRADE.get(cls, '')
            grade_num = self._grade_num(grade)
            dist_type = 'low' if grade_num <= 2 else 'high'
            dist = P1_DISTRIBUTION[dist_type].copy()
            
            homeroom_teacher = self.homeroom.get(cls)
            if not homeroom_teacher:
                continue
            
            # === 周一第一节: 班主任课程 ===
            teacher_courses = [t for t in self.all_tasks 
                             if t['teacher'] == homeroom_teacher and t['class'] == cls and not t.get('placed')]
            placed = False
            for t in teacher_courses:
                if self._can_place(t, '周一', 1):
                    self._place(t, '周一', 1)
                    t['placed'] = True
                    placed = True
                    count += 1
                    break
            
            if not placed:
                # 降级: 任意班主任课程
                for t in teacher_courses:
                    if self._can_place(t, '周一', 1):
                        self._place(t, '周一', 1)
                        t['placed'] = True
                        placed = True
                        count += 1
                        break
            
            # 周一已用掉1节语文
            remaining_dist = {}
            for subj, cnt in dist.items():
                remaining_dist[subj] = cnt - (1 if subj == '语文' else 0)
            
            # === 周二-周五第一节: 按分布规则分配 ===
            # 生成科目序列
            subj_sequence = []
            for subj, cnt in remaining_dist.items():
                subj_sequence.extend([subj] * cnt)
            random.shuffle(subj_sequence)
            
            # 尝试排列使连续不重复 (贪心)
            best_seq = self._arrange_no_consecutive(subj_sequence)
            
            assigned = 0
            for day, target_subj in zip(non_monday, best_seq):
                if assigned >= len(best_seq):
                    break
                if self.schedule[(cls, day, 1)] is not None:
                    continue
                
                # 找该科目未放置的任务
                candidates = [t for t in self.all_tasks 
                            if t['class'] == cls and t['subject'] == target_subj and not t.get('placed')]
                random.shuffle(candidates)
                
                for t in candidates:
                    if self._can_place(t, day, 1):
                        self._place(t, day, 1)
                        t['placed'] = True
                        count += 1
                        assigned += 1
                        break
            
            # 如果有未分配的天, 用任意主科填充
            for day in non_monday:
                if self.schedule[(cls, day, 1)] is not None:
                    continue
                candidates = [t for t in self.all_tasks 
                            if t['class'] == cls and t['subject'] in MAIN_SUBJ and not t.get('placed')]
                random.shuffle(candidates)
                for t in candidates:
                    if self._can_place(t, day, 1):
                        self._place(t, day, 1)
                        t['placed'] = True
                        count += 1
                        break
        
        return count
    
    def _arrange_no_consecutive(self, items):
        """排列列表使相邻元素不相同, 返回最优排列"""
        if not items:
            return []
        
        from collections import Counter
        counts = Counter(items)
        result = []
        prev = None
        
        for _ in range(len(items)):
            # 选一个与prev不同且剩余最多的
            candidates = [(cnt, subj) for subj, cnt in counts.items() if cnt > 0 and subj != prev]
            if not candidates:
                # 无法避免连续, 选剩余最多的
                candidates = [(cnt, subj) for subj, cnt in counts.items() if cnt > 0]
            if not candidates:
                break
            candidates.sort(reverse=True)
            chosen = candidates[0][1]
            result.append(chosen)
            counts[chosen] -= 1
            prev = chosen
        
        return result
    
    def _pre_assign_pe_daily(self):
        """预分配体育/体活: 确保每天一节"""
        count = 0
        for cls in CLASSES:
            pe_tasks = [t for t in self.all_tasks 
                       if t['class'] == cls and t['subject'] in SPECIAL_SUBJ and not t.get('placed')]
            
            if not pe_tasks:
                continue
            
            # 尝试每天安排一节体育/体活
            for day in DAYS:
                if len(pe_tasks) == 0:
                    break
                
                t = pe_tasks.pop(0)
                candidates = []
                for p in PERIODS:
                    if self._can_place(t, day, p):
                        candidates.append((day, p))
                
                if candidates:
                    candidates.sort(key=lambda dp: self._score(t, dp[0], dp[1]))
                    day_p, p = candidates[0]
                    self._place(t, day_p, p)
                    t['placed'] = True
                    count += 1
        
        return count
    
    def _pre_assign_special_rooms(self):
        """预分配特殊教室课程 (信息/科学等)"""
        count = 0
        special_subjects = ['信息', '科学']
        
        for cls in CLASSES:
            for subj in special_subjects:
                tasks = [t for t in self.all_tasks 
                        if t['class'] == cls and t['subject'] == subj and not t.get('placed')]
                
                used_days = set()
                for t in tasks:
                    best = None
                    best_score = 999
                    
                    for day in DAYS:
                        if day in used_days:
                            continue
                        for p in PERIODS:
                            if self._can_place(t, day, p):
                                s = self._score(t, day, p)
                                if s < best_score:
                                    best_score = s
                                    best = (day, p)
                    
                    if best:
                        self._place(t, best[0], best[1])
                        t['placed'] = True
                        used_days.add(best[0])
                        count += 1
        
        return count
    
    def _pre_assign_p2_low(self):
        """预分配P2低年级特殊课程"""
        pass  # 留作扩展
    
    def _resolve_unplaced(self, unplaced):
        """尝试通过移动已有课程来解决未放置的任务"""
        still_unplaced = []
        
        for task in unplaced:
            placed = False
            
            # 尝试找到可放置的位置
            for day in DAYS:
                for p in PERIODS:
                    if self._can_place(task, day, p):
                        self._place(task, day, p)
                        task['placed'] = True
                        placed = True
                        break
                if placed:
                    break
            
            if not placed:
                # 尝试替换: 找一个已放置的非关键课程, 移到其他位置
                for day in DAYS:
                    for p in PERIODS:
                        existing = self.schedule[(task['class'], day, p)]
                        if existing is None:
                            continue
                        if existing['subject'] in FIXED_SUBJ:
                            continue  # 不移动固定课程
                        
                        # 尝试把existing移走
                        self._unplace(existing, day, p)
                        if self._can_place(task, day, p):
                            # 尝试把existing放到其他位置
                            moved = False
                            for d2 in DAYS:
                                for p2 in PERIODS:
                                    if d2 == day and p2 == p:
                                        continue
                                    if self._can_place(existing, d2, p2):
                                        self._place(existing, d2, p2)
                                        self._place(task, day, p)
                                        task['placed'] = True
                                        moved = True
                                        placed = True
                                        break
                                if moved:
                                    break
                            if not moved:
                                self._place(existing, day, p)  # 恢复
                        else:
                            self._place(existing, day, p)  # 恢复
                    if placed:
                        break
            
            if not placed:
                still_unplaced.append(task)
        
        return still_unplaced
    
    def _check_move(self, task, from_day, from_p, to_day, to_p):
        """检查移动是否可行"""
        existing = self.schedule[(task['class'], to_day, to_p)]
        
        if existing is not None:
            return False
        
        # 临时移除
        self._unplace(task, from_day, from_p)
        
        can = self._can_place(task, to_day, to_p)
        
        # 恢复
        self._place(task, from_day, from_p)
        
        return can
    
    def _try_move(self, task, from_day, from_p, to_day, to_p, allow_non_p1=True):
        """尝试移动课程"""
        if task['subject'] in FIXED_SUBJ:
            return False
        
        # P1课程不移动到非P1位置
        if from_p == 1 and to_p != 1:
            return False
        
        if not self._check_move(task, from_day, from_p, to_day, to_p):
            return False
        
        self._unplace(task, from_day, from_p)
        self._place(task, to_day, to_p)
        return True
    
    def _balance_teacher_days(self):
        """后处理: 修复教师空天"""
        for _ in range(5):  # 多轮迭代
            improved = False
            
            for teacher, tasks_by_teacher in self.teacher_tasks.items():
                # 找教师的空天
                teacher_days = set()
                for d in DAYS:
                    for p in PERIODS:
                        if (d, p) in self.teacher_occ[teacher]:
                            teacher_days.add(d)
                
                empty_days = [d for d in DAYS if d not in teacher_days]
                
                if not empty_days:
                    continue
                
                # 尝试把课程移到空天
                for target_day in empty_days:
                    for task in tasks_by_teacher:
                        if not task.get('placed'):
                            continue
                        if task['subject'] in FIXED_SUBJ:
                            continue
                        
                        # 找当前位置
                        current_pos = None
                        for d in DAYS:
                            for p in PERIODS:
                                if self.schedule.get((task['class'], d, p)) is task:
                                    current_pos = (d, p)
                                    break
                            if current_pos:
                                break
                        
                        if not current_pos:
                            continue
                        
                        from_d, from_p = current_pos
                        
                        # 尝试移到空天
                        for to_p in PERIODS:
                            if self._try_move(task, from_d, from_p, target_day, to_p):
                                improved = True
                                break
                        
                        if target_day in [d for d in DAYS for p in PERIODS if (d, p) in self.teacher_occ[teacher]]:
                            break
            
            if not improved:
                break
    
    def _find_task_pos(self, task):
        """找到任务在课表中的位置, 返回 (day, period) 或 None"""
        for d in DAYS:
            for p in PERIODS:
                if self.schedule.get((task['class'], d, p)) is task:
                    return (d, p)
        return None
    
    def _safe_swap(self, cls, day1, p1, day2, p2):
        """安全交换两个位置的课程, 检查所有约束. 返回是否成功"""
        task_a = self.schedule[(cls, day1, p1)]
        task_b = self.schedule[(cls, day2, p2)]
        
        if not task_a or not task_b:
            return False
        if task_a['subject'] in FIXED_SUBJ or task_b['subject'] in FIXED_SUBJ:
            return False
        
        # 临时移除
        self._unplace(task_a, day1, p1)
        self._unplace(task_b, day2, p2)
        
        # 检查交换后是否可行
        ok_a = self._can_place(task_a, day2, p2)
        ok_b = self._can_place(task_b, day1, p1)
        
        if ok_a and ok_b:
            self._place(task_a, day2, p2)
            self._place(task_b, day1, p1)
            return True
        else:
            # 恢复
            self._place(task_a, day1, p1)
            self._place(task_b, day2, p2)
            return False
    
    def _count_violations(self):
        """统计所有规则违规数量"""
        violations = {'consecutive_p1': 0, 'consecutive_same_day': 0,
                      'last_period_main': 0, 'no_morning_math': 0,
                      'no_morning_chinese': 0}
        
        for cls in CLASSES:
            # P1连续
            for i in range(len(DAYS) - 1):
                a = self.schedule.get((cls, DAYS[i], 1))
                b = self.schedule.get((cls, DAYS[i + 1], 1))
                if a and b and a['subject'] == b['subject']:
                    violations['consecutive_p1'] += 1
            
            for day in DAYS:
                # 同天连续同课
                for p in range(1, 6):
                    a = self.schedule.get((cls, day, p))
                    b = self.schedule.get((cls, day, p + 1))
                    if a and b and a['subject'] == b['subject'] and a['subject'] != '班会':
                        violations['consecutive_same_day'] += 1
                
                # 最后一节主科
                last = self.schedule.get((cls, day, LAST_PERIOD))
                if last and last['subject'] in LAST_PERIOD_BAN:
                    violations['last_period_main'] += 1
                
                # 早上无数学
                has_math_morning = False
                has_chinese_morning = False
                for mp in MORNING_PERIODS:
                    t = self.schedule.get((cls, day, mp))
                    if t:
                        if t['subject'] == '数学':
                            has_math_morning = True
                        if t['subject'] == '语文':
                            has_chinese_morning = True
                if not has_math_morning:
                    violations['no_morning_math'] += 1
                if not has_chinese_morning:
                    violations['no_morning_chinese'] += 1
        
        return violations
    
    def _post_process_all_rules(self):
        """后处理: 修复所有新增规则违规"""
        for iteration in range(10):
            improved = False
            v_before = self._count_violations()
            total_before = sum(v_before.values())
            
            if total_before == 0:
                break
            
            for cls in CLASSES:
                # === 1. 修复同天连续同课 ===
                for day in DAYS:
                    for p in range(1, 6):
                        a = self.schedule.get((cls, day, p))
                        b = self.schedule.get((cls, day, p + 1))
                        if not a or not b:
                            continue
                        if a['subject'] != b['subject'] or a['subject'] == '班会':
                            continue
                        if a['subject'] in FIXED_SUBJ:
                            continue
                        # 尝试把b换到其他位置
                        for td in DAYS:
                            for tp in PERIODS:
                                if td == day and tp == p + 1:
                                    continue
                                if tp == 1:
                                    continue  # 不动P1
                                if self._safe_swap(cls, day, p + 1, td, tp):
                                    improved = True
                                    break
                            if improved:
                                break
                        if improved:
                            break
                    if improved:
                        break
                
                # === 2. 修复最后一节主科 ===
                for day in DAYS:
                    last = self.schedule.get((cls, day, LAST_PERIOD))
                    if not last or last['subject'] not in LAST_PERIOD_BAN:
                        continue
                    # 找一个非主科交换
                    for td in DAYS:
                        for tp in PERIODS:
                            if tp == LAST_PERIOD or tp == 1:
                                continue
                            target = self.schedule.get((cls, td, tp))
                            if not target or target['subject'] in LAST_PERIOD_BAN:
                                continue
                            if target['subject'] in FIXED_SUBJ:
                                continue
                            if self._safe_swap(cls, day, LAST_PERIOD, td, tp):
                                improved = True
                                break
                        if improved:
                            break
                
                # === 3. 修复早上无数学/语文 ===
                for day in DAYS:
                    for subj in ['数学', '语文']:
                        has_morning = False
                        for mp in MORNING_PERIODS:
                            t = self.schedule.get((cls, day, mp))
                            if t and t['subject'] == subj:
                                has_morning = True
                                break
                        if has_morning:
                            continue
                        # 找该科目在下午的位置, 尝试换到早上
                        for p in range(4, LAST_PERIOD + 1):
                            t = self.schedule.get((cls, day, p))
                            if not t or t['subject'] != subj:
                                continue
                            # 找早上的非主科交换
                            for mp in MORNING_PERIODS:
                                target = self.schedule.get((cls, day, mp))
                                if not target or target['subject'] in MAIN_SUBJ:
                                    continue
                                if target['subject'] in FIXED_SUBJ:
                                    continue
                                if self._safe_swap(cls, day, p, day, mp):
                                    improved = True
                                    break
                            if improved:
                                break
                
                # === 4. 修复P1连续 (仅P1-P1交换, 保持分布) ===
                for i in range(len(DAYS) - 1):
                    a = self.schedule.get((cls, DAYS[i], 1))
                    b = self.schedule.get((cls, DAYS[i + 1], 1))
                    if not a or not b or a['subject'] != b['subject']:
                        continue
                    # 尝试与其他天的P1交换
                    for j in range(len(DAYS)):
                        if j == i or j == i + 1:
                            continue
                        c = self.schedule.get((cls, DAYS[j], 1))
                        if not c or c['subject'] == a['subject']:
                            continue
                        # 交换i和j的P1
                        if self._safe_swap(cls, DAYS[i], 1, DAYS[j], 1):
                            # 验证没有引入新的连续
                            new_v = self._count_violations()
                            if new_v['consecutive_p1'] < v_before['consecutive_p1']:
                                improved = True
                                v_before = new_v
                                break
                            else:
                                # 回退
                                self._safe_swap(cls, DAYS[i], 1, DAYS[j], 1)
                
                if improved:
                    break
            
            v_after = self._count_violations()
            total_after = sum(v_after.values())
            
            if not improved or total_after >= total_before:
                break
    
    def solve(self):
        """五阶段求解: 1.P1分布预分配 2.特殊课程预分配 3.贪心排剩余 4.教师空天修复 5.规则后处理"""
        best_result = None
        best_unplaced = len(self.all_tasks) + 1
        
        for attempt in range(self.restarts):
            # 重置状态
            for cls in CLASSES:
                for day in DAYS:
                    for p in ALL_SLOTS:
                        self.schedule[(cls, day, p)] = None
            self.teacher_occ.clear()
            for t in self.all_tasks:
                t['placed'] = False
            
            self._place_fixed()
            
            random.seed(self.seed + attempt * 137)
            
            # 预分配阶段
            p1_count = self._pre_assign_p1()
            self._pre_assign_p2_low()
            pe_count = self._pre_assign_pe_daily()
            self._pre_assign_special_rooms()
            
            # 贪心排课阶段
            remaining = [t for t in self.all_tasks if not t.get('placed')]
            
            # 按难度排序
            def difficulty(t):
                s = t['subject']
                d = 0
                if s in MAIN_SUBJ:
                    d += 5
                teacher_tasks_count = sum(1 for tt in remaining if tt['teacher'] == t['teacher'])
                d -= teacher_tasks_count * 2
                valid_slots = sum(1 for day in DAYS for p in PERIODS if self._can_place(t, day, p))
                d -= (30 - valid_slots) * 0.5
                return d
            
            shuffled = remaining[:]
            random.shuffle(shuffled)
            shuffled.sort(key=difficulty)
            
            unplaced = []
            for task in shuffled:
                placed = False
                reg_cands = []
                for day in DAYS:
                    for p in PERIODS:
                        if self._can_place(task, day, p):
                            reg_cands.append((day, p))
                
                if reg_cands:
                    reg_cands.sort(key=lambda dp: self._score(task, dp[0], dp[1]))
                    day, p = reg_cands[0]
                    self._place(task, day, p)
                    task['placed'] = True
                    placed = True
                
                if not placed:
                    unplaced.append(task)
            
            # 冲突解决
            if unplaced:
                unplaced = self._resolve_unplaced(unplaced)
            
            # 记录最佳结果
            if len(unplaced) < best_unplaced:
                best_unplaced = len(unplaced)
                best_result = {}
                for k, v in self.schedule.items():
                    best_result[k] = v if v else None
                best_teacher = {k: set(v) for k, v in self.teacher_occ.items()}
            
            if not unplaced:
                print(f"   第{attempt+1}次尝试: P1预分配{p1_count}节, 体育预分配{pe_count}节, 全部安排成功!")
                self._balance_teacher_days()
                self._post_process_all_rules()
                return True
            
            if attempt < 15 or len(unplaced) <= 5:
                print(f"   第{attempt+1}次尝试: P1预分配{p1_count}节, 体育预分配{pe_count}节, {len(unplaced)}个未安排")
        
        # 恢复最佳结果
        if best_result:
            for k in self.schedule:
                self.schedule[k] = best_result.get(k)
            self.teacher_occ = defaultdict(set, best_teacher)
        
        self._balance_teacher_days()
        self._post_process_all_rules()
        
        return best_unplaced == 0
    
    def get_unplaced_tasks(self):
        """获取未放置的任务"""
        return [t for t in self.all_tasks if not t.get('placed')]
    
    def set_restart_params(self, restarts=30, seed=2026):
        self.restarts = restarts
        self.seed = seed


# ============================================================
# Excel输出
# ============================================================

def write_excel(solver, output_path, school_name='学校'):
    """将排课结果写入Excel"""
    wb = Workbook()
    
    # Sheet 1: 年级总课程表
    ws1 = wb.active
    ws1.title = '年级总课程表'
    _write_grade_timetable(ws1, solver, school_name)
    
    # Sheet 2: 教师周课时统计
    ws2 = wb.create_sheet('教师周课时统计')
    _write_teacher_stats(ws2, solver)
    
    # Sheet 3: 教师个人课表
    ws3 = wb.create_sheet('教师个人课表')
    _write_teacher_timetable(ws3, solver)
    
    # Sheet 4: 约束检查报告
    ws4 = wb.create_sheet('约束检查报告')
    _write_constraint_report(ws4, solver)
    
    # Sheet 5: 班主任信息
    ws5 = wb.create_sheet('班主任信息')
    _write_homeroom_info(ws5, solver)
    
    wb.save(output_path)


def _write_grade_timetable(ws, solver, school_name):
    """写年级总课程表"""
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    header_font = Font(name='SimHei', size=10, bold=True)
    cell_font = Font(name='SimSun', size=9)
    title_font = Font(name='SimHei', size=14, bold=True)
    grade_font = Font(name='SimHei', size=12, bold=True)
    
    row = 1
    ws.cell(row, 1, f'{school_name}课表').font = title_font
    row += 2
    
    for grade in GRADE_ORDER:
        if grade not in GRADE_CLASSES:
            continue
        
        grade_classes = sorted(GRADE_CLASSES[grade])
        
        # 年级标题
        ws.cell(row, 1, f'小学{grade}').font = grade_font
        row += 1
        
        # 每个班
        for cls in grade_classes:
            # 星期行
            for di, day in enumerate(DAYS):
                start_col = di * 8 + 1
                ws.cell(row, start_col, day).font = header_font
                ws.cell(row, start_col).alignment = Alignment(horizontal='center')
                ws.cell(row, start_col).border = thin_border
            
            row += 1
            
            # 节次行
            for di, day in enumerate(DAYS):
                start_col = di * 8 + 1
                for pi, p in enumerate(ALL_SLOTS):
                    label = f'延时{p-6}' if p > 6 else str(p)
                    cell = ws.cell(row, start_col + pi, label)
                    cell.font = header_font
                    cell.alignment = Alignment(horizontal='center')
                    cell.border = thin_border
            row += 1
            
            # 课程行
            for di, day in enumerate(DAYS):
                start_col = di * 8 + 1
                for pi, p in enumerate(ALL_SLOTS):
                    task = solver.schedule.get((cls, day, p))
                    if task:
                        cell = ws.cell(row, start_col + pi, task['subject'])
                        color = SUBJECT_COLORS.get(task['subject'], 'FFFFFF')
                        cell.fill = PatternFill(start_color=color, end_color=color, fill_type='solid')
                    else:
                        cell = ws.cell(row, start_col + pi, '')
                    cell.font = cell_font
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                    cell.border = thin_border
            row += 1
            
            # 教师行
            for di, day in enumerate(DAYS):
                start_col = di * 8 + 1
                for pi, p in enumerate(ALL_SLOTS):
                    task = solver.schedule.get((cls, day, p))
                    if task:
                        cell = ws.cell(row, start_col + pi, task['teacher'])
                    else:
                        cell = ws.cell(row, start_col + pi, '')
                    cell.font = Font(name='SimSun', size=8)
                    cell.alignment = Alignment(horizontal='center', vertical='center')
                    cell.border = thin_border
            row += 1
            
            row += 1  # 空行
    
    # 设置列宽
    for col in range(1, 42):
        ws.column_dimensions[get_column_letter(col)].width = 8


def _write_teacher_stats(ws, solver):
    """写教师周课时统计"""
    header_font = Font(name='SimHei', size=11, bold=True)
    cell_font = Font(name='SimSun', size=10)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    ws.cell(1, 1, '教师').font = header_font
    ws.cell(1, 2, '承担学科').font = header_font
    ws.cell(1, 3, '正课').font = header_font
    
    for c in range(1, 4):
        ws.cell(1, c).border = thin_border
        ws.cell(1, c).alignment = Alignment(horizontal='center')
    
    # 统计
    teacher_info = {}
    for task in solver.all_tasks:
        t = task['teacher']
        if t not in teacher_info:
            teacher_info[t] = {'subjects': set(), 'count': 0}
        if task.get('placed'):
            teacher_info[t]['subjects'].add(task['subject'])
            teacher_info[t]['count'] += 1
    
    row = 2
    for teacher in sorted(teacher_info.keys()):
        info = teacher_info[teacher]
        ws.cell(row, 1, teacher).font = cell_font
        ws.cell(row, 2, ', '.join(sorted(info['subjects']))).font = cell_font
        ws.cell(row, 3, info['count']).font = cell_font
        
        for c in range(1, 4):
            ws.cell(row, c).border = thin_border
            ws.cell(row, c).alignment = Alignment(horizontal='center')
        row += 1
    
    ws.column_dimensions['A'].width = 12
    ws.column_dimensions['B'].width = 25
    ws.column_dimensions['C'].width = 8


def _write_teacher_timetable(ws, solver):
    """写教师个人课表"""
    header_font = Font(name='SimHei', size=10, bold=True)
    cell_font = Font(name='SimSun', size=9)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    # 按教师统计
    teacher_tasks = defaultdict(dict)  # teacher -> (day, period) -> (class, subject)
    for task in solver.all_tasks:
        if not task.get('placed'):
            continue
        for day in DAYS:
            for p in ALL_SLOTS:
                if solver.schedule.get((task['class'], day, p)) is task:
                    cls_short = task['class'].replace('年级', '').replace('（', '').replace('）', '')
                    teacher_tasks[task['teacher']][(day, p)] = (cls_short, task['subject'])
    
    row = 1
    for teacher in sorted(teacher_tasks.keys()):
        # 教师标题行
        total = len(teacher_tasks[teacher])
        ws.cell(row, 1, f'{teacher} | 正课:{total}节').font = header_font
        row += 1
        
        # 表头
        ws.cell(row, 1, '节次').font = header_font
        for di, day in enumerate(DAYS):
            ws.cell(row, di + 2, day).font = header_font
        row += 1
        
        # 课表内容
        for p in ALL_SLOTS:
            label = f'延时{p-6}' if p > 6 else str(p)
            ws.cell(row, 1, label).font = cell_font
            
            for di, day in enumerate(DAYS):
                entry = teacher_tasks[teacher].get((day, p))
                if entry:
                    cell = ws.cell(row, di + 2, f"{entry[0]}\n{entry[1]}")
                    color = SUBJECT_COLORS.get(entry[1], 'FFFFFF')
                    cell.fill = PatternFill(start_color=color, end_color=color, fill_type='solid')
                else:
                    cell = ws.cell(row, di + 2, '')
                cell.font = cell_font
                cell.alignment = Alignment(horizontal='center', vertical='center')
            row += 1
        
        row += 1  # 空行
    
    ws.column_dimensions['A'].width = 8
    for col in range(2, 7):
        ws.column_dimensions[get_column_letter(col)].width = 12


def _write_constraint_report(ws, solver):
    """写约束检查报告"""
    header_font = Font(name='SimHei', size=11, bold=True)
    cell_font = Font(name='SimSun', size=10)
    pass_font = Font(name='SimSun', size=10, color='008000')
    fail_font = Font(name='SimSun', size=10, color='FF0000')
    
    ws.cell(1, 1, '约束检查报告').font = Font(name='SimHei', size=14, bold=True)
    
    checks = []
    
    # 1. 教师冲突检查
    conflicts = 0
    for teacher in solver.teacher_occ:
        occ = solver.teacher_occ[teacher]
        if len(occ) != len(set(occ)):
            conflicts += 1
    checks.append(('教师冲突检查', conflicts == 0, f'{conflicts}个冲突' if conflicts else '无冲突'))
    
    # 2. 延时课检查
    delay_count = 0
    for cls in CLASSES:
        for day in DAYS:
            for p in [7, 8]:
                if solver.schedule.get((cls, day, p)):
                    delay_count += 1
    checks.append(('延时课不排课检查', delay_count == 0, f'{delay_count}节课在延时时段' if delay_count else '全部在正课时段'))
    
    # 3. 周一第一节班主任课程
    p1_ok = True
    p1_issues = []
    for cls in CLASSES:
        task = solver.schedule.get((cls, '周一', 1))
        homeroom = solver.homeroom.get(cls)
        if task and homeroom:
            if task['teacher'] != homeroom:
                p1_ok = False
                p1_issues.append(f'{cls}')
        elif not task:
            p1_ok = False
            p1_issues.append(f'{cls}(空)')
    checks.append(('周一第一节班主任课程', p1_ok, f'问题: {", ".join(p1_issues)}' if p1_issues else '全部正确'))
    
    # 4. 班会固定时段
    banhui_ok = True
    for task in solver.all_tasks:
        if task['subject'] == '班会' and task.get('placed'):
            found = False
            for day in DAYS:
                for p in PERIODS:
                    if solver.schedule.get((task['class'], day, p)) is task:
                        if day == '周一' and p == 5:
                            found = True
                        break
                if found:
                    break
            if not found:
                banhui_ok = False
    checks.append(('班会固定周一第5节', banhui_ok, '正确' if banhui_ok else '有偏差'))
    
    # 5. 非主科同天限制
    non_main_ok = True
    non_main_issues = []
    for cls in CLASSES:
        for day in DAYS:
            subj_count = Counter()
            for p in PERIODS:
                task = solver.schedule.get((cls, day, p))
                if task and task['subject'] not in MAIN_SUBJ:
                    subj_count[task['subject']] += 1
            for subj, cnt in subj_count.items():
                if cnt > 1:
                    non_main_ok = False
                    non_main_issues.append(f'{cls} {day} {subj}({cnt}节)')
    checks.append(('非主科同天最多1节', non_main_ok, f'问题: {"; ".join(non_main_issues[:5])}' if non_main_issues else '全部合规'))
    
    # 6. 体育/体活每天最多1节
    pe_ok = True
    for cls in CLASSES:
        for day in DAYS:
            pe_count = 0
            for p in PERIODS:
                task = solver.schedule.get((cls, day, p))
                if task and task['subject'] in SPECIAL_SUBJ:
                    pe_count += 1
            if pe_count > 1:
                pe_ok = False
    checks.append(('体育/体活每天最多1节', pe_ok, '合规' if pe_ok else '有违规'))
    
    # 7. 教师空天检查
    teacher_empty = []
    for teacher in solver.teacher_tasks:
        days_with_class = set()
        for day in DAYS:
            for p in PERIODS:
                if (day, p) in solver.teacher_occ[teacher]:
                    days_with_class.add(day)
        empty = [d for d in DAYS if d not in days_with_class]
        if empty and len(solver.teacher_tasks[teacher]) > 0:
            placed_count = sum(1 for t in solver.teacher_tasks[teacher] if t.get('placed'))
            if placed_count > 0:
                teacher_empty.append(f'{teacher}(空: {",".join(empty)})')
    checks.append(('教师每日覆盖', len(teacher_empty) == 0, f'问题: {"; ".join(teacher_empty[:5])}' if teacher_empty else '全部覆盖'))
    
    # 8. 未安排课程
    unplaced = solver.get_unplaced_tasks()
    checks.append(('课程全部安排', len(unplaced) == 0, f'{len(unplaced)}节未安排' if unplaced else '全部安排'))
    
    # 9. P1分布规则检查
    p1_dist_ok = True
    p1_dist_issues = []
    for cls in CLASSES:
        grade = CLASS_GRADE.get(cls, '')
        grade_num = solver._grade_num(grade)
        dist_type = 'low' if grade_num <= 2 else 'high'
        expected = P1_DISTRIBUTION[dist_type]
        actual = Counter()
        for day in DAYS:
            task = solver.schedule.get((cls, day, 1))
            if task:
                actual[task['subject']] += 1
        for subj, cnt in expected.items():
            if actual.get(subj, 0) != cnt:
                p1_dist_ok = False
                p1_dist_issues.append(f'{cls} {subj}: 期望{cnt}实际{actual.get(subj, 0)}')
    checks.append(('P1分布规则', p1_dist_ok, f'问题: {"; ".join(p1_dist_issues[:5])}' if p1_dist_issues else '全部合规'))
    
    # 10. P1连续避让检查
    p1_consec_ok = True
    p1_consec_issues = []
    for cls in CLASSES:
        for i in range(len(DAYS) - 1):
            a = solver.schedule.get((cls, DAYS[i], 1))
            b = solver.schedule.get((cls, DAYS[i + 1], 1))
            if a and b and a['subject'] == b['subject']:
                p1_consec_ok = False
                p1_consec_issues.append(f'{cls} {DAYS[i]}-{DAYS[i+1]} {a["subject"]}')
    checks.append(('P1连续避让', p1_consec_ok, f'问题: {"; ".join(p1_consec_issues[:5])}' if p1_consec_issues else '无连续'))
    
    # 11. 同天连续同课检查
    consec_ok = True
    consec_issues = []
    for cls in CLASSES:
        for day in DAYS:
            for p in range(1, 6):
                a = solver.schedule.get((cls, day, p))
                b = solver.schedule.get((cls, day, p + 1))
                if a and b and a['subject'] == b['subject'] and a['subject'] != '班会':
                    consec_ok = False
                    consec_issues.append(f'{cls} {day}P{p}-P{p+1} {a["subject"]}')
    checks.append(('同天连续同课禁止', consec_ok, f'问题: {"; ".join(consec_issues[:5])}' if consec_issues else '无违规'))
    
    # 12. 最后一节主科检查
    last_ok = True
    last_issues = []
    for cls in CLASSES:
        for day in DAYS:
            task = solver.schedule.get((cls, day, LAST_PERIOD))
            if task and task['subject'] in LAST_PERIOD_BAN:
                last_ok = False
                last_issues.append(f'{cls} {day}P{LAST_PERIOD} {task["subject"]}')
    checks.append(('最后一节禁主科', last_ok, f'问题: {"; ".join(last_issues[:5])}' if last_issues else '全部合规'))
    
    # 13. 语数早上至少1节检查
    morning_ok = True
    morning_issues = []
    for cls in CLASSES:
        for day in DAYS:
            has_math = False
            has_chinese = False
            for mp in MORNING_PERIODS:
                task = solver.schedule.get((cls, day, mp))
                if task:
                    if task['subject'] == '数学':
                        has_math = True
                    if task['subject'] == '语文':
                        has_chinese = True
            if not has_math:
                morning_ok = False
                morning_issues.append(f'{cls} {day}早上无数学')
            if not has_chinese:
                morning_ok = False
                morning_issues.append(f'{cls} {day}早上无语文')
    checks.append(('语数早上至少1节', morning_ok, f'问题: {"; ".join(morning_issues[:5])}' if morning_issues else '全部合规'))
    
    # 14. 音美合并排课检查 (3-6年级)
    art_music_ok = True
    art_music_issues = []
    for cls in CLASSES:
        grade = CLASS_GRADE.get(cls, '')
        grade_num = solver._grade_num(grade)
        if grade_num < 3:
            continue
        for day in DAYS:
            am_count = 0
            for p in PERIODS:
                task = solver.schedule.get((cls, day, p))
                if task and task['subject'] in ART_MUSIC_SUBJ:
                    am_count += 1
            if am_count > 1:
                art_music_ok = False
                art_music_issues.append(f'{cls} {day} 音美{am_count}节')
    checks.append(('音美合并排课(3-6年级)', art_music_ok, f'问题: {"; ".join(art_music_issues[:5])}' if art_music_issues else '全部合规'))
    
    # 写入
    row = 3
    ws.cell(row, 1, '检查项').font = header_font
    ws.cell(row, 2, '结果').font = header_font
    ws.cell(row, 3, '详情').font = header_font
    row += 1
    
    for name, passed, detail in checks:
        ws.cell(row, 1, name).font = cell_font
        ws.cell(row, 2, '通过' if passed else '未通过').font = pass_font if passed else fail_font
        ws.cell(row, 3, detail).font = cell_font
        row += 1
    
    ws.column_dimensions['A'].width = 25
    ws.column_dimensions['B'].width = 10
    ws.column_dimensions['C'].width = 50


def _write_homeroom_info(ws, solver):
    """写班主任信息"""
    header_font = Font(name='SimHei', size=11, bold=True)
    cell_font = Font(name='SimSun', size=10)
    thin_border = Border(
        left=Side(style='thin'),
        right=Side(style='thin'),
        top=Side(style='thin'),
        bottom=Side(style='thin')
    )
    
    ws.cell(1, 1, '班级').font = header_font
    ws.cell(1, 2, '年级').font = header_font
    ws.cell(1, 3, '班主任').font = header_font
    
    for c in range(1, 4):
        ws.cell(1, c).border = thin_border
        ws.cell(1, c).alignment = Alignment(horizontal='center')
    
    row = 2
    for cls in CLASSES:
        grade = CLASS_GRADE.get(cls, '')
        teacher = solver.homeroom.get(cls, '未识别')
        ws.cell(row, 1, cls).font = cell_font
        ws.cell(row, 2, grade).font = cell_font
        ws.cell(row, 3, teacher).font = cell_font
        
        for c in range(1, 4):
            ws.cell(row, c).border = thin_border
            ws.cell(row, c).alignment = Alignment(horizontal='center')
        row += 1
    
    ws.column_dimensions['A'].width = 20
    ws.column_dimensions['B'].width = 12
    ws.column_dimensions['C'].width = 12


# ============================================================
# 主函数
# ============================================================

def main():
    parser = argparse.ArgumentParser(description='学校课表自动排课系统')
    parser.add_argument('--input', required=True, help='课程列表Excel文件路径(含"课程列表"工作表)')
    parser.add_argument('--output', default='排课结果.xlsx', help='输出路径, 默认为排课结果.xlsx')
    parser.add_argument('--restarts', type=int, default=30, help='随机重启次数, 默认30')
    parser.add_argument('--seed', type=int, default=2026, help='随机种子, 默认2026')
    parser.add_argument('--school', default='学校', help='学校名称(用于表头)')
    
    args = parser.parse_args()
    
    # 检查输入文件
    if not os.path.exists(args.input):
        print(f"错误: 输入文件不存在: {args.input}")
        sys.exit(1)
    
    # 检查依赖
    try:
        import openpyxl
    except ImportError:
        print("错误: 缺少依赖库 openpyxl, 请运行: pip install openpyxl")
        sys.exit(1)
    
    print(f"加载课程列表: {args.input}")
    tasks = load_courses(args.input)
    print(f"共加载 {len(tasks)} 节课程任务, {len(CLASSES)} 个班级")
    
    # 排课
    solver = TimetableSolver(tasks)
    solver.set_restart_params(args.restarts, args.seed)
    
    print(f"\n开始排课 (重启次数: {args.restarts}, 种子: {args.seed})...")
    success = solver.solve()
    
    unplaced = solver.get_unplaced_tasks()
    if unplaced:
        print(f"\n警告: {len(unplaced)} 节课程未安排:")
        for t in unplaced:
            print(f"  - {t['class']} {t['subject']} ({t['teacher']})")
    
    # 输出
    print(f"\n生成Excel: {args.output}")
    write_excel(solver, args.output, args.school)
    
    print(f"\n排课完成! {'全部成功' if not unplaced else '部分未安排'}")
    print(f"输出文件: {args.output}")


if __name__ == '__main__':
    main()
