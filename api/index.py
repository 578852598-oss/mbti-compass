"""
api/index.py (Vercel) 或 backend.py (本地)
- 已内置 HTML 的 MBTI_BANK 题库（8 种类型 * 30 题）
- 计分不再写死“反向题号集合”，完全基于题库中的 reversed 字段

接口：
POST /score
GET  /bank/{mbti_type}  (可选：前端要拉题库时用)
GET  /health
"""
import os
import json

from __future__ import annotations

from math import sqrt
from typing import Any, Dict, List, Literal, Optional, Union

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel, Field, validator


SCALE_MIN = 1
SCALE_MAX = 6

SCALE_MIN_DEFAULT = SCALE_MIN
SCALE_MAX_DEFAULT = SCALE_MAX

MbtiType = str

# MbtiType = Literal[
#     "INTP", "INFJ", "INTJ", "ENTJ", "ENFJ", "ENTP", "ISFJ", "ISTP",
#     # 你 HTML 下拉里有，但当前题库缺失：这里仍允许传入（会报错提示缺题库）
#     "ENFP", "INFP",
# ]


# -----------------------------
# 题库：从你 index.html 的 const MBTI_BANK 迁移而来
# 每题字段：id, text, type, reversed
# -----------------------------
MBTI_BANK = {
    'INTP': {
        "scale_min": 1,
        "scale_max": 6,
        'questions': [
            {'id': 1, 'text': '当你的推理与现实反馈不一致时，你愿意调整自己的判断。', 'type': 'maturity', 'reversed': False},
            {'id': 2, 'text': '你常把想法停留在脑中推演，很难进入验证或执行。', 'type': 'maturity', 'reversed': True},
            {'id': 3, 'text': '你能把复杂想法讲清楚，并让别人听懂或用起来。', 'type': 'maturity', 'reversed': False},
            {'id': 4, 'text': '你会因为担心“还不够完美”而拖延输出。', 'type': 'maturity', 'reversed': True},
            {'id': 5, 'text': '你容易陷入自我怀疑，担心自己其实不够聪明。', 'type': 'maturity', 'reversed': True},
            {'id': 6, 'text': '你能在不同观点中找到共同结构，而不是执着于谁对谁错。', 'type': 'maturity', 'reversed': False},
            {'id': 7, 'text': '你容易把问题想得太复杂，导致无法开始。', 'type': 'maturity', 'reversed': True},
            {'id': 8, 'text': '即使被质疑，你也能冷静对待并重新检验自己的推理。', 'type': 'maturity', 'reversed': False},
            {'id': 9, 'text': '你会因为现实琐事太多而感到厌烦，想逃回自己的世界。', 'type': 'maturity', 'reversed': True},
            {'id': 10, 'text': '你能持续在现实中做小步验证，而不是只停留在思考。', 'type': 'maturity', 'reversed': False},
            {'id': 11, 'text': '你会反复在脑中重播过去的细节，找哪里出了问题。', 'type': 'loop', 'reversed': False},
            {'id': 12, 'text': '你会因为不确定而不断查资料，却迟迟不下结论。', 'type': 'loop', 'reversed': False},
            {'id': 13, 'text': '你会把自己关起来思考，越想越孤立。', 'type': 'loop', 'reversed': False},
            {'id': 14, 'text': '你会变得特别挑剔，觉得别人都不够严谨。', 'type': 'loop', 'reversed': False},
            {'id': 15, 'text': '你会不断复盘细节，反而错过新的可能性。', 'type': 'loop', 'reversed': False},
            {'id': 16, 'text': '你会陷入“我早就知道会这样”的消极循环。', 'type': 'loop', 'reversed': False},
            {'id': 17, 'text': '你会把小事放大成系统性问题，难以行动。', 'type': 'loop', 'reversed': False},
            {'id': 18, 'text': '你会被旧经验束缚，很难尝试新做法。', 'type': 'loop', 'reversed': False},
            {'id': 19, 'text': '你会不断推演最坏情况，导致迟迟不决。', 'type': 'loop', 'reversed': False},
            {'id': 20, 'text': '你会因为思考过载而陷入瘫痪，什么都不想做。', 'type': 'loop', 'reversed': False},
            {'id': 21, 'text': '你会突然变得非常情绪化，想被理解和安慰。', 'type': 'grip', 'reversed': False},
            {'id': 22, 'text': '你会觉得“没人懂我”，然后变得敏感或易怒。', 'type': 'grip', 'reversed': False},
            {'id': 23, 'text': '你会开始怀疑自己是不是不讨人喜欢。', 'type': 'grip', 'reversed': False},
            {'id': 24, 'text': '你会强烈渴望被看见、被肯定。', 'type': 'grip', 'reversed': False},
            {'id': 25, 'text': '你会开始在意别人是不是在否定你。', 'type': 'grip', 'reversed': False},
            {'id': 26, 'text': '你会突然想把关系搞清楚，甚至情绪爆发。', 'type': 'grip', 'reversed': False},
            {'id': 27, 'text': '你会变得特别在意“别人怎么想我”。', 'type': 'grip', 'reversed': False},
            {'id': 28, 'text': '你会在社交中失去分寸，或突然想切断一切。', 'type': 'grip', 'reversed': False},
            {'id': 29, 'text': '你会更在意他人评价，甚至做出不符合自己节奏的选择。', 'type': 'grip', 'reversed': False},
            {'id': 30, 'text': '你会出现明显的摆烂冲动，或想把事情一把推翻。', 'type': 'grip', 'reversed': False},
        ]
    },
    'INFJ': {
        "scale_min": 1,
        "scale_max": 6,
        'questions': [
            {'id': 1, 'text': '当现实情况与你的直觉预判不符时，你能灵活调整而不固执己见。', 'type': 'maturity', 'reversed': False},
            {'id': 2, 'text': '你会因为害怕破坏和谐，而压抑自己真正的想法。', 'type': 'maturity', 'reversed': True},
            {'id': 3, 'text': '你能清晰表达自己的边界，而不是默默承受。', 'type': 'maturity', 'reversed': False},
            {'id': 4, 'text': '你会过度为别人负责，导致自己精疲力尽。', 'type': 'maturity', 'reversed': True},
            {'id': 5, 'text': '你会因为别人不理解而陷入强烈的失望或受伤。', 'type': 'maturity', 'reversed': True},
            {'id': 6, 'text': '你能在理想与现实之间找到可行路径，而不是只沉浸在意义里。', 'type': 'maturity', 'reversed': False},
            {'id': 7, 'text': '你会觉得“没人懂我”，于是逐渐疏远所有人。', 'type': 'maturity', 'reversed': True},
            {'id': 8, 'text': '你能识别别人的情绪与自己的情绪，并做区分。', 'type': 'maturity', 'reversed': False},
            {'id': 9, 'text': '你会把别人的负面情绪都揽在自己身上。', 'type': 'maturity', 'reversed': True},
            {'id': 10, 'text': '你能在关心别人时，也照顾好自己的需求。', 'type': 'maturity', 'reversed': False},
            {'id': 11, 'text': '你会切断与人连接，陷入冷静但孤立的思考。', 'type': 'loop', 'reversed': False},
            {'id': 12, 'text': '你会反复分析别人为什么这样对你。', 'type': 'loop', 'reversed': False},
            {'id': 13, 'text': '你会觉得自己看透一切，别人都很肤浅。', 'type': 'loop', 'reversed': False},
            {'id': 14, 'text': '你会不断在心里审判别人，却不说出来。', 'type': 'loop', 'reversed': False},
            {'id': 15, 'text': '你会陷入“意义感丧失”的虚无循环。', 'type': 'loop', 'reversed': False},
            {'id': 16, 'text': '你会把自己关起来，拒绝任何安慰。', 'type': 'loop', 'reversed': False},
            {'id': 17, 'text': '你会越想越觉得人际关系很麻烦。', 'type': 'loop', 'reversed': False},
            {'id': 18, 'text': '你会用逻辑解释情绪，反而越来越麻木。', 'type': 'loop', 'reversed': False},
            {'id': 19, 'text': '你会因为过度思考而迟迟无法行动。', 'type': 'loop', 'reversed': False},
            {'id': 20, 'text': '你会反复推演未来风险，导致焦虑升级。', 'type': 'loop', 'reversed': False},
            {'id': 21, 'text': '你会对噪音、气味、杂乱等环境刺激异常敏感。', 'type': 'grip', 'reversed': False},
            {'id': 22, 'text': '你会突然想放纵自己（暴食、刷手机、购物）。', 'type': 'grip', 'reversed': False},
            {'id': 23, 'text': '你会变得冲动、易怒，甚至对小事爆炸。', 'type': 'grip', 'reversed': False},
            {'id': 24, 'text': '你会执着于把事情“搞对”，反而更崩溃。', 'type': 'grip', 'reversed': False},
            {'id': 25, 'text': '你会突然对身体状况焦虑（健康、疼痛、症状）。', 'type': 'grip', 'reversed': False},
            {'id': 26, 'text': '你会报复性地追求即时快乐，无法停下。', 'type': 'grip', 'reversed': False},
            {'id': 27, 'text': '你会对现实细节特别抓狂（“怎么这么乱/这么吵”）。', 'type': 'grip', 'reversed': False},
            {'id': 28, 'text': '你会突然想逃离一切责任。', 'type': 'grip', 'reversed': False},
            {'id': 29, 'text': '你会变得很难专注，脑子像被拉扯。', 'type': 'grip', 'reversed': False},
            {'id': 30, 'text': '你会出现“我不管了”的摆烂或彻底崩溃冲动。', 'type': 'grip', 'reversed': False},
        ]
    },
    'INTJ': {
        "scale_min": 1,
        "scale_max": 6,
        'questions': [
            {'id': 1, 'text': '你能把远景拆成可执行步骤，并持续推进。', 'type': 'maturity', 'reversed': False},
            {'id': 2, 'text': '你会因为别人效率低而失去耐心，难以协作。', 'type': 'maturity', 'reversed': True},
            {'id': 3, 'text': '你能在必要时调整计划，而不是死守原路线。', 'type': 'maturity', 'reversed': False},
            {'id': 4, 'text': '你会把情绪当成弱点，强行压下去。', 'type': 'maturity', 'reversed': True},
            {'id': 5, 'text': '你会因为“不够完美”而迟迟不愿推出成果。', 'type': 'maturity', 'reversed': True},
            {'id': 6, 'text': '你能接受他人的建议并进行现实校验。', 'type': 'maturity', 'reversed': False},
            {'id': 7, 'text': '你会对别人不理解你感到愤怒或轻蔑。', 'type': 'maturity', 'reversed': True},
            {'id': 8, 'text': '你能在战略与现实之间保持连接。', 'type': 'maturity', 'reversed': False},
            {'id': 9, 'text': '你会因琐事干扰而烦躁，想远离现实。', 'type': 'maturity', 'reversed': True},
            {'id': 10, 'text': '你能持续复盘并优化系统，而不陷入偏执。', 'type': 'maturity', 'reversed': False},
            {'id': 11, 'text': '你会沉溺在自我价值判断中，觉得别人都不行。', 'type': 'loop', 'reversed': False},
            {'id': 12, 'text': '你会把问题归因于“他们不配合”，而不是重新校验。', 'type': 'loop', 'reversed': False},
            {'id': 13, 'text': '你会不断在心里写“悲剧英雄剧本”。', 'type': 'loop', 'reversed': False},
            {'id': 14, 'text': '你会变得固执己见，拒绝外界信息。', 'type': 'loop', 'reversed': False},
            {'id': 15, 'text': '你会陷入“我必须证明自己是对的”的执念。', 'type': 'loop', 'reversed': False},
            {'id': 16, 'text': '你会把自己隔离起来，不让任何人靠近。', 'type': 'loop', 'reversed': False},
            {'id': 17, 'text': '你会对人际关系变得冷漠或厌烦。', 'type': 'loop', 'reversed': False},
            {'id': 18, 'text': '你会被内心道德感绑架，反而更难行动。', 'type': 'loop', 'reversed': False},
            {'id': 19, 'text': '你会过度解读别人行为，觉得他们在针对你。', 'type': 'loop', 'reversed': False},
            {'id': 20, 'text': '你会越想越觉得世界没救，陷入悲观。', 'type': 'loop', 'reversed': False},
            {'id': 21, 'text': '你会报复性放纵（暴食、购物、沉迷感官刺激）。', 'type': 'grip', 'reversed': False},
            {'id': 22, 'text': '你会对身体感受异常敏感或焦躁。', 'type': 'grip', 'reversed': False},
            {'id': 23, 'text': '你会突然想“毁掉一切”，推翻现状。', 'type': 'grip', 'reversed': False},
            {'id': 24, 'text': '你会无法自控地追求即时快感。', 'type': 'grip', 'reversed': False},
            {'id': 25, 'text': '你会陷入“我不配/我不够好”的自我怀疑。', 'type': 'grip', 'reversed': False},
            {'id': 26, 'text': '你会对细节抓狂（脏乱差、噪音、身体不适）。', 'type': 'grip', 'reversed': False},
            {'id': 27, 'text': '你会冲动消费或冲动做决定。', 'type': 'grip', 'reversed': False},
            {'id': 28, 'text': '你会突然变得很情绪化或幼稚。', 'type': 'grip', 'reversed': False},
            {'id': 29, 'text': '你会对生活小事失控，出现无力或烦躁。', 'type': 'grip', 'reversed': False},
            {'id': 30, 'text': '你会进入摆烂/瘫痪，甚至彻底停摆。', 'type': 'grip', 'reversed': False},
        ]
    },
    'ENTJ': {
        "scale_min": 1,
        "scale_max": 6,
        'questions': [
            {'id': 1, 'text': '你能在压力下仍保持战略视角，而不是只顾眼前。', 'type': 'maturity', 'reversed': False},
            {'id': 2, 'text': '你会因为别人慢而不耐烦，甚至想直接接管。', 'type': 'maturity', 'reversed': True},
            {'id': 3, 'text': '你能听进不同意见，并调整决策。', 'type': 'maturity', 'reversed': False},
            {'id': 4, 'text': '你会把情绪当成干扰，压制它。', 'type': 'maturity', 'reversed': True},
            {'id': 5, 'text': '你会因为担心失败而过度控制。', 'type': 'maturity', 'reversed': True},
            {'id': 6, 'text': '你能在推进目标的同时照顾团队节奏。', 'type': 'maturity', 'reversed': False},
            {'id': 7, 'text': '你会对无效沟通感到厌烦并切断交流。', 'type': 'maturity', 'reversed': True},
            {'id': 8, 'text': '你能在高效与可持续之间做平衡。', 'type': 'maturity', 'reversed': False},
            {'id': 9, 'text': '你会把人当工具，忽视他们的感受。', 'type': 'maturity', 'reversed': True},
            {'id': 10, 'text': '你能在压力下保持清晰边界与自我照顾。', 'type': 'maturity', 'reversed': False},
            {'id': 11, 'text': '你会陷入无休止忙碌，停不下来。', 'type': 'loop', 'reversed': False},
            {'id': 12, 'text': '你会不断追求刺激与效率，却失去方向感。', 'type': 'loop', 'reversed': False},
            {'id': 13, 'text': '你会把生活塞满任务，不敢空下来。', 'type': 'loop', 'reversed': False},
            {'id': 14, 'text': '你会越忙越焦虑，反而更失控。', 'type': 'loop', 'reversed': False},
            {'id': 15, 'text': '你会不断推进，却感觉自己不知道为什么推进。', 'type': 'loop', 'reversed': False},
            {'id': 16, 'text': '你会对任何停顿感到不安。', 'type': 'loop', 'reversed': False},
            {'id': 17, 'text': '你会不断想“再快一点”，忽视长期代价。', 'type': 'loop', 'reversed': False},
            {'id': 18, 'text': '你会因为没有结果而愤怒，变得强硬。', 'type': 'loop', 'reversed': False},
            {'id': 19, 'text': '你会把目标当成唯一意义，忽视内在需求。', 'type': 'loop', 'reversed': False},
            {'id': 20, 'text': '你会越做越麻木，像推土机一样。', 'type': 'loop', 'reversed': False},
            {'id': 21, 'text': '你会突然感到孤独、被误解，想被安慰。', 'type': 'grip', 'reversed': False},
            {'id': 22, 'text': '你会出现强烈自我怀疑：“我是不是不够好”。', 'type': 'grip', 'reversed': False},
            {'id': 23, 'text': '你会变得敏感，觉得别人不支持你。', 'type': 'grip', 'reversed': False},
            {'id': 24, 'text': '你会想找人倾诉，但又不想显得脆弱。', 'type': 'grip', 'reversed': False},
            {'id': 25, 'text': '你会突然很在意别人是否认可你。', 'type': 'grip', 'reversed': False},
            {'id': 26, 'text': '你会情绪爆发或想摊牌解决关系问题。', 'type': 'grip', 'reversed': False},
            {'id': 27, 'text': '你会在意别人是否把你当回事。', 'type': 'grip', 'reversed': False},
            {'id': 28, 'text': '你会出现摆烂冲动，或想把事情推翻。', 'type': 'grip', 'reversed': False},
            {'id': 29, 'text': '你会变得想被照顾，不想再扛。', 'type': 'grip', 'reversed': False},
            {'id': 30, 'text': '你会突然很委屈，想“我为什么要这样”。', 'type': 'grip', 'reversed': False},
        ]
    },
    'ENFJ': {
        "scale_min": 1,
        "scale_max": 6,
        'questions': [
            {'id': 1, 'text': '你能用温和而清晰的方式影响他人，而不是操控或讨好。', 'type': 'maturity', 'reversed': False},
            {'id': 2, 'text': '你会为了让别人开心而忽略自己的需求。', 'type': 'maturity', 'reversed': True},
            {'id': 3, 'text': '你能设立边界，不把所有人的情绪都扛在身上。', 'type': 'maturity', 'reversed': False},
            {'id': 4, 'text': '你会因为不被认可而强烈受挫。', 'type': 'maturity', 'reversed': True},
            {'id': 5, 'text': '你会过度在意别人的评价，导致焦虑。', 'type': 'maturity', 'reversed': True},
            {'id': 6, 'text': '你能在照顾别人时，也保持自我方向。', 'type': 'maturity', 'reversed': False},
            {'id': 7, 'text': '你会压抑真实情绪，只维持表面和谐。', 'type': 'maturity', 'reversed': True},
            {'id': 8, 'text': '你能看清自己为何想帮助别人，而不是出于空洞责任感。', 'type': 'maturity', 'reversed': False},
            {'id': 9, 'text': '你会把别人的需求当成自己的义务。', 'type': 'maturity', 'reversed': True},
            {'id': 10, 'text': '你能把热情转化为可持续行动。', 'type': 'maturity', 'reversed': False},
            {'id': 11, 'text': '你会迷失在外界反馈里，害怕被遗忘。', 'type': 'loop', 'reversed': False},
            {'id': 12, 'text': '你会不断刷存在感，难以安静下来。', 'type': 'loop', 'reversed': False},
            {'id': 13, 'text': '你会过度关注形象，担心别人怎么看你。', 'type': 'loop', 'reversed': False},
            {'id': 14, 'text': '你会陷入社交焦虑：我是不是不够受欢迎。', 'type': 'loop', 'reversed': False},
            {'id': 15, 'text': '你会把生活排满社交，反而更空。', 'type': 'loop', 'reversed': False},
            {'id': 16, 'text': '你会沉迷于“被需要”的感觉，停不下来。', 'type': 'loop', 'reversed': False},
            {'id': 17, 'text': '你会对安静感到不安，想找点热闹。', 'type': 'loop', 'reversed': False},
            {'id': 18, 'text': '你会不断输出，却感觉内心更疲惫。', 'type': 'loop', 'reversed': False},
            {'id': 19, 'text': '你会因为没人回应而受伤并更用力。', 'type': 'loop', 'reversed': False},
            {'id': 20, 'text': '你会越社交越麻木，像在表演。', 'type': 'loop', 'reversed': False},
            {'id': 21, 'text': '你会变得冷酷、挑剔，像在审判别人。', 'type': 'grip', 'reversed': False},
            {'id': 22, 'text': '你会突然很想“讲道理”，不再想共情。', 'type': 'grip', 'reversed': False},
            {'id': 23, 'text': '你会因为一点不合理就爆炸，变得刻薄。', 'type': 'grip', 'reversed': False},
            {'id': 24, 'text': '你会陷入强烈的批判：他们怎么这么蠢。', 'type': 'grip', 'reversed': False},
            {'id': 25, 'text': '你会突然不想再管任何人。', 'type': 'grip', 'reversed': False},
            {'id': 26, 'text': '你会用逻辑去拆别人的情绪，反而更伤人。', 'type': 'grip', 'reversed': False},
            {'id': 27, 'text': '你会对关系失望，想切断一切。', 'type': 'grip', 'reversed': False},
            {'id': 28, 'text': '你会变得很难相信别人是真心的。', 'type': 'grip', 'reversed': False},
            {'id': 29, 'text': '你会对小事也很苛刻，难以放松。', 'type': 'grip', 'reversed': False},
            {'id': 30, 'text': '你会出现“算了我不管了”的摆烂或冷漠。', 'type': 'grip', 'reversed': False},
        ]
    },
    'ENTP': {
        "scale_min": 1,
        "scale_max": 6,
        'questions': [
            {'id': 1, 'text': '你能把灵感落到结构中，并推进到可验证结果。', 'type': 'maturity', 'reversed': False},
            {'id': 2, 'text': '你会因为觉得无聊而频繁换方向，很难完成闭环。', 'type': 'maturity', 'reversed': True},
            {'id': 3, 'text': '你能在争论中抓住核心，而不是只为赢。', 'type': 'maturity', 'reversed': False},
            {'id': 4, 'text': '你会为了刺激而挑衅别人，哪怕没必要。', 'type': 'maturity', 'reversed': True},
            {'id': 5, 'text': '你会担心自己其实没有价值，只是嘴上厉害。', 'type': 'maturity', 'reversed': True},
            {'id': 6, 'text': '你能在多种可能性中做收敛与选择。', 'type': 'maturity', 'reversed': False},
            {'id': 7, 'text': '你会用玩笑掩盖认真需求，避免脆弱。', 'type': 'maturity', 'reversed': True},
            {'id': 8, 'text': '你能把探索欲转化为持续学习与产出。', 'type': 'maturity', 'reversed': False},
            {'id': 9, 'text': '你会因为怕被束缚而拒绝承诺。', 'type': 'maturity', 'reversed': True},
            {'id': 10, 'text': '你能在变化中保持自我节奏与逻辑一致。', 'type': 'maturity', 'reversed': False},
            {'id': 11, 'text': '你会为了被喜欢而不断刷存在感。', 'type': 'loop', 'reversed': False},
            {'id': 12, 'text': '你会陷入争论成瘾，停不下来。', 'type': 'loop', 'reversed': False},
            {'id': 13, 'text': '你会用热闹掩盖内在空虚。', 'type': 'loop', 'reversed': False},
            {'id': 14, 'text': '你会过度在意外界反馈，难以独处。', 'type': 'loop', 'reversed': False},
            {'id': 15, 'text': '你会不断找刺激，却越来越焦虑。', 'type': 'loop', 'reversed': False},
            {'id': 16, 'text': '你会不敢停下来，一停就难受。', 'type': 'loop', 'reversed': False},
            {'id': 17, 'text': '你会讲话越来越多，但逻辑越来越散。', 'type': 'loop', 'reversed': False},
            {'id': 18, 'text': '你会沉迷于外界新鲜感，忽视深度。', 'type': 'loop', 'reversed': False},
            {'id': 19, 'text': '你会为了好玩而做决定，缺乏收敛。', 'type': 'loop', 'reversed': False},
            {'id': 20, 'text': '你会越玩越累，却停不下来。', 'type': 'loop', 'reversed': False},
            {'id': 21, 'text': '你会突然对健康/细节异常焦虑。', 'type': 'grip', 'reversed': False},
            {'id': 22, 'text': '你会对身体不适过度敏感，担心出问题。', 'type': 'grip', 'reversed': False},
            {'id': 23, 'text': '你会变得固执、谨慎，失去幽默感。', 'type': 'grip', 'reversed': False},
            {'id': 24, 'text': '你会反复检查细节，怕出错。', 'type': 'grip', 'reversed': False},
            {'id': 25, 'text': '你会对日常琐事抓狂，觉得一切都不顺。', 'type': 'grip', 'reversed': False},
            {'id': 26, 'text': '你会变得特别想待在熟悉环境，拒绝变化。', 'type': 'grip', 'reversed': False},
            {'id': 27, 'text': '你会突然很想规矩生活，却又做不到。', 'type': 'grip', 'reversed': False},
            {'id': 28, 'text': '你会把小问题放大成灾难，紧张兮兮。', 'type': 'grip', 'reversed': False},
            {'id': 29, 'text': '你会出现“我是不是要完蛋”的焦虑。', 'type': 'grip', 'reversed': False},
            {'id': 30, 'text': '你会摆烂、逃避，失去探索欲。', 'type': 'grip', 'reversed': False},
        ]
    },
    'ISFJ': {
        "scale_min": 1,
        "scale_max": 6,
        'questions': [
            {'id': 1, 'text': '你能在照顾他人时，也不忘照顾自己。', 'type': 'maturity', 'reversed': False},
            {'id': 2, 'text': '你常把自己的需求压下去，觉得“没关系”。', 'type': 'maturity', 'reversed': True},
            {'id': 3, 'text': '你会因为担心冲突而不敢表达不满。', 'type': 'maturity', 'reversed': True},
            {'id': 4, 'text': '你会过度为别人的感受负责，导致内耗。', 'type': 'maturity', 'reversed': True},
            {'id': 5, 'text': '你能清晰表达需求，而不是期待别人猜到。', 'type': 'maturity', 'reversed': False},
            {'id': 6, 'text': '你会翻旧账，把过去委屈积累成怨气。', 'type': 'maturity', 'reversed': True},
            {'id': 7, 'text': '你能在传统与变化之间找到平衡。', 'type': 'maturity', 'reversed': False},
            {'id': 8, 'text': '你会把自己放在最后，直到崩溃。', 'type': 'maturity', 'reversed': True},
            {'id': 9, 'text': '你能在承担责任时，也给自己留出空间。', 'type': 'maturity', 'reversed': False},
            {'id': 10, 'text': '你会害怕未知变化，宁愿硬撑在熟悉里。', 'type': 'maturity', 'reversed': True},
            {'id': 11, 'text': '你会不断回忆别人对你不好的细节。', 'type': 'loop', 'reversed': False},
            {'id': 12, 'text': '你会反复翻旧账，觉得自己很委屈。', 'type': 'loop', 'reversed': False},
            {'id': 13, 'text': '你会用冷暴力表达不满，而不是沟通。', 'type': 'loop', 'reversed': False},
            {'id': 14, 'text': '你会把“他们欠我”挂在心里。', 'type': 'loop', 'reversed': False},
            {'id': 15, 'text': '你会在心里计较每一次付出与回报。', 'type': 'loop', 'reversed': False},
            {'id': 16, 'text': '你会越想越生气，但又不说。', 'type': 'loop', 'reversed': False},
            {'id': 17, 'text': '你会觉得别人不懂感恩，从而更冷。', 'type': 'loop', 'reversed': False},
            {'id': 18, 'text': '你会不断回忆过去更好的时候，难以适应现在。', 'type': 'loop', 'reversed': False},
            {'id': 19, 'text': '你会把小事放大成“他们不在乎我”。', 'type': 'loop', 'reversed': False},
            {'id': 20, 'text': '你会陷入委屈循环，越想越累。', 'type': 'loop', 'reversed': False},
            {'id': 21, 'text': '你会对未来充满灾难想象，变得恐慌。', 'type': 'grip', 'reversed': False},
            {'id': 22, 'text': '你会把未知当成巨大威胁。', 'type': 'grip', 'reversed': False},
            {'id': 23, 'text': '你会突然想逃离责任，什么都不想管。', 'type': 'grip', 'reversed': False},
            {'id': 24, 'text': '你会焦虑到无法专注，脑子停不下来。', 'type': 'grip', 'reversed': False},
            {'id': 25, 'text': '你会对变化非常敏感，感觉不安全。', 'type': 'grip', 'reversed': False},
            {'id': 26, 'text': '你会变得多疑，担心会发生坏事。', 'type': 'grip', 'reversed': False},
            {'id': 27, 'text': '你会开始怀疑自己是否能应付未来。', 'type': 'grip', 'reversed': False},
            {'id': 28, 'text': '你会过度担心各种可能性，难以放松。', 'type': 'grip', 'reversed': False},
            {'id': 29, 'text': '你会觉得世界不稳定，想抓住点什么。', 'type': 'grip', 'reversed': False},
            {'id': 30, 'text': '你会出现“我要跑路/我要躲起来”的冲动。', 'type': 'grip', 'reversed': False},
        ]
    },
    'ISTP': {
        "scale_min": 1,
        "scale_max": 6,
        'questions': [
            {'id': 1, 'text': '你能在行动中保持冷静与判断力。', 'type': 'maturity', 'reversed': False},
            {'id': 2, 'text': '你会因为不想麻烦而拒绝沟通需求。', 'type': 'maturity', 'reversed': True},
            {'id': 3, 'text': '你能在必要时与他人协作，而不是完全单打独斗。', 'type': 'maturity', 'reversed': False},
            {'id': 4, 'text': '你会压抑情绪，觉得“无所谓”，其实在积累。', 'type': 'maturity', 'reversed': True},
            {'id': 5, 'text': '你能在自由与责任之间找到平衡。', 'type': 'maturity', 'reversed': False},
            {'id': 6, 'text': '你会逃避承诺或长期计划，怕被束缚。', 'type': 'maturity', 'reversed': True},
            {'id': 7, 'text': '你能把兴趣转化为稳定技能与成果。', 'type': 'maturity', 'reversed': False},
            {'id': 8, 'text': '你会因为厌烦规则而故意对抗。', 'type': 'maturity', 'reversed': True},
            {'id': 9, 'text': '你会对情感表达不耐烦，甚至回避。', 'type': 'maturity', 'reversed': True},
            {'id': 10, 'text': '你能在压力下保持节奏，而不是完全摆烂或爆掉。', 'type': 'maturity', 'reversed': False},
            {'id': 11, 'text': '你会陷入虚无与怀疑：做这些有什么意义。', 'type': 'loop', 'reversed': False},
            {'id': 12, 'text': '你会在脑子里空转，迟迟不愿动手。', 'type': 'loop', 'reversed': False},
            {'id': 13, 'text': '你会变得消极，觉得一切都没用。', 'type': 'loop', 'reversed': False},
            {'id': 14, 'text': '你会开始怀疑别人动机，像阴谋论。', 'type': 'loop', 'reversed': False},
            {'id': 15, 'text': '你会越想越丧，动不起来。', 'type': 'loop', 'reversed': False},
            {'id': 16, 'text': '你会把自己关起来，不想见人。', 'type': 'loop', 'reversed': False},
            {'id': 17, 'text': '你会觉得世界很烦，想彻底躲开。', 'type': 'loop', 'reversed': False},
            {'id': 18, 'text': '你会不断想“算了”，对什么都提不起劲。', 'type': 'loop', 'reversed': False},
            {'id': 19, 'text': '你会在脑中反复推演，但不愿实际尝试。', 'type': 'loop', 'reversed': False},
            {'id': 20, 'text': '你会越想越麻木，像瘫痪。', 'type': 'loop', 'reversed': False},
            {'id': 21, 'text': '你会突然变得很在意别人是否喜欢你。', 'type': 'grip', 'reversed': False},
            {'id': 22, 'text': '你会情绪爆炸或像孩子一样发脾气。', 'type': 'grip', 'reversed': False},
            {'id': 23, 'text': '你会觉得没人理解你，于是敏感或易怒。', 'type': 'grip', 'reversed': False},
            {'id': 24, 'text': '你会突然很想得到肯定，甚至讨好。', 'type': 'grip', 'reversed': False},
            {'id': 25, 'text': '你会想摊牌解决关系问题。', 'type': 'grip', 'reversed': False},
            {'id': 26, 'text': '你会在社交里失去分寸或突然想切断联系。', 'type': 'grip', 'reversed': False},
            {'id': 27, 'text': '你会很在意别人怎么看你。', 'type': 'grip', 'reversed': False},
            {'id': 28, 'text': '你会想被照顾，不想再扛。', 'type': 'grip', 'reversed': False},
            {'id': 29, 'text': '你会突然很委屈，想“我为什么要这样”。', 'type': 'grip', 'reversed': False},
            {'id': 30, 'text': '你会摆烂或爆掉，出现彻底停摆。', 'type': 'grip', 'reversed': False},
        ]
    },
}


here = os.path.dirname(os.path.abspath(__file__))
candidates = [
    os.path.join(here, "bank.json"),
    os.path.join(os.path.dirname(here), "bank.json"),
]

BANK: Dict[str, Any] = MBTI_BANK  # type: ignore



def _get_bank_for_type(mbti_type: str) -> Dict[str, Any]:
    t = (mbti_type or "").upper().strip()
    if t not in BANK:
        raise HTTPException(status_code=404, detail=f"Bank not found for type={t}")
    return BANK[t]


# -------------------------
# Scoring (server-side only)
# -------------------------
def _reverse_if_needed(raw: int, reversed_: bool, scale_min: int, scale_max: int) -> int:
    # same logic: v = (max + min) - v
    return (scale_max + scale_min) - raw if reversed_ else raw


def _normalize(score_sum: int, min_sum: int, max_sum: int) -> int:
    if max_sum == min_sum:
        return 0
    v = (score_sum - min_sum) / (max_sum - min_sum)
    v = max(0.0, min(1.0, v))
    return int(round(v * 100))


def _coherence(values: List[int]) -> int:
    if not values:
        return 0
    mean = sum(values) / len(values)
    var = sum((x - mean) ** 2 for x in values) / len(values)
    std = sqrt(var)
    return int(round((1 - min(1.0, std / 2.5)) * 100))


NarrativeKey = Literal["stable", "overload", "highLoop", "mixed"]


def _pick_narrative_key(l: int, g: int, load: int) -> NarrativeKey:
    if g >= 65 or load >= 75:
        return "overload"
    if l >= 65:
        return "highLoop"
    if l < 35 and g < 35 and load < 65:
        return "stable"
    return "mixed"


def compute_scores_and_report(mbti_type: str, answers: Dict[int, int]) -> Dict[str, Any]:
    bank = _get_bank_for_type(mbti_type)
    questions: List[Dict[str, Any]] = bank.get("questions", [])

    scale_min = int(bank.get("scale_min", SCALE_MIN_DEFAULT))
    scale_max = int(bank.get("scale_max", SCALE_MAX_DEFAULT))

    if len(questions) != 30:
        # allow but warn-like error to keep consistency
        raise HTTPException(status_code=500, detail=f"Bank questions count != 30 for {mbti_type}")

    # Validate: all qids present, values in range
    qids = [int(q["id"]) for q in questions]
    missing = [qid for qid in qids if qid not in answers]
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing answers for qids: {missing}")

    bad = {qid: v for qid, v in answers.items() if v < scale_min or v > scale_max}
    if bad:
        raise HTTPException(status_code=400, detail=f"Answer values must be {scale_min}..{scale_max}. Bad: {bad}")

    # bounds per dimension: 10 questions each
    per_dim = 10
    min_sum = per_dim * scale_min
    max_sum = per_dim * scale_max

    maturity_vals: List[int] = []
    loop_vals: List[int] = []
    grip_vals: List[int] = []
    raw_vals: List[int] = []

    maturity_sum = 0
    loop_sum = 0
    grip_sum = 0

    for q in questions:
        qid = int(q["id"])
        raw = int(answers[qid])
        raw_vals.append(raw)

        qtype = str(q.get("type", "")).strip()
        rev = bool(q.get("reversed", False))

        v = _reverse_if_needed(raw, rev, scale_min, scale_max)

        if qtype == "maturity":
            maturity_vals.append(v)
            maturity_sum += v
        elif qtype == "loop":
            loop_vals.append(v)
            loop_sum += v
        elif qtype == "grip":
            grip_vals.append(v)
            grip_sum += v
        else:
            raise HTTPException(status_code=500, detail=f"Unknown question type: {qtype} (qid={qid})")

    m = _normalize(maturity_sum, min_sum, max_sum)
    l = _normalize(loop_sum, min_sum, max_sum)
    g = _normalize(grip_sum, min_sum, max_sum)

    coh = int(round((_coherence(maturity_vals) + _coherence(loop_vals) + _coherence(grip_vals)) / 3))

    mean_raw = sum(raw_vals) / len(raw_vals)
    load = int(round(((mean_raw - scale_min) / (scale_max - scale_min)) * 100))

    inv_loop = 100 - l
    inv_grip = 100 - g
    inv_load = 100 - load

    # weights (keep on server only)
    overall = int(round(0.25 * m + 0.20 * coh + 0.20 * inv_loop + 0.20 * inv_grip + 0.15 * inv_load))

    scores = {"m": m, "l": l, "g": g, "coh": coh, "load": load, "o": overall}

    # -------------------------
    # descriptions (server-side, so front-end has zero logic)
    # -------------------------
    def desc_m(val: int) -> str:
        if val >= 67:
            return "高：整合度较高，能把想法、情绪与现实反馈合在一起，行动更稳定。"
        if val >= 34:
            return "中：思路与自我认知在成形，持续迭代会越来越顺。"
        return "低：容易被旧模式牵引；更需要外部反馈与小步验证。"

    def desc_l(val: int) -> str:
        if val < 35:
            return "低：反复推演较少，启动成本更低。"
        if val < 65:
            return "中：有一定反刍，偶尔卡在细节里。"
        return "高：更容易反复纠结，行动阻力增大。"

    def desc_g(val: int) -> str:
        if val < 35:
            return "低：压力信号较轻，恢复更容易。"
        if val < 65:
            return "中：负荷期需要刻意恢复与边界。"
        return "高：处在高压边缘，注意力更难稳定。"

    def desc_load(val: int) -> str:
        if val < 35:
            return "轻：节奏较松，余量更足。"
        if val < 65:
            return "中：强度适中，注意别长期无休。"
        return "重：整体偏满，优先做减负与恢复。"

    def desc_coh(val: int) -> str:
        if val >= 70:
            return "高：作答更一致，内在标准较清晰。"
        if val >= 55:
            return "中：状态略有波动，但仍可自我校准。"
        return "低：近期可能摇摆较多，建议先稳节奏。"

    def desc_o(val: int) -> str:
        if val >= 75:
            return "充盈：恢复与输出相对平衡，适合做中长期推进。"
        if val >= 55:
            return "可用：可稳定推进，但避免把强度拉满太久。"
        if val >= 35:
            return "偏疲：更需要恢复与拆解任务，先把可交付做小。"
        return "高压：建议减负优先：睡眠、饮食、轻运动与求助。"

    descriptions = {
        "m": desc_m(m),
        "l": desc_l(l),
        "g": desc_g(g),
        "load": desc_load(load),
        "coh": desc_coh(coh),
        "o": desc_o(overall),
    }

    # -------------------------
    # Narrative (keep in backend)
    # You can plug your own MBTI narrative dict here.
    # For now: default narrative only (safe fallback)
    # -------------------------
    key: NarrativeKey = _pick_narrative_key(l, g, load)

    def default_insight(k: NarrativeKey) -> str:
        if k == "stable":
            return "你当前更像“稳态推进”：想得清楚、行动阻力不大，同时还能保留恢复空间。"
        if k == "overload":
            return f"你处在“高负荷/高压”区间：压力信号更强（Grip {g}/100，负荷 {load}/100），注意力更难稳定。"
        if k == "highLoop":
            return f"你的内耗倾向偏高（Loop {l}/100）：可能在反复推演、过度打磨或过度比较，导致启动成本变高。"
        return f"当前状态：可推进但不算满稳（Loop {l} / Grip {g} / Load {load}）。负荷或压力有一定存在感。"

    def default_advice(k: NarrativeKey) -> str:
        if k == "stable":
            return "把优势用在“可交付的小步”上：每周固定 1 次复盘，并留出 1～2 个无任务时段做恢复。"
        if k == "overload":
            return "优先做恢复与减负：把今天目标缩减为 1 件可交付小成果；睡眠与饮食先稳定，再做身体回正。"
        if k == "highLoop":
            return "做一次“外部打断”：安排 30 分钟低门槛行动（整理/散步/写 10 行计划），让身体先动起来。"
        return "今天用“最小交付 + 明确休息”推进：只保留 1 个最小成果，同时给自己留出恢复窗口。"

    insight = default_insight(key)
    advice = default_advice(key)

    # -------------------------
    # Radar data (server computed, front only renders)
    # -------------------------
    radar = {
        "labels": ["认知成熟度", "自洽度", "内耗弹性", "压力弹性", "负荷余量", "状态指数"],
        "values": [m, coh, 100 - l, 100 - g, 100 - load, overall],
    }

    # status_tag: fully server-defined (front doesn’t infer)
    status_tag = {
        "stable": "稳态推进",
        "overload": "高压/过载",
        "highLoop": "高内耗循环",
        "mixed": "轻度波动",
    }[key]

    return {
        "type": (mbti_type or "").upper().strip(),
        "scores": scores,
        "descriptions": descriptions,
        "narrative_key": key,
        "status_tag": status_tag,
        "insight": insight,
        "advice": advice,
        "radar": radar,
    }


# -------------------------
# API Schemas
# -------------------------
class ReportRequest(BaseModel):
    type: MbtiType = Field(..., description="MBTI type, e.g. INTP")
    answers: Dict[str, int] = Field(..., description='answers as {"1":3,"2":6,...}')

    @validator("type")
    def _upper(cls, v: str) -> str:
        return (v or "").upper().strip()

    @validator("answers")
    def _nonempty(cls, v: Dict[str, int]) -> Dict[str, int]:
        if not v:
            raise ValueError("answers is empty")
        return v


# -------------------------
# FastAPI app
# -------------------------
app = FastAPI(title="MBTI Compass API", version="2.0.0")

# If you deploy frontend+backend on different domains, enable CORS.
# If on same Vercel domain, it's fine to keep as-is.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten if you want: ["https://your-domain.vercel.app"]
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    return {"ok": True}


@app.get("/api/bank")
def get_bank(type: str = Query(..., description="MBTI type, e.g. INTP")):
    bank = _get_bank_for_type(type)

    # return ONLY what frontend needs to render
    # do NOT expose `type` / `reversed` fields, to reduce copy risk
    questions = bank.get("questions", [])
    out_questions = [{"id": int(q["id"]), "text": str(q["text"])} for q in questions]

    return {
        "type": (type or "").upper().strip(),
        "scale_min": int(bank.get("scale_min", SCALE_MIN_DEFAULT)),
        "scale_max": int(bank.get("scale_max", SCALE_MAX_DEFAULT)),
        "questions": out_questions,
    }


@app.post("/api/report")
def report(req: ReportRequest):
    # answers: {"1":3,...} -> {1:3,...}
    try:
        answers_int: Dict[int, int] = {}
        for k, v in req.answers.items():
            ks = str(k).strip()
            if ks.upper().startswith("Q"):
                ks = ks[1:]
            qid = int(ks)
            answers_int[qid] = int(v)
    except Exception:
        raise HTTPException(status_code=400, detail="answers keys must be numeric (e.g. '1'..'30')")

    return compute_scores_and_report(req.type, answers_int)


# Local run:
# uvicorn api.index:app --reload
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)