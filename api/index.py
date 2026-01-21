from __future__ import annotations
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware # <--- 新增这行
from pydantic import BaseModel
from typing import Dict, List
import statistics
import random


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源（本地调试用）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# ==========================================
# 1. 核心数据：题库
# ==========================================

MBTI_BANK = {
    "INTP": [
        {"id": 1, "text": "当你的推理与现实反馈不一致时，你愿意调整自己的判断。", "type": "maturity", "reversed": False},
        {"id": 2, "text": "你常把想法停留在脑中推演，很难进入验证或执行。", "type": "maturity", "reversed": True},
        {"id": 3, "text": "你能承认情绪是信息的一种，并愿意倾听它。", "type": "maturity", "reversed": False},
        {"id": 4, "text": "你更愿意依赖熟悉的方法，而回避探索新路径。", "type": "maturity", "reversed": True},
        {"id": 5, "text": "你经常“想得很多、动得很少”，导致计划反复推倒重来。", "type": "maturity", "reversed": True},
        {"id": 6, "text": "你能把抽象想法讲清楚，让别人听得懂、接得住。", "type": "maturity", "reversed": False},
        {"id": 7, "text": "你很难对不同观点保持好奇，容易直接否定。", "type": "maturity", "reversed": True},
        {"id": 8, "text": "你既能提出新点子，也能耐心处理落地细节。", "type": "maturity", "reversed": False},
        {"id": 9, "text": "你会因追求“更完美的方案”而迟迟无法启动。", "type": "maturity", "reversed": True},
        {"id": 10, "text": "你会主动寻找外界反馈，以发现自己的盲点。", "type": "maturity", "reversed": False},
        {"id": 11, "text": "你最近会反复回想过去的失误，很难放下。", "type": "loop", "reversed": False},
        {"id": 12, "text": "面对新机会时，你的第一反应是担心重蹈覆辙。", "type": "loop", "reversed": False},
        {"id": 13, "text": "你会陷入长时间分析，但最后很难产出具体行动。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你更相信自己掌握的细节，而对新方向缺乏信心。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你会回避社交或新信息，因为它们让你更累。", "type": "loop", "reversed": False},
        {"id": 16, "text": "你会为一些并不关键的小问题消耗大量精力。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你明明知道该推进，却迟迟动不起来。", "type": "loop", "reversed": False},
        {"id": 18, "text": "你会对建议变得更防御，觉得别人不理解你的处境。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你会在脑中反复演练最坏情况，从而更难决定。", "type": "loop", "reversed": False},
        {"id": 20, "text": "你更倾向于维持熟悉的状态，而回避改变。", "type": "loop", "reversed": False},
        {"id": 21, "text": "压力大时，你会更敏感，容易误解别人的意图。", "type": "grip", "reversed": False},
        {"id": 22, "text": "你会用吃、睡、刷短视频等方式“麻醉式”恢复。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你会因小事情绪爆发，和以往的自己不太一样。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你会强烈渴望被看见、被肯定。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你会觉得大脑很乱，难以保持清晰思考。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你会用讽刺、冷处理等方式表达不满。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你会觉得自己付出很多却得不到回报，从而更委屈。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你很难集中注意力，容易机械性地刷手机。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你会更在意他人评价，甚至做出不符合自己节奏的选择。", "type": "grip", "reversed": False},
        {"id": 30, "text": "你会出现明显的摆烂冲动，或想把事情一把推翻。", "type": "grip", "reversed": False}
    ],
    "INFJ": [
        {"id": 1, "text": "当现实情况与你的直觉预判不符时，你能灵活调整而不固执己见。", "type": "maturity", "reversed": False},
        {"id": 2, "text": "你经常活在未来的愿景里，而忽略了当下的生活琐事和身体照顾。", "type": "maturity", "reversed": True},
        {"id": 3, "text": "你能在坚持自我价值观的同时，用他人能接受的方式温和地表达。", "type": "maturity", "reversed": False},
        {"id": 4, "text": "你总觉得自己的洞察力“高人一等”，很难真正听取他人的建议。", "type": "maturity", "reversed": True},
        {"id": 5, "text": "因为过度追求完美的时机或方案，你的很多理想从未开始执行。", "type": "maturity", "reversed": True},
        {"id": 6, "text": "你能将复杂的抽象直觉，转化为具体可行的步骤去帮助他人。", "type": "maturity", "reversed": False},
        {"id": 7, "text": "一旦认定了某件事的意义，你就会忽略客观现实的阻碍强行推进。", "type": "maturity", "reversed": True},
        {"id": 8, "text": "你不仅能共情他人的痛苦，还能设立健康的边界保护自己的能量。", "type": "maturity", "reversed": False},
        {"id": 9, "text": "你习惯甚至享受一种“曲高和寡”的孤独感，而拒绝融入群体。", "type": "maturity", "reversed": True},
        {"id": 10, "text": "你会主动通过实际行动来验证你的直觉，而不仅仅是在脑中推演。", "type": "maturity", "reversed": False},
        {"id": 11, "text": "最近你把自己封闭起来，觉得社交纯粹是在浪费时间。", "type": "loop", "reversed": False},
        {"id": 12, "text": "你会像手术刀一样冷酷地剖析身边人的动机，觉得他们都很虚伪。", "type": "loop", "reversed": False},
        {"id": 13, "text": "你陷入一种逻辑死循环，试图在脑中构建一个无懈可击的真理。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你变得非常批判和挑剔，对他人的情感表达感到不耐烦。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你觉得自己彻底“看透”了某些事情的悲剧结局，因此拒绝任何尝试。", "type": "loop", "reversed": False},
        {"id": 16, "text": "你拒绝向外求助，坚信只有自己才能解决自己的问题。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你脑中有大量的分析和批判，但在外人看来你只是在发呆或沉默。", "type": "loop", "reversed": False},
        {"id": 18, "text": "你对外部世界感到一种虚无感，觉得一切都没有意义。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你会为了证明自己的逻辑正确，而忽略在这个过程中对他人的伤害。", "type": "loop", "reversed": False},
        {"id": 20, "text": "你固执地坚持自己的主观判断，即使客观事实摆在眼前也不愿承认。", "type": "loop", "reversed": False},
        {"id": 21, "text": "压力极大时，你会突然沉迷于暴饮暴食、酗酒或疯狂购物。", "type": "grip", "reversed": False},
        {"id": 22, "text": "你会对环境中的噪音、强光或混乱感到前所未有的暴躁。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你会突然痴迷于整理房间、打扫卫生或纠结外表细节。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你会做出一些平时绝对不会做的冲动、冒险或鲁莽的行为。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你感觉身体感官被无限放大，一点点不适都会让你抓狂。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你会因为找不到某样东西或电器故障而瞬间情绪崩溃。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你会用机械性的感官刺激（如无脑刷剧、打游戏）来麻痹大脑。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你会觉得自己正在与物理世界“为敌”，觉得万物都在针对你。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你会突然过度关注当下的享乐，完全抛弃了长远的计划。", "type": "grip", "reversed": False},
        {"id": 30, "text": "你有一种强烈的破坏欲，想要摔东西或毁掉正在做的事。", "type": "grip", "reversed": False}
    ],

    "INFP": [
        {"id": 1, "text": "你能将内心丰富的情感转化为某种形式的作品（文字、艺术、行动），而不仅仅是空想。", "type": "maturity", "reversed": False},
        {"id": 2, "text": "你经常因为害怕冲突或被批评，而不敢表达自己真实的价值观。", "type": "maturity", "reversed": True},
        {"id": 3, "text": "你对他人的不同生活方式保持开放和好奇，而不是用自己的道德标准暗自评判。", "type": "maturity", "reversed": False},
        {"id": 4, "text": "你经常觉得自己是受害者，认为这个世界对你太残酷、太不公平。", "type": "maturity", "reversed": True},
        {"id": 5, "text": "你在面对困难时，习惯通过“幻想一个完美的未来”来逃避现实的压力。", "type": "maturity", "reversed": True},
        {"id": 6, "text": "你能够接纳自己的不完美，并意识到成长是一个动态的过程。", "type": "maturity", "reversed": False},
        {"id": 7, "text": "你对外界的评价极度敏感，一句无心的话就能让你难过好几天。", "type": "maturity", "reversed": True},
        {"id": 8, "text": "你不仅有同情心，还能在关键时刻为了捍卫信念而表现出惊人的坚定。", "type": "maturity", "reversed": False},
        {"id": 9, "text": "你经常因为“感觉不对”就随意放弃已经开始的重要计划。", "type": "maturity", "reversed": True},
        {"id": 10, "text": "你愿意走出舒适区去接触新的人和事，以此来丰富你的内心世界。", "type": "maturity", "reversed": False},

        {"id": 11, "text": "最近你总是反复回想过去犯过的错误或尴尬瞬间，感到深深的羞耻。", "type": "loop", "reversed": False},
        {"id": 12, "text": "你觉得自己被困住了，这辈子就这样了，对未来没有任何新鲜的期待。", "type": "loop", "reversed": False},
        {"id": 13, "text": "你拒绝尝试任何新事物，只愿意呆在熟悉的环境里重复旧的模式。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你变得特别记仇，过去的一点小伤害在脑海里被无限放大。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你通过不断回忆“过去的美好时光”来逃避现在的平庸，却越发感到失落。", "type": "loop", "reversed": False},
        {"id": 16, "text": "你把自己隔离起来，拒绝与朋友交流，觉得没人能理解你的痛苦。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你对细节变得异常执着，反复检查自己哪里做得不够好。", "type": "loop", "reversed": False},
        {"id": 18, "text": "你内心充满了一种陈旧的、沉重的忧郁感，很难提得起劲。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你认为现在的困境是无法改变的宿命，放弃了寻找出路的努力。", "type": "loop", "reversed": False},
        {"id": 20, "text": "你对外界的新建议充耳不闻，固守着自己的一套旧逻辑。", "type": "loop", "reversed": False},

        {"id": 21, "text": "压力极大时，你会突然变得非常刻薄，用最伤人的逻辑去攻击别人。", "type": "grip", "reversed": False},
        {"id": 22, "text": "你会突然对“效率”变得病态执着，急于把所有事情立刻解决。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你觉得周围的人都笨得不可救药，对他们的无能感到极度愤怒。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你会开启“暴君模式”，强行命令别人照你说的做，不容反驳。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你变得愤世嫉俗，认为所谓的理想和情感都是毫无价值的垃圾。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你会为了完成任务而完全无视自己和他人的感受，变得冷酷无情。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你会突然罗列出一堆清单或计划，试图强行控制失序的生活，但往往半途而废。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你对他人的评价变得非黑即白，没有任何中间地带。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你感到一种要摧毁一切的冲动，只因为事情没有按计划进行。", "type": "grip", "reversed": False},
        {"id": 30, "text": "你会指责别人拖累了你，把所有的不满都向外发泄。", "type": "grip", "reversed": False}
    ],
    
    "INTJ": [
        {"id": 1, "text": "你不仅有宏大的愿景，还能制定出严密可行的执行步骤。", "type": "maturity", "reversed": False},
        {"id": 2, "text": "当客观数据与你的直觉相悖时，你会认为是数据错了，拒绝修正观点。", "type": "maturity", "reversed": True},
        {"id": 3, "text": "你能够接受“足够好”的方案并推进，而不是为了追求完美而停滞不前。", "type": "maturity", "reversed": False},
        {"id": 4, "text": "你经常因为觉得别人的执行力太差或太蠢，而拒绝与任何人合作。", "type": "maturity", "reversed": True},
        {"id": 5, "text": "你为了维护自己的理论模型，会有意无意地忽略那些反面证据。", "type": "maturity", "reversed": True},
        {"id": 6, "text": "你愿意为了达成目标而妥协部分细节，注重结果的有效性。", "type": "maturity", "reversed": False},
        {"id": 7, "text": "你总是活在未来，导致当下的生活一团糟，甚至无法照顾好自己。", "type": "maturity", "reversed": True},
        {"id": 8, "text": "你能够用客观、逻辑的语言向他人解释你的直觉，而不是让他们“只管照做”。", "type": "maturity", "reversed": False},
        {"id": 9, "text": "你内心深处有一种智力优越感，很难真正听取他人的建议。", "type": "maturity", "reversed": True},
        {"id": 10, "text": "你会主动设立一个个里程碑，通过阶段性成果来验证你的远见。", "type": "maturity", "reversed": False},
        {"id": 11, "text": "最近你觉得周围的人都不可信，甚至觉得他们在暗中针对你。", "type": "loop", "reversed": False},
        {"id": 12, "text": "你沉浸在一种“没有人能理解我”的悲剧英雄感中，并拒绝沟通。", "type": "loop", "reversed": False},
        {"id": 13, "text": "你会反复咀嚼过去被背叛或被误解的经历，感到愤愤不平。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你变得非常情绪化和敏感，这与平时那个理性的你判若两人。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你仅仅依据个人的好恶（而非客观事实）就对他人的动机进行道德审判。", "type": "loop", "reversed": False},
        {"id": 16, "text": "你完全切断了与外部世界的互动，活在自己的精神堡垒里。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你觉得自己也是为了大家好，但为什么总是被辜负？", "type": "loop", "reversed": False},
        {"id": 18, "text": "你对未来充满了灾难化的想象，并且深信这些坏结果一定会发生。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你拒绝接受任何客观解释，固执地相信自己的主观感受才是真理。", "type": "loop", "reversed": False},
        {"id": 20, "text": "你在没有任何证据的情况下，就已经在心里给某件事判了死刑。", "type": "loop", "reversed": False},
        {"id": 21, "text": "压力极大时，你会突然开始暴饮暴食、酗酒或沉迷于肉体享乐。", "type": "grip", "reversed": False},
        {"id": 22, "text": "你会因为一点点噪音、强光或环境混乱而变得暴怒。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你会突然痴迷于清洁、整理或某些无关紧要的物理细节。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你会产生一种强烈的冲动，想要把眼前的东西砸烂或毁掉。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你会进行报复性的冲动消费，买一堆完全没用的东西。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你感觉大脑停止了思考，完全被当下的感官欲望所控制。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你会突然做一些高风险、鲁莽的身体活动（如飙车、极限运动）。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你对自己的外表或身体状况突然产生极度的焦虑或强迫性关注。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你觉得自己像是在和整个物理世界作战，所有东西都在和你作对。", "type": "grip", "reversed": False},
        {"id": 30, "text": "你通过过度的机械性劳动（如一直做家务）来逃避思考。", "type": "grip", "reversed": False}
    ],

    "ENTJ": [
        {"id": 1, "text": "你不仅追求当下的胜利，更在意这个胜利是否符合长期的战略蓝图。", "type": "maturity", "reversed": False},
        {"id": 2, "text": "你经常打断别人的发言，认为他们的想法太蠢或太慢，完全不值得听。", "type": "maturity", "reversed": True},
        {"id": 3, "text": "你懂得“灰度管理”，明白并非所有事情都需要通过高压手段立刻解决。", "type": "maturity", "reversed": False},
        {"id": 4, "text": "为了达成目标，你会毫不犹豫地牺牲团队成员的利益或情感，视人为工具。", "type": "maturity", "reversed": True},
        {"id": 5, "text": "你经常因为追求速度而忽略了潜在的隐患，导致后期返工。", "type": "maturity", "reversed": True},
        {"id": 6, "text": "你能够识别并培养他人的潜力，而不是仅仅把他们当作执行指令的手脚。", "type": "maturity", "reversed": False},
        {"id": 7, "text": "你对异己的声音零容忍，任何反对意见都会被你视为挑战权威。", "type": "maturity", "reversed": True},
        {"id": 8, "text": "你在做决策时，能够平衡“理性的最优解”与“人心的接受度”。", "type": "maturity", "reversed": False},
        {"id": 9, "text": "你沉迷于权力和地位的象征，而忽略了创造真正的价值。", "type": "maturity", "reversed": True},
        {"id": 10, "text": "你会定期复盘，承认自己的决策失误并迅速调整方向。", "type": "maturity", "reversed": False},
        {"id": 11, "text": "你感到必须每时每刻都在“做事”，一旦停下来思考就会感到极度焦虑。", "type": "loop", "reversed": False},
        {"id": 12, "text": "你开始追求即时的满足感（如赚快钱、感官享乐），抛弃了长远计划。", "type": "loop", "reversed": False},
        {"id": 13, "text": "你变得非常鲁莽，不做调研就直接拍板，只想立刻看到结果。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你对他人的“慢动作”完全失去耐心，经常表现出暴躁的攻击性。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你通过高强度的物质享受（名车、派对、奢侈品）来证明自己的成功。", "type": "loop", "reversed": False},
        {"id": 16, "text": "你发现自己像个无头苍蝇一样忙碌，但其实并没有解决核心问题。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你排斥任何深度的理论探讨，觉得那些都是“浪费时间的废话”。", "type": "loop", "reversed": False},
        {"id": 18, "text": "你试图用强硬的态度碾压一切，不管对方说得有没有道理。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你为了维持表面的“赢家形象”，不惜透支身体或财务。", "type": "loop", "reversed": False},
        {"id": 20, "text": "你很难独处，需要不断的外界刺激（热闹、竞争）来填补空虚。", "type": "loop", "reversed": False},
        {"id": 21, "text": "最近你突然觉得没人真正关心你，大家都只是在利用你。", "type": "grip", "reversed": False},
        {"id": 22, "text": "你会因为一些微不足道的小事而感到深深的委屈，甚至想哭。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你开始质疑自己奋斗半生的意义，觉得一切都空虚无聊。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你变得对身边人的忠诚度极度敏感，总觉得有人要背叛你。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你突然变得很“甚至有些迷信”，试图从非理性的角度寻找安慰。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你感觉自己的逻辑能力突然消失了，被混乱的情绪淹没。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你会躲起来生闷气，觉得全世界都对不起你。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你对别人的评价变得异常敏感，一句批评就能击碎你的自尊。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你觉得自己一直戴着面具生活，内心深处是一个没人爱的孤儿。", "type": "grip", "reversed": False},
        {"id": 30, "text": "你会突然爆发出强烈的情绪（愤怒或悲伤），把身边人吓一跳。", "type": "grip", "reversed": False}
    ],
    "ENFJ": [
        {"id": 1, "text": "你不仅能让大家感到开心，更能通过深刻的洞察力指引他们成长的方向。", "type": "maturity", "reversed": False},
        {"id": 2, "text": "你常常为了维持表面的和谐，而不得不压抑自己真实的想法和需求。", "type": "maturity", "reversed": True},
        {"id": 3, "text": "你能够一眼看穿他人行为背后的深层动机，而不仅仅停留在表面。", "type": "maturity", "reversed": False},
        {"id": 4, "text": "你的自我价值感几乎完全取决于他人对你的赞美和肯定。", "type": "maturity", "reversed": True},
        {"id": 5, "text": "你经常打着“为你好”的旗号，强行介入他人的生活或做决定。", "type": "maturity", "reversed": True},
        {"id": 6, "text": "你懂得设立健康的边界，在帮助他人的同时不会耗尽自己的能量。", "type": "maturity", "reversed": False},
        {"id": 7, "text": "你很难拒绝别人的请求，即使那会让你自己陷入困境。", "type": "maturity", "reversed": True},
        {"id": 8, "text": "你善于挖掘每个人的潜力，并能通过愿景激励团队共同前进。", "type": "maturity", "reversed": False},
        {"id": 9, "text": "你经常感到自己像个“变色龙”，在不同人面前扮演不同的角色，弄丢了真实的自己。", "type": "maturity", "reversed": True},
        {"id": 10, "text": "当群体走向错误方向时，你敢于为了长远利益而提出反对意见，哪怕破坏暂时的气氛。",
         "type": "maturity", "reversed": False},
        {"id": 11, "text": "你最近极度渴望热闹，一刻也闲不下来，必须通过社交来填补时间。", "type": "loop", "reversed": False},
        {"id": 12, "text": "你变得过度在意自己的外表、形象或排场，花费大量精力在“面子工程”上。", "type": "loop", "reversed": False},
        {"id": 13, "text": "你为了融入群体或活跃气氛，会不假思索地做出一些冲动、浮夸的行为。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你发现自己开始热衷于肤浅的八卦或是非，而不再进行有深度的对话。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你对“错过”（FOMO）感到极度焦虑，看到别人聚会没叫你就会很难受。", "type": "loop", "reversed": False},
        {"id": 16, "text": "你根本无法独处，一旦安静下来就会感到莫名的恐慌和空虚。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你变得非常急躁，只追求当下的快乐和反馈，完全不想未来的后果。", "type": "loop", "reversed": False},
        {"id": 18, "text": "你对他人的评价反应过度，为了博取关注而做出戏剧化的举动。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你感觉自己像是在“表演”生活，虽然周围很热闹，内心却觉得很空洞。", "type": "loop", "reversed": False},
        {"id": 20, "text": "你会盲目追随当下的潮流或他人的意见，完全失去了自己的主见。", "type": "loop", "reversed": False},
        {"id": 21, "text": "最近你突然变得很冷漠，开始用批判性的眼光审视身边的人。", "type": "grip", "reversed": False},
        {"id": 22, "text": "你会揪住别人话语中的逻辑漏洞不放，变得非常爱钻牛角尖。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你觉得周围的人都很虚伪、愚蠢，只有你一个人看透了“丑陋的真相”。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你开始自我隔离，沉迷于研究一些晦涩的理论或数据，以此逃避情感。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你对自己进行残酷的逻辑批判，列举出无数证据证明自己是无能的。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你感到情感系统完全关闭了，只剩下冷冰冰的、甚至带有攻击性的逻辑。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你会突然因为一个逻辑上的小问题，而全盘否定一段关系的价值。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你认为别人的善意背后一定有某种功利性的逻辑动机。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你试图用绝对理性的方式去解决所有情感问题，结果把事情搞得更糟。", "type": "grip", "reversed": False},
        {"id": 30, "text": "你脑子里充满了复杂的阴谋论，觉得世界是一个巨大的、设计精密的谎言。", "type": "grip", "reversed": False}
    ],
    "ENTP": [
        {"id": 1, "text": "你不仅擅长发现别人的逻辑漏洞，更能提出具有建设性的替代方案。", "type": "maturity", "reversed": False},
        {"id": 2, "text": "你经常为了享受“赢”的快感而与人争论，哪怕你其实心里并不认同那个观点。", "type": "maturity", "reversed": True},
        {"id": 3, "text": "你有能力筛选那些漫无边际的想法，并用严谨的逻辑将其转化为可落地的项目。", "type": "maturity", "reversed": False},
        {"id": 4, "text": "你开启了无数个新计划，但真正完成的寥寥无几，留下一堆烂摊子。", "type": "maturity", "reversed": True},
        {"id": 5, "text": "你经常因为觉得无聊或失去新鲜感，就随意抛弃对他人的承诺。", "type": "maturity", "reversed": True},
        {"id": 6, "text": "你能够客观地分析问题，不会让个人好恶或外界评价干扰你的逻辑判断。", "type": "maturity", "reversed": False},
        {"id": 7, "text": "你习惯用戏谑或嘲讽的态度对待严肃问题，以此来逃避真正的责任。", "type": "maturity", "reversed": True},
        {"id": 8, "text": "你不仅热衷于打破旧规则，也懂得建立更优的新规则来维持秩序。", "type": "maturity", "reversed": False},
        {"id": 9, "text": "你因为过度自信，经常在准备不足的情况下盲目冒险，导致失败。", "type": "maturity", "reversed": True},
        {"id": 10, "text": "你会主动反思自己的逻辑框架，并愿意根据新的事实进行自我修正。", "type": "maturity", "reversed": False},
        {"id": 11, "text": "你最近极度渴望别人的关注，甚至不惜通过制造混乱或恶作剧来博眼球。", "type": "loop", "reversed": False},
        {"id": 12, "text": "你变得非常在意别人怎么看你，为了讨好群体而放弃了自己的逻辑原则。", "type": "loop", "reversed": False},
        {"id": 13, "text": "你感到内心空虚，必须不断地与人互动或寻求外界刺激来填补。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你发现自己变得情绪化和甚至有些操纵性，试图通过情感影响他人。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你对“被孤立”或“不受欢迎”感到前所未有的焦虑和恐惧。", "type": "loop", "reversed": False},
        {"id": 16, "text": "你做决定时不再依据理性分析，而是看大家喜欢什么或流行什么。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你像个停不下来的“小丑”，在人群中过度表演，回到家却觉得精疲力尽。", "type": "loop", "reversed": False},
        {"id": 18, "text": "你变得偏执，总觉得别人在背后议论你或针对你。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你无法忍受独处和思考，一旦安静下来就会陷入恐慌。", "type": "loop", "reversed": False},
        {"id": 20, "text": "你对批评反应过度，会为了维护面子而进行非理性的反击。", "type": "loop", "reversed": False},
        {"id": 21, "text": "你最近突然对身体健康产生极度焦虑，总怀疑自己得了什么大病。", "type": "grip", "reversed": False},
        {"id": 22, "text": "你会反复咀嚼过去的一个微小失误，感到无法释怀的悔恨。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你突然变得极度保守和僵化，拒绝任何新的可能性或改变。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你开始对细节产生强迫症般的关注（如反复检查文档、整理物品）。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你感到思维枯竭，完全想不出任何新点子，大脑像生锈了一样。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你变得非常孤僻，只想缩在床上或家里，切断与外界的一切联系。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你感到身体极其沉重、疲惫，除了机械性的吃饭睡觉什么都不想做。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你觉得自己过去的所有尝试都是失败的，陷入一种深深的虚无感。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你对日程表或计划的微小变动感到异常烦躁，失去了往日的灵活。", "type": "grip", "reversed": False},
        {"id": 30, "text": "你觉得自己正在慢慢“腐烂”，被琐碎的现实生活彻底压垮。", "type": "grip", "reversed": False}
    ],
    "ENFP": [
        {"id": 1, "text": "你不仅有无穷的新点子，还能筛选出那些最符合你内心价值观的去坚持执行。", "type": "maturity", "reversed": False},
        {"id": 2, "text": "你经常因为不懂拒绝或过度热情，答应了别人太多你根本做不到的事。", "type": "maturity", "reversed": True},
        {"id": 3, "text": "你能够深入体察他人的情感，并用你的乐观给予他们深层的精神支持。", "type": "maturity", "reversed": False},
        {"id": 4, "text": "你总是“三分钟热度”，一旦事情变得枯燥或困难，你就会立马逃跑。", "type": "maturity", "reversed": True},
        {"id": 5, "text": "你经常为了获得别人的喜爱而隐藏真实的自己，事后又感到很委屈。", "type": "maturity", "reversed": True},
        {"id": 6, "text": "你能够在追求自由的同时，承担起对他人的责任和承诺。", "type": "maturity", "reversed": False},
        {"id": 7, "text": "你对批评极度敏感，容易因为别人的一句话而全盘否定自己。", "type": "maturity", "reversed": True},
        {"id": 8, "text": "你能够勇敢地捍卫自己的信念，即使这意味着要与其重要的人发生冲突。", "type": "maturity", "reversed": False},
        {"id": 9, "text": "你的情绪起伏极大，经常让身边的人感到忽冷忽热，摸不着头脑。", "type": "maturity", "reversed": True},
        {"id": 10, "text": "你会定期反思自己的行为是否违背了初心，并进行自我修正。", "type": "maturity", "reversed": False},
        
        {"id": 11, "text": "你最近变得像个工作狂，用疯狂的忙碌来逃避面对内心的真实感受。", "type": "loop", "reversed": False},
        {"id": 12, "text": "你变得异常强势和急躁，对他人的情绪反应感到不耐烦，只想快点出结果。", "type": "loop", "reversed": False},
        {"id": 13, "text": "你开启了一个又一个新项目，纯粹是为了追求“完成”的快感，而不管质量。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你感到内心空洞，似乎失去了灵魂，变成了一个只会执行任务的机器。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你对他人的建议充耳不闻，固执地推行自己的想法，表现出罕见的独断。", "type": "loop", "reversed": False},
        {"id": 16, "text": "你无法忍受任何形式的等待或停顿，必须时刻保持“在路上”的状态。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你开始用逻辑和效率来压抑自己的情感需求，觉得感性是软弱的表现。", "type": "loop", "reversed": False},
        {"id": 18, "text": "你变得非常防御，一旦有人质疑你的计划，你就会激烈反击。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你发现自己即使在休息时大脑也在高速运转，根本停不下来。", "type": "loop", "reversed": False},
        {"id": 20, "text": "你忽略了身边人的感受，只把他们当作实现你目标的工具。", "type": "loop", "reversed": False},
        
        {"id": 21, "text": "最近你变得异常沉默和退缩，只想把自己藏在家里，切断社交。", "type": "grip", "reversed": False},
        {"id": 22, "text": "你突然对身体的一点小病痛极度焦虑，总觉得自己得了绝症。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你陷入对过去的无尽反刍，反复回想那些失败的细节，觉得未来没希望了。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你变得极其死板和挑剔，对家里的卫生或物品摆放产生强迫症。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你感觉大脑一片空白，所有的灵感都枯竭了，世界变得灰暗无趣。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你变得非常保守，拒绝尝试任何新事物，只敢做最熟悉、最安全的事。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你感到身体极其沉重，仿佛失去了对肢体的控制，只想躺着不动。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你觉得周围的一切都在针对你，甚至是一些微不足道的琐事。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你对自己变得极其刻薄，列举出无数证据证明自己是一无是处的。", "type": "grip", "reversed": False},
        {"id": 30, "text": "你通过机械性地重复某些行为（如反复洗手、检查门锁）来寻求安全感。", "type": "grip", "reversed": False}
        ],

    "ISTJ": [
        # Maturity (Si-Te): 靠谱、有序、讲道理
        {"id": 1, "text": "只要是你经手的事情，哪怕没人检查，你也会把细节做到位。", "type": "maturity", "reversed": False},
        {"id": 2, "text": "如果计划突然被打乱，你会极度烦躁，很难立刻适应新情况。", "type": "maturity", "reversed": True},
        {"id": 3, "text": "做决定时，你会优先参考“以前是怎么做的”，而不是“这事有什么新花样”。", "type": "maturity", "reversed": False},
        {"id": 4, "text": "你经常因为觉得别人干活太粗糙，而忍不住把活拿过来自己重做。", "type": "maturity", "reversed": True},
        {"id": 5, "text": "你能够把家里或电脑里的文件整理得井井有条，找东西从来不超过1分钟。", "type": "maturity", "reversed": False},
        {"id": 6, "text": "你很难直接表达情感，觉得用行动（比如做饭、修东西）比说“我爱你”更实在。", "type": "maturity", "reversed": False},
        {"id": 7, "text": "你非常反感那些迟到、不守规矩或者说话不算数的人。", "type": "maturity", "reversed": False},
        {"id": 8, "text": "为了维持秩序，你有时会显得不近人情，甚至有点死板。", "type": "maturity", "reversed": True},
        {"id": 9, "text": "你在着手做任何事之前，必须先看到明确的步骤或说明书。", "type": "maturity", "reversed": False},
        {"id": 10, "text": "当你累的时候，你更愿意一个人待着整理思绪，而不是找人倾诉。", "type": "maturity", "reversed": False},

        # Loop (Si-Fi): 记仇、委屈、翻旧账
        {"id": 11, "text": "最近你脑子里总是忍不住回放过去犯过的错误，或者尴尬的瞬间。", "type": "loop", "reversed": False},
        {"id": 12, "text": "你觉得只有你自己才是最辛苦的，别人都在偷懒或占你便宜。", "type": "loop", "reversed": False},
        {"id": 13, "text": "你会把很久以前别人对你的冒犯记得清清楚楚，并在心里默默扣分。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你对周围人的情感反应变得迟钝，甚至有点冷漠，不想理任何人。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你觉得自己付出了一切，却得不到应有的感谢，感到深深的委屈。", "type": "loop", "reversed": False},
        {"id": 16, "text": "你拒绝接受新的做事方法，固执地认为“老办法”才是唯一正确的。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你会因为一点小细节没做好，就全盘否定整个项目的价值。", "type": "loop", "reversed": False},
        {"id": 18, "text": "你陷入了一种“受害者心态”，觉得全世界都对不起你。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你变得非常挑剔，专门盯着别人的缺点和毛病看。", "type": "loop", "reversed": False},
        {"id": 20, "text": "你把心里话憋着不说，通过生闷气或冷战来表达不满。", "type": "loop", "reversed": False},

        # Grip (Ne): 灾难化想象、崩盘
        {"id": 21, "text": "最近你脑子里总是冒出“万一出大事怎么办”的念头，哪怕没什么依据。", "type": "grip", "reversed": False},
        {"id": 22, "text": "你会突然冲动地想要打破常规，做一些平时绝对不会做的冒险决定。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你觉得未来一片黑暗，无论怎么努力，最后肯定会失败。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你会把一些毫不相关的小倒霉事联系起来，觉得这是大难临头的征兆。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你变得语无伦次，平时条理清晰的你，突然不知道该怎么把话说清楚。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你对未知的事物感到前所未有的恐惧，甚至不敢看新闻或接电话。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你会突然对很多事情失去兴趣，甚至想抛下一切责任逃跑。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你感觉脑子像浆糊一样，完全没法进行逻辑思考。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你会因为找不到一样东西，就突然情绪崩溃，大发雷霆。", "type": "grip", "reversed": False},
        {"id": 30, "text": "你觉得周围的一切都在失控，就像开车时刹车失灵了一样。", "type": "grip", "reversed": False}
    ],

    "ISFJ": [
        # Maturity (Si-Fe): 照顾、细致、温和
        {"id": 1, "text": "你能记得住朋友不吃香菜、同事的咖啡加什么糖这种小细节。", "type": "maturity", "reversed": False},
        {"id": 2, "text": "你很难拒绝别人的请求，哪怕那个请求会让你自己很累。", "type": "maturity", "reversed": True},
        {"id": 3, "text": "在大家争论的时候，你通常是那个试图打圆场、维持和气的人。", "type": "maturity", "reversed": False},
        {"id": 4, "text": "你习惯通过具体的服务（做饭、跑腿）来表达关心，而不是只动嘴皮子。", "type": "maturity", "reversed": False},
        {"id": 5, "text": "你经常觉得“如果我不做，这事就没人管了”，所以把责任都揽在身上。", "type": "maturity", "reversed": True},
        {"id": 6, "text": "你做事情非常稳，哪怕环境再乱，你也能按部就班地把手头的活干好。", "type": "maturity", "reversed": False},
        {"id": 7, "text": "你非常在意别人对你的看法，一句无心的批评能让你难受好几天。", "type": "maturity", "reversed": True},
        {"id": 8, "text": "你尊重传统和规矩，觉得按老一辈的经验办事最不容易出错。", "type": "maturity", "reversed": False},
        {"id": 9, "text": "你总是在照顾别人，却很少主动说出自己的需求。", "type": "maturity", "reversed": True},
        {"id": 10, "text": "当朋友难过时，你是一个非常好的倾听者，能让他们感到被接纳。", "type": "maturity", "reversed": False},

        # Loop (Si-Ti): 钻牛角尖、冷漠、算账
        {"id": 11, "text": "最近你不想理任何人，觉得社交纯粹是在浪费精力。", "type": "loop", "reversed": False},
        {"id": 12, "text": "你会反复琢磨以前的一句对话，分析自己是不是说错了，或者对方是不是在讽刺你。", "type": "loop", "reversed": False},
        {"id": 13, "text": "你开始变得挑剔，觉得周围的人都笨手笨脚，什么都做不好。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你心里积压了很多不满，在脑子里一遍遍演练怎么怼回去，但现实中却不说。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你对别人的痛苦变得麻木，甚至冷冷地想“这都是他们自找的”。", "type": "loop", "reversed": False},
        {"id": 16, "text": "你过于纠结逻辑细节，非要分出个谁对谁错，完全不顾感情。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你觉得自己过去对他人的好都是不值得的，产生了一种被辜负的愤怒。", "type": "loop", "reversed": False},
        {"id": 18, "text": "你通过疯狂地做家务或整理东西来逃避思考，拒绝停下来。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你固执地坚持自己的那一套流程，谁劝都不听，变得非常死板。", "type": "loop", "reversed": False},
        {"id": 20, "text": "你把自己封闭起来，不回消息，不接电话，甚至不想出门。", "type": "loop", "reversed": False},

        # Grip (Ne): 恐慌、灾难化、不知所措
        {"id": 21, "text": "最近你总是莫名其妙地心慌，感觉有什么坏事要发生了。", "type": "grip", "reversed": False},
        {"id": 22, "text": "你会把一点点身体不舒服（如头痛），联想到自己得了绝症。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你面对任何变化（如搬家、换工作）都感到极度恐惧，只想躲起来。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你会突然说出一些非常悲观、消极的话，把身边人吓一跳。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你感觉脑子里有无数个声音在吵架，完全没法集中注意力。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你会不停地向别人确认“真的没事吗？”，但别人的安慰根本没用。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你可能会因为压力大而暴饮暴食，或者彻底吃不下饭。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你觉得现实世界变得很不真实，像是在做噩梦一样。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你会突然冲动地想要逃离现在的生活，去一个没人认识的地方。", "type": "grip", "reversed": False},
        {"id": 30, "text": "你觉得自己彻底失去了对生活的控制，像风中的叶子一样无助。", "type": "grip", "reversed": False}
    ],

    "ESTJ": [
        # Maturity (Te-Si): 效率、执行、管理
        {"id": 1, "text": "你非常讲究效率，最讨厌磨磨唧唧、没有结果的会议。", "type": "maturity", "reversed": False},
        {"id": 2, "text": "在混乱的局面下，你通常是第一个站出来指挥大家该干什么的人。", "type": "maturity", "reversed": False},
        {"id": 3, "text": "你很难理解那些情绪化的人，觉得他们是在无理取闹。", "type": "maturity", "reversed": True},
        {"id": 4, "text": "你做决定非常果断，一旦定下来就不喜欢轻易更改。", "type": "maturity", "reversed": False},
        {"id": 5, "text": "你非常看重规则和承诺，说了几点到就一定要几点到。", "type": "maturity", "reversed": False},
        {"id": 6, "text": "为了达成目标，你有时会忽略别人的感受，说话比较直接伤人。", "type": "maturity", "reversed": True},
        {"id": 7, "text": "你擅长把复杂的任务拆解成一步步可执行的计划。", "type": "maturity", "reversed": False},
        {"id": 8, "text": "你总是那个检查进度、确保大家都在干活的人。", "type": "maturity", "reversed": False},
        {"id": 9, "text": "你对那种“光说不练”的人零容忍。", "type": "maturity", "reversed": False},
        {"id": 10, "text": "你经常因为工作或责任而牺牲休息时间，是个典型的工作狂。", "type": "maturity", "reversed": True},

        # Loop (Te-Ne): 瞎忙、多疑、控制狂
        {"id": 11, "text": "最近你总是觉得如果不盯着，底下的人肯定会出乱子。", "type": "loop", "reversed": False},
        {"id": 12, "text": "你脑子里冒出很多“防患于未然”的念头，搞得自己和周围人都很累。", "type": "loop", "reversed": False},
        {"id": 13, "text": "你甚至开始微管理（Micro-manage），连怎么发邮件这种小事都要管。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你根本停不下来，觉得一旦停下来思考，事情就会失控。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你对新的可能性变得过度敏感，总觉得有什么隐患没被发现。", "type": "loop", "reversed": False},
        {"id": 16, "text": "你为了效率而牺牲了质量，急匆匆地把事情做完，结果全是漏洞。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你变得非常急躁，别人话还没说完你就打断，急着下结论。", "type": "loop", "reversed": False},
        {"id": 18, "text": "你无法忍受任何形式的“等待”，哪怕只是等红绿灯都会让你暴怒。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你试图掌控一切，包括别人的私生活或想法。", "type": "loop", "reversed": False},
        {"id": 20, "text": "你觉得只有你自己是靠谱的，周围人都是拖后腿的。", "type": "loop", "reversed": False},

        # Grip (Fi): 情绪爆发、委屈、甚至哭泣
        {"id": 21, "text": "你突然觉得自己很孤独，觉得没人真正关心你，只把你当工具人。", "type": "grip", "reversed": False},
        {"id": 22, "text": "平时从不流泪的你，最近可能会因为一点小委屈就控制不住想哭。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你觉得自己的价值观被践踏了，对某些人和事产生强烈的道德愤怒。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你会变得异常敏感，别人一个眼神不对，你就觉得他在针对你。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你突然不想工作了，觉得奋斗这么多年一点意义都没有。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你会把自己关起来生闷气，谁来劝你你都觉得他在看笑话。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你身体会出现莫名其妙的疼痛，比如胃痛、背痛，查不出原因。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你对身边亲近的人发火，发完火又陷入深深的自责。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你觉得自己是一个没人爱的失败者，尽管你在事业上很成功。", "type": "grip", "reversed": False},
        {"id": 30, "text": "你会突然变得很“甚至有些迷信”，试图寻求非理性的心理安慰。", "type": "grip", "reversed": False}
    ],

    "ESFJ": [
        # Maturity (Fe-Si): 热情、组局、周到
        {"id": 1, "text": "你是朋友圈里的组织委员，聚会、送礼这些事你总能安排得妥妥当当。", "type": "maturity", "reversed": False},
        {"id": 2, "text": "你非常在意大家是否开心，如果有人冷场，你会立刻想办法活跃气氛。", "type": "maturity", "reversed": False},
        {"id": 3, "text": "你对朋友的生日、纪念日记得很清楚，并会送上贴心的祝福。", "type": "maturity", "reversed": False},
        {"id": 4, "text": "你经常因为过度操心别人的事，而把自己搞得精疲力尽。", "type": "maturity", "reversed": True},
        {"id": 5, "text": "你很看重面子和评价，害怕在人群中显得格格不入。", "type": "maturity", "reversed": True},
        {"id": 6, "text": "你喜欢稳定、和谐的环境，非常讨厌冲突和争吵。", "type": "maturity", "reversed": False},
        {"id": 7, "text": "你会因为别人没有按你期待的方式回应你的好意，而感到失落。", "type": "maturity", "reversed": True},
        {"id": 8, "text": "你做事很讲规矩，不喜欢的那些标新立异、破坏规则的人。", "type": "maturity", "reversed": False},
        {"id": 9, "text": "你在做决定时，会优先考虑“大家会怎么看”，而不是“我想怎么做”。", "type": "maturity", "reversed": True},
        {"id": 10, "text": "你非常乐于助人，觉得被需要是你价值的体现。", "type": "maturity", "reversed": False},

        # Loop (Fe-Ne): 讨好、焦虑、甚至八卦
        {"id": 11, "text": "最近你总是担心自己说错了话，得罪了人，哪怕根本没这回事。", "type": "loop", "reversed": False},
        {"id": 12, "text": "为了讨好别人，你可能会说一些言不由衷的话，或者答应过分的要求。", "type": "loop", "reversed": False},
        {"id": 13, "text": "你变得特别爱打听消息，试图通过掌握信息来获得安全感。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你会脑补出很多别人不喜欢你的理由，越想越焦虑。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你根本停不下来，一会儿找这个聊，一会儿找那个聊，却不敢独处。", "type": "loop", "reversed": False},
        {"id": 16, "text": "你对别人的情绪变化反应过度，别人皱个眉你都要紧张半天。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你甚至会随大流，去做一些自己其实不喜欢、但大家都在做的事。", "type": "loop", "reversed": False},
        {"id": 18, "text": "你非常容易受骗，因为你太想相信别人是好人了。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你觉得自己如果不努力维持，大家的关系就会散掉。", "type": "loop", "reversed": False},
        {"id": 20, "text": "你为了合群，把自己真实的性格完全藏了起来。", "type": "loop", "reversed": False},

        # Grip (Ti): 冷漠、挑刺、愤世嫉俗
        {"id": 21, "text": "那个热情的你突然不见了，你开始对周围的人非常冷漠。", "type": "grip", "reversed": False},
        {"id": 22, "text": "你会突然盯着别人的逻辑漏洞猛烈攻击，说话非常刻薄。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你觉得周围的人都虚伪透顶，只有你一个人看穿了真相。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你开始怀疑一切关系的价值，觉得“人终究是孤独的”。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你对那些情感充沛的表达感到恶心，觉得那是矫情。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你会躲在角落里读一些晦涩的书或理论，试图用逻辑解释世界。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你对别人的求助视而不见，心想“管我屁事，你自己解决”。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你觉得自己一直以来都被人利用了，充满了怨气。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你变得非常固执，听不进任何人的劝解，哪怕是好意的。", "type": "grip", "reversed": False},
        {"id": 30, "text": "你甚至想破坏现有的关系，比如故意跟好朋友吵架。", "type": "grip", "reversed": False}
    ],

    "ISTP": [
        # Maturity (Ti-Se): 动手、解决、冷静
        {"id": 1, "text": "遇到东西坏了，你的第一反应是拆开看看能不能修，而不是打电话叫人。", "type": "maturity", "reversed": False},
        {"id": 2, "text": "你非常讨厌废话多的会议，只想知道“重点是什么”和“我要做什么”。", "type": "maturity", "reversed": False},
        {"id": 3, "text": "面对突发危机（如车祸、停电），你通常比周围人都要冷静。", "type": "maturity", "reversed": False},
        {"id": 4, "text": "你喜欢尝试各种工具、机械或者运动项目，享受操控的感觉。", "type": "maturity", "reversed": False},
        {"id": 5, "text": "你经常因为觉得事情太麻烦或者太无聊，就拖着不做。", "type": "maturity", "reversed": True},
        {"id": 6, "text": "你不太擅长处理别人的情绪，如果有人在你面前哭，你会很想逃跑。", "type": "maturity", "reversed": True},
        {"id": 7, "text": "你喜欢自由，非常反感被别人管着或者被计划束缚。", "type": "maturity", "reversed": False},
        {"id": 8, "text": "你说话通常很简短，直击要害，不会绕弯子。", "type": "maturity", "reversed": False},
        {"id": 9, "text": "你做事追求“最省力原则”，能用一步解决绝不用两步。", "type": "maturity", "reversed": False},
        {"id": 10, "text": "你经常在心里吐槽别人的逻辑漏洞，觉得他们怎么连这个都想不通。", "type": "maturity", "reversed": False},

        # Loop (Ti-Ni): 阴谋论、瘫痪、虚无
        {"id": 11, "text": "最近你什么都不想干，觉得做什么都没意义，反正是徒劳。", "type": "loop", "reversed": False},
        {"id": 12, "text": "你开始过度解读别人的话，总觉得他们背后有某种针对你的阴谋。", "type": "loop", "reversed": False},
        {"id": 13, "text": "你把自己关在房间里，不出门，不动手，只在脑子里空想。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你对未来充满了非常悲观的预测，并坚信这些坏事一定会发生。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你变得愤世嫉俗，觉得整个社会规则都是骗局。", "type": "loop", "reversed": False},
        {"id": 16, "text": "你甚至开始怀疑自己以前掌握的技能都是没用的垃圾。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你对外界的信息充耳不闻，固执地活在自己的逻辑闭环里。", "type": "loop", "reversed": False},
        {"id": 18, "text": "你误读了别人的沉默或眼神，认定他们是在嘲笑你。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你陷入了一种精神上的麻痹状态，不想动，连游戏都不想打。", "type": "loop", "reversed": False},
        {"id": 20, "text": "你试图构建一套大理论来解释一切，但完全没有现实依据。", "type": "loop", "reversed": False},

        # Grip (Fe): 情绪失控、求关注、敏感
        {"id": 21, "text": "平时面无表情的你，最近可能会因为一点小事突然大吼大叫。", "type": "grip", "reversed": False},
        {"id": 22, "text": "你突然变得特别在意别人怎么看你，甚至觉得自己被所有人抛弃了。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你会莫名其妙地流泪，或者情绪低落到极点，控制不住。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你开始抱怨没人关心你，没人理解你的付出。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你会做出一些很戏剧化的举动（比如摔门、拉黑）来表达愤怒。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你对人际关系中的“气氛”变得过敏，一点尴尬都让你受不了。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你为了维持表面的和平，不得不忍气吞声，心里却恨得牙痒痒。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你会用阴阳怪气的方式说话，而不是直接说问题。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你觉得自己就像个情绪垃圾桶，装满了别人的负能量。", "type": "grip", "reversed": False},
        {"id": 30, "text": "你感到一种深深的孤独，渴望有人能来救你。", "type": "grip", "reversed": False}
    ],

    "ISFP": [
        # Maturity (Fi-Se): 审美、自我、当下
        {"id": 1, "text": "你非常在乎这件事是否“符合你的心意”，如果不喜欢，给多少钱你都不想做。", "type": "maturity", "reversed": False},
        {"id": 2, "text": "你对颜色、声音、味道非常敏感，能发现别人注意不到的美感。", "type": "maturity", "reversed": False},
        {"id": 3, "text": "你喜欢用具体的作品（画画、穿搭、手工）来表达你自己。", "type": "maturity", "reversed": False},
        {"id": 4, "text": "你非常随性，不喜欢做长远的计划，觉得走到哪算哪最好。", "type": "maturity", "reversed": False},
        {"id": 5, "text": "你很难直接拒绝别人，通常会用“拖着不做”或者消失来表达拒绝。", "type": "maturity", "reversed": True},
        {"id": 6, "text": "你需要大量的独处空间，如果一直有人在旁边唠叨，你会疯掉。", "type": "maturity", "reversed": False},
        {"id": 7, "text": "你对批评非常敏感，觉得那是对你人格的攻击。", "type": "maturity", "reversed": True},
        {"id": 8, "text": "你待人真诚，讨厌虚伪和客套的场面话。", "type": "maturity", "reversed": False},
        {"id": 9, "text": "你行动力很强，想到什么好玩的会立刻去体验。", "type": "maturity", "reversed": False},
        {"id": 10, "text": "你经常被评价为“有个性”或者“很难捉摸”。", "type": "maturity", "reversed": False},

        # Loop (Fi-Ni): 被害妄想、自闭、绝望
        {"id": 11, "text": "最近你觉得全世界都跟你作对，觉得自己注定是个失败者。", "type": "loop", "reversed": False},
        {"id": 12, "text": "你对别人的眼神或话语过度解读，觉得他们都在看不起你。", "type": "loop", "reversed": False},
        {"id": 13, "text": "你把自己关在家里，切断了跟外界的联系，沉浸在悲伤里。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你对未来没有任何期待，觉得人生就是一片灰暗。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你变得非常固执，认定了一个死理，谁劝都不听。", "type": "loop", "reversed": False},
        {"id": 16, "text": "你甚至开始讨厌自己以前喜欢的那些爱好，觉得都没意义。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你在脑子里编造了很多别人背叛你的剧情，越想越真。", "type": "loop", "reversed": False},
        {"id": 18, "text": "你觉得自己是独一无二的“受难者”，没人能理解你的痛苦。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你对现实生活完全失去了兴趣，不想吃饭，不想洗澡。", "type": "loop", "reversed": False},
        {"id": 20, "text": "你觉得命运对你太不公平了，充满了怨恨。", "type": "loop", "reversed": False},

        # Grip (Te): 暴躁、控制、死板
        {"id": 21, "text": "那个随和的你突然变得非常凶，像个暴君一样指使别人干活。", "type": "grip", "reversed": False},
        {"id": 22, "text": "你突然开始追求极端的效率，嫌弃所有人动作太慢。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你会列出一大堆计划表，强迫自己必须按时完成，完不成就发火。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你说话变得非常难听、直接，专门戳别人的痛处。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你对混乱的容忍度降为零，看到一点不整齐就抓狂。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你觉得必须立刻、马上解决问题，一秒钟都不能等。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你试图控制周围的一切，包括别人的想法。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你变得非常功利，觉得没有用的东西就该扔掉（包括感情）。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你对那些情感流露表现出极度的不耐烦。", "type": "grip", "reversed": False},
        {"id": 30, "text": "你觉得自己正在孤军奋战，必须靠强硬的手段才能活下去。", "type": "grip", "reversed": False}
    ],

    "ESTP": [
        # Maturity (Se-Ti): 行动、破局、魅力
        {"id": 1, "text": "你是个行动派，遇到问题不喜欢开会讨论，而是直接上手试错。", "type": "maturity", "reversed": False},
        {"id": 2, "text": "你非常敏锐，能立刻注意到环境中的变化（比如谁换了发型，哪里的路灯坏了）。", "type": "maturity", "reversed": False},
        {"id": 3, "text": "你喜欢追求刺激和挑战，平淡无奇的生活会让你觉得窒息。", "type": "maturity", "reversed": False},
        {"id": 4, "text": "你在社交场合游刃有余，很擅长说服别人或者活跃气氛。", "type": "maturity", "reversed": False},
        {"id": 5, "text": "你做事往往三分钟热度，很难长期坚持做一件枯燥的事。", "type": "maturity", "reversed": True},
        {"id": 6, "text": "你很讲究实际利益，不喜欢那些虚头巴脑的理论或画大饼。", "type": "maturity", "reversed": False},
        {"id": 7, "text": "你甚至有点享受危机，因为那时候你的脑子转得最快。", "type": "maturity", "reversed": False},
        {"id": 8, "text": "你不喜欢遵守死规矩，觉得规矩就是用来打破的。", "type": "maturity", "reversed": False},
        {"id": 9, "text": "你可能会因为冲动而说错话，但你会想办法圆回来。", "type": "maturity", "reversed": False},
        {"id": 10, "text": "你通过身体的活动（运动、开车、操作机器）来思考，而不是坐着想。", "type": "maturity", "reversed": False},

        # Loop (Se-Fe): 显摆、跟风、死要面子
        {"id": 11, "text": "最近你为了博取别人的关注，可能会做一些很夸张、甚至危险的举动。", "type": "loop", "reversed": False},
        {"id": 12, "text": "你非常在意面子，为了不丢脸，甚至会撒谎或吹牛。", "type": "loop", "reversed": False},
        {"id": 13, "text": "你变得很盲从，看到别人炒股你也炒，看到别人干啥你也干啥，没了自己的判断。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你沉迷于吃喝玩乐或者感官刺激，完全不想停下来思考。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你对别人的评价反应过度，如果有人不给你面子，你会想报复。", "type": "loop", "reversed": False},
        {"id": 16, "text": "你试图操纵别人的情绪来达到自己的目的。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你觉得只要外表看起来光鲜亮丽，就代表你成功了。", "type": "loop", "reversed": False},
        {"id": 18, "text": "你甚至会欺负弱小，来显示自己的强大。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你根本坐不住，必须时刻保持忙碌，哪怕是无意义的瞎忙。", "type": "loop", "reversed": False},
        {"id": 20, "text": "你忽略了长期的后果，只顾眼前的爽快。", "type": "loop", "reversed": False},

        # Grip (Ni): 迷信、恐惧、疑神疑鬼
        {"id": 21, "text": "平时胆子最大的你，突然开始怕黑、怕鬼，或者变得很迷信。", "type": "grip", "reversed": False},
        {"id": 22, "text": "你觉得肯定有坏事要发生，这种直觉让你甚至不敢出门。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你会把别人的一个眼神解读成“他要害我”的信号。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你突然对人生感到极度的空虚，觉得以前追求的快乐都没意义。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你觉得自己被某种看不见的力量控制了，逃不掉。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你会做噩梦，或者脑子里全是恐怖的画面。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你变得非常退缩，不敢做任何决定，生怕选错了就万劫不复。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你试图从星座、算命里找答案，而不是相信自己的能力。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你觉得身边的人都不可信，都在骗你。", "type": "grip", "reversed": False},
        {"id": 30, "text": "你感到一种深深的绝望，觉得自己这辈子就这样了。", "type": "grip", "reversed": False}
    ],

    "ESFP": [
        # Maturity (Se-Fi): 乐天、感染力、助人
        {"id": 1, "text": "你是人群中的开心果，只要有你在，气氛就不会冷场。", "type": "maturity", "reversed": False},
        {"id": 2, "text": "你非常慷慨，愿意和朋友分享你的好东西（食物、衣服、快乐）。", "type": "maturity", "reversed": False},
        {"id": 3, "text": "你活在当下，觉得享受这一秒比担忧下一秒重要得多。", "type": "maturity", "reversed": False},
        {"id": 4, "text": "你对朋友的情绪变化很敏感，能迅速给他们提供实际的安慰（比如带去吃顿好的）。", "type": "maturity", "reversed": False},
        {"id": 5, "text": "你很难长时间集中注意力做一件枯燥的事，容易分心。", "type": "maturity", "reversed": True},
        {"id": 6, "text": "你喜欢成为焦点的感觉，不喜欢被忽视或冷落。", "type": "maturity", "reversed": False},
        {"id": 7, "text": "你做事比较冲动，经常还没想清楚后果就已经干了。", "type": "maturity", "reversed": True},
        {"id": 8, "text": "你非常重视外表和打扮，觉得这是一种对自己和对他人的尊重。", "type": "maturity", "reversed": False},
        {"id": 9, "text": "你待人真诚热情，没有什么城府。", "type": "maturity", "reversed": False},
        {"id": 10, "text": "你觉得工作就是为了赚钱享受生活，不喜欢那种苦行僧式的奋斗。", "type": "maturity", "reversed": False},

        # Loop (Se-Te): 瞎忙、强制、甚至霸道
        {"id": 11, "text": "最近你为了逃避内心的空虚，把日程表排得满满的，一刻都不敢停。", "type": "loop", "reversed": False},
        {"id": 12, "text": "你变得很强势，强行安排别人的生活，觉得“我这是为你好”。", "type": "loop", "reversed": False},
        {"id": 13, "text": "你说话变得很冲，只讲效率不讲人情，甚至会骂人。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你通过疯狂购物或者暴饮暴食来填补内心的洞，但根本填不满。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你变得非常功利，开始算计每段关系能带给你什么好处。", "type": "loop", "reversed": False},
        {"id": 16, "text": "你甚至会变得有点霸道，不许别人反驳你的意见。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你对那些“慢吞吞”的人完全没耐心，恨不得替他们做。", "type": "loop", "reversed": False},
        {"id": 18, "text": "你忽略了自己的真实感受，像个机器一样运转。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你觉得只有看得见的成果（钱、地位）才是真实的，其他都是虚的。", "type": "loop", "reversed": False},
        {"id": 20, "text": "你拒绝承认自己累了，硬撑着也要把场面撑下去。", "type": "loop", "reversed": False},

        # Grip (Ni): 灰暗、丧、甚至抑郁
        {"id": 21, "text": "那个爱笑的你突然不见了，你把自己关在房间里，谁也不想见。", "type": "grip", "reversed": False},
        {"id": 22, "text": "你觉得未来一片灰暗，毫无希望，甚至想到了死。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你开始怀疑朋友都在骗你，觉得世界上没有真情。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你会因为一点小挫折就觉得整个人生都失败了。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你变得非常神神叨叨，觉得有什么不好的东西缠着你。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你对以前喜欢的活动完全提不起兴趣，觉得都很无聊。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你觉得自己很脏、很丑陋，陷入深深的自我厌恶。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你甚至会做出一些自残的行为，或者极度消极。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你脑子里全是消极的念头，甩都甩不掉。", "type": "grip", "reversed": False},
        {"id": 30, "text": "你觉得这是一个巨大的阴谋，你是无辜的受害者。", "type": "grip", "reversed": False}
    ]
}

# ==========================================
# 2. 核心数据：文案逻辑
# ==========================================

NARRATIVE_TEMPLATES = {
    "INTP": {
        "stable": {
            "insight": "当前状态：【清醒的架构师】。你的脑子现在很清楚，好奇心也很足。想问题既有逻辑，又愿意看新东西，这是你最舒服的状态。",
            "advice": "【动手做】：别光想，想是没结果的。把那个念头写下来，或者写几行代码跑一跑。只要“做出来”，哪怕是个草稿，这事儿就算成了。"
        },
        "overload": { # Grip
            "insight": "当前状态：【情绪上头】(Fe Grip)。平时讲道理的你不见了。你现在特别敏感，觉得别人都在针对你，或者觉得自己没人要，特别委屈。",
            "advice": "【闭嘴睡觉】：别分析了，这时候你的脑子是乱的。承认自己就是情绪不好。吃顿好的，睡一觉。这时候你需要的是休息，不是讲道理。"
        },
        "highLoop": { # Loop
            "insight": "当前状态：【死钻牛角尖】(Ti-Si Loop)。你卡在过去的出错细节里出不来了，翻来覆去想“当时如果那样就好了”，完全听不进新消息。",
            "advice": "【出门转转】：你的脑子现在是死水一潭。必须强行打断。去个没去过的地方，或者看部没看过的电影。只要有“新东西”进来，死循环就破了。"
        },
        "crisis": { # Crisis
            "insight": "当前状态：【彻底死机】(CRISIS)。既钻牛角尖，又情绪崩溃。你觉得脑子转不动，心里还堵得慌，感觉自己特别废，什么都做不了。",
            "advice": "【拔掉电源】：别挣扎了，越挣扎陷得越深。今天什么决定都别做。躺平，发呆，允许自己当一天废人。电充满了再开机。"
        }
    },
    "INFJ": {
        "stable": {
            "insight": "当前状态：【温和的引路人】。你的直觉很准，也能照顾到别人的感受。你现在既能看透问题，又不会显得冷漠，是一种很有力量的温柔。",
            "advice": "【省着点用】：你的同情心是有限的，别谁都帮。每天留一个小时，关上门，谁的消息也不回。这段时间只属于你自己，不属于任何人。"
        },
        "overload": { # Grip
            "insight": "当前状态：【感官过载】(Se Grip)。你被现实里的琐事逼疯了。可能在大吃大喝、疯狂买东西，或者对噪音、强光特别烦躁，想砸东西。",
            "advice": "【对自己好点】：别想意义了，不想人生。去洗个热水澡，或者去捏捏泡泡纸。让身体舒服一点，你的脑子自然就静下来了。"
        },
        "highLoop": { # Loop
            "insight": "当前状态：【冷漠的旁观者】(Ni-Ti Loop)。你把自己关起来了，冷冷地看着所有人，觉得他们都蠢，都不值得救。这其实是你太累了，在自我防御。",
            "advice": "【找个人说话】：哪怕是找人聊聊废话。只要你的想法说出口，被别人听到，那种“与世隔绝”的死结就会松动。别老在脑子里自己跟自己下棋。"
        },
        "crisis": { # Crisis
            "insight": "当前状态：【精神分裂般痛苦】(CRISIS)。既觉得人生没意义，又被现实折磨得要死。你现在处于一种极度想要逃离，但又动弹不得的状态。",
            "advice": "【物理断网】：关机，拉窗帘。告诉重要的人你有事失联一天。别试图解决任何问题。你现在的任务只有一个：好好睡一觉，明天再说。"
        }
    },
    "INTJ": {
        "stable": {
            "insight": "当前状态：【靠谱的操盘手】。你有计划，也有执行力。你不光知道未来要去哪，还知道今天该走哪一步。现在的你，效率很高。",
            "advice": "【抬头看路】：走得太快容易丢人。偶尔停两分钟，听听旁边人的唠叨，没准里面有你没注意到的坑。"
        },
        "overload": { # Grip
            "insight": "当前状态：【报复性放纵】(Se Grip)。绷太紧断了。你现在可能在暴饮暴食、熬夜打游戏，或者莫名其妙发大火，控制不住想破坏点什么。",
            "advice": "【去出汗】：别骂自己堕落。你的身体在替脑子抗议。去跑步，去打拳，跑到没力气为止。把那股火气发泄出去，你就正常了。"
        },
        "highLoop": { # Loop
            "insight": "当前状态：【被迫害妄想】(Ni-Fi Loop)。你太相信自己的直觉了，觉得总有人想害你，或者觉得全世界都不懂你。你脱离现实了。",
            "advice": "【列证据】：启动你的逻辑。把你的担心写下来，一条条问自己：“有证据吗？”用事实说话，别光靠猜。"
        },
        "crisis": { # Crisis
            "insight": "当前状态：【想毁掉一切】(CRISIS)。你认定未来没希望了，现在只想把手头的事全砸了。这是一种甚至想玉石俱焚的危险心态。",
            "advice": "【绑住双手】：不管你现在多想辞职、分手或骂人，忍住。把这个念头封存48小时。去睡觉，盯着墙看都行。别动，这时候一动就是错。"
        }
    },
    "INFP": {
        "stable": {
            "insight": "当前状态：【真实的创作者】。你对自己诚实，对世界也温柔。现在的你，敏感不是毛病，而是天线，能接收到别人没注意到的美好。",
            "advice": "【写出来】：灵感跑得快。不管是用文字、画画还是录音，把你的感觉记录下来。这是你证明自己存在过的最好方式。"
        },
        "overload": { # Grip
            "insight": "当前状态：【暴躁的工头】(Te Grip)。那个温柔的你没了，变得特别刻薄、急躁。你嫌弃所有人都太慢、太笨，包括你自己。",
            "advice": "【放过自己】：你凶别人是因为你心里慌。你装出来的“高效率”是假的。承认自己搞不定吧，这不丢人。那个不完美的你，也值得被爱。"
        },
        "highLoop": { # Loop
            "insight": "当前状态：【反刍旧账】(Fi-Si Loop)。你躲在回忆里，一遍遍想以前犯过的傻、丢过的人。你不想出门，只想沉浸在这种难过里。",
            "advice": "【破点小例】：别逼自己大改变。去喝杯没喝过的奶茶，走条新路。只要一点点新鲜感，就能打破这个发霉的房间。"
        },
        "crisis": { # Crisis
            "insight": "当前状态：【自我攻击】(CRISIS)。你在回忆里骂自己，在现实里攻击别人。你觉得无论过去还是未来，都烂透了。",
            "advice": "【当个孩子】：别反省了，越想越错。吃点小时候爱吃的零食，看部老动画片。把自己当成生病的小朋友哄一哄。"
        }
    },
    "ENTP": {
        "stable": {
            "insight": "当前状态：【落地的发明家】。你的脑洞很大，但逻辑跟得上。你不是为了杠而杠，而是真的看到了更好的办法。这时候的你最有魅力。",
            "advice": "【做完它】：挑一件小事，逼自己把它彻底做完，别做到一半就跑。看到成品的快乐，比光想点子更实在。"
        },
        "overload": { # Grip
            "insight": "当前状态：【疑神疑鬼】(Si Grip)。那个洒脱的你没了。你突然开始担心身体生病，或者对一些无关紧要的细节特别纠结，甚至有点迷信。",
            "advice": "【去按摩】：你脑子过载了。别去医院查这查那，去按个摩，吃顿好的。把身体照顾舒服了，你的灵感就回来了。"
        },
        "highLoop": { # Loop
            "insight": "当前状态：【渴望关注】(Ne-Fe Loop)。你太在意别人怎么看你了。为了博眼球，你可能在做些夸张的事，看起来热闹，心里其实很空。",
            "advice": "【关网闭关】：你现在太吵了。切断反馈，把自己关小黑屋。问自己：“不管别人怎么看，这事逻辑通吗？”找回你那个冷静的内核。"
        },
        "crisis": { # Crisis
            "insight": "当前状态：【混乱崩溃】(CRISIS)。在外人面前是个小丑，回家觉得自己得了绝症。你在笑，但心里在发抖。",
            "advice": "【找点事做】：你需要秩序。去打扫卫生，去抄书，去数豆子。做这种最枯燥的事，能让你的心跳慢下来。"
        }
    },
    "ENTJ": {
        "stable": {
            "insight": "当前状态：【靠谱的老大】。你有目标，也懂怎么带人。你现在不光为了赢，还懂得怎么让大家一起赢。这时候你最强大。",
            "advice": "【听听人话】：你现在很强。趁这时候，去听听那些平时不敢说话的人的意见。往往你没看到的坑，就在他们嘴里。",
        },
        "overload": { # Grip
            "insight": "当前状态：【委屈的暴君】(Fi Grip)。你觉得自己累死累活，还没人理解你。突然觉得自己很可怜，甚至想哭，觉得一切都没意义。",
            "advice": "【认怂】：别硬撑了。找个不相干的朋友，承认你累了。说一句“我不行了”，天塌不下来。"
        },
        "highLoop": { # Loop
            "insight": "当前状态：【瞎忙】(Te-Se Loop)。你不想思考，只想忙。你通过疯狂工作或享乐来麻痹自己。看着像推土机，其实不知道往哪开。",
            "advice": "【强制停车】：你现在是无头苍蝇。必须强制独处。停下来什么都别做，方向感才会回来。现在的“忙”是在偷懒。"
        },
        "crisis": { # Crisis
            "insight": "当前状态：【虚无的狂怒】(CRISIS)。行动上横冲直撞，心里却觉得自己是个没人爱的孤儿。你正开着着火的车冲向悬崖。",
            "advice": "【暂停键】：任何决定，推迟一周再说。你现在是瞎的。去个没人认识你的地方，发呆，呼吸。别干正事。"
        }
    },
    "ENFJ": {
        "stable": {
            "insight": "当前状态：【温暖的领队】。你能看懂人，也能带好队。你不再是毫无原则的烂好人，而是能带着大家一起变好的引路人。",
            "advice": "【自私一点】：每周给自己几个小时，谁的情绪都别管。在这段时间里，你不需要做一个好人，甚至不需要做个人。"
        },
        "overload": { # Grip
            "insight": "当前状态：【刻薄的杠精】(Ti Grip)。温暖的你没了，变得愤世嫉俗。你挑剔别人的逻辑漏洞，觉得所有人都是虚伪的垃圾。",
            "advice": "【去找小狗】：你现在的逻辑是有毒的。去和小猫小狗待一会，它们不需要你照顾，也不会骗你。你需要被简单的感情融化。"
        },
        "highLoop": { # Loop
            "insight": "当前状态：【焦虑的演员】(Fe-Se Loop)。你疯狂社交，生怕错过什么。你像是在表演“生活”，周围很热闹，你心里觉得空荡荡的。",
            "advice": "【关机独处】：你转得太快了。必须减速。关机，看书，写日记。强迫自己面对孤独，别往人堆里凑。"
        },
        "crisis": { # Crisis
            "insight": "当前状态：【面具碎了】(CRISIS)。为了维持形象累得要死，心里却恨透了这群鼓掌的人，也恨那个表演的自己。",
            "advice": "【消失】：请假，消失。去个不需要你演戏的地方。把面具撕了。想哭就哭，想骂人就骂人。先找回自己。"
        }
    },
    "ENFP": {
        "stable": {
            "insight": "当前状态：【发光的小太阳】。你点子多，心肠好。你对自己诚实，对人热情。这时候的你，既有理想，又能干点实事。",
            "advice": "【别太散】：你的精力有限，别谁都答应。学会拒绝，把最好的状态留给真正懂你的人和事。"
        },
        "overload": { # Grip
            "insight": "当前状态：【灰暗的死板】(Si Grip)。灵气没了，变得抑郁、死板。你觉得自己身体出问题了，或者觉得未来完蛋了，一点希望都没有。",
            "advice": "【吃点好的】：别逼自己出门。现在的解药是“安全感”。吃小时候爱吃的，看老剧。允许自己当个无聊的普通人，等电充好。"
        },
        "highLoop": { # Loop
            "insight": "当前状态：【失控列车】(Ne-Te Loop)。你不敢停下来感受内心，只想疯狂忙碌证明自己。看着效率高，其实心里是麻木的。",
            "advice": "【听听心跳】：停下手里的活。找个安静地儿，问自己：“我现在难过吗？”把那个被你关在门外的真实感受接回来。"
        },
        "crisis": { # Crisis
            "insight": "当前状态：【彻底耗干】(CRISIS)。在外装作无所不能，回家瘫在床上动不了。你在透支未来的命，维持现在的假象。",
            "advice": "【躺平】：必须要停了。哪怕是生病，也是身体在救你。接受“我现在很废”。彻底躺平，不需要励志，只需要休息。"
        }
    },
    "ISFJ": {
        "stable": {
            "insight": "当前状态：【温柔的后盾】。你细心又靠谱。难得的是，你开始懂得“先爱自己再爱别人”，付出得刚刚好，自己也不累。",
            "advice": "【奖励自己】：你做得够多了。别把闲着当罪恶。每周留半天，不做任何正事，就是喝茶、发呆，自私一点没关系。"
        },
        "overload": { # Grip
            "insight": "当前状态：【灾难妄想】(Ne Grip)。你脑子里全是灾难片。觉得无论怎么做未来都会出大事，把一点小风险想得特别可怕。",
            "advice": "【洗洗盘子】：别想“万一”了。去做件具体的小事：叠衣服、洗盘子。手只要动起来，脑子里的灾难片就停了。"
        },
        "highLoop": { # Loop
            "insight": "当前状态：【记仇】(Si-Ti Loop)。你不体谅人了，躲在角落算旧账。想的全是“谁对不起我”，变得冷漠又固执。",
            "advice": "【直接说】：别让人家猜你的委屈，猜不到的。直接说：“我累了，帮帮我。”说出来，你就没那么大怨气了。"
        },
        "crisis": { # Crisis
            "insight": "当前状态：【全面崩塌】(CRISIS)。恨过去的人，怕未来的事。觉得最熟悉的生活都在散架，不知道往哪躲。",
            "advice": "【找个依靠】：别一个人扛了。你是照顾别人的那个人，但现在你得被照顾。找个信得过的人，哭一场。你需要一个拥抱。"
        }
    },
    "ISTP": {
        "stable": {
            "insight": "当前状态：【冷静的高手】。逻辑好，动手能力强。你现在像水一样灵活，既能解决麻烦，也能享受自由。这时候你最酷。",
            "advice": "【玩点难的】：你现在状态正好。如果觉得无聊，去学个难点的新技能。你需要一点挑战来让脑子兴奋起来。"
        },
        "overload": { # Grip
            "insight": "当前状态：【情绪炸弹】(Fe Grip)。那个冷酷的你没了，变得特别情绪化。觉得没人尊重你，或者被复杂的人际关系搞得想吐。",
            "advice": "【去发泄】：别讲道理，没用。你需要发泄。去健身、打沙袋、吼两嗓子。把火气排出去，理智就回来了。"
        },
        "highLoop": { # Loop
            "insight": "当前状态：【阴谋论】(Ti-Ni Loop)。你不看现实了，躲在脑子里空想。觉得做什么都没意义，甚至怀疑一切都是骗局，不想动弹。",
            "advice": "【动起来】：你的脑子中毒了，解药在手上。立刻动手，修个东西，或者拼个模型。只要手摸到真实的东西，虚无感就散了。"
        },
        "crisis": { # Crisis
            "insight": "当前状态：【困兽】(CRISIS)。觉得世界是假的，又觉得自己被所有人孤立。既愤怒又无力，随时可能爆发。",
            "advice": "【强刺激】：吃最辣的菜，洗冷水澡，剧烈运动。你需要强烈的物理刺激来确认自己还“活着”。别想了，先让心跳快起来。"
        }
    },

    "ISTJ": {
        "stable": {
            "insight": "当前状态：【定海神针】。你现在的状态就是“靠谱”两个字。事情都在按计划走，细节都在你掌控里。你是那种如果世界末日了，还会坚持把今天的日报写完的人。",
            "advice": "【适当偷懒】：你的系统运转很完美，但太紧了。试着在计划表里故意留一个“空白格”。如果不按计划行事天也没塌下来，那就是你赢了。"
        },
        "overload": { # Grip (Ne)
            "insight": "当前状态：【灾难编剧】(Ne Grip)。平时稳如老狗的你，突然开始慌了。脑子里全是“万一出事怎么办”，哪怕只是丢了一把钥匙，你都觉得人生要完蛋。",
            "advice": "【回到桌面】：别想那些还没发生的破事。看看眼前，桌子乱不乱？地脏不脏？把桌子收拾干净，把地拖一遍。只要手里有活干，你就没空瞎想。"
        },
        "highLoop": { # Loop (Si-Fi)
            "insight": "当前状态：【委屈的记账员】(Si-Fi Loop)。你一遍遍回忆过去，觉得自己以前做得那么好，为什么现在受这种气？你越想越觉得自己是全天下最倒霉的老实人。",
            "advice": "【撕掉旧账】：以前的事翻篇了，别老拿出来嚼。去吃顿好的，或者买件一直舍不得买的衣服。对自己好一点，别光顾着在那儿生闷气。"
        },
        "crisis": { # Crisis
            "insight": "当前状态：【系统蓝屏】(CRISIS)。既觉得过去白干了（Loop），又觉得未来没指望（Grip）。你现在处于一种“瘫痪”状态，想动动不了，想哭哭不出。",
            "advice": "【强制重启】：你现在的脑子是死机的。去睡觉，睡不着就闭目养神。把所有责任都抛下，告诉自己：“今天我不干了”。你需要彻底关机一晚。"
        }
    },

    "ESTJ": {
        "stable": {
            "insight": "当前状态：【总指挥】。你现在的效率高得可怕。你清楚每个人该干什么，事情该怎么推进。只要你在场，混乱就不敢露头。你是天生的管事人。",
            "advice": "【少说两句】：你现在很强，但容易压得别人喘不过气。试着把那个“你是对的”的话咽回去一半。有时候，闭嘴比下命令更显威信。"
        },
        "overload": { # Grip (Fi)
            "insight": "当前状态：【崩溃的暴君】(Fi Grip)。那个铁面无私的你不见了。你突然觉得自己没人爱，觉得这帮手下（或家人）都是白眼狼，委屈得甚至想在大街上哭。",
            "advice": "【允许矫情】：别憋着。你也是肉做的。找个没人的地方，或者信任的人，骂几句脏话，或者哭一场。承认自己也会受伤，不丢人。"
        },
        "highLoop": { # Loop (Te-Ne)
            "insight": "当前状态：【瞎指挥】(Te-Ne Loop)。你不想停下来，但其实是在乱忙。你脑子里冒出无数个“最坏情况”，为了防这些情况，你把周围人折腾得半死，还没出结果。",
            "advice": "【坐下喝茶】：你现在是在做无用功。强迫自己坐下，喝杯茶，停十分钟。问自己：“这件事真的需要现在做吗？”只要停下来，你的理智就回来了。"
        },
        "crisis": { # Crisis
            "insight": "当前状态：【暴怒的火山】(CRISIS)。你一边疯狂地想控制一切（Loop），一边觉得自己是世界上最孤独的可怜虫（Grip）。你现在像个随时会炸的高压锅。",
            "advice": "【撤离现场】：离开你的工作岗位，离开那个让你生气的人。去个空旷的地方，吼两嗓子。别做决定，现在的决定全是带着火药味的，会炸伤你自己。"
        }
    },

    "ESFJ": {
        "stable": {
            "insight": "当前状态：【热心肠的组长】。你能照顾好每个人的情绪，也能把事情安排得井井有条。大家跟你在一起很舒服，你也从这种被需要的感觉里获得了力量。",
            "advice": "【关上耳朵】：你现在很好，但太在意别人的评价了。试着做一件可能会让某人不高兴、但你自己想做的事。你会发现，被讨厌一次也没什么大不了。"
        },
        "overload": { # Grip (Ti)
            "insight": "当前状态：【刻薄的杠精】(Ti Grip)。温暖的你没了，变得冷冰冰的。你开始挑别人的刺，说话夹枪带棒，觉得周围人都是蠢货，恨不得跟所有人断交。",
            "advice": "【不要思考】：你现在的逻辑是扭曲的。别想“他为什么这么做”，越想越气。去撸猫，去浇花，去抱抱你的孩子。做点不需要动脑子的事。"
        },
        "highLoop": { # Loop (Fe-Ne)
            "insight": "当前状态：【讨好型焦虑】(Fe-Ne Loop)。你太怕得罪人了。脑补出无数种“如果我这么做，他会不会生气”的剧情。你像个陀螺一样围着别人转，把自己搞丢了。",
            "advice": "【断网保平安】：关掉微信，关掉电话。把自己关在房间里。问自己：“我现在想吃什么？想睡吗？”先把你这具身体照顾好，别人死不了。"
        },
        "crisis": { # Crisis
            "insight": "当前状态：【歇斯底里】(CRISIS)。你拼命想讨好别人（Loop），心里却在疯狂攻击别人（Grip）。你觉得自己付出了一切，最后却是个笑话。",
            "advice": "【谁都别理】：现在谁来找你都别理。去洗个热水澡，把门锁好。大哭一场。你现在不需要讲道理，只需要把肚子里的委屈全吐出来。"
        }
    },

    "ISFP": {
        "stable": {
            "insight": "当前状态：【自在的艺术家】。你活在当下，怎么舒服怎么来。你对美、对味道、对声音特别敏感。现在的你，就像一只晒太阳的猫，谁也别想打扰你的节奏。",
            "advice": "【出个作品】：别光顾着感受，动动手。画张画，做个菜，或者拼个乐高。把你心里的那个感觉变成看得见的东西，你会更有成就感。"
        },
        "overload": { # Grip (Te)
            "insight": "当前状态：【暴躁工头】(Te Grip)。那个随和的你不见了。你突然开始讲效率，嫌别人磨叽，想强行控制事情的走向，变得特别凶，像变了个人。",
            "advice": "【别装了】：你不是那种效率机器，别逼自己当强人。承认自己现在就是乱了。把手里的活儿一扔，去睡一觉。天塌下来有高个子顶着。"
        },
        "highLoop": { # Loop (Fi-Ni)
            "insight": "当前状态：【被害妄想】(Fi-Ni Loop)。你钻进牛角尖了。觉得这件事肯定成不了，觉得自己注定要失败。你对未来的想象全是灰色的，越想越绝望。",
            "advice": "【出门晒太阳】：你的脑子发霉了。出门，去公园，去便利店。看看真实的树，摸摸真实的商品。只要感官动起来，那些吓人的幻觉就散了。"
        },
        "crisis": { # Crisis
            "insight": "当前状态：【自我毁灭】(CRISIS)。你觉得未来没希望（Loop），现在又很暴躁（Grip）。你甚至想干点冲动的事（比如辞职、分手、花光积蓄）来打破这个局面。",
            "advice": "【别动钱包】：把手机交给你信任的人，或者锁起来。今天不要做任何决定，尤其是花钱和说狠话的决定。吃顿高热量的垃圾食品，睡觉。"
        }
    },

    "ESTP": {
        "stable": {
            "insight": "当前状态：【甚至有点帅的混球】。你反应快，胆子大，遇到问题直接上手解决。你现在的状态就是“干了再说”，而且往往干得还不错。你是活在现实里的赢家。",
            "advice": "【想得深点】：你现在冲劲很足，但容易只看眼前。做决定前，哪怕多想这一步：“如果不成，我能兜底吗？”只要多这一步，你就无敌了。"
        },
        "overload": { # Grip (Ni)
            "insight": "当前状态：【突然怂了】(Ni Grip)。那个天不怕地不怕的你，突然开始信命了。你觉得肯定有坏事发生，觉得这就是宿命，变得神神叨叨，甚至不敢出门。",
            "advice": "【去举铁】：别瞎想，你的直觉一般都不准。你需要的是物理刺激。去健身房，把铁片举起来。当你肌肉充血的时候，那些神神叨叨的念头就没了。"
        },
        "highLoop": { # Loop (Se-Fe)
            "insight": "当前状态：【孔雀开屏】(Se-Fe Loop)。你太想证明自己了。到处显摆，为了面子死撑，或者跟人吹牛。你看起来很热闹，其实是在掩饰心里的发虚。",
            "advice": "【闭嘴干活】：别发朋友圈了，别看有多少人点赞。找件具体的事（比如修车、整理电脑），安安静静把它做完。用结果说话，别用嘴。"
        },
        "crisis": { # Crisis
            "insight": "当前状态：【亡命之徒】(CRISIS)。你为了面子硬撑（Loop），心里却怕得要死（Grip）。你现在可能会做极其危险、不计后果的事来掩饰恐慌。",
            "advice": "【找人按住你】：你现在是失控的。找个靠谱的兄弟，跟他说：“我这几天不对劲，看着我点。”别碰酒精，别碰车。老实待着。"
        }
    },

    "ESFP": {
        "stable": {
            "insight": "当前状态：【聚光灯C位】。你热情、好玩，有你在的地方就不冷场。你享受现在的每一秒，这种快乐的感染力是你最大的天赋。大家都喜欢跟你待在一起。",
            "advice": "【存点钱】：你现在很容易为了开心冲动消费。开心很重要，但别透支。买东西前数三个数，或者把钱换成定期。留点后路总是对的。"
        },
        "overload": { # Grip (Ni)
            "insight": "当前状态：【世界末日】(Ni Grip)。那个乐天派不见了。你突然变得特别丧，觉得人生没意义，觉得自己这辈子就这样了，甚至开始怀疑朋友都在骗你。",
            "advice": "【别照镜子】：你现在看什么都是灰色的。别想未来，你的长项是现在。去吃火锅，去K歌，去找人陪你疯。把那个丧气的你给震走。"
        },
        "highLoop": { # Loop (Se-Te)
            "insight": "当前状态：【瞎忙活】(Se-Te Loop)。你不敢停下来，一停下来就慌。你哪怕没事干也要找事干，或者强行命令别人干这干那，其实就是为了逃避心里的空虚。",
            "advice": "【坐下别动】：你现在像只无头苍蝇。强迫自己坐下，放空十分钟。难受也忍着。只有面对了这份空虚，你才能真的静下来。"
        },
        "crisis": { # Crisis
            "insight": "当前状态：【躁郁循环】(CRISIS)。一会兴奋得想上天（Loop），一会绝望得想跳楼（Grip）。你在这两极之间反复横跳，把自己搞得精疲力尽。",
            "advice": "【回家躺平】：现在的任何社交都是在消耗你。回家，洗澡，关灯，听最舒缓的音乐。像给手机充电一样，给自己充一晚上的电。明天再说。"
        }
    }
}

DEFAULT_NARRATIVE = {
    "stable": {
        "insight": "你当前更像“稳态推进”：想得清楚、行动阻力不大，同时还能保留恢复空间。",
        "advice": "把优势用在“可交付的小步”上：每周固定 1 次复盘，并留出 1～2 个无任务时段做恢复。"
    },
    "overload": {
        "insight": "你处在“高负荷/高压”区间：压力信号更强，注意力更难稳定。",
        "advice": "优先做恢复与减负：把今天目标缩减为 1 件可交付小成果；睡眠与饮食先稳定，再做身体回正。"
    },
    "highLoop": {
        "insight": "你的内耗倾向偏高：可能在反复推演、过度打磨或过度比较，导致启动成本变高。",
        "advice": "做一次“外部打断”：安排 30 分钟低门槛行动（整理/散步/写 10 行计划），让身体先动起来。"
    },
    "mixed": {
        "insight": "当前状态：【可推进但不算满稳】。你不在内耗高区，但负荷或压力有一定存在感。",
        "advice": "【稳住节奏】：今天用“最小交付 + 明确休息”推进：只保留 1 个最小成果，同时给自己留出恢复窗口。"
    }
}

# ==========================================
# 新增：未来一个月建议库
# ==========================================
# ==========================================
# 4. 付费版深度建议库 (Analysts - 紫色组)
# ==========================================
FUTURE_ADVICE = {
    "INTP": {
        "crisis": {
            "title": "紧急休眠：系统重装指南",
            "text": """
【深度分析】
你现在处于极度危险的“瘫痪”状态。Ti-Si Loop 让你陷入对过去错误的无限反刍，每一件陈芝麻烂谷子的破事都被你翻出来重新审判自己；同时 Fe Grip 让你对外界极其敏感，觉得“没人理解我”、“我注定孤独”，甚至会有莫名其妙的哭泣冲动。你的逻辑内核（Ti）已经破碎，而负责探索的雷达（Ne）完全关闭。你既不想动脑，也不想动身，像一台风扇坏掉却还在满负荷运转的电脑，随时会烧毁。

【为什么会这样】
你的主导功能 Ti 正在攻击你自己，它不再分析世界，而在肢解你的自尊。第三功能 Si 提供了错误的数据库（全是黑历史）。最可怕的是劣势功能 Fe 夺取了控制权，让你表现得像个情绪化的孩子。此刻的你，智商离线，情绪过载。

【未来30天怎么过】
1. 第1-3天：绝对物理隔绝。请假。拉黑或者静音所有让你感到压力的人。不要试图解决任何问题。你的任务只有一个：像植物一样活着。吃饭，睡觉，盯着天花板发呆。允许自己“废掉”。
2. 第4-10天：低压输入。不要看那种需要动脑的硬核书。去看无脑爽文，看纪录片，或者玩那种不需要社交的单机游戏。我们需要一点点 Fe 的安抚（通过故事里的情感）和一点点 Ne 的刺激（新剧情），但不能过量。
3. 第11-30天：微型创造。不要立大项。买个乐高，或者写一段只有50行的代码，或者画个草图。重点是“手脑配合”。当你的手开始创造具体的东西时，Ti 会重新上线去处理结构，Si 会变成经验库而不是审判官。
"""
        },
        "grip": {
            "title": "情感过敏：低压社交复健",
            "text": """
【深度分析】
你现在的状态很反常。平时那个“关我屁事”的冷酷逻辑学家不见了，取而代之的是一个委屈、敏感、甚至有点讨好型人格倾向的“小可怜”。你会因为别人回消息慢了而焦虑，觉得大家都在针对你。你渴望连接，又害怕受伤。这是劣势功能 Fe 在“造反”，它在尖叫着索取关注和爱。

【为什么会这样】
因为长期过度使用逻辑（Ti），你的精神能量耗尽，一直被压抑的情感需求（Fe）爆发了。你现在没有逻辑防御力，任何情绪攻击都能造成暴击。这时候强行用逻辑分析“我为什么难过”是没用的，因为你的逻辑系统已经甚至开始帮着情绪找借口了。

【未来30天怎么过】
1. 第一周：承认软弱。找一个你认为最安全、智商在线的朋友（或者心理咨询师）。告诉他：“我最近状态不对，很情绪化。”不要让他给你提建议，只需要他听着。单纯的“被看见”就能平复 Fe 的暴躁。
2. 第二周：非语言表达。Fe 的能量需要出口。如果不想说话，就去听音乐，听那种撕心裂肺的或者极其治愈的。或者写日记，把那些毫无逻辑的矫情话全写下来，然后烧掉。
3. 后半月：辅助功能 Ne 介入。情绪平复后，我们需要 Ne 来转移注意力。去逛一个你从没去过的论坛板块，或者研究一个冷门的话题（比如苏美尔文明的饮食）。用“好奇心”来替代“对他人的焦虑”。当你的大脑开始因为一个新知识而兴奋时，你就痊愈了。
"""
        },
        "loop": {
            "title": "变量引入：打破逻辑死锁",
            "text": """
【深度分析】
你现在像个老古董。你拒绝任何新信息，固执地守着自己的一亩三分地。遇到问题，你的第一反应不是“有什么新办法”，而是“以前是怎么失败的”。你在脑子里一遍遍复盘过去的细节，试图找出完美的解释，但越想越僵化。你变得无趣、拖延、且充满防御性。

【为什么会这样】
这是典型的 Ti-Si 死循环。你的逻辑（Ti）失去了外向直觉（Ne）的供血，只能不断挖掘内部记忆（Si）。就像CPU在空转，不读取新数据，只发热不产出。解药很简单：必须强行引入“随机变量”。

【未来30天怎么过】
1. 第一周：强行随机。每天做一个违背习惯的决定。平时喝咖啡，今天喝茶。平时走大路，今天钻胡同。平时看科技新闻，今天看娱乐八卦。这种微小的“不确定性”会刺激你的 Ne 探头查看。
2. 第二周：跨界碰撞。找一个完全不同行业的人聊天，或者读一本跟你专业八竿子打不着的书。不要去批判其中的逻辑漏洞，而是强迫自己问：“这东西有什么好玩的？”
3. 后半月：输出原型。Loop 让你只想不动。现在，强迫自己把脑子里的想法做一个“最小可行性产品（MVP）”。哪怕是个烂得要死的草稿。只要它变成了现实里的东西，Ne 就会为了完善它而自动运转起来，带你走出封闭的房间。
"""
        },
        "growth": {
            "title": "系统构建：智慧实体化",
            "text": """
【深度分析】
恭喜，你现在处于 INTP 的黄金状态。你的逻辑（Ti）清晰且结构化，同时你的好奇心（Ne）极其旺盛，像触手一样捕捉着世界的各种可能性。你不焦虑也不固执，处于一种“心流”之中。这时候的你，不是只会空想的哲学家，而是能设计未来的架构师。

【为什么会这样】
Ti 负责搭建骨架，Ne 负责填充血肉，Si 负责提供经验支撑，Fe 负责在最后稍微美化一下界面。四种功能各司其职。现在的关键是：不要让这些能量在脑内空转，必须将其“降维”到物理世界。

【未来30天怎么过】
1. 确立核心项目。本月只专注一个大项目。它可以是一个复杂的理论体系，一套代码，或者一本小说。这个项目必须难到让你兴奋，但又具体到可以拆解。
2. 建立外部Deadline。INTP 在舒适区容易懒散。找一个靠谱的伙伴（最好是 ENTJ 或 ESTJ），让他做你的监工。或者在社交媒体上公开你的计划，利用一点点 Fe（怕丢人）来倒逼行动。
3. 记录与迭代。随身带个本子。这时候你的灵感是井喷的，任何一个闪念都可能价值连城。记下来，然后用 Ti 把它归档到你的系统里。这个月，你要做的是把智慧变成资产。
"""
        }
    },

    "INTJ": {
        "crisis": {
            "title": "废墟重建：绝境求生手册",
            "text": """
【深度分析】
你正处于精神崩溃的边缘。Ni-Fi Loop 让你陷入深度的偏执，觉得全世界都在针对你，没人配得上你的愿景；而 Se Grip 让你对现实世界充满仇恨，你可能在放纵肉欲（暴食、酗酒）和极度禁欲之间反复横跳。你觉得未来已死，甚至产生了一种想要毁掉现有生活的冲动。你是一座正在燃烧的孤岛。

【为什么会这样】
你的主导功能 Ni 能够预见未来，但现在它被 Fi 染上了黑色的情绪，只预见灾难。辅助功能 Te（理性执行）完全下线，导致你失去了改变现实的能力。劣势功能 Se 像个暴徒，试图通过极端的感官刺激来麻痹痛苦。

【未来30天怎么过】
1. 前7天：物理拘束。你现在极度危险。禁止做任何重大决策（辞职、分手、投资）。把你的信用卡锁起来。如果可能，把你的计划告诉一个理性的朋友，让他按住你。你需要像戒毒一样戒掉“毁灭欲”。
2. 中旬：数据清洗。Fi 制造了大量“我觉得有人害我”的幻觉。启动 Te 的第一步是“写下来”。把你的恐惧一条条列出来，旁边列出客观证据。你会发现 90% 的恐惧都是没有事实支撑的臆想。
3. 月末：最小执行。不要想“重建帝国”。先修好那个坏掉的水龙头。Te 需要通过“搞定物理世界的小事”来重启。每完成一件小事，你的掌控感就会回来一分。
"""
        },
        "grip": {
            "title": "感官着陆：驯服野兽",
            "text": """
【深度分析】
你感觉自己“脏了”或者“堕落了”。平时那个自律、禁欲、高智商的你，最近可能沉迷于刷短视频、暴饮暴食、疯狂买没用的东西，或者对环境噪音极其敏感，动不动就暴怒。你厌恶这样的自己，觉得这是低级的表现，但你停不下来。

【为什么会这样】
这是劣势功能 Se 的报复性反弹。因为你长期过度生活在精神世界（Ni），忽视了肉体（Se）的需求。现在身体在罢工，它在用最原始的方式夺取控制权。解药不是“自律”，而是“高质量的感官安抚”。

【未来30天怎么过】
1. 第一周：合法放纵。不要对抗 Se。去吃顿好的（高级的那种），去按摩，去买一套质感很好的床品。用“精致的体验”替代“廉价的放纵”。告诉自己：这是给身体的贡品，不是堕落。
2. 第二周：运动排毒。Se 的能量需要出口。去进行高强度的无氧运动，拳击、举铁、冲刺跑。让你那无处安放的破坏欲通过汗水排出去。当你肌肉酸痛时，你的大脑反而会获得久违的宁静。
3. 后半月：辅助功能 Te 介入。将 Se 的体验纳入计划。比如把“每周三次健身”或“每周一次探店”写入你的日程表。当感官享受变成“计划的一部分”时，Te 就重新掌权了，你也就安全了。
"""
        },
        "loop": {
            "title": "事实核查：走出被害妄想",
            "text": """
【深度分析】
你变得极度封闭和傲慢。你切断了与外界的交流，认为周围人都是蠢货，不配理解你的想法。你在脑子里构建了一个完美的逻辑闭环，论证自己是悲剧英雄，而世界是黑暗的。你沉浸在“没人懂我”的优越感和孤独感中，行动力为零。

【为什么会这样】
Ni-Fi Loop 让你失去了通过 Te（外部思维）与现实校准的能力。Ni 提供了洞察，Fi 提供了主观价值判断。两者结合，你就活在了自己的幻想世界里。你需要的不是安慰，而是冷冰冰的“客观事实”。

【未来30天怎么过】
1. 第一周：强制外化。必须找个人说话。不是找人倾诉感情（Fi），而是找人辩论观点（Te）。找一个逻辑强的人，把你的理论讲给他听。当你的想法必须变成语言说出口时，你自然会发现其中的逻辑漏洞。
2. 第二周：数据对抗。你觉得某件事行不通？好，去做市场调研，去查论文，去找数据。用 Excel 表格来打败你的直觉。Te 的本质是“验证”。
3. 后半月：制定战略。一旦 Te 被激活，你就会发现之前的担忧很多是情绪化的。现在，重新制定计划。不是为了证明你是对的，而是为了把事情做成。将你的愤怒转化为推进项目的燃料。
"""
        },
        "growth": {
            "title": "帝国扩张：战略落地月",
            "text": """
【深度分析】
现在的你，处于 INTJ 的巅峰形态。你的直觉（Ni）精准地看到了未来的趋势，执行力（Te）如军队般高效，情感（Fi）为你提供了坚定的信念底色，感官（Se）能让你注意到关键的细节。你就像一位正在下盲棋的宗师，每一步都算无遗策。

【为什么会这样】
这是 Ni 和 Te 的完美双人舞。Ni 指明方向，Te 铺设道路。现在的风险在于：你可能跑得太快，把团队或资源甩掉了。或者你太专注于长远，忽略了脚下的坑。

【未来30天怎么过】
1. 宏观复盘。利用现在的清晰度，重新审视你的年度甚至五年计划。哪些步骤是可以加速的？哪些资源是闲置的？这是一个“做乘法”的月份。
2. 向下兼容。你的短板在于人。利用 Te 的逻辑去分析你身边的人，把他们放在合适的位置上。不要嫌他们笨，把他们当成你棋盘上的棋子。向他们解释你的愿景（Ni to Te），让他们成为你的助力。
3. 现实锚点。为了防止飘得太高，每天保留一个“落地时刻”。比如亲自处理一件一线的小事，或者做半小时家务。保持对物理世界的触感，能让你的战略更接地气。
"""
        }
    },

    "ENTJ": {
        "crisis": {
            "title": "强制停车：防止过劳死",
            "text": """
【深度分析】
你已经透支了。Te-Se Loop 让你像个无头苍蝇一样疯狂忙碌，只要停下一秒你就会感到恐慌；而 Fi Grip 让你内心深处充满了自我厌恶和空虚感，“我这么拼命到底是为了什么？”你可能正在通过滥用药物、酒精或疯狂工作来麻痹这种空虚。你在驾驶一辆没有刹车的赛车。

【为什么会这样】
Te（效率）过载，Se（感官）失控，Ni（愿景）断线，Fi（情感）崩溃。你失去了方向感，只剩下了速度。你试图用战术上的勤奋来掩盖战略上的迷茫。这是典型的“执行者倦怠”。

【未来30天怎么过】
1. 前3天：彻底停机。这不仅是建议，是命令。扔掉手机，去深山老林，或者去医院体检。你需要物理上的强制静止。哪怕只是坐着发呆，也要忍受那种“我不做事就是废物”的焦虑感。
2. 中旬：寻找意义。Ni 需要重新上线。不谈工作，谈人生。读哲学，读传记，思考“五年后我想成为什么样的人”。你需要重新找到那个能让你热泪盈眶的愿景（Ni），而不是盯着下个月的KPI（Te）。
3. 月末：做减法。砍掉你手上50%的工作。是的，一半。把它们分发出去，或者直接不做。承认你的精力有限。用剩下的50%精力去攻克那个最符合你新愿景的堡垒。
"""
        },
        "grip": {
            "title": "情感风暴：允许自己做个人",
            "text": """
【深度分析】
你感到前所未有的脆弱。你觉得自己是个骗子，觉得周围人都把你当工具，觉得没人真心爱你。你会因为一件小事（比如下属的一个眼神）而感到深深的委屈，甚至想躲在被子里哭。这对强势的你来说，简直是奇耻大辱。

【为什么会这样】
这是劣势功能 Fi 的爆发。你长期忽视自己的情感需求，把它们压在心底。现在它们反弹了。这时候你不需要逻辑开导，需要的是“无条件的接纳”。此时 Te 是失效的，因为感情这种事，没法计算投入产出比。

【未来30天怎么过】
1. 第一周：情感宣泄。找一个跟你的利益圈子完全无关的朋友（FP类型最好），或者你的伴侣。告诉他：“我最近很累，很难过。”不要装强硬。只要你承认了自己的脆弱，Fi 的攻击性就会减半。
2. 第二周：独处内省。既然 Ni 是辅助功能，利用它来向内看。写日记，分析这种情绪的来源。你会发现，这些情绪往往源于你对自己太苛刻。试着像管理员工一样，管理一下你自己，给那个受伤的自己批几天假。
3. 后半月：战略调整。当情绪平复后，利用 Ni 把这次危机转化为养分。思考：是不是我的管理风格太硬了？是不是我忽略了团队的情感建设？将 Fi 的感悟融入到你未来的领导风格中。
"""
        },
        "loop": {
            "title": "战略闭关：甚至需要慢下来",
            "text": """
【深度分析】
你变得粗鲁、急躁、短视。你想要立刻看到结果，一秒都不能等。你拍脑袋做决定，稍微遇到阻力就暴跳如雷。你看起来执行力爆表，但其实是在瞎忙。你正在失去大局观，变成了一个平庸的工头。

【为什么会这样】
Te-Se Loop 让你切断了与辅助功能 Ni（直觉/远见）的联系。你被眼前的细节和即时的反馈（Se）绑架了，忘记了长远的战略（Ni）。你需要的是“慢下来”，甚至“停下来”。

【未来30天怎么过】
1. 第一周：禁言禁行。在会议上强迫自己最后发言。在做决定前强迫自己多等24小时。人为地制造“延迟”。这种延迟会让 Se 的冲动冷却，让 Ni 有机会插嘴说：“老板，这事儿好像不对劲。”
2. 第二周：深度思考。安排“战略独处日”。这一天不处理邮件，不回消息。只思考三个问题：目前的局势是什么？潜在的危机在哪？我们要去的终点变了吗？
3. 后半月：重塑愿景。把你思考的结果写成文档，或者画成图。当你重新看清地图全貌时，你那种暴躁的控制欲就会消失，取而代之的是指挥官的从容。
"""
        },
        "growth": {
            "title": "王者归来：柔性领导力",
            "text": """
【深度分析】
现在的你，是无坚不摧的。Te 提供了强大的逻辑架构，Ni 提供了深远的战略眼光，Se 让你能敏锐地捕捉机会，Fi 让你有了底线和人情味。你不再是一个只会下命令的机器，而是一个能激发团队潜能的领袖。

【为什么会这样】
由 Ni 指引方向，由 Te 扫除障碍。这是 ENTJ 最自然的征服状态。现在的挑战在于：如何让这种状态可持续？如何让你的团队能跟上你的节奏，而不是被你拖死？

【未来30天怎么过】
1. 授权与培养。你现在太强了，所以要克制自己“亲自上手”的冲动。利用 Te 去构建系统，而不是解决单点问题。培养你的副手，把你的思维模型（Ni）教给他们，而不只是下达指令。
2. 文化建设。利用你状态好的时候，去关注一下团队的“软实力”。搞搞团建，聊聊愿景。用 Ni 的感染力去凝聚人心，而不仅仅是用 Te 的KPI去考核。
3. 跨界整合。你的视野（Ni）现在很开阔。去接触一些其他领域的强者。寻找战略合作伙伴。这个月适合做那些能改变格局的大事，而不是纠结细节。
"""
        }
    },

    "ENTP": {
        "crisis": {
            "title": "混乱之子：秩序重建计划",
            "text": """
【深度分析】
你现在就像小丑电影里的主角。Ne-Fe Loop 让你在人群中疯狂表演，渴望关注，甚至撒谎、操纵；而 Si Grip 让你在独处时陷入对身体和细节的极度恐慌。你觉得自己病了，或者被过去的一个小错误死死缠住。外表癫狂，内核恐惧。你正在解体。

【为什么会这样】
Ne（发散）失控，制造了无穷的混乱；Fe（情感）让你过度依赖外界反馈；Si（经验/身体）作为劣势功能，像个记仇的管家，拿着放大镜找你的茬。辅助功能 Ti（逻辑）完全下线，你失去了判断真假的能力。

【未来30天怎么过】
1. 前3天：感官剥夺。切断所有社交媒体。不要发朋友圈，不要看点赞。你需要切断 Fe 的供养。把自己关在家里，除了必需品，什么都不买，什么都不看。
2. 中旬：机械秩序。你需要 Ti 和 Si 的结合：秩序。去做最枯燥的事：抄书、练字、拼图、整理Excel表格。这些不需要创意、只需要逻辑和耐心的事，能帮你把破碎的自我拼回来。
3. 月末：逻辑复盘。当心跳平稳后，用 Ti 冷酷地审视最近的行为。问自己：“我做这些是为了什么？符合逻辑吗？”把那些为了博眼球而做的蠢事列入黑名单。
"""
        },
        "grip": {
            "title": "疑病焦虑：身体复苏指南",
            "text": """
【深度分析】
那个天不怕地不怕的你，突然变成了林黛玉。你觉得心脏疼，觉得胃不舒服，觉得最近运气特别差。你开始回忆五年前是不是得罪了谁，或者陷入对某个琐碎细节（比如文档格式）的强迫性纠结。你变得保守、退缩、毫无灵气。

【为什么会这样】
这是劣势功能 Si 的反噬。因为你长期忽视身体，忽视细节，忽视过去。现在 Si 让你体验到了“肉体的沉重”。这时候不能用 Ne（想点别的）来逃避，因为你的身体在报警。你需要辅助功能 Ti 来理性地处理这些信号。

【未来30天怎么过】
1. 第一周：专业体检。别在百度上查病，那会吓死你。去正规医院做个体检。拿到报告（Ti 的证据），证明自己没死。这是最快的止恐剂。
2. 第二周：舒适疗法。Si 需要的是安抚。去按摩，去泡澡，去吃妈妈做的菜。穿最舒服的衣服。把生活节奏降到最慢。像照顾老人一样照顾自己。
3. 后半月：微习惯养成。不要试图变成自律达人。用 Ti 设计一个极简的健康系统：比如“每天喝三杯水”。只要你能坚持一个小习惯，Si 带来的掌控感就会压倒恐惧感。
"""
        },
        "loop": {
            "title": "流量乞丐：逻辑隔离区",
            "text": """
【深度分析】
你现在太“油”了。你为了讨好别人，或者为了显得自己很牛，满嘴跑火车。你过度承诺，却什么都兑现不了。你沉迷于点赞、掌声和社交快感，但内心深处觉得我很空虚，甚至不知道自己是谁。

【为什么会这样】
Ne-Fe Loop 让你变成了随波逐流的变色龙。Ne 让你看到别人想听什么，Fe 让你去说别人想听的。你丢掉了辅助功能 Ti（批判性思维）。你不再追求真理，只追求效果。你需要找回你的“刺”。

【未来30天怎么过】
1. 第一周：物理禁言。卸载社交软件。推掉所有聚会。每天必须独处3小时以上。刚开始你会觉得痒，觉得被世界遗忘了。忍着。
2. 第二周：深度阅读。读哲学，读硬科幻，读逻辑学。读那些枯燥但深刻的东西。让大脑重新开始进行复杂的逻辑推演（Ti），而不是简单的条件反射。
3. 后半月：批判性输出。写一篇文章，或者录一段话，只说真话，哪怕得罪人。用 Ti 的手术刀去解剖一个现象。当你不再试图讨好谁，而是试图说服谁时，那个犀利的 ENTP 就回来了。
"""
        },
        "growth": {
            "title": "降维打击：闭环交付月",
            "text": """
【深度分析】
此刻的你，是上帝的宠儿。Ne 让你看到了无限的可能性，Ti 让你能从逻辑上验证这些可能性，Fe 让你能把这些想法推销出去，Si 让你能勉强记得吃饭睡觉。你充满魅力，才思泉涌。

【为什么会这样】
唯一的风险是：想法太多，落地太少。ENTP 最容易死在“三分钟热度”。从 Ne（点子）到 Ti（方案）你很熟，但从 Ti 到 Si（执行细节）是你的死穴。本月的重点是“完成”。

【未来30天怎么过】
1. 单点爆破。把你脑子里的100个点子杀掉99个。只留一个。最可行的那个。发誓这个月只做这一件事。把它当成一个实验，必须产出实验报告。
2. 引入外援。找个 SJ 型的伙伴（工具人），或者用 Ti 设计一套自动化的流程。把那些如果你自己做肯定会半途而废的细节工作外包出去。你只负责核心逻辑的攻关。
3. 定义“完成”。ENTP 所谓的“做完了”通常是“我想通了”。不行。给自己定一个物理标准：代码上线了？文章发表了？钱到账了？只有物理世界的反馈，才能真正验证你的天才。
"""
        }
    },
    
    "INFJ": {
        "crisis": {
            "title": "🛌 强制关机：身心极度透支",
            "text": """
【深度分析】
你现在的情况不仅仅是累，而是“透支”。Loop 让你觉得活着没意思，甚至对人很冷漠；Grip 让你对周围的环境（声音、光线、混乱）特别没耐心，或者暴饮暴食。你一边觉得世界很吵，一边觉得自己很空。这是身体和精神双重罢工的信号。

【为什么会这样】
因为你平时吸纳了太多别人的情绪垃圾，却没有及时清理。你的直觉（Ni）不仅没能帮你指向未来，反而和内向思考（Ti）联手攻击你自己，让你觉得“一切都没有意义”。同时，被你压抑太久的感官需求（Se）开始爆发，让你变得焦躁不安。

【未来30天怎么过】
1. 第1-3天：像生病一样养着。请假，或者推掉所有非必要的社交。告诉朋友你这几天不舒服。拉上窗帘，点个香薰，或者只是睡觉。现在的你不需要“振作”，只需要“消失”几天。
2. 第4-10天：做点手里能拿住的事。别思考人生大道理了。去收拾屋子，去给植物换个盆，或者手洗几件衣服。让手接触水，接触泥土。这种真实的触感（Se）能慢慢把飘在半空中的你拉回地面。
3. 第11-30天：只对一个人说话。找那个最懂你、最口风紧的朋友。不要聊宏大的话题，只聊你的委屈。把你心里的那些“毒素”吐出来。当你的情绪被接纳了，那个温柔的你自然就回来了。
"""
        },
        "grip": {
            "title": "身体安抚：照顾好你的感官",
            "text": """
【深度分析】
你最近可能变得很反常：要么是控制不住地买买买、吃吃吃，要么是对一点点噪音、脏乱都忍不了，发很大的火。你觉得自己变得很俗气、很暴躁，一点也不像平时的自己。

【为什么会这样】
这是劣势功能 Se（外向感觉）的报复。你长期活在精神世界里，忽略了身体的感受。现在身体在抗议，它在用这种极端的方式提醒你：我也是需要被照顾的。

【未来30天怎么过】
1. 第一周：不带脑子的享受。别批判自己堕落。去吃顿好的，去按摩，去买那件摸起来很舒服的衣服。把这当成给身体的“贡品”。只要身体舒服了，你的情绪就会平稳一半。
2. 第二周：走进大自然。如果觉得屋里闷，就去公园走走。不是去跑步健身，就是去散步，看看树，吹吹风。大自然的频率是最能安抚 INFJ 的。
3. 后半月：哪怕做一点点运动。不需要高强度，哪怕是睡前拉伸十分钟，或者练一次瑜伽。重新建立和身体的连接，别再把它当成一个仅仅用来装大脑的容器。
"""
        },
        "loop": {
            "title": "🗣 走出孤岛：找人聊聊天",
            "text": """
【深度分析】
你把自己关起来了。表面上可能还在应付，但心里已经切断了跟所有人的连接。你冷冷地看着周围，觉得大家都很肤浅，或者觉得没人能懂你。你在脑子里自己跟自己辩论，越想越觉得没希望。

【为什么会这样】
这是 Ni-Ti 死循环。你切断了辅助功能 Fe（外向情感），也就是切断了“人味儿”。没有了外部的反馈，你的直觉就变成了毫无根据的胡思乱想，逻辑就变成了自我攻击的武器。

【未来30天怎么过】
1. 第一周：打破沉默。强迫自己每天跟一个活人说点“废话”。不是工作对接，就是闲聊。比如跟快递员说声谢谢，跟同事聊聊午饭。这点微弱的连接感，是你打破冰封的第一步。
2. 第二周：表达观点，而非情绪。找个能理性讨论问题的人，把你最近思考的某个观点讲给他听。看看他的反应。通常你会发现，现实并没有你脑补的那么糟糕。
3. 后半月：帮一个小忙。Fe 的核心是“利他”。去帮朋友一个小忙，或者喂喂流浪猫。当你感觉到自己被需要的时候，你就从那个孤岛上解脱了。
"""
        },
        "growth": {
            "title": "愿景落地：把想法变成现实",
            "text": """
【深度分析】
现在的你状态很好。你看得清未来的方向，也愿意去理解和帮助他人。你既有深度，又有温度。这是 INFJ 最迷人的时刻——像一位温和的引路人。

【为什么会这样】
你的 Ni（直觉）指明了方向，Fe（情感）帮你召集了伙伴，Ti（逻辑）帮你筛选了信息。现在的关键是，不要让这些美好的愿景只停留在脑子里。

【未来30天怎么过】
1. 写下来。这周的任务是把你的长期计划写成文字。越具体越好。不是为了给别人看，是为了让你自己确信它是可行的。
2. 设立边界。状态好更有可能被别人消耗。提前规定好，每天哪几个小时是绝对属于你自己的工作时间，谁来也不见。保护好你的能量。
3. 推进一步。选一件你一直想做但不敢做的大事（比如写书、换工作、表白），在这个月迈出第一步。哪怕只是发一封邮件。现在的直觉是准的，信它。
"""
        }
    },

    "INFP": {
        "crisis": {
            "title": "🛡 停止自责：自我保护月",
            "text": """
【深度分析】
你现在对自己充满了厌恶。Loop 让你沉浸在过去失败的回忆里，觉得“我这辈子都改不了了”；Grip 让你对周围的人变得很凶，或者对自己要求极其苛刻。你一边攻击别人，一边在心里把自己骂得一文不值。

【为什么会这样】
你的核心功能 Fi（内向情感）受伤了，躲进了回忆（Si）里疗伤，导致你不想面对新事物。而原本不擅长的 Te（外向思考）跳出来接管局面，它用一种粗暴的、不近人情的方式试图维持秩序，结果让你更痛苦。

【未来30天怎么过】
1. 第1-3天：像孩子一样被原谅。停止一切反省。你没有错，你只是累了。买点童年爱吃的零食，看那个看过十遍的老动画片。告诉自己：“就算我什么都做不好，也没关系。”
2. 第4-10天：微小的整理。混乱的环境会加重你的焦虑。不需要大扫除，哪怕只是把书桌的一角理干净，或者把脏衣服扔进洗衣机。这能让你稍微感觉好一点。
3. 第11-30天：用手去创造。INFP 的疗愈在指尖。去涂鸦，去捏泥巴，去写只有自己能看懂的诗。不要管好不好看，把心里的那团乱麻通过手“流”出来，你就通畅了。
"""
        },
        "grip": {
            "title": "软化内心：别逼自己太紧",
            "text": """
【深度分析】
那个随和、温柔的你不见了。你突然变得特别急躁，嫌弃别人动作慢，嫌弃自己效率低。你列了一堆计划表，强迫自己像机器一样执行，完不成就发火。你变得很硬，硬得像块石头。

【为什么会这样】
这是劣势功能 Te 的爆发。因为内心太焦虑，你试图通过“控制外部世界”来寻找安全感。但你装出来的强势是虚的，因为忽略了你最宝贵的感受。

【未来30天怎么过】
1. 第一周：撕掉计划表。承认吧，你根本不是那种按表操课的人。把那些逼死你的待办事项全删了。只留下一件今天必须做的事，其他的随缘。
2. 第二周：承认我不行。当你想骂人（或者骂自己）的时候，停三秒，深呼吸，说：“我搞不定了，我需要休息。”示弱不丢人，那是你回归真实的开始。
3. 后半月：做点没用的事。Te 最讨厌“无用”。你要反着来。去发呆，去观察一片叶子，去漫无目的地闲逛。找回那个松弛的、柔软的自己。
"""
        },
        "loop": {
            "title": "推开门：尝试一点新鲜事",
            "text": """
【深度分析】
你躲在舒适区里不肯出来。总是回想以前的事，或者反复咀嚼某种遗憾的情绪。你拒绝认识新朋友，拒绝去新地方，觉得外面的世界很危险，还是躲在被窝里最安全。

【为什么会这样】
这是 Fi-Si 死循环。你只关注内部感受（Fi）和过去经验（Si），切断了探索世界的好奇心（Ne）。房间里的空气如果不流通，是会发霉的。

【未来30天怎么过】
1. 第一周：换条路走。不需要大冒险。下班回家换条路，或者去一家没吃过的面馆。点一杯从没喝过的饮料。这种微小的“新鲜感”就是给 Ne 的养分。
2. 第二周：读一本新书。不要老看以前喜欢的那些了。找一本完全陌生领域的书，或者看一部新出的电影。让新的故事进入你的脑子，把陈旧的回忆挤出去。
3. 后半月：分享你的想法。把你最近的一个脑洞，讲给朋友听，或者发在网上。当你的想法引起了别人的共鸣，你会重新发现，原来外面的世界也挺有趣的。
"""
        },
        "growth": {
            "title": "表达自我：让才华流动",
            "text": """
【深度分析】
现在的你，眼睛里有光。你对自己很诚实，对世界很温柔。你不仅能感知到那些细微的美好，还有动力把它们表达出来。你是最棒的倾听者，也是最有灵气的创作者。

【为什么会这样】
Fi 让你拥有内核，Ne 让你拥有翅膀。现在的你，是脚踩大地（Si）、仰望星空（Ne）的状态。Te 也能偶尔出来帮帮忙，让你把想法落地。

【未来30天怎么过】
1. 搞个作品。别让灵感跑了。这个月给自己定个小目标：写完那篇小说，画完那幅画，或者剪完那个视频。把你的内心世界具象化。
2. 寻找同频的人。去参加一个读书会，或者加入一个兴趣小组。和那些能听懂你“火星语”的人待在一起。你们的能量会互相放大。
3. 记录美好。每天记三件让你开心的小事。这能帮你积累正向的 Si（经验库），等下次情绪低落的时候，这些就是你的救命药丸。
"""
        }
    },

    "ENFJ": {
        "crisis": {
            "title": "情感耗竭：面具卸载月",
            "text": """
【深度分析】
你累到不想说话。平时那个总是照顾大家的小太阳，现在心里充满了怨气。Loop 让你停不下来地无效社交，Grip 让你在内心疯狂批判所有人。你觉得自己一直在演戏，演得很累，但又不敢停下来，怕一停下来就没人喜欢你了。

【为什么会这样】
你一直在对外输出能量（Fe），却忘了给自己充电。Ni（洞察力）被忽视了，Ti（逻辑）在阴暗角落里发酵成了攻击性。你为了维持“好人”的人设，透支了灵魂。

【未来30天怎么过】
1. 第1-3天：消失一下。请假，关机，去一个没人认识你的地方待两天。或者在家里把门锁好。不需要向任何人解释。这段时间，你只对自己负责。
2. 第4-10天：宣泄怨气。找个树洞（日记本或者陌生网友），把你对这个世界的看法全说出来。哪怕是骂人的话。承认自己也有阴暗面，这没什么，这很真实。
3. 第11-30天：独处阅读。强迫自己独处。看点有深度的书（心理学、哲学）。让 Ni 重新上线。你会发现，你的价值不来自于“让别人开心”，而来自于你本身的存在。
"""
        },
        "grip": {
            "title": "停止挑刺：简单地去爱",
            "text": """
【深度分析】
你变得不像你了。平时宽容的你，现在特别爱钻牛角尖。揪住别人的一句话不放，过度分析逻辑，觉得大家都在骗你，或者觉得所有人都很蠢。你变得冷漠、刻薄。

【为什么会这样】
这是劣势功能 Ti 的爆发。当情感压力过大时，你那不成熟的逻辑功能跳出来试图保护你，但它用的方式是“攻击”和“质疑”。

【未来30天怎么过】
1. 第一周：和小动物待着。人太复杂了，你现在处理不了。去撸猫，遛狗。动物的爱是简单的、无条件的。它们能融化你那个因为防御而变得冰冷的心。
2. 第二周：停止想“为什么”。别去分析别人的动机。很多时候没那么多为什么，别人就是随口一说。放过别人，也是放过你自己。
3. 后半月：做点机械劳动。做饭、拼图、填色。做点不需要动脑子、只需要动手的事。让大脑休息一下，逻辑批判自然就停了。
"""
        },
        "loop": {
            "title": "暂停营业：无意义的忙碌",
            "text": """
【深度分析】
你像个停不下来的陀螺。每天排满了聚会、饭局，生怕错过任何消息。你看起来朋友很多，很热闹，但夜深人静的时候，你觉得心里空荡荡的，不知道自己在忙什么。

【为什么会这样】
这是 Fe-Se 死循环。你过度追求外界的反馈（Fe）和当下的刺激（Se），切断了向内思考的通道（Ni）。你在用热闹来掩盖孤独。

【未来30天怎么过】
1. 第一周：学会说“不”。这周拒绝三个不重要的聚会。刚开始你会焦虑，觉得“他们会不会不高兴”。忍住。你会发现，地球离了你照样转。
2. 第二周：写日记。每天花20分钟，只跟自己对话。问自己：“今天我开心吗？我真正想要的是什么？”把注意力从别人身上收回来。
3. 后半月：深度对谈。约一个真正有思想的朋友，进行一次深度的聊天。聊聊未来，聊聊人生。不要聊八卦。你需要有质量的交流，而不是数量。
"""
        },
        "growth": {
            "title": "深度引领：做真正的领袖",
            "text": """
【深度分析】
你现在的状态非常有感染力。你不仅能照顾大家的情绪，还能指出成长的方向。你不再是为了讨好而付出，而是为了共同的目标而引领。大家信赖你，是因为你既温暖又强大。

【为什么会这样】
Fe 让你连接他人，Ni 让你看清方向。当这两个功能平衡时，你就是天生的精神领袖。

【未来30天怎么过】
1. 做个榜样。不要光是用嘴说教。你想让大家变成什么样，你自己先做成什么样。你的行动比语言更有力量。
2. 培养新人。利用你的洞察力，去发现身边人的潜力。给他们机会，鼓励他们成长。成就他人，是你最大的成就感来源。
3. 留足空间。即使是领袖也需要休息。一定要留出“后台休息区”。只有你自己的能量满了，才能持续地发光发热。
"""
        }
    },

    "ENFP": {
        "crisis": {
            "title": "电量耗尽：居家充电月",
            "text": """
【深度分析】
你在外面还在死撑，表现得像个没心没肺的开心果（Loop），但一回家就瘫在床上，觉得身体哪哪都不舒服，对未来充满了莫名的恐惧（Grip）。你感觉自己被掏空了，只剩下一个疲惫的驱壳。

【为什么会这样】
你过度透支了自己的探索欲（Ne），忽略了身体和内心的承受力。Si（内向感觉）作为劣势功能，开始用生病、疲劳、强迫症来强制你停下来。你现在不是懒，是没电了。

【未来30天怎么过】
1. 第1-3天：彻底躺平。别回消息，别看新闻。睡觉，睡到自然醒。点外卖，吃点高热量的东西。这时候不需要自律，需要的是像冬眠的熊一样休息。
2. 第4-10天：老友记。不要去认识新朋友了，太累。找那一两个最熟的老朋友，穿睡衣聊天，或者一起打游戏。在熟悉的人面前，你不需要表演快乐。
3. 第11-30天：整理生活。把房间收拾一下，把囤积的东西扔一扔。当外部环境变得清爽有序时，你那个混乱的内心也会跟着平静下来。
"""
        },
        "grip": {
            "title": "寻找安稳：不要逼自己",
            "text": """
【深度分析】
那个灵气十足的你不见了。你突然变得很死板、很胆小。你担心自己得了绝症，或者反复检查门锁，对细节特别较真。你觉得生活充满了危险，只想缩在壳里。

【为什么会这样】
这是劣势功能 Si 的爆发。平时你最烦细节和重复，现在它们反过来控制了你。你在潜意识里渴望安全感，但表现出来的是过度焦虑。

【未来30天怎么过】
1. 第一周：吃熟悉的饭。别去探店了。去吃你从小吃到大的那家店，或者妈妈做的菜。熟悉的味道能给 Si 极大的安全感。
2. 第二周：规律作息。试着每天同一时间起床，同一时间睡觉。虽然听起来很无聊，但这种“可预测性”是你现在的解药。
3. 后半月：温习旧爱。重读一本喜欢的书，重看一部老电影。在已知的情节里，你会找回久违的平静。
"""
        },
        "loop": {
            "title": "回归内心：空转的马达",
            "text": """
【深度分析】
你看起来很忙，项目一个接一个，点子一个接一个。你说话很快，走路很快，甚至有点强势。但如果你停下来问自己“我现在的感觉是什么”，你可能答不上来。你麻木了。

【为什么会这样】
这是 Ne-Te 死循环。你切断了辅助功能 Fi（内向情感），变成了一个只会执行任务的机器。你跑得太快，把灵魂丢在了后面。

【未来30天怎么过】
1. 第一周：每天发呆15分钟。什么都不做，不带手机，就坐着发呆。刚开始你会很慌，想找事做。忍住。你需要把那个被屏蔽的 Fi 信号重新接通。
2. 第二周：写情绪日记。记录你的心情，而不是日程。今天难过吗？为什么？把关注点从“我要做什么”转移到“我是怎么想的”。
3. 后半月：做件没用的事。去公园吹泡泡，去画一幅没人看的画。做一些没有产出、不能赚钱、纯粹为了自己开心的事。
"""
        },
        "growth": {
            "title": "专注行动：从想法到现实",
            "text": """
【深度分析】
你现在简直在发光。脑子里有无数好点子（Ne），心里有坚定的信念（Fi），而且居然还能沉下心来去执行（Te）。你有热情，也有行动力。这是 ENFP 最容易出成果的时候。

【为什么会这样】
四种功能配合默契。Ne 负责开拓，Fi 负责把关，Te 负责落地，Si 负责稳住底盘。现在的你，势不可挡。

【未来30天怎么过】
1. 只选一件事。你的天敌是“分心”。这个月，把你那10个好点子砍掉9个，只留最想做的那一个。集中所有火力攻下它。
2. 找个监督员。找个靠谱的朋友（最好是 J 人），让他定期检查你的进度。有点外部压力，能帮你度过那些枯燥的执行期。
3. 完成比完美重要。别纠结细节。先把东西做出来，哪怕是个半成品。只要它面世了，就是你的胜利。
"""
        }
    },
    
    "ISTJ": {
        "crisis": {
            "title": "强制重启：系统严重故障",
            "text": """
【深度分析】
你现在正处于“卡死”状态。一方面，你陷在过去的回忆里，反复纠结以前犯过的错，觉得自己这辈子都很失败（Loop）；另一方面，你对未来充满了恐慌，觉得不管做什么都会出乱子，甚至想放弃一切逃跑（Grip）。你既动弹不得，又焦虑万分。

【为什么会这样】
你的主导功能 Si（内向感觉）变成了审判官，不再提供经验，只提供悔恨。劣势功能 Ne（外向直觉）完全失控，制造了无数虚假的灾难预警。你原本引以为傲的条理和逻辑（Te）此刻完全下线，留你一个人在混乱中裸奔。

【未来30天怎么过】
1. 第1-3天：执行极简模式。停止所有复杂的思考。除了吃饭、睡觉、上班（如果必须去），不要做任何额外的事。把生活简化到只剩生存。你需要物理上的静止来让混乱的思绪沉淀。
2. 第4-10天：整理物理环境。混乱的房间会加重你的焦虑。花时间把桌面理干净，把衣柜叠整齐。当你的手在整理具体物品时，你的 Si 功能会从“悔恨”模式切换回“秩序”模式。看着整齐的房间，你的心就稳了。
3. 第11-30天：执行微小计划。不要定大目标。定一个“每天喝8杯水”或者“每天读5页书”的小计划，并严格执行。用这种微小的成功来告诉大脑：生活依然在我的掌控之中。
"""
        },
        "grip": {
            "title": "停止灾难化：回归眼前",
            "text": """
【深度分析】
平时稳重的你，最近变得疑神疑鬼。可能只是丢了个钱包，你就觉得人生要完蛋了；或者身体一点不舒服，你就怀疑是绝症。你脑子里全是负面的“万一……怎么办”，整个人处于一种非理性的惊恐中。

【为什么会这样】
这是劣势功能 Ne 的爆发。你平时习惯了确定的已知，压抑了对未知的探索。现在未知反扑了，它以“灾难想象”的形式出现。你想用逻辑去反驳它，但现在的你没有逻辑，只有恐惧。

【未来30天怎么过】
1. 第一周：禁止预测未来。每当脑子里冒出“万一”这个词，立刻对自己喊停。强制把注意力拉回到眼前。看看手里的杯子，摸摸桌子的纹理。关注“现在”哪怕一分钟，焦虑就会中断。
2. 第二周：做熟悉的事。去吃你最常吃的那家馆子，走你最熟的那条路，做你最擅长的那项工作。用大量重复的、熟悉的经验（Si）来构筑防线，把那些吓人的未知挡在外面。
3. 后半月：验证事实。如果你担心生病，就去体检。如果你担心工作，就去问老板。拿到确切的报告或答复。用冷冰冰的事实（Te）打败虚无缥缈的想象。
"""
        },
        "loop": {
            "title": "走出死胡同：停止翻旧账",
            "text": """
【深度分析】
你变得非常难相处。你拒绝接受任何新建议，固执地坚持“老规矩”。同时，你心里积压了很多委屈，一遍遍回想别人以前是怎么对不起你的，越想越气，变得冷漠又挑剔。

【为什么会这样】
这是 Si-Fi 死循环。你只看过去（Si）和自己的感受（Fi），切断了外部的客观标准（Te）。你把自己锁在一个充满了陈旧怨气的房间里，拒绝开窗透气。

【未来30天怎么过】
1. 第一周：对自己好一点。Loop 状态下的你往往对自己也很抠门。去买件质量好的衣服，或者吃顿贵的。用物质上的舒适感来安抚那个委屈的 Fi。
2. 第二周：尝试新工具。工作上，强迫自己试用一个新的软件，或者换一种新的记录方式。哪怕一开始很别扭。只要引入一点点新变量，那种僵化的死循环就会松动。
3. 后半月：列出客观清单。当你觉得“别人都对不起我”时，拿纸笔列出来。具体的事件、时间、对错。一旦落实到纸面， Te 就会介入，你会发现很多委屈其实是你自己的情绪放大。
"""
        },
        "growth": {
            "title": "优化升级：从执行到管理",
            "text": """
【深度分析】
现在的你，可靠得像座山。生活井井有条，工作滴水不漏。你是团队里最让人放心的人。你不仅能把自己的事做好，还能帮周围人建立秩序。

【为什么会这样】
Si 提供了丰富的经验库，Te 提供了高效的执行手段，Fi 让你有了责任心。你处于一种高效运转的稳态中。

【未来30天怎么过】
1. 适当放权。你现在做得太好了，容易把别人的活也干了。试着分出去一点。相信别人即使只做到80分，天也不会塌下来。
2. 优化流程。利用你敏锐的细节观察力，去优化工作流程，而不仅仅是埋头苦干。从“把事做完”进阶到“把做事的方法变简单”。
3. 预留弹性空间。在你的日程表里，故意留出10%的空白时间，什么都不排。这是给突发情况的缓冲，也是给你自己的奖励。
"""
        }
    },

    "ISFJ": {
        "crisis": {
            "title": "全面过载：情绪与秩序的双重崩塌",
            "text": """
【深度分析】
你感觉生活失控了。一方面，你对过去的人和事充满了怨恨，觉得自己的付出喂了狗（Loop）；另一方面，你对未来充满了灾难性的想象，一点风吹草动都能让你崩溃（Grip）。你想躲起来，但又怕躲起来后一切全完了。

【为什么会这样】
你一直在透支。Fe（情感）透支了你去照顾别人，Si（经验）透支了你去维持现状。现在它们都枯竭了。冷酷的 Ti（逻辑）和混乱的 Ne（直觉）接管了大脑，让你变得既刻薄又惊慌。

【未来30天怎么过】
1. 第1-3天：切断求助通道。把手机调成勿扰，或者直接告诉大家“我这几天有事”。停止做任何人的“垃圾桶”或“保姆”。你现在的电量只够维持自己的呼吸。
2. 第4-10天：机械性劳动。去做那些不需要动脑、但有明确结果的事：比如十字绣、拼图、深层清洁厨房。这种重复的动作能给你的大脑带来急需的安宁感。
3. 第11-30天：向信得过的人倾诉。不要憋着。找一个嘴严的朋友，把你心里的怨气全说出来。不用讲道理，就说“我好累，我很烦”。说出来，毒就排了一半。
"""
        },
        "grip": {
            "title": "直面恐惧：别自己吓自己",
            "text": """
【深度分析】
你最近变得神经质。可能丈夫晚回来半小时，你就脑补出车祸现场；可能老板皱个眉，你就觉得自己要被开除了。你被无数个恐怖的“万一”包围，吃不下饭，睡不着觉。

【为什么会这样】
这是劣势功能 Ne 的恶作剧。你习惯了安稳，对不可控的未知非常抗拒。压力大时，这种抗拒变成了恐惧，大脑自动生成最坏的剧本。

【未来30天怎么过】
1. 第一周：回到当下。恐惧源于未来，平静源于当下。当你害怕时，立刻去做一件具体的事：数数窗外有几棵树，摸摸衣服的面料。强制把意识拉回此时此刻。
2. 第二周：整理旧物。翻翻老照片，整理以前的日记。这些确定的、温暖的过去记忆（Si），是你对抗未知恐惧的最强盾牌。
3. 后半月：验证猜想。如果你怕老板开除你，就去问问他对你最近工作的评价。你会发现现实往往比你脑补的要温和得多。
"""
        },
        "loop": {
            "title": "解开心结：停止内耗",
            "text": """
【深度分析】
你表面上可能还在笑，但心里已经把某些人拉黑了。你反复琢磨他们以前说的一句话、做的一个动作，分析他们是不是在针对你。你变得冷漠、记仇，觉得谁都靠不住。

【为什么会这样】
这是 Si-Ti 死循环。你切断了与人的真实连接（Fe），躲在角落里用片面的逻辑（Ti）去审判回忆（Si）。越想越觉得只有自己是受害者。

【未来30天怎么过】
1. 第一周：直接表达需求。你现在的怨气多半是因为别人没按你的预期做。别让人猜。直接说：“我很累，能不能帮我把垃圾倒了？”只要说出口，你就不会那么委屈了。
2. 第二周：主动社交。不是那种应酬，而是找能让你放松的人。哪怕只是和邻居聊两句天气。重新启动 Fe，你会发现大家其实没那么坏。
3. 后半月：换个发型或衣服。改变一下外在形象。这点小小的改变能打破你内部的僵化状态，给你一种“重新开始”的暗示。
"""
        },
        "growth": {
            "title": "平衡之道：先爱自己",
            "text": """
【深度分析】
你现在是全场最温暖的存在。你能敏锐地察觉到谁不开心，也能迅速把混乱的局面收拾妥当。你有原则，也有爱心。大家都很依赖你，而你也乐在其中。

【为什么会这样】
Si 让你做事靠谱，Fe 让你待人温暖。Ti 帮你理清了边界，Ne 让你对新事物保持了适度的开放。这是 ISFJ 最健康的状态。

【未来30天怎么过】
1. 建立边界。越是这种时候，越要学会说不。对于那些只会索取不懂回报的人，温和但坚定地拒绝。把能量留给值得的人。
2. 自我奖励。这周给自己买个礼物，或者去吃顿好的。不要理由，仅仅因为你想。你要习惯“对自己好”这件事。
3. 记录美好。每天记下三件让你感到温暖的小事。这会成为你未来的精神储备，在下一个低谷期支撑你。
"""
        }
    },

    "ESTJ": {
        "crisis": {
            "title": "刹车检修：避免引擎爆缸",
            "text": """
【深度分析】
你现在像个随时会炸的高压锅。工作中，你疯狂地微管理，甚至想替每个人把活干了（Loop）；情感上，你觉得自己孤独无助，觉得全世界都背叛了你，甚至会在没人的时候痛哭（Grip）。你极其暴躁，又极其脆弱。

【为什么会这样】
你一直用 Te（强力执行）来压制一切，现在压不住了。Ne（多疑）让你看到了无数漏洞，Fi（情感）让你感受到了深深的委屈。你试图用更疯狂的工作来掩盖情绪，但这只会让你崩溃得更快。

【未来30天怎么过】
1. 第1-3天：强制撤离。离开你的工作岗位，哪怕只有两天。如果继续待在那里，你一定会骂人或者做出错误的开除决定。去个空旷的地方，吼两嗓子，或者剧烈运动。把火气发泄出去。
2. 第4-10天：承认情绪。找个跟工作无关的朋友，或者心理咨询师。承认你受伤了，承认你也会感到无助。对于 ESTJ 来说，承认软弱是最大的勇敢，也是治愈的开始。
3. 第11-30天：被动执行。回到工作后，强迫自己只做配角。只听汇报，不给具体指令。让团队自己去转。你会发现，离了你，地球照样转，而且可能转得还不错。
"""
        },
        "grip": {
            "title": "情绪疏导：拥抱内在小孩",
            "text": """
【深度分析】
那个铁面无私的你不见了。你突然变得非常敏感，觉得别人看你的眼神不对，觉得大家都不尊重你。你感到一种难以名状的悲伤，觉得自己奋斗了半天全是空的。

【为什么会这样】
这是劣势功能 Fi 的爆发。你长期像机器一样运转，忽略了自己的情感需求。现在机器过热了，情感像蒸汽一样喷涌而出。

【未来30天怎么过】
1. 第一周：独处疗伤。不要在这个状态下做决策，肯定情绪化。每天留一小时给自己，听听歌，看看电影。允许自己不做任何“有用”的事。
2. 第二周：写下感受。不要写工作日志，写心情。把你的委屈、愤怒、迷茫都写下来。看着纸上的字，你的理性（Te）会慢慢回来处理它们。
3. 后半月：寻找非功利爱好。去养花，去画画，去玩乐高。做一些没有KPI、没有输赢的事。这能滋养你干枯的内心。
"""
        },
        "loop": {
            "title": "停止空转：把效率降下来",
            "text": """
【深度分析】
你觉得自己忙得要死，但仔细一看，其实是在瞎忙。你为了防范那些根本没发生的“意外”，制定了繁琐到变态的规则。你把周围人折腾得半死，项目进度却反而慢了。

【为什么会这样】
这是 Te-Ne 死循环。你只顾着执行（Te）和想象潜在风险（Ne），忘了回顾过去的经验（Si）。你像个没头苍蝇一样乱撞。

【未来30天怎么过】
1. 第一周：坐下喝茶。当你急得想跳脚时，强迫自己坐下，喝杯茶，深呼吸5分钟。问自己：“这件事真的十万火急吗？”通常不是。
2. 第二周：复盘旧案。遇到问题，别想新招。去翻以前的档案，问问老员工以前是怎么解决的。用 Si 的稳重来压制 Ne 的浮躁。
3. 后半月：删减流程。检查你制定的规则，砍掉那些为了“万一”而设立的繁琐步骤。回归简单，回归常识。
"""
        },
        "growth": {
            "title": "卓越管理：刚柔并济",
            "text": """
【深度分析】
你现在是天生的指挥官。你的指令清晰明确，且合情合理。你不仅能搞定事情，还能照顾到团队的士气。大家愿意跟着你干，因为你既强大又公平。

【为什么会这样】
Te 让你高效，Si 让你稳重，Ne 让你能看到创新点，Fi 让你有了人情味。四种功能各司其职，你就是那个把控全场的定海神针。

【未来30天怎么过】
1. 倾听反面意见。利用你现在的自信，去听听那些刺耳的声音。往往最好的改进建议就藏在反对意见里。
2. 关注他人成长。不要只盯着KPI。花点时间指导下属，教他们方法。培养出能独当一面的人，才是最高级的管理。
3. 享受成果。别光顾着赶路。项目完成了，带大家去庆祝一下。也给自己买个好东西。学会享受胜利，你才会有动力去打下一场仗。
"""
        }
    },

    "ESFJ": {
        "crisis": {
            "title": "社交隔离：情感排毒",
            "text": """
【深度分析】
你现在极度痛苦。一方面，你拼命想讨好所有人，生怕被抛弃（Loop）；另一方面，你心里恨透了这群“白眼狼”，觉得他们都在利用你（Grip）。你在极度的卑微和极度的愤怒之间撕扯，整个人都要碎了。

【为什么会这样】
你的 Fe（情感）因为过度透支而枯竭，Ti（逻辑）因为长期压抑而黑化。你失去了自我，完全活在别人的眼光里。你试图用更用力的讨好来换取认可，得到的却是轻视，这让你彻底崩盘。

【未来30天怎么过】
1. 第1-3天：物理失联。这是救命的一步。关掉朋友圈，退掉那些吵闹的群。告诉家人你要休息。把注意力从别人身上硬生生扯回来。
2. 第4-10天：逻辑梳理。拿张纸，把你对每个人的付出和回报列出来。启动 Ti 的计算功能。你会发现，有些关系早就该断了。看着冷冰冰的数字，你的心会硬起来。
3. 第11-30天：建立新规矩。重新出现在社交圈时，立个新规矩：比如“我不借钱”或“我不帮人带孩子”。守住这个规矩。你会发现，真正尊重你的朋友反而更看重你了。
"""
        },
        "grip": {
            "title": "停止批判：简单生活",
            "text": """
【深度分析】
那个热心肠的你不见了。你突然变得冷若冰霜，看谁都不顺眼。你揪住别人的话柄不放，用最刻薄的语言攻击他们。你觉得人性本恶，觉得一切关系都是虚伪的交易。

【为什么会这样】
这是劣势功能 Ti 的反噬。当你的好意长期被忽视时，你体内的逻辑功能跳出来保护你，但它是个生手，所以表现得非常极端和愤世嫉俗。

【未来30天怎么过】
1. 第一周：停止分析。别想“他为什么这么做”，越想越黑暗。去干活。去把家里里里外外打扫一遍。用身体的劳累来停止大脑的黑化。
2. 第二周：和小动物相处。人太复杂了，去和狗玩，去喂流浪猫。动物的反应是直接的、真实的。它们能治愈你对关系的失望。
3. 后半月：看点治愈系。看那种简单的、美好的电影或书。你需要重新确认：虽然世界上有坏人，但美好依然存在。
"""
        },
        "loop": {
            "title": "自我回归：不再讨好",
            "text": """
【深度分析】
你变得像个焦虑的雷达。时刻扫描周围人的情绪，谁皱个眉你都要紧张半天。你到处打听消息，生怕自己被排挤。你为了合群，说着言不由衷的话，活得像个面具人。

【为什么会这样】
这是 Fe-Ne 死循环。你完全活在外部世界（Fe+Ne），切断了内部的稳定经验（Si）。你像浮萍一样随波逐流。

【未来30天怎么过】
1. 第一周：断网保平安。下班后关机。不看谁给你点赞了，不看群消息。刚开始你会恐慌，觉得错过了全世界。坚持住，三天后你会感到前所未有的清净。
2. 第二周：照顾身体。问自己：我现在冷吗？饿吗？累吗？把关注点放在自己的身体感受上。给自己做顿饭，好好泡个澡。把爱分给自己一点。
3. 后半月：做个“坏人”。试着拒绝一次别人的请求。就一次。比如“不行，我今天没空”。说完别解释。你会发现，天没塌，你也没被拉黑。
"""
        },
        "growth": {
            "title": "和谐中心：自信发光",
            "text": """
【深度分析】
你是人群中的核心。你不仅能把大家照顾得很好，还能把事情安排得井井有条。大家跟你在一起很舒服，也很信服你。你既有亲和力，又有掌控力。

【为什么会这样】
Fe 让你连接他人，Si 让你做事靠谱，Ne 让你有趣，Ti 帮你守住底线。四种功能平衡运作，你就是最棒的组织者。

【未来30天怎么过】
1. 组织一次聚会。利用你的天赋，组个局。看着大家开心的样子，你会获得巨大的能量。
2. 分清主次。在帮助别人的同时，别忘了自己的核心目标。先把自己的工作做完，再去帮别人。
3. 接受赞美。当别人夸你时，不要谦虚地说“哪里哪里”，大大方方地说“谢谢”。你值得这些赞美。
"""
        }
    },

    "ISTP": {
        "crisis": {
            "title": "死机重启：物理暴力破解",
            "text": """
【深度分析】
你现在处于一种极其危险的“自毁”模式。一方面，你觉得一切都毫无意义，整天把自己关在房间里发呆（Loop）；另一方面，你的情绪处于爆发边缘，一点小事（比如网卡了一下）就能让你砸键盘，或者觉得全世界都在针对你（Grip）。你既冷漠又狂暴。

【为什么会这样】
Ti-Ni 死循环让你脱离了现实，陷入了虚无主义的黑洞。而劣势功能 Fe（情感）在压力下彻底失控，让你变得像个甚至有点歇斯底里的孩子。你的逻辑系统已经烧坏了，语言系统也下线了。

【未来30天怎么过】
1. 第1-3天：高强度消耗。别讲道理，别思考。去跑个五公里，去打拳，去游泳。你需要把体内那股想毁掉点什么的能量，通过肌肉释放出去。把自己累到倒头就睡，是最好的镇静剂。
2. 第4-10天：单一任务模式。找一件需要动手但不费脑子的事：拼高达、修自行车、给键盘换轴。只要你的手在动，你的脑子就会慢慢冷却下来。此时禁止处理任何复杂的人际关系。
3. 第11-30天：回归感官。去吃点极辣的东西，或者去洗冷水澡。强烈的感官刺激能把你从那个“一切都没意义”的虚无世界里拽出来。哪怕是痛感，也比麻木强。
"""
        },
        "grip": {
            "title": "情绪宣泄：允许自己发疯",
            "text": """
【深度分析】
平时那个酷酷的、话不多的你不见了。你突然变得特别敏感，觉得朋友不尊重你，觉得老板在给你穿小鞋。你甚至会莫名其妙地流眼泪，或者在大街上突然大吼大叫。你觉得自己失控了，很丢人。

【为什么会这样】
这是劣势功能 Fe 的爆发。你平时压抑了太多的情绪，把它们锁在地下室。现在地下室炸了。你处理不了这种复杂的情感洪流，所以表现得非常极端。

【未来30天怎么过】
1. 第一周：物理隔离。当你觉得想发火时，立刻离开现场。躲进厕所，或者带上降噪耳机。切断外部的噪音来源。你需要绝对的安静来平复心跳。
2. 第二周：非语言发泄。别试图用嘴解释你的感受，你会越描越黑。去打沙袋，去撕废纸，去吼歌。用身体把情绪排出去。
3. 后半月：简单社交。找个话少、靠谱的朋友，一起打个球或者喝杯酒。不要聊心事，就是单纯地待在一起。这种低压力的陪伴能治愈你的孤独感。
"""
        },
        "loop": {
            "title": "打破瘫痪：手比脑快",
            "text": """
【深度分析】
你什么都不想干。你躺在床上，脑子里构思了无数个计划，或者分析了无数个阴谋论，但手指头都懒得动一下。你觉得“反正做了也没用”，陷入了一种逻辑上的瘫痪。

【为什么会这样】
这是 Ti-Ni 死循环。你切断了辅助功能 Se（外向感觉），也就是切断了与真实世界的接触。你活在纯粹的理论推演里，而没有现实数据来校准，导致越想越悲观。

【未来30天怎么过】
1. 第一周：强制出门。别管去哪，先穿鞋出门。哪怕只是去楼下便利店买瓶水。只要你走在街上，看到真实的人和车，你的 Se 就会自动激活。
2. 第二周：解决一个小麻烦。修好家里那个滴水的水龙头，或者把乱成一团的线理好。这种具体的、即时的正反馈，能瞬间打破你的虚无感。
3. 后半月：学习新技能。学个滑板，学个攀岩。让身体去学习，而不是让脑子去学习。当你的身体在应对挑战时，你就没空想那些有的没的了。
"""
        },
        "growth": {
            "title": "全能工匠：自由流动",
            "text": """
【深度分析】
现在的你，像水一样灵活，像刀一样锋利。你逻辑清晰（Ti），反应敏捷（Se），直觉准确（Ni）。遇到任何问题，你都能迅速找到最优解。你享受当下，既自由又强大。

【为什么会这样】
你成功整合了思考与行动。不再纠结意义，而是专注于解决问题。这是 ISTP 最迷人的状态：冷静的操盘手。

【未来30天怎么过】
1. 挑战高难度。现在的你处理日常事务是大材小用。去接那个最难的项目，去玩那个最难的游戏。你需要压力来保持兴奋。
2. 优化工具。看看你手头的工具（电脑、软件、器械），有没有可以升级或优化的地方？工欲善其事，必先利其器。
3. 记录灵感。你的 Ni 偶尔会给你一些天才的直觉。别忽略它，记下来。这可能就是你下一个大动作的起点。
"""
        }
    },

    "ISFP": {
        "crisis": {
            "title": "自我放逐：停止内耗",
            "text": """
【深度分析】
你现在觉得自己是个彻底的废物。Loop 让你觉得自己这辈子一事无成，只能是个受害者；Grip 让你变得暴躁、刻薄，看谁都不顺眼，甚至想把所有东西都扔了。你想消失，想躲到一个没人能找到你的洞里。

【为什么会这样】
Fi（情感）让你陷入自我攻击，Ni（直觉）让你看不到未来，Te（逻辑）让你试图用粗暴的控制来掩盖恐慌。你把所有门窗都关死了，自己在里面窒息。

【未来30天怎么过】
1. 第1-3天：感官急救。吃你最爱吃的东西，不管热量。睡最软的枕头。听最喜欢的歌。你需要用极度的舒适感来包裹那个受伤的自己。
2. 第4-10天：创作疗愈。别管好不好看，去画画，去涂鸦，去把旧衣服剪了改着玩。ISFP 的语言不是文字，是色彩和形状。把心里的毒素通过手流出来。
3. 第11-30天：走进自然。去公园，去海边。不是去运动，是去发呆。看看云怎么飘，看看树叶怎么动。大自然无声的陪伴最能安抚你。
"""
        },
        "grip": {
            "title": "卸下铠甲：承认做不到",
            "text": """
【深度分析】
那个随性温柔的你不见了。你突然变成了暴君。嫌弃别人干活慢，嫌弃家里乱。你列了一堆计划表，逼自己像机器一样执行，完不成就发火。你变得冷酷、无情。

【为什么会这样】
这是劣势功能 Te 的爆发。因为内心太不安，你试图通过控制外部世界来寻找安全感。但这种强撑出来的效率，只会让你更累。

【未来30天怎么过】
1. 第一周：撕掉计划。承认吧，你根本做不到按表操课。把那些待办事项全删了。今天只想做一件事？那就只做这一件。其他的爱谁谁。
2. 第二周：直接躺平。当你觉得想骂人的时候，直接躺在地上（或者沙发上）。告诉自己：“我不管了。”一旦你放弃控制，那种紧绷感瞬间就没了。
3. 后半月：做无用的事。去吹泡泡，去观察蚂蚁搬家。做那些在别人眼里浪费时间、但在你眼里很有趣的事。找回你的松弛感。
"""
        },
        "loop": {
            "title": "走出幻觉：拥抱真实",
            "text": """
【深度分析】
你觉得自己被全世界针对了。别人一个眼神，你就能脑补出一场大戏，觉得他在嘲笑你。你把自己关起来，甚至开始讨厌以前喜欢的爱好。你沉浸在“我很惨”的剧本里出不来。

【为什么会这样】
这是 Fi-Ni 死循环。你用主观感受（Fi）去验证消极的直觉（Ni），完全切断了与真实世界（Se）的核对。你活在自己的噩梦里。

【未来30天怎么过】
1. 第一周：出门晒太阳。字面意思，去晒太阳。Se 需要光和热的刺激。只要身体暖和了，心里的阴霾就会散一点。
2. 第二周：去逛街。去摸摸衣服的料子，闻闻香水的味道。看看真实的世界是什么样的。你会发现，现实其实挺热闹的，没人有空专门针对你。
3. 后半月：做个小作品。拍一张好看的照片，修好了发出来。当你的审美被现实具象化，并收到别人的点赞时，你的自信就回来了。
"""
        },
        "growth": {
            "title": "自由灵魂：美的创造者",
            "text": """
【深度分析】
你现在的状态美极了。你活在当下，对美有极高的敏感度。你忠于自我，不在乎世俗的眼光。你像一只自由的鸟，飞到哪就把美带到哪。

【为什么会这样】
Fi 让你有内核，Se 让你有感知，Ni 让你有灵气，Te 让你能把想法落地。你是天生的艺术家。

【未来30天怎么过】
1. 大胆表达。别藏着掖着。把你独特的穿搭穿出去，把你独特的观点说出来。现在的你非常有感染力。
2. 体验新奇。去尝试一个你没玩过的艺术形式（比如陶艺、染布）。新鲜的体验会给你的灵感库（Se）不断加料。
3. 记录生活。用视频或照片记录下你眼中的世界。你的视角是独特的，这些记录将来都是宝藏。
"""
        }
    },

    "ESTP": {
        "crisis": {
            "title": "悬崖勒马：危险信号",
            "text": """
【深度分析】
你正在失控。为了掩饰内心的恐惧，你可能会做极其危险的事：飙车、豪赌、或者挑起激烈的冲突（Loop）。但当你一个人的时候，你又怕得要死，迷信各种征兆，觉得大难临头（Grip）。你在用外表的疯狂来掩饰内核的崩塌。

【为什么会这样】
Se（感官）过载让你追求极端刺激，Fe（情感）让你死要面子撑着，Ni（直觉）作为劣势功能在疯狂制造恐怖片。你就像一辆油门踩死、刹车失灵的赛车。

【未来30天怎么过】
1. 第1-3天：找人看住你。这绝不是开玩笑。把你所有能动用的资金锁起来。把车钥匙交给朋友。告诉你在乎的人：“我最近容易冲动，帮我踩着点刹车。”你需要外部强制力。
2. 第4-10天：物理消耗。去健身房，举那种把你压得喘不过气的大重量。或者去爬山，爬到累瘫。你需要用极致的肉体痛苦，来压制精神上的躁动。
3. 第11-30天：做确定的事。不要投资，不要冒险。去做那些投入一分就有一分回报的事（比如搬砖、打扫卫生、整理数据）。用确定性来安抚 Ni 的恐惧。
"""
        },
        "grip": {
            "title": "破除迷信：相信数据",
            "text": """
【深度分析】
那个天不怕地不怕的你，突然怂了。你开始变得神神叨叨，信星座、信算命、信各种不好的预兆。你不敢做决定，生怕选错了就万劫不复。你变得疑神疑鬼，觉得谁都不可信。

【为什么会这样】
这是劣势功能 Ni 的反噬。你平时只看眼前，忽略未来。现在未来来找你算账了，你没有应对经验，所以把它妖魔化了。

【未来30天怎么过】
1. 第一周：禁止瞎想。每当你想“未来会怎样”的时候，给自己一个耳光（轻拍）。告诉自己：我想象的都是假的。
2. 第二周：看数据。如果你担心生病，去体检看报告。如果你担心没钱，去查账单。用辅助功能 Ti（逻辑）去分析冷冰冰的事实。数据不会骗人，也不会吓人。
3. 后半月：做短期计划。别想五年后。只想明天干什么。把时间颗粒度缩短到“天”。只要你能搞定明天，未来就搞得定。
"""
        },
        "loop": {
            "title": "低调潜行：闭嘴干活",
            "text": """
【深度分析】
你太想红了，太想证明自己了。你到处吹牛，许下做不到的承诺。你甚至会去欺负弱小来显摆自己的强大。你看起来很风光，其实心里发虚，因为你知道自己只是个空壳子。

【为什么会这样】
这是 Se-Fe 死循环。你完全活在别人的眼光里（Fe），追求表面的浮夸（Se），丢掉了内在的逻辑判断（Ti）。你变成了流量的奴隶。

【未来30天怎么过】
1. 第一周：朋友圈停更。消失一周。不发任何动态。看看没了那些点赞，你还活不活得下去。忍受这种被遗忘的冷清。
2. 第二周：独立作业。找一件不需要跟人合作的事，自己一个人把它做完。修好一辆车，或者写完一份报告。用结果来证明能力，而不是用嘴。
3. 后半月：复盘逻辑。问自己：我做这件事是为了爽，还是真的有价值？启动 Ti 的批判性思维，把那些华而不实的项目砍掉。
"""
        },
        "growth": {
            "title": "破局专家：实干家",
            "text": """
【深度分析】
现在的你，简直是无敌的。你反应极快，能瞬间看透局势（Se），并迅速找到解决办法（Ti）。你有魅力（Fe），也有直觉（Ni）。你是天生的创业者和救火队员。

【为什么会这样】
你把对现实的敏锐感知和理性的逻辑分析完美结合了。你不空想，你只实干。

【未来30天怎么过】
1. 解决大麻烦。去接手那个别人都搞不定的烂摊子。混乱是你的阶梯。你现在的状态最适合乱中取胜。
2. 带带新人。利用你的 Fe，把你的经验教给别人。不要只会自己干，学会带着一帮人干。这能放大你的价值。
3. 深思一步。在行动前，多花5分钟想想：这事做成了以后呢？稍微调用一下 Ni，你的成功会更持久。
"""
        }
    },

    "ESFP": {
        "crisis": {
            "title": "停机维护：远离喧嚣",
            "text": """
【深度分析】
你现在是崩溃的。你在外面疯狂社交、大笑、搞怪，不想停下来（Loop），但一转身就想哭，觉得人生一片黑暗，充满了阴谋和绝望（Grip）。你用最热闹的面具，掩盖最破碎的心。

【为什么会这样】
你一直在用 Se（感官刺激）麻痹自己，忽略了 Fi（内心感受）。现在 Ni（阴暗直觉）作为劣势功能出来清算，让你觉得未来毫无希望。你透支了所有的快乐额度。

【未来30天怎么过】
1. 第1-3天：回家。推掉所有局，不管多重要。回到父母家，或者自己最安全的窝。关机。洗个热水澡，换上睡衣。你需要回到最原始、最安全的状态。
2. 第4-10天：只吃不聊。哪怕约朋友，也只约那种能陪你安安静静吃饭的。不要聊八卦，不要聊工作。就是吃饭。感受食物的味道。把注意力收回到感官享受本身。
3. 第11-30天：听悲伤的歌。不要强颜欢笑了。去听那种很丧的歌，看很虐的电影。哭出来。让 Fi 的悲伤流淌出来，别憋着。哭累了，你就好了。
"""
        },
        "grip": {
            "title": "驱散阴霾：动起来",
            "text": """
【深度分析】
那个乐天派不见了。你变得很丧，甚至有点抑郁。你觉得身边的人都在骗你，觉得这辈子就这样了，没救了。你把自己关在屋里，哪里也不想去。

【为什么会这样】
这是劣势功能 Ni 的爆发。你平时只看当下，现在突然被迫看未来，所以看到的都是灾难。你陷入了从未有过的精神内耗。

【未来30天怎么过】
1. 第一周：别照镜子。别盯着自己看，越看越觉得自己糟糕。出门，去人多的地方。去超市，去夜市。烟火气是你最好的抗抑郁药。
2. 第二周：K歌。或者跳舞。去这种能大声宣泄的地方。把身体里的郁闷通过声音和汗水排出去。ESFP 的治愈必须是动态的。
3. 后半月：约最好的朋友。告诉他你很难过。不要让他劝你，让他带你去玩。只要玩起来，你就活过来了。
"""
        },
        "loop": {
            "title": "寻找重心：停止表演",
            "text": """
【深度分析】
你停不下来。必须每时每刻都有事做，有人陪。你甚至变得有点霸道，强行安排别人的生活。你买了一堆不需要的东西，吃了一堆不需要的饭。你在填补空虚，但越填越空。

【为什么会这样】
这是 Se-Te 死循环。你只顾着追求外部刺激（Se）和控制（Te），切断了内心真实的感受（Fi）。你把自己变成了一个只会享乐的空心人。

【未来30天怎么过】
1. 第一周：没收钱包。限制自己的消费。当你不能通过买买买来获得快感时，你不得不面对内心的无聊。
2. 第二周：独处一小时。每天试着一个人待一小时。不看手机。刚开始你会抓狂。坚持住。问自己：“我到底喜欢什么？不是别人喜欢的，是我喜欢的。”
3. 后半月：做件无利可图的事。去当义工，或者帮邻居遛狗。做一件没有回报、没有掌声的事。找回你内心那个纯粹善良的 Fi。
"""
        },
        "growth": {
            "title": "超级明星：传递快乐",
            "text": """
【深度分析】
你现在的状态太棒了。你是所有人的开心果。你真诚、热情、大方。你不仅自己玩得开心，还能把快乐传染给每一个人。你活在当下，闪闪发光。

【为什么会这样】
Se 让你敏锐地感知世界，Fi 让你真诚待人，Te 帮你把聚会安排得妥妥当当。你是天生的明星。

【未来30天怎么过】
1. 存点钱。趁着状态好，理智尚存，赶紧存点钱。给未来的自己留点后路。
2. 带动大家。利用你的感染力，组织大家做点有意义的事（比如慈善义卖，或者集体运动）。你的能量可以用来做更大的事。
3. 享受当下。继续保持。不要担心未来。你最大的天赋就是把今天过好。只要过好每一个今天，未来自然会好。
"""
        }
    }

}

# ==========================================
# 3. Pydantic 模型
# ==========================================

class QuestionItem(BaseModel):
    id: int
    text: str


class SubmitRequest(BaseModel):
    mbti: str
    answers: Dict[str, int]


class AnalysisResult(BaseModel):
    maturity: int
    loop: int
    grip: int
    load: int
    coherence: int
    overall: int
    insight: str
    advice: str
    pill_text: str
    chart_data: List[int]
    month_title: str
    month_text: str


# ==========================================
# 4. 辅助函数
# ==========================================

def calculate_coherence(values: List[int]) -> int:
    """计算自洽度：基于标准差"""
    if not values:
        return 0
    if len(values) < 2:
        return 100
    stdev = statistics.pstdev(values)
    # 2.5 是 1-6 量表下的经验上限
    score = (1 - min(1, stdev / 2.5)) * 100
    return int(round(score))


def normalize(score: int, min_val: int, max_val: int) -> int:
    if max_val == min_val:
        return 0
    val = (score - min_val) / (max_val - min_val)
    return int(round(min(1, max(0, val)) * 100))


# ==========================================
# 5. API 接口
# ==========================================

@app.get("/api/questions/{mbti_type}", response_model=List[QuestionItem])
def get_questions(mbti_type: str):
    mbti = mbti_type.upper()
    if mbti not in MBTI_BANK:
        # 如果没有该类型题库，返回默认或报错
        if "INTP" in MBTI_BANK:
            questions = MBTI_BANK["INTP"]
        else:
            raise HTTPException(status_code=404, detail="MBTI type not found")
    else:
        questions = MBTI_BANK[mbti]

    # 随机打乱题目顺序
    shuffled = random.sample(questions, len(questions))

    return [QuestionItem(id=q["id"], text=q["text"]) for q in shuffled]


@app.post("/api/submit", response_model=AnalysisResult)
def submit_answers(req: SubmitRequest):
    mbti = req.mbti.upper()
    if mbti not in MBTI_BANK:
        raise HTTPException(status_code=400, detail="Invalid MBTI type")

    questions = MBTI_BANK[mbti]
    q_map = {str(q["id"]): q for q in questions}

    scores = {"maturity": 0, "loop": 0, "grip": 0}
    raw_values = []
    cat_values = {"maturity": [], "loop": [], "grip": []}

    cat_counts = {"maturity": 0, "loop": 0, "grip": 0}
    for q in questions:
        cat_counts[q["type"]] += 1

    SCALE_MIN = 1
    SCALE_MAX = 6

    for q_id_str, user_val in req.answers.items():
        if q_id_str not in q_map:
            continue

        q_cfg = q_map[q_id_str]

        final_val = user_val
        if q_cfg["reversed"]:
            final_val = (SCALE_MAX + SCALE_MIN) - user_val

        scores[q_cfg["type"]] += final_val
        raw_values.append(user_val)
        cat_values[q_cfg["type"]].append(final_val)

    def get_norm_score(cat):
        count = cat_counts[cat]
        if count == 0: return 0
        min_possible = count * SCALE_MIN
        max_possible = count * SCALE_MAX
        return normalize(scores[cat], min_possible, max_possible)

    res_m = get_norm_score("maturity")
    res_l = get_norm_score("loop")
    res_g = get_norm_score("grip")

    if raw_values:
        avg_raw = sum(raw_values) / len(raw_values)
        res_load = int(round((avg_raw - SCALE_MIN) / (SCALE_MAX - SCALE_MIN) * 100))
    else:
        res_load = 0

    coh_m = calculate_coherence(cat_values["maturity"])
    coh_l = calculate_coherence(cat_values["loop"])
    coh_g = calculate_coherence(cat_values["grip"])
    res_coh = int(round((coh_m + coh_l + coh_g) / 3))

    res_overall = int(round(
        0.25 * res_m +
        0.20 * res_coh +
        0.20 * (100 - res_l) +
        0.20 * (100 - res_g) +
        0.15 * (100 - res_load)
    ))

    state_key = "mixed"

    # 对应 advice_key 的 "crisis"
    if res_l >= 60 and res_g >= 60:
        state_key = "crisis"
    # 对应 advice_key 的 "grip" (注意这里原本叫 overload)
    elif res_g >= 60:
        state_key = "overload"
    # 对应 advice_key 的 "loop" (注意这里原本叫 highLoop)
    elif res_l >= 60:
        state_key = "highLoop"
    else:
        state_key = "stable"

    # 获取 narrative
    narrative_pack = NARRATIVE_TEMPLATES.get(mbti, DEFAULT_NARRATIVE)
    content = narrative_pack.get(state_key, narrative_pack.get("overload", DEFAULT_NARRATIVE["overload"]))

    # 未来建议
    CRISIS_THRESHOLD = 60  # 两个都高于此值算危机
    HIGH_THRESHOLD = 60  # 单个高于此值算高

    advice_key = "growth"  # 默认为成长

    if res_l >= CRISIS_THRESHOLD and res_g >= CRISIS_THRESHOLD:
        advice_key = "crisis"
    elif res_g >= HIGH_THRESHOLD:
        advice_key = "grip"
    elif res_l >= HIGH_THRESHOLD:
        advice_key = "loop"
    else:
        advice_key = "growth"

    # 获取文案 (如果没有配置该类型，给个默认空对象防止报错)
    type_advice = FUTURE_ADVICE.get(mbti, {
        "crisis": {"title": "建议生成中", "text": "专家正在编写该类型的建议..."},
        "grip": {"title": "建议生成中", "text": "专家正在编写该类型的建议..."},
        "loop": {"title": "建议生成中", "text": "专家正在编写该类型的建议..."},
        "growth": {"title": "建议生成中", "text": "专家正在编写该类型的建议..."}
    })

    final_advice = type_advice[advice_key]

    pill_text = "可用"
    if res_overall >= 75:
        pill_text = "充盈"
    elif res_overall >= 55:
        pill_text = "可用"
    elif res_overall >= 35:
        pill_text = "偏疲"
    else:
        pill_text = "高压"

    return AnalysisResult(
        maturity=res_m,
        loop=res_l,
        grip=res_g,
        load=res_load,
        coherence=res_coh,
        overall=res_overall,
        insight=content["insight"],
        advice=content["advice"],
        month_title=final_advice["title"],
        month_text=final_advice["text"],
        pill_text=pill_text,
        chart_data=[res_m, res_coh, 100 - res_l, 100 - res_g, 100 - res_load, res_overall]
    )