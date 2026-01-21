from __future__ import annotations
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, List
import statistics
import random

app = FastAPI()

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
        {"id": 1, "text": "当现实情况与你的直觉预判不符时，你能灵活调整而不固执己见。", "type": "maturity",
         "reversed": False},
        {"id": 2, "text": "你经常活在未来的愿景里，而忽略了当下的生活琐事和身体照顾。", "type": "maturity",
         "reversed": True},
        {"id": 3, "text": "你能在坚持自我价值观的同时，用他人能接受的方式温和地表达。", "type": "maturity",
         "reversed": False},
        {"id": 4, "text": "你总觉得自己的洞察力“高人一等”，很难真正听取他人的建议。", "type": "maturity",
         "reversed": True},
        {"id": 5, "text": "因为过度追求完美的时机或方案，你的很多理想从未开始执行。", "type": "maturity",
         "reversed": True},
        {"id": 6, "text": "你能将复杂的抽象直觉，转化为具体可行的步骤去帮助他人。", "type": "maturity",
         "reversed": False},
        {"id": 7, "text": "一旦认定了某件事的意义，你就会忽略客观现实的阻碍强行推进。", "type": "maturity",
         "reversed": True},
        {"id": 8, "text": "你不仅能共情他人的痛苦，还能设立健康的边界保护自己的能量。", "type": "maturity",
         "reversed": False},
        {"id": 9, "text": "你习惯甚至享受一种“曲高和寡”的孤独感，而拒绝融入群体。", "type": "maturity", "reversed": True},
        {"id": 10, "text": "你会主动通过实际行动来验证你的直觉，而不仅仅是在脑中推演。", "type": "maturity",
         "reversed": False},
        {"id": 11, "text": "最近你把自己封闭起来，觉得社交纯粹是在浪费时间。", "type": "loop", "reversed": False},
        {"id": 12, "text": "你会像手术刀一样冷酷地剖析身边人的动机，觉得他们都很虚伪。", "type": "loop",
         "reversed": False},
        {"id": 13, "text": "你陷入一种逻辑死循环，试图在脑中构建一个无懈可击的真理。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你变得非常批判和挑剔，对他人的情感表达感到不耐烦。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你觉得自己彻底“看透”了某些事情的悲剧结局，因此拒绝任何尝试。", "type": "loop",
         "reversed": False},
        {"id": 16, "text": "你拒绝向外求助，坚信只有自己才能解决自己的问题。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你脑中有大量的分析和批判，但在外人看来你只是在发呆或沉默。", "type": "loop",
         "reversed": False},
        {"id": 18, "text": "你对外部世界感到一种虚无感，觉得一切都没有意义。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你会为了证明自己的逻辑正确，而忽略在这个过程中对他人的伤害。", "type": "loop",
         "reversed": False},
        {"id": 20, "text": "你固执地坚持自己的主观判断，即使客观事实摆在眼前也不愿承认。", "type": "loop",
         "reversed": False},
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
    "INTJ": [
        {"id": 1, "text": "你不仅有宏大的愿景，还能制定出严密可行的执行步骤。", "type": "maturity", "reversed": False},
        {"id": 2, "text": "当客观数据与你的直觉相悖时，你会认为是数据错了，拒绝修正观点。", "type": "maturity",
         "reversed": True},
        {"id": 3, "text": "你能够接受“足够好”的方案并推进，而不是为了追求完美而停滞不前。", "type": "maturity",
         "reversed": False},
        {"id": 4, "text": "你经常因为觉得别人的执行力太差或太蠢，而拒绝与任何人合作。", "type": "maturity",
         "reversed": True},
        {"id": 5, "text": "你为了维护自己的理论模型，会有意无意地忽略那些反面证据。", "type": "maturity",
         "reversed": True},
        {"id": 6, "text": "你愿意为了达成目标而妥协部分细节，注重结果的有效性。", "type": "maturity", "reversed": False},
        {"id": 7, "text": "你总是活在未来，导致当下的生活一团糟，甚至无法照顾好自己。", "type": "maturity",
         "reversed": True},
        {"id": 8, "text": "你能够用客观、逻辑的语言向他人解释你的直觉，而不是让他们“只管照做”。", "type": "maturity",
         "reversed": False},
        {"id": 9, "text": "你内心深处有一种智力优越感，很难真正听取他人的建议。", "type": "maturity", "reversed": True},
        {"id": 10, "text": "你会主动设立一个个里程碑，通过阶段性成果来验证你的远见。", "type": "maturity",
         "reversed": False},
        {"id": 11, "text": "最近你觉得周围的人都不可信，甚至觉得他们在暗中针对你。", "type": "loop", "reversed": False},
        {"id": 12, "text": "你沉浸在一种“没有人能理解我”的悲剧英雄感中，并拒绝沟通。", "type": "loop", "reversed": False},
        {"id": 13, "text": "你会反复咀嚼过去被背叛或被误解的经历，感到愤愤不平。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你变得非常情绪化和敏感，这与平时那个理性的你判若两人。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你仅仅依据个人的好恶（而非客观事实）就对他人的动机进行道德审判。", "type": "loop",
         "reversed": False},
        {"id": 16, "text": "你完全切断了与外部世界的互动，活在自己的精神堡垒里。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你觉得自己也是为了大家好，但为什么总是被辜负？", "type": "loop", "reversed": False},
        {"id": 18, "text": "你对未来充满了灾难化的想象，并且深信这些坏结果一定会发生。", "type": "loop",
         "reversed": False},
        {"id": 19, "text": "你拒绝接受任何客观解释，固执地相信自己的主观感受才是真理。", "type": "loop",
         "reversed": False},
        {"id": 20, "text": "你在没有任何证据的情况下，就已经在心里给某件事判了死刑。", "type": "loop", "reversed": False},
        {"id": 21, "text": "压力极大时，你会突然开始暴饮暴食、酗酒或沉迷于肉体享乐。", "type": "grip", "reversed": False},
        {"id": 22, "text": "你会因为一点点噪音、强光或环境混乱而变得暴怒。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你会突然痴迷于清洁、整理或某些无关紧要的物理细节。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你会产生一种强烈的冲动，想要把眼前的东西砸烂或毁掉。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你会进行报复性的冲动消费，买一堆完全没用的东西。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你感觉大脑停止了思考，完全被当下的感官欲望所控制。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你会突然做一些高风险、鲁莽的身体活动（如飙车、极限运动）。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你对自己的外表或身体状况突然产生极度的焦虑或强迫性关注。", "type": "grip",
         "reversed": False},
        {"id": 29, "text": "你觉得自己像是在和整个物理世界作战，所有东西都在和你作对。", "type": "grip",
         "reversed": False},
        {"id": 30, "text": "你通过过度的机械性劳动（如一直做家务）来逃避思考。", "type": "grip", "reversed": False}
    ],
    "ENTJ": [
        {"id": 1, "text": "你不仅追求当下的胜利，更在意这个胜利是否符合长期的战略蓝图。", "type": "maturity",
         "reversed": False},
        {"id": 2, "text": "你经常打断别人的发言，认为他们的想法太蠢或太慢，完全不值得听。", "type": "maturity",
         "reversed": True},
        {"id": 3, "text": "你懂得“灰度管理”，明白并非所有事情都需要通过高压手段立刻解决。", "type": "maturity",
         "reversed": False},
        {"id": 4, "text": "为了达成目标，你会毫不犹豫地牺牲团队成员的利益或情感，视人为工具。", "type": "maturity",
         "reversed": True},
        {"id": 5, "text": "你经常因为追求速度而忽略了潜在的隐患，导致后期返工。", "type": "maturity", "reversed": True},
        {"id": 6, "text": "你能够识别并培养他人的潜力，而不是仅仅把他们当作执行指令的手脚。", "type": "maturity",
         "reversed": False},
        {"id": 7, "text": "你对异己的声音零容忍，任何反对意见都会被你视为挑战权威。", "type": "maturity",
         "reversed": True},
        {"id": 8, "text": "你在做决策时，能够平衡“理性的最优解”与“人心的接受度”。", "type": "maturity",
         "reversed": False},
        {"id": 9, "text": "你沉迷于权力和地位的象征，而忽略了创造真正的价值。", "type": "maturity", "reversed": True},
        {"id": 10, "text": "你会定期复盘，承认自己的决策失误并迅速调整方向。", "type": "maturity", "reversed": False},
        {"id": 11, "text": "你感到必须每时每刻都在“做事”，一旦停下来思考就会感到极度焦虑。", "type": "loop",
         "reversed": False},
        {"id": 12, "text": "你开始追求即时的满足感（如赚快钱、感官享乐），抛弃了长远计划。", "type": "loop",
         "reversed": False},
        {"id": 13, "text": "你变得非常鲁莽，不做调研就直接拍板，只想立刻看到结果。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你对他人的“慢动作”完全失去耐心，经常表现出暴躁的攻击性。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你通过高强度的物质享受（名车、派对、奢侈品）来证明自己的成功。", "type": "loop",
         "reversed": False},
        {"id": 16, "text": "你发现自己像个无头苍蝇一样忙碌，但其实并没有解决核心问题。", "type": "loop",
         "reversed": False},
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
        {"id": 1, "text": "你不仅能让大家感到开心，更能通过深刻的洞察力指引他们成长的方向。", "type": "maturity",
         "reversed": False},
        {"id": 2, "text": "你常常为了维持表面的和谐，而不得不压抑自己真实的想法和需求。", "type": "maturity",
         "reversed": True},
        {"id": 3, "text": "你能够一眼看穿他人行为背后的深层动机，而不仅仅停留在表面。", "type": "maturity",
         "reversed": False},
        {"id": 4, "text": "你的自我价值感几乎完全取决于他人对你的赞美和肯定。", "type": "maturity", "reversed": True},
        {"id": 5, "text": "你经常打着“为你好”的旗号，强行介入他人的生活或做决定。", "type": "maturity", "reversed": True},
        {"id": 6, "text": "你懂得设立健康的边界，在帮助他人的同时不会耗尽自己的能量。", "type": "maturity",
         "reversed": False},
        {"id": 7, "text": "你很难拒绝别人的请求，即使那会让你自己陷入困境。", "type": "maturity", "reversed": True},
        {"id": 8, "text": "你善于挖掘每个人的潜力，并能通过愿景激励团队共同前进。", "type": "maturity",
         "reversed": False},
        {"id": 9, "text": "你经常感到自己像个“变色龙”，在不同人面前扮演不同的角色，弄丢了真实的自己。", "type": "maturity",
         "reversed": True},
        {"id": 10, "text": "当群体走向错误方向时，你敢于为了长远利益而提出反对意见，哪怕破坏暂时的气氛。",
         "type": "maturity", "reversed": False},
        {"id": 11, "text": "你最近极度渴望热闹，一刻也闲不下来，必须通过社交来填补时间。", "type": "loop",
         "reversed": False},
        {"id": 12, "text": "你变得过度在意自己的外表、形象或排场，花费大量精力在“面子工程”上。", "type": "loop",
         "reversed": False},
        {"id": 13, "text": "你为了融入群体或活跃气氛，会不假思索地做出一些冲动、浮夸的行为。", "type": "loop",
         "reversed": False},
        {"id": 14, "text": "你发现自己开始热衷于肤浅的八卦或是非，而不再进行有深度的对话。", "type": "loop",
         "reversed": False},
        {"id": 15, "text": "你对“错过”（FOMO）感到极度焦虑，看到别人聚会没叫你就会很难受。", "type": "loop",
         "reversed": False},
        {"id": 16, "text": "你根本无法独处，一旦安静下来就会感到莫名的恐慌和空虚。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你变得非常急躁，只追求当下的快乐和反馈，完全不想未来的后果。", "type": "loop",
         "reversed": False},
        {"id": 18, "text": "你对他人的评价反应过度，为了博取关注而做出戏剧化的举动。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你感觉自己像是在“表演”生活，虽然周围很热闹，内心却觉得很空洞。", "type": "loop",
         "reversed": False},
        {"id": 20, "text": "你会盲目追随当下的潮流或他人的意见，完全失去了自己的主见。", "type": "loop",
         "reversed": False},
        {"id": 21, "text": "最近你突然变得很冷漠，开始用批判性的眼光审视身边的人。", "type": "grip", "reversed": False},
        {"id": 22, "text": "你会揪住别人话语中的逻辑漏洞不放，变得非常爱钻牛角尖。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你觉得周围的人都很虚伪、愚蠢，只有你一个人看透了“丑陋的真相”。", "type": "grip",
         "reversed": False},
        {"id": 24, "text": "你开始自我隔离，沉迷于研究一些晦涩的理论或数据，以此逃避情感。", "type": "grip",
         "reversed": False},
        {"id": 25, "text": "你对自己进行残酷的逻辑批判，列举出无数证据证明自己是无能的。", "type": "grip",
         "reversed": False},
        {"id": 26, "text": "你感到情感系统完全关闭了，只剩下冷冰冰的、甚至带有攻击性的逻辑。", "type": "grip",
         "reversed": False},
        {"id": 27, "text": "你会突然因为一个逻辑上的小问题，而全盘否定一段关系的价值。", "type": "grip",
         "reversed": False},
        {"id": 28, "text": "你认为别人的善意背后一定有某种功利性的逻辑动机。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你试图用绝对理性的方式去解决所有情感问题，结果把事情搞得更糟。", "type": "grip",
         "reversed": False},
        {"id": 30, "text": "你脑子里充满了复杂的阴谋论，觉得世界是一个巨大的、设计精密的谎言。", "type": "grip",
         "reversed": False}
    ],
    "ENTP": [
        {"id": 1, "text": "你不仅擅长发现别人的逻辑漏洞，更能提出具有建设性的替代方案。", "type": "maturity",
         "reversed": False},
        {"id": 2, "text": "你经常为了享受“赢”的快感而与人争论，哪怕你其实心里并不认同那个观点。", "type": "maturity",
         "reversed": True},
        {"id": 3, "text": "你有能力筛选那些漫无边际的想法，并用严谨的逻辑将其转化为可落地的项目。", "type": "maturity",
         "reversed": False},
        {"id": 4, "text": "你开启了无数个新计划，但真正完成的寥寥无几，留下一堆烂摊子。", "type": "maturity",
         "reversed": True},
        {"id": 5, "text": "你经常因为觉得无聊或失去新鲜感，就随意抛弃对他人的承诺。", "type": "maturity",
         "reversed": True},
        {"id": 6, "text": "你能够客观地分析问题，不会让个人好恶或外界评价干扰你的逻辑判断。", "type": "maturity",
         "reversed": False},
        {"id": 7, "text": "你习惯用戏谑或嘲讽的态度对待严肃问题，以此来逃避真正的责任。", "type": "maturity",
         "reversed": True},
        {"id": 8, "text": "你不仅热衷于打破旧规则，也懂得建立更优的新规则来维持秩序。", "type": "maturity",
         "reversed": False},
        {"id": 9, "text": "你因为过度自信，经常在准备不足的情况下盲目冒险，导致失败。", "type": "maturity",
         "reversed": True},
        {"id": 10, "text": "你会主动反思自己的逻辑框架，并愿意根据新的事实进行自我修正。", "type": "maturity",
         "reversed": False},
        {"id": 11, "text": "你最近极度渴望别人的关注，甚至不惜通过制造混乱或恶作剧来博眼球。", "type": "loop",
         "reversed": False},
        {"id": 12, "text": "你变得非常在意别人怎么看你，为了讨好群体而放弃了自己的逻辑原则。", "type": "loop",
         "reversed": False},
        {"id": 13, "text": "你感到内心空虚，必须不断地与人互动或寻求外界刺激来填补。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你发现自己变得情绪化和甚至有些操纵性，试图通过情感影响他人。", "type": "loop",
         "reversed": False},
        {"id": 15, "text": "你对“被孤立”或“不受欢迎”感到前所未有的焦虑和恐惧。", "type": "loop", "reversed": False},
        {"id": 16, "text": "你做决定时不再依据理性分析，而是看大家喜欢什么或流行什么。", "type": "loop",
         "reversed": False},
        {"id": 17, "text": "你像个停不下来的“小丑”，在人群中过度表演，回到家却觉得精疲力尽。", "type": "loop",
         "reversed": False},
        {"id": 18, "text": "你变得偏执，总觉得别人在背后议论你或针对你。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你无法忍受独处和思考，一旦安静下来就会陷入恐慌。", "type": "loop", "reversed": False},
        {"id": 20, "text": "你对批评反应过度，会为了维护面子而进行非理性的反击。", "type": "loop", "reversed": False},
        {"id": 21, "text": "你最近突然对身体健康产生极度焦虑，总怀疑自己得了什么大病。", "type": "grip",
         "reversed": False},
        {"id": 22, "text": "你会反复咀嚼过去的一个微小失误，感到无法释怀的悔恨。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你突然变得极度保守和僵化，拒绝任何新的可能性或改变。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你开始对细节产生强迫症般的关注（如反复检查文档、整理物品）。", "type": "grip",
         "reversed": False},
        {"id": 25, "text": "你感到思维枯竭，完全想不出任何新点子，大脑像生锈了一样。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你变得非常孤僻，只想缩在床上或家里，切断与外界的一切联系。", "type": "grip",
         "reversed": False},
        {"id": 27, "text": "你感到身体极其沉重、疲惫，除了机械性的吃饭睡觉什么都不想做。", "type": "grip",
         "reversed": False},
        {"id": 28, "text": "你觉得自己过去的所有尝试都是失败的，陷入一种深深的虚无感。", "type": "grip",
         "reversed": False},
        {"id": 29, "text": "你对日程表或计划的微小变动感到异常烦躁，失去了往日的灵活。", "type": "grip",
         "reversed": False},
        {"id": 30, "text": "你觉得自己正在慢慢“腐烂”，被琐碎的现实生活彻底压垮。", "type": "grip", "reversed": False}
    ],
    "ISFJ": [
        {"id": 1, "text": "你能敏锐地记住他人的喜好和细节，并用实际行动让他们感到被珍视。", "type": "maturity",
         "reversed": False},
        {"id": 2, "text": "你经常因为不好意思拒绝，而承担了许多本不属于你的责任。", "type": "maturity", "reversed": True},
        {"id": 3, "text": "面对变化，你第一反应通常是抗拒，觉得“按老规矩办”才是最安全的。", "type": "maturity",
         "reversed": True},
        {"id": 4, "text": "你为了维持表面的和谐，经常把自己的真实委屈吞进肚子里。", "type": "maturity", "reversed": True},
        {"id": 5, "text": "你能够在照顾家人的同时，依然保留属于自己的时间和爱好。", "type": "maturity",
         "reversed": False},
        {"id": 6, "text": "你习惯通过付出和牺牲来换取他人的认可，一旦没得到回应就倍感失落。", "type": "maturity",
         "reversed": True},
        {"id": 7, "text": "你不仅做事细致靠谱，还能在混乱中为他人提供稳定的情绪支持。", "type": "maturity",
         "reversed": False},
        {"id": 8, "text": "你经常觉得“如果我不做，这件事就没人能做好了”，因此甚至不敢休息。", "type": "maturity",
         "reversed": True},
        {"id": 9, "text": "你能够分清哪些是你的责任，哪些是别人该承担的课题，不过度干涉。", "type": "maturity",
         "reversed": False},
        {"id": 10, "text": "你会因为过度在意别人的看法，而反复纠结自己的一言一行是否得体。", "type": "maturity",
         "reversed": True},
        {"id": 11, "text": "最近你变得不想理人，觉得与其跟人打交道，不如自己待着清净。", "type": "loop",
         "reversed": False},
        {"id": 12, "text": "你会反复回想过去某个人对你的冒犯，越想越生气，觉得无法释怀。", "type": "loop",
         "reversed": False},
        {"id": 13, "text": "你开始用非常挑剔的眼光审视周围，觉得每个人都有毛病，都很自私。", "type": "loop",
         "reversed": False},
        {"id": 14, "text": "你陷入了一种“死板的逻辑”中，觉得必须按某个流程做，谁劝都不听。", "type": "loop",
         "reversed": False},
        {"id": 15, "text": "你觉得自己过去对他人的付出都是不值得的，产生了一种愤世嫉俗的念头。", "type": "loop",
         "reversed": False},
        {"id": 16, "text": "你会把过往的细节像过电影一样在脑海里播放，专门寻找别人对不起你的证据。", "type": "loop",
         "reversed": False},
        {"id": 17, "text": "你对他人的情感表达感到麻木甚至厌烦，甚至会说出冷漠伤人的话。", "type": "loop",
         "reversed": False},
        {"id": 18, "text": "你变得异常固执，坚持自己的经验才是对的，拒绝接受任何新的解释。", "type": "loop",
         "reversed": False},
        {"id": 19, "text": "你试图通过疯狂地整理、归纳或纠结细节来逃避人际关系中的问题。", "type": "loop",
         "reversed": False},
        {"id": 20, "text": "你内心积压了很多不满，但你选择不说，而是用冷暴力或消极抵抗来应对。", "type": "loop",
         "reversed": False},
        {"id": 21, "text": "最近你脑子里总是冒出“万一出事了怎么办”的念头，对未来充满恐惧。", "type": "grip",
         "reversed": False},
        {"id": 22, "text": "你会突然觉得现有的生活摇摇欲坠，仿佛一切都要崩塌了。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你会因为未知和不确定性而感到极度焦虑，严重影响睡眠。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你可能会突然想要打破常规，做一些极其冲动、反常、不计后果的决定。", "type": "grip",
         "reversed": False},
        {"id": 25, "text": "你觉得眼前充满了无数种糟糕的可能性，让你完全不知道该怎么迈出下一步。", "type": "grip",
         "reversed": False},
        {"id": 26, "text": "你会把一些毫不相关的小事联系起来，得出一个可怕的负面结论。", "type": "grip",
         "reversed": False},
        {"id": 27, "text": "你感到思维混乱，平日里井井有条的你突然变得丢三落四、不知所措。", "type": "grip",
         "reversed": False},
        {"id": 28, "text": "你对任何变化都表现出过激的恐慌反应，觉得那是危险的信号。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你会不停地向别人确认“会没事的吧？”，但别人的安慰根本无法让你心安。", "type": "grip",
         "reversed": False},
        {"id": 30, "text": "你觉得自己失去了对生活的控制权，像是在一艘即将沉没的船上。", "type": "grip",
         "reversed": False}
    ],
    "ISTP": [
        {"id": 1, "text": "你不仅能发现问题的逻辑漏洞，还能立刻动手找到解决办法。", "type": "maturity",
         "reversed": False},
        {"id": 2, "text": "你经常因为嫌麻烦，而对重要的事情采取“摆烂”或拖延的态度。", "type": "maturity",
         "reversed": True},
        {"id": 3, "text": "面对突发状况，你通常能保持冷静，并迅速做出最有利的反应。", "type": "maturity",
         "reversed": False},
        {"id": 4, "text": "你为了追求感官刺激（如飙车、极限运动），经常不顾后果地盲目冒险。", "type": "maturity",
         "reversed": True},
        {"id": 5, "text": "你能够用简洁精准的语言阐述复杂的原理，而不是故弄玄虚。", "type": "maturity",
         "reversed": False},
        {"id": 6, "text": "你对他人的情感极其冷漠，甚至在他人的痛苦面前表现得无动于衷。", "type": "maturity",
         "reversed": True},
        {"id": 7, "text": "你既享受独处的自由，也能在必要时融入群体，展现出幽默感。", "type": "maturity",
         "reversed": False},
        {"id": 8, "text": "你经常在这个项目中途因为失去了兴趣而半途而废，没有任何交代。", "type": "maturity",
         "reversed": True},
        {"id": 9, "text": "你总是等到最后一刻才行动，且经常因为误判时间而搞砸事情。", "type": "maturity",
         "reversed": True},
        {"id": 10, "text": "你愿意为了掌握一项技能而进行枯燥的重复练习，追求技术上的精进。", "type": "maturity",
         "reversed": False},
        {"id": 11, "text": "最近你变得非常消极，觉得做什么都没有意义，反正结果早就注定了。", "type": "loop",
         "reversed": False},
        {"id": 12, "text": "你开始过度解读别人的话，总觉得他们背后有某种针对你的阴谋。", "type": "loop",
         "reversed": False},
        {"id": 13, "text": "你把自己关在家里，完全切断了与物理世界的接触，陷入大脑的空转。", "type": "loop",
         "reversed": False},
        {"id": 14, "text": "你对未来充满了悲观的预测，并坚信这些坏事一定会发生。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你变得愤世嫉俗，看什么都不顺眼，觉得周围的人都是傻瓜。", "type": "loop", "reversed": False},
        {"id": 16, "text": "你试图在脑海中构建一个宏大的理论来解释一切，但完全脱离了现实证据。", "type": "loop",
         "reversed": False},
        {"id": 17, "text": "你对行动失去了兴趣，宁愿躺着空想也不愿动手去验证一下。", "type": "loop", "reversed": False},
        {"id": 18, "text": "你觉得整个社会规则都是骗局，产生了一种强烈的反叛但无力的情绪。", "type": "loop",
         "reversed": False},
        {"id": 19, "text": "你误读了别人的沉默或微表情，认定他们是在嘲笑你或排挤你。", "type": "loop", "reversed": False},
        {"id": 20, "text": "你陷入了一种精神上的麻痹状态，既不快乐，也不痛苦，只是单纯的停滞。", "type": "loop",
         "reversed": False},
        {"id": 21, "text": "你突然觉得自己被所有人抛弃了，没人关心你，没人爱你。", "type": "grip", "reversed": False},
        {"id": 22, "text": "你会因为一点小事而突然情绪大爆发，甚至摔东西或大吼大叫。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你变得对他人的评价极度敏感，别人一个眼神就能让你难受半天。", "type": "grip",
         "reversed": False},
        {"id": 24, "text": "你开始甚至有点“歇斯底里”，表现出平时绝对不会有的戏剧化情感。", "type": "grip",
         "reversed": False},
        {"id": 25, "text": "你感到一种难以名状的孤独感，渴望得到别人的肯定和安抚。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你会用消极攻击（冷战、阴阳怪气）的方式来表达你的不满，而不是直接解决。", "type": "grip",
         "reversed": False},
        {"id": 27, "text": "你觉得自己付出了很多却没得到回报，变成了一个充满了怨气的受害者。", "type": "grip",
         "reversed": False},
        {"id": 28, "text": "你发现自己控制不住地流泪或情绪低落，逻辑思维完全下线。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你为了维持某种人际关系的和谐，而做出极度违背自己意愿的妥协。", "type": "grip",
         "reversed": False},
        {"id": 30, "text": "你感到自己的边界被侵犯了，但又不知道如何拒绝，最后只能情绪崩溃。", "type": "grip",
         "reversed": False}
    ],
    "ENFP": [
        {"id": 1, "text": "你能够将新奇的点子与真实的价值观结合，而不是随波逐流。", "type": "maturity",
         "reversed": False},
        {"id": 2, "text": "你经常因为三分钟热度，开启了很多项目却很少能善始善终。", "type": "maturity", "reversed": True},
        {"id": 3, "text": "你能在追求可能性的同时，察觉并照顾到他人的真实感受。", "type": "maturity", "reversed": False},
        {"id": 4, "text": "你经常情绪化地做决定，事后又因为不切实际而后悔。", "type": "maturity", "reversed": True},
        {"id": 5, "text": "你经常逃避细节和枯燥的执行工作，导致好想法落地困难。", "type": "maturity", "reversed": True},
        {"id": 6, "text": "你能够通过真诚的表达感染他人，成为团队的精神支柱。", "type": "maturity", "reversed": False},
        {"id": 7, "text": "你因为过度渴望被喜欢，而常常在人际关系中失去原则。", "type": "maturity", "reversed": True},
        {"id": 8, "text": "你既能仰望星空，也能脚踏实地处理眼前的苟且。", "type": "maturity", "reversed": False},
        {"id": 9, "text": "你因为想法太多且经常变卦，让周围的人感到不可靠。", "type": "maturity", "reversed": True},
        {"id": 10, "text": "你会定期反思自己的价值观，确保行动不违背本心。", "type": "maturity", "reversed": False},
        {"id": 11, "text": "你最近变得非常强势、独断，听不进任何人的反对意见。", "type": "loop", "reversed": False},
        {"id": 12, "text": "你切断了内心的感受，像个工作狂一样疯狂忙碌来麻痹自己。", "type": "loop", "reversed": False},
        {"id": 13, "text": "你变得急功近利，只想快速看到结果，忽略了过程中的意义。", "type": "loop", "reversed": False},
        {"id": 14, "text": "你对他人的效率低感到极度不耐烦，表现出前所未有的暴躁。", "type": "loop", "reversed": False},
        {"id": 15, "text": "你为了证明自己，盲目地追求世俗定义的成功标准。", "type": "loop", "reversed": False},
        {"id": 16, "text": "你拒绝面对内心的脆弱，用逻辑和效率来防御一切。", "type": "loop", "reversed": False},
        {"id": 17, "text": "你变得喜欢发号施令，试图控制周围的一切人和事。", "type": "loop", "reversed": False},
        {"id": 18, "text": "你对“无用”的情感交流感到厌烦，觉得那是在浪费时间。", "type": "loop", "reversed": False},
        {"id": 19, "text": "你感觉自己像个机器人在运转，内心却是一片荒芜。", "type": "loop", "reversed": False},
        {"id": 20, "text": "你通过不断的行动来逃避思考自己真正想要什么。", "type": "loop", "reversed": False},
        {"id": 21, "text": "你突然变得极度保守，对未来充满恐惧，不敢尝试任何新事物。", "type": "grip", "reversed": False},
        {"id": 22, "text": "你对身体的微小不适感到过度焦虑，怀疑自己生了重病。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你会陷入对过去细节的无限纠结中，后悔当初不该那样做。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你变得非常孤僻，甚至有点抑郁，完全失去了往日的活力。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你对细节变得吹毛求疵，对周围的混乱感到无法忍受。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你感觉思维枯竭，脑子里没有任何新点子，只有无尽的沉重。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你会机械地重复做一些琐碎的家务或整理工作来逃避现实。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你觉得自己一无是处，过去的所有努力都是没有意义的。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你对任何计划外的变动都感到极度恐慌和抗拒。", "type": "grip", "reversed": False},
        {"id": 30, "text": "你感觉自己被困在一个狭小的盒子里，透不过气来。", "type": "grip", "reversed": False}
    ]
}

# ==========================================
# 2. 核心数据：文案逻辑
# ==========================================

NARRATIVE_TEMPLATES = {
    "INTP": {
        "stable": {
            "insight": "当前状态：【落地的智者】。你的逻辑体系（Ti）正在开放地接纳新信息（Ne）。你既有深度的思考，又对未知保持好奇，这是创造力爆发的最佳状态。",
            "advice": "【微小输出】：利用现在的状态，尝试将你的一个概念“实体化”（写下来、做个Demo），别让它只停留在脑海里。"},
        "overload": {
            "insight": "当前状态：【情绪溃堤】(Grip爆发)。平时冷静的逻辑防线已崩塌，你现在可能感到前所未有的委屈、敏感，觉得“没人喜欢我”或渴望被照顾。",
            "advice": "【情绪急救】：承认自己“系统过热”。现在的你没法讲道理。请立刻停止工作，吃点好吃的，承认自己也是有血有肉的人，这不丢人。"},
        "highLoop": {
            "insight": "当前状态：【僵化的硬盘】(Loop闭环)。你困在了过去的数据里（Si），反复分析“哪里出错了”，却拒绝摄入新信息。这让你变得固执且行动瘫痪。",
            "advice": "【引入变量】：你的大脑缺氧了。哪怕是去一条陌生的街道散步（激活Ne），或者看一部没看过的烂片，只要是“新的输入”，就能打破这个死循环。"}
    },
    "INFJ": {
        "stable": {
            "insight": "当前状态：【温和的平衡者】。直觉（Ni）为你指引方向，情感（Fe）助你连接他人。你既没有沉溺于空想，也没有被外界的情绪洪流淹没。",
            "advice": "【能量护城河】：保持这种节奏。但请记住，你的共情力是有限资源。每周预留一个“绝对静音时段”，不处理任何人的情绪垃圾。"},
        "overload": {
            "insight": "当前状态：【感官过载】(Grip爆发)。你可能正处于“由于长期无法对外说不”而导致的报复性反弹中，表现为暴饮暴食、对环境噪音极度敏感或冲动消费。",
            "advice": "【物理阻断】：现在的你不需要“意义”，只需要“五感安抚”。立刻切断社交网络，去洗个热水澡、或是睡个长觉。允许自己像个孩子一样任性一回。"},
        "highLoop": {
            "insight": "当前状态：【自我隔离的审判者】(Loop闭环)。你切断了与人的连接，陷入了冷漠的逻辑分析中，甚至觉得“没有人值得我救赎”，这是一种防御性的傲慢。",
            "advice": "【强制外化】：打破死循环的唯一方法是Fe。不需要解决大问题，找一个信任的朋友，仅仅是把你的想法“说出来”，而不是在脑子里“盘明白”。"}
    },
    "INTJ": {
        "stable": {
            "insight": "当前状态：【远见执行者】。你的愿景（Ni）与执行力（Te）完美咬合。你不仅看得到未来，还在一步步将现实推向那个未来。",
            "advice": "【现实校准】：在推进宏大计划时，偶尔停下来确认一下身边人的状态。有时候，稍微慢一点，是为了走得更远。"},
        "overload": {
            "insight": "当前状态：【破坏性放纵】(Grip爆发)。长期的精神紧绷导致了“断崖式下跌”。你可能正在沉迷于暴食、酗酒、疯狂购物或无意义的感官刺激中，甚至有毁灭一切的冲动。",
            "advice": "【感官着陆】：不要自我批判。你的身体在替你的大脑抗议。去进行高强度的运动（如拳击、跑步），把体内的攻击性安全地释放出去。"},
        "highLoop": {
            "insight": "当前状态：【偏执的孤岛】(Loop闭环)。你过度信任自己的主观感受（Fi），认为全世界都在针对你，或陷入“没人能理解我”的悲剧英雄叙事中，脱离了客观现实。",
            "advice": "【事实核查】：启动你的Te。把你的担忧列成清单，逐一问自己：“有客观数据支持这个结论吗？”让外部事实来击穿你的主观幻觉。"}
    },
    "ENTJ": {
        "stable": {
            "insight": "当前状态：【真正的指挥官】。你的执行力（Te）由深远的洞察力（Ni）指引。你不再是单纯为了赢而战，而是在构建一个可持续的生态系统。",
            "advice": "【柔性领导力】：你现在很强大。利用这个时期，去倾听那些平时你觉得“声音太小”的人的意见。往往盲点就藏在那些被你忽略的细节里。"},
        "overload": {
            "insight": "当前状态：【落难的国王】(Grip爆发)。你那无坚不摧的逻辑盔甲碎裂了，露出了最脆弱的内核。你感到被全世界孤立、误解，陷入深深的自我怀疑和受害者心态中。",
            "advice": "【情感接纳】：不要试图用逻辑去分析这些情绪。找一个非利益相关的朋友，承认你的疲惫和软弱。示弱不是失败，是人性的回归。"},
        "highLoop": {
            "insight": "当前状态：【失控的推土机】(Loop闭环)。你切断了战略思考（Ni），陷入了盲目的忙碌中。你通过无休止的工作或物质消费来麻痹自己，虽横冲直撞却不知去向。",
            "advice": "【强制暂停】：你的油门踩死了，但方向盘丢了。必须强制自己独处。只有静下来，你的直觉才能重新上线，告诉你真正的方向。"}
    },
    "ENFJ": {
        "stable": {
            "insight": "当前状态：【启迪心灵的导师】。你的共情能力（Fe）被深远的洞察力（Ni）所锚定。你不再是只会讨好的“滥好人”，而是一位真正能引领他人成长的领袖。",
            "advice": "【向内关照】：哪怕是太阳也需要夜晚。每周给自己一段“不为任何人负责”的时间，只做让自己快乐的事，不需要有意义，也不需要照顾谁的情绪。"},
        "overload": {
            "insight": "当前状态：【冷酷的检察官】(Grip爆发)。温暖的你消失了，取而代之的是一个愤世嫉俗、吹毛求疵的逻辑机器。你觉得所有人都是虚伪的，甚至在脑中无情地审判自己。",
            "advice": "【停止分析】：你现在的逻辑是“有毒”的。去和那些无条件爱你、且不需要你照顾的人（比如家人或宠物）待在一起。你需要被温暖的情感重新“融化”。"},
        "highLoop": {
            "insight": "当前状态：【焦虑的表演者】(Loop闭环)。你切断了深度思考，迷失在外界的喧嚣中。你看起来光鲜亮丽，但内心充满了“一旦停下来就会被遗忘”的恐慌。",
            "advice": "【深度独处】：你现在是一只停不下来的陀螺。必须强制减速。关掉手机，去读一本深奥的书，或者写日记。强迫自己面对孤独。"}
    },
    "ENTP": {
        "stable": {
            "insight": "当前状态：【落地的发明家】。你的脑洞（Ne）被逻辑（Ti）精准地捕捉和构建。你不再是为了辩论而辩论，而是在用你的智慧拆解旧世界的谬误，构建新世界的蓝图。",
            "advice": "【完成闭环】：选择一个你最看好的项目，强迫自己把它推进到 100% 完成，而不是停在 90%。成品的快感会比“可能性的快感”更持久。"},
        "overload": {
            "insight": "当前状态：【神经质的隐士】(Grip爆发)。那个天马行空的你消失了，取而代之的是一个对身体健康过度焦虑、对细节吹毛求疵、甚至陷入抑郁和自闭的人。",
            "advice": "【身体复苏】：别想了，你的大脑现在是死机的。你需要的是“感官安抚”。去吃顿好的、去按摩。照顾好你的身体，你的灵感自然会回来。"},
        "highLoop": {
            "insight": "当前状态：【焦虑的小丑】(Loop闭环)。你切断了内部逻辑，迷失在外界的反馈中。你可能正在通过哗众取宠、制造混乱来刷存在感，内心却充满了对“不受欢迎”的恐惧。",
            "advice": "【逻辑隔离】：你现在太“吵”了。你需要切断外界反馈。把自己关进小黑屋，问自己：“不管别人怎么看，这件事在逻辑上成立吗？”找回你那个冷酷的内核。"}
    },
    "ISFJ": {
        "stable": {
            "insight": "当前状态：【温柔的守护者】。你的经验（Si）与爱心（Fe）正完美结合。你不仅细致入微，更难得的是，你开始懂得“爱自己是爱别人的前提”，在付出中找到了平衡。",
            "advice": "【自我奖赏】：亲爱的，你做得已经够多了。请不要把“空闲时间”视作一种罪恶。每周专门留出半天时间，不做任何“有用”的事，只是喝茶或发呆。"},
        "overload": {
            "insight": "当前状态：【惊慌的迷路者】(Grip爆发)。劣势Ne正在你的大脑里制造“灾难片”。你被“未知的恐惧”淹没，觉得无论怎么做未来都会出大问题，甚至想冲动逃离。",
            "advice": "【回到当下】：停止思考未来！去做一件极其具体的小事：比如整理衣柜、手洗几件衣服。用指尖的触感把自己拉回安全的现实中。"},
        "highLoop": {
            "insight": "当前状态：【委屈的审判官】(Loop闭环)。你切断了对外的温暖，把自己锁在过去的回忆里生闷气。你心里反复盘算“谁对不起我”，变得冷漠、记仇。",
            "advice": "【表达需求】：你在等别人“猜”到你的委屈，但这是徒劳的。直接告诉对方：“我现在很累，我需要你帮我。”说出来，那一刻你就解脱了。"}
    },
    "ISTP": {
        "stable": {
            "insight": "当前状态：【冷静的操盘手】。你的逻辑内核（Ti）与对现实的敏锐度（Se）配合完美。你是最高效的问题解决者，享受当下的自由，也能处理好手头的麻烦。",
            "advice": "【保持流动】：你现在就像水一样灵活。如果感到无聊，去学习一项新的硬核技能（如编程、机械、极限运动），这能让你的多巴胺维持在健康水平。"},
        "overload": {
            "insight": "当前状态：【失控的火山】(Grip爆发)。那个“冷酷”的你不见了，你变得异常情绪化、敏感，像个孩子一样发脾气。你可能觉得自己被忽视了，或者为了别人的事感到精疲力尽。",
            "advice": "【物理隔离】：别试图用逻辑分析情绪。你需要的是独处 + 发泄。去健身房举铁、去打沙袋。把那股奇怪的能量通过身体排出去，你的理智就会回来。"},
        "highLoop": {
            "insight": "当前状态：【瘫痪的阴谋论者】(Loop闭环)。你切断了与物理世界的连接，困在大脑里空转。你觉得“做什么都没意义”，或者怀疑周围的一切都有阴谋，行动力归零。",
            "advice": "【强制行动】：你的大脑中毒了，解药在手上。立刻动起来，哪怕是修一个坏掉的水龙头。只要你的手开始触碰真实的物体，虚无的死循环就会瓦解。"}
    },
    "ENFP": {
        "stable": {
            "insight": "当前状态：【闪光的启发者】。你的Ne与Fi正处于美妙的共振中。你不仅是人群中的开心果，更是灵魂的摆渡人。你对自己诚实，对他人温暖，既有理想又有行动。",
            "advice": "【守护边界】：你的能量太珍贵了，不要随意挥霍。对别人说“不”，就是对自己说“是”。继续保持你的热情，但要把核心能量留给真正懂你的人。"},
        "overload": {
            "insight": "当前状态：【褪色的气球】(Grip爆发)。那个充满灵气的你不见了，取而代之的是一个抑郁、疑病、对细节吹毛求疵的人。你觉得身体出了问题，或者未来一片黑暗。",
            "advice": "【感官疗愈】：不要逼自己去社交。现在的解药是“熟悉的安稳”：吃童年喜欢的食物、看老电影。允许自己做一个无聊的普通人，直到能量回归。"},
        "highLoop": {
            "insight": "当前状态：【失速的列车】(Loop闭环)。你切断了内心的感受，试图用疯狂的忙碌来证明自己。你看起来效率很高、很强势，但你的内心是麻木的。",
            "advice": "【回归内心】：停下手里的工作。找一个安静的地方，问自己：“我现在的感觉是什么？”悲伤？愤怒？把那个被你关在门外的小孩子接回来。"}
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
    if res_g >= 65 or res_load >= 75:
        state_key = "overload"
    elif res_l >= 65:
        state_key = "highLoop"
    elif res_l < 35 and res_g < 35 and res_load < 65:
        state_key = "stable"

    narrative_pack = NARRATIVE_TEMPLATES.get(mbti, DEFAULT_NARRATIVE)
    content = narrative_pack.get(state_key, DEFAULT_NARRATIVE[state_key])

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
        pill_text=pill_text,
        chart_data=[res_m, res_coh, 100 - res_l, 100 - res_g, 100 - res_load, res_overall]
    )