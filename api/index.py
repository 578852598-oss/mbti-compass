from __future__ import annotations
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import statistics
import random
from urllib.parse import urlencode
import hashlib
import time
from fastapi import FastAPI, Request, HTTPException
import os
import uuid
import httpx
from fastapi.responses import PlainTextResponse

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
        {"id": 6, "text": "你能把复杂的原理，用简单的大白话讲给外行听。", "type": "maturity", "reversed": False},
        {"id": 7, "text": "听到不合逻辑的观点，你会立刻打断或在心里翻白眼，而不是听听看。", "type": "maturity", "reversed": True},
        {"id": 8, "text": "你不仅能提出天马行空的构想，还能耐着性子去处理琐碎的落地步骤。", "type": "maturity", "reversed": False},
        {"id": 9, "text": "你会因追求“更完美的方案”而迟迟无法启动。", "type": "maturity", "reversed": True},
        {"id": 10, "text": "你会主动问别人“我是不是哪里没考虑到”，而不是等着别人来挑刺。", "type": "maturity", "reversed": False},
        {"id": 11,"text": "你最近像是在回放老电影，不断咀嚼过去的某个尴尬瞬间或错误。","type": "loop","reversed": False},
        {"id": 12,"text": "面对新机会，你脑子里跳出的全是以前失败的经历，吓得不想动。","type": "loop","reversed": False},
        {"id": 13,"text": "别人提出新建议，你的第一反应是挑刺，列举十个行不通的理由。","type": "loop","reversed": False},
        {"id": 14,"text": "你只相信自己亲自验证过的数据，对别人的经验完全听不进去。","type": "loop","reversed": False},
        {"id": 15,"text": "你把自己关起来，觉得外面的世界很吵、很蠢，不想和任何人交流。","type": "loop","reversed": False},
        {"id": 16,"text": "你抠细节抠到了魔怔的程度，完全忘记了原本要做什么。","type": "loop","reversed": False},
        {"id": 17,"text": "你对身体的一点小病痛异常敏感，甚至怀疑自己得了大病。","type": "loop","reversed": False},
        {"id": 18,"text": "你觉得自己不仅没做成事，甚至连原本引以为傲的逻辑能力都在退化。","type": "loop","reversed": False},
        {"id": 19,"text": "你用“为了稳妥”当借口，拒绝任何形式的改变或冒险。","type": "loop","reversed": False},
        {"id": 20,"text": "你陷入了一种“分析瘫痪”，想得越细，越觉得哪里都是坑。","type": "loop","reversed": False},
        {"id": 21,"text": "平时很淡定的你，突然因为一点小事就炸毛，甚至想摔东西。","type": "grip","reversed": False},
        {"id": 22,"text": "你会陷入一种机械性的重复（如无休止地刷视频、玩游戏），只为麻痹那股莫名涌上来的情绪。","type": "grip","reversed": False},
        {"id": 23,"text": "你总觉得大家都在针对你，甚至觉得别人在背后说你坏话。","type": "grip","reversed": False},
        {"id": 24,"text": "你突然变得特别委屈，觉得自己付出了一切，却没人领情。","type": "grip","reversed": False},
        {"id": 25,"text": "平时逻辑清晰的大脑像变成了浆糊，根本无法进行复杂的思考。","type": "grip","reversed": False},
        {"id": 26,"text": "你会阴阳怪气地说话，试图刺痛别人，这和平时的你判若两人。","type": "grip","reversed": False},
        {"id": 27,"text": "你极度渴望被别人肯定，甚至为了讨好别人而去做蠢事。","type": "grip","reversed": False},
        {"id": 28,"text": "你觉得自己非常孤独，觉得世界上没人能理解你。","type": "grip","reversed": False},
        {"id": 29,"text": "你对身边亲近的人发火，发完火后又陷入深深的自我厌恶。","type": "grip","reversed": False},
        {"id": 30,"text": "你不仅想摆烂，甚至有一种想把现有生活“一把火烧了”的破坏冲动。","type": "grip","reversed": False}
    ],

    "INFJ": [
        {"id": 1, "text": "当现实情况和你想的不一样时，你能承认自己错了，而不是死鸭子嘴硬。", "type": "maturity","reversed": False},
        {"id": 2, "text": "你总是活在脑子里的未来图景里，结果连饭都忘了吃，或者把日子过得一团糟。", "type": "maturity","reversed": True},
        {"id": 3, "text": "你有自己的原则，但说话很好听，能用别人听得进去的方式表达出来。", "type": "maturity","reversed": False},
        {"id": 4, "text": "你总觉得自己看人特别准，觉得别人的建议都很浅薄，根本听不进去。", "type": "maturity","reversed": True},
        {"id": 5, "text": "你总想等一个“完美的时机”再动手，结果想了半天，最后什么都没干。", "type": "maturity","reversed": True},
        {"id": 6, "text": "你能把脑子里那些玄乎的直觉，变成一步步具体的计划，真的帮到别人。", "type": "maturity","reversed": False},
        {"id": 7, "text": "一旦你认定这事儿“有意义”，哪怕现实条件根本不允许，你也要硬着头皮干。", "type": "maturity","reversed": True},
        {"id": 8, "text": "你心很软，能理解别人的痛苦，但也会保护自己，不会让自己被情绪垃圾淹没。", "type": "maturity","reversed": False},
        {"id": 9, "text": "你其实挺享受“没人懂我”的感觉，故意把自己边缘化，不合群。", "type": "maturity","reversed": True},
        {"id": 10, "text": "你会真的动手去试错，来验证你的猜想，而不是光在脑子里瞎推演。", "type": "maturity","reversed": False},

        # Loop (Ni-Ti 循环)：变得冷漠、封闭、自以为是
        {"id": 11, "text": "最近你有一些自闭了，觉得出去社交纯粹是浪费生命，谁都不想理。", "type": "loop","reversed": False},
        {"id": 12, "text": "你变得很冷血，像看显微镜一样分析身边的人，觉得他们都很虚伪、都有目的。", "type": "loop","reversed": False},
        {"id": 13, "text": "你陷入了死脑筋，非要在脑子里想出一套完美的逻辑，觉得只有自己是对的。", "type": "loop","reversed": False},
        {"id": 14, "text": "你变得特别刻薄挑剔，看到别人哭哭啼啼或者情绪化，你只会觉得烦。", "type": "loop","reversed": False},
        {"id": 15, "text": "你觉得这事儿肯定没戏（虽然没发生），所以干脆一开始就放弃了。", "type": "loop","reversed": False},
        {"id": 16, "text": "你死都不肯求助，坚信只有自己才能救自己，觉得别人都帮不上忙。", "type": "loop","reversed": False},
        {"id": 17, "text": "表面上你在发呆，其实脑子里在进行激烈的辩论，谁也插不进嘴。", "type": "loop","reversed": False},
        {"id": 18, "text": "你觉得干什么都没劲，整个世界看起来都很空虚，毫无意义。", "type": "loop", "reversed": False},
        {"id": 19, "text": "为了证明你的逻辑是对的，你说话变得很伤人，完全不在乎会不会刺痛别人。", "type": "loop","reversed": False},
        {"id": 20, "text": "哪怕事实摆在眼前，你也觉得是事实错了，还是坚持你脑子里的那套判断。", "type": "loop","reversed": False},

        # Grip (Se 爆发)：感官失控、暴躁、想毁东西
        {"id": 21, "text": "压力大到极点时，你会突然开始暴饮暴食、疯狂买没用的东西，或者沉迷酒精。", "type": "grip","reversed": False},
        {"id": 22, "text": "你对周围的声音、光线特别敏感，稍微吵一点你就会甚至想打人。", "type": "grip","reversed": False},
        {"id": 23, "text": "你会突然像得了强迫症一样，疯狂打扫卫生，或者死抠某个细节不放。", "type": "grip","reversed": False},
        {"id": 24, "text": "你会突然“发疯”，做一些平时绝对不敢做的冲动、冒险的事。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你感觉身体特别难受，衣服上的标签、一点点疼痛都会让你抓狂。", "type": "grip","reversed": False},
        {"id": 26, "text": "你会因为找不到钥匙、或者电脑死机这种小事，瞬间崩溃大哭。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你只会在沙发上葛优瘫，无脑刷剧、打游戏，麻痹自己。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你感觉周围的东西都在故意给你找茬，看哪儿都不顺眼，在那儿碍你的事。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你会突然变得很堕落，觉得“今朝有酒今朝醉”，不管以后咋样了。", "type": "grip","reversed": False},
        {"id": 30, "text": "你心里有一股无名火，特别想摔杯子、砸东西，或者把手头的事全毁了。", "type": "grip","reversed": False}
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
        {"id": 15, "text": "你生怕被大家落下，只要看到别人聚会没喊你，心里就特别难受。", "type": "loop", "reversed": False},
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
        {"id": 22, "text": "你会把一点点身体不舒服（如头痛），就觉得自己很严重，甚至觉得自己得了绝症。", "type": "grip", "reversed": False},
        {"id": 23, "text": "你面对任何变化（如搬家、换工作）都感到极度恐惧，只想躲起来。", "type": "grip", "reversed": False},
        {"id": 24, "text": "你会突然说出一些非常悲观、消极的话，把身边人吓一跳。", "type": "grip", "reversed": False},
        {"id": 25, "text": "你感觉脑子里有无数个声音在吵架，完全没法集中注意力。", "type": "grip", "reversed": False},
        {"id": 26, "text": "你会不停地向别人确认“真的没事吗？”，但别人的安慰根本没用。", "type": "grip", "reversed": False},
        {"id": 27, "text": "你可能会因为压力大而暴饮暴食，或者彻底吃不下饭。", "type": "grip", "reversed": False},
        {"id": 28, "text": "你觉得现实世界变得很不真实，像是在做噩梦一样。", "type": "grip", "reversed": False},
        {"id": 29, "text": "你会突然冲动地想要逃离现在的生活，去一个没人认识的地方。", "type": "grip", "reversed": False},
        {"id": 30, "text": "你感觉现在啥都乱了套，平时能搞定的事现在怎么都搞不定，心里特别没底。", "type": "grip", "reversed": False}
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
        {"id": 13, "text": "你现在什么都不放心，连怎么发邮件这种芝麻小事，都要盯着别人做。", "type": "loop", "reversed": False},
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
            "title": "压力过大，先先别硬撑了",
            "text": """
【当前心理状态与行为表现评估】

综合你目前的各项测试数据和行为反馈，你现在正处于一种由长期高压导致的心力严重透支和行动完全停滞的状态。在荣格认知功能理论的框架下，你当前的评估结果为“Loop+Grip”双重叠加态。具体来说，你正在经历“内倾思考（Ti）与内倾感觉（Si）的负向循环（Loop）”，并且同时伴随着“劣势功能外倾情感（Fe）的失控爆发（Grip）”。

这种状态意味着你原有的日常问题解决机制已经完全停摆，而备用的应急情绪处理机制正在以一种混乱的方式运转。你并不是生病了，这只是你的心理能量在极度枯竭时的一种自我保护和系统报错反应。你的大脑为了节省能量，关闭了负责探索外部世界的通道，导致你被困在了自己过去的负面经验里无法脱身。

【具体困境与情绪特征】

在日常生活中，这种双重叠加态会让你表现出非常明显的反常行为。首先，你会发现自己几乎失去了处理当下现实问题的动力，哪怕是非常简单的工作或生活琐事，你都会觉得极其艰难，一直拖延。你的注意力被迫集中在过去发生的失误、遗憾或者尴尬的事情上。你的大脑会不受控制地不断提取这些负面的记忆。

在这个过程中，你最核心的逻辑分析能力（Ti）不仅没有用来帮你解决眼前的客观问题，反而把这些过去的负面记忆当成了铁证。你的大脑开始针对这些过去的事情进行严密的逻辑推导，最后得出一个非常笃定的结论：你是一个没有能力的人，或者你当下的处境已经完全没有办法挽回了。因为这个结论是你自己推导出来的，所以你深信不疑。

同时，由于劣势功能的爆发，你对周围环境和别人的态度变得极度敏感。别人一句非常普通的客套话，或者稍微迟缓一点的信息回复，都会被你解读为对你的否定或厌恶。你会感到一种强烈的、无法排解的孤独感，主观上认定世界上没有任何人能真正理解你的处境。在某些特定的时刻，你甚至会出现没有明显原因的流泪冲动，或者突然对亲近的人发脾气，事后又感到非常强烈的内疚。整体来看，你原本引以为傲的客观理性思考能力已经暂时下线，你的情绪负荷已经严重超载，整个人处于一种易怒、脆弱且极度内耗的状态之中。

【深层心理机制分析：为什么会变成这样】

这种状态的根本原因，在于你内在的认知功能能量分配彻底失衡，导致你原有的心理信息处理顺序发生了错乱。

在正常且健康的状态下，你的主导功能内倾思考（Ti）负责在内部构建严密的逻辑体系和判断标准，而你的辅助功能外倾直觉（Ne）负责从外部广阔的世界中收集新的信息、新的视角和各种可能性。这两个功能配合得很好，Ne提供新鲜的客观素材，Ti负责加工处理，从而让你能够冷静、高效地解决问题。

但是，在长期的压力、挫折或者过度劳累下，你的心理能量被大量消耗。外倾直觉（Ne）是一个非常消耗能量的功能，为了保存体力，你的大脑强制关闭了Ne。这就导致你的逻辑系统接收不到外界任何新鲜的信息和积极的反馈。

在没有新信息输入的情况下，你的主导功能Ti依然需要工作，它只能向内部去寻找素材。这时，它对接上了你的第三功能内倾感觉（Si）。Si负责记录你过去所有的经验和细节。因为你当前正处于情绪和能量的低谷期，根据记忆提取的规律，Si给你翻找出来的全部都是失败的经历、没有解决的冲突、别人批评你的话语，或者是你犯过的错误。

你的大脑针对这些有偏差的负面经历反复进行逻辑推导，形成了一个死循环。你越是分析，就越觉得过去的错误无法弥补；你越觉得无法弥补，Si就越会提供更多失败的细节来证明你是对的。这就是所谓的Ti-Si Loop（负向循环）。你在这个循环里耗尽了所有的精力，导致你对现实生活中的任何事情都提不起兴趣，也做不出任何有效的行动。

【劣势功能失控的逻辑】

长期的自我批判和精神内耗，把你维持日常理性所需要的心理能量彻底耗尽了。平时被你压抑在潜意识底层的第四功能——也就是劣势功能外倾情感（Fe）——失去了理智的压制，直接跳出来接管了你的行为。这就是所谓的Fe Grip（劣势功能被情绪控制）。

因为你平时很少主动去锻炼和使用Fe，它在处理人际关系和情绪表达时的运作方式是非常原始、粗糙且缺乏分寸的。正常人的Fe是用来感知外部气氛、维护群体和谐的。但在你极度疲惫、Ti完全失效的现在，Fe强行占据了主导地位，迫使你用未经处理、极其直接的情绪去面对外界。

这就导致你表现出了跟平时完全不一样的状态。平时你是一个讲究逻辑、不喜欢表露情绪的人。现在你却变得极度情绪化和非理性。你会突然极其渴望别人的认可和安慰，但同时又觉得别人给的安慰非常虚伪，从而把试图靠近你的人推开。你的情绪会变得非常两极分化，要么强压怒火直到某一个极小的瞬间彻底爆发，要么陷入极度的自怜自艾中无法自拔。你甚至会用一种讨好别人或者过度迎合别人的方式来确认自己是不是被抛弃了，但这种行为做完之后，你又会觉得非常屈辱和疲惫。这是因为你正在用你不擅长的工具处理你最不擅长的问题。

【30天状态恢复与调整计划】

针对目前这种认知功能全面停滞和过载的状态，调整的核心思路非常明确：你绝对不能试图用思考来解决思考造成的问题。你不能再逼着自己去想明白什么大道理，或者立刻去解决某个复杂的工作难题。

恢复正常的顺序必须是：首先通过物理手段降低外部刺激，切断一切引发情绪波动的反馈源；其次，通过被动的行为安抚暴躁的劣势功能Fe，同时稍微唤醒辅助功能Ne；最后，通过极其简单的动手实践，让主导功能Ti和第三功能Si重新在现实客观事物上建立起健康的联系，从而彻底打破负向循环。以下是为你制定的、严格分为三个阶段的30天恢复计划：

【第一阶段：物理隔离与彻底断联（第1-3天）】

【具体行动建议】

在这个阶段，你需要用物理手段强制停止运转。请切断所有不必要的社交联系和工作联系。如果条件允许，请立刻请假休息三天。在这三天内，把手机调成静音模式，关闭所有社交软件的消息通知。屏蔽掉所有平时会让你感到焦虑、有压迫感的人，暂时退出或者静音所有的工作群和闲聊群。

这三天里，绝对不要试图去做任何涉及到未来规划的决定，不要回复任何需要你思考才能给出的信息，也不要强迫自己去打扫卫生或者解决任何实际问题。你的唯一任务就是维持最基本的生理运转条件。饿了就吃最容易获取的食物，困了就睡觉。哪怕你一整天只是躺在床上看着天花板发呆，什么都不做，这也是符合当前阶段调整要求的有效行为。

【阶段目标】

这个阶段的核心目标是把外界的所有压力源和信息源彻底隔绝。因为你的劣势功能Fe现在处于极度过敏的状态，外界的任何一句话、一个眼神，都会被你错误地解读为攻击。所以必须消除这些外部触发点。你需要允许自己现在就是一个毫无生产力、处于绝对停滞状态的普通人。停止跟自己当下的无力感作斗争，不要觉得休息是可耻的。只有切断了外部刺激，你内部耗散能量的速度才会真正慢下来。

【第二阶段：低负荷输入与情绪安抚（第4-10天）】

【具体行动建议】

经过前三天的绝对静音，你的心理防御机制已经稍微恢复了一些弹性。现在可以开始缓慢地接触一些不需要进行逻辑分析的外部信息。这个阶段的绝对禁忌是：千万不要看任何复杂的专业书籍，不要看任何教导你怎么成功、怎么自律的材料，也不要接手任何费脑子的分析性工作任务。

你需要做的是去看一些情节极其简单、不需要猜测结局的电影、电视剧，或者节奏缓慢的自然风光纪录片。你也可以选择玩一些完全不需要跟真人进行社交、不用承受竞技压力的单人电子游戏。比如简单的消除游戏、种田模拟类游戏等。如果天气可以，去公园里找个长椅坐半个小时，只是观察路过的行人和树叶，不去和任何人搭话。

【阶段目标】

这个阶段有两重目标。第一重目标是通过这些简单的、有明确情感导向的影视剧情或者游戏设定，给你的情绪（劣势功能Fe）一个非常安全、不用承担现实后果的出口。当你在看剧或者玩游戏时感受到了情绪的起伏，你的Fe就在被慢慢地安抚和疏导，它就不会再突然在现实生活中爆发。

第二重目标是，这些低强度的视觉、听觉和剧情刺激，能够非常轻微地唤醒你沉睡的辅助功能Ne。新鲜的画面和简单的剧情会慢慢把你的注意力从内部反复咀嚼的负面回忆中拉出来，强制转移到外部的客观事物上。你的大脑开始接收新数据了，内部的死循环就开始出现裂缝了。

【第三阶段：微型动手任务与功能重启（第11-30天）】

【具体行动建议】

到了这个阶段，你的情绪已经相对稳定，不再容易随时崩溃，注意力也有所恢复。你需要开始做一些难度极低、并且能在短时间内立刻看到物理实物结果的动手任务。

具体的选择可以因人而异，但原则是固定的。比如，你可以去拼一个基础款的乐高模型，或者买一个简单的木作拼装套件。你可以照着菜谱去厨房里严格按照步骤切菜、称重、炒出一个简单的菜。如果你对计算机熟悉，去写几十行结构非常简单、运行后能直接看到界面变化的无聊代码。或者拿出一张纸，照着网上的教程画几根简单的线条。

重点在于：不要给自己设定任何宏大的目标，不要要求作品有多完美。你的关注点必须完全放在“动作”和“即时反馈”上。我拧进了一颗螺丝，这个部件就固定住了；我把水烧开了，面条放进去就会变软。每一次动手，都必须在几分钟到半小时内看到具体的物理变化。

【阶段目标】

这个阶段的核心目标是彻底打破Ti-Si Loop。通过实际的操作，你强制你的主导逻辑功能（Ti）停止分析过去的概念，转而去处理眼前的、客观的、具体的物理结构。当你按照说明书去拼装模型或者做菜时，你的记忆功能（Si）会从“提供负面历史记录的来源”，重新变回“指导当下如何正确操作的经验储备”。

在这个动手的过程中，你的Ti在分析图纸，你的Si在核对步骤，两个功能在具体的客观事物上重新建立了健康的配合关系。当你看向你刚刚拼好的模型或者做好的饭菜时，你会获得一个不容置疑的客观事实：你能够掌控当前的局面，你能够产出有条理的结果。这个客观事实会直接推翻你在第一阶段脑补出来的“我一无是处”的错误结论。当认知功能恢复了正常的处理顺序，你的理性思考状态就会全面回归，你也就彻底走出了这次的双重叠加态危机。"""
        },
        "grip": {
            "title": "情绪上头：不用刻意去迎合别人",
            "text": """
Gemini said
【当前心理状态与行为表现评估】

综合你目前的各项测试数据和行为反馈，你现在正处于一种非常典型的、由突发性高压或长期情绪压抑导致的“Grip（劣势功能失控爆发）”状态。在荣格认知功能理论的框架下，这意味着你作为INTP，你最核心的、平时最依赖的理性思考功能已经完全宕机，而你平时极力压抑在潜意识最底层的劣势功能——外倾情感（Fe），突破了理智的防线，全面接管了你的大脑和行为。

这种状态对于一个平时习惯于用严密逻辑来处理所有问题的人来说，是非常陌生且令人恐惧的。你会感觉自己完全变成了另外一个人。你原本引以为傲的客观分析能力、对事物的冷静判断力，在这一刻全部消失了。取而代之的是极度剧烈、混乱且无法控制的情绪波动。你并没有失去理智，而是你的心理能量已经耗尽，你的大脑被迫启动了一套你最不熟悉的备用应急系统来面对外界。这只是一种暂时的功能失调，是你内在心理压力超出承受极限后的一种强制排气反应。

【具体困境与情绪特征】

在日常生活中，处于Grip状态会让你表现出与平时截然相反的反常行为。最明显的特征是，你对人际关系和外界的评价变得极度敏感和脆弱。

正常状态下，你对别人的看法并不太在意，你只在乎事情是否符合逻辑。但在现在这个状态下，别人一个没有及时回复的信息、一个稍微冷淡的眼神，或者一句无心的玩笑话，都会立刻在你心里引发巨大的波澜。你会非常主观地认定别人在讨厌你、排斥你，或者对你感到失望。你会花几个小时甚至几天的时间去反复回想一段普通的对话，试图从中找出你得罪别人的证据。

你不仅会感到被孤立，还会产生一种强烈的、不合理的渴望，去寻求别人的认同和安慰。你会突然对亲近的人倾诉大量的情绪，说出很多平时绝对不会说的话，甚至会用一种近乎讨好的方式去确认对方是否还在乎你。但矛盾的是，当别人真的来安慰你、给你提供情感支持时，你又会立刻觉得对方非常虚伪，或者觉得对方根本没有真正理解你，从而用非常伤人的话语把试图靠近你的人推开。

此外，你还会经历非常剧烈的情绪起伏。你可能会在没有遇到任何明显挫折的情况下，突然感到极度的悲伤，甚至有控制不住流泪的冲动。或者，你会因为一件极其微小的、平时完全不会在意的小事，突然爆发强烈的愤怒，对周围的人大发雷霆。事后，当你的理智短暂回归时，你会对自己的这些情绪化行为感到极度的内疚和羞耻，这种羞耻感又会进一步加重你的心理负担，让你觉得自己彻底失去了控制。你现在被困在一种既渴望被理解、又极度害怕被伤害的混乱情绪中。

【深层心理机制分析：为什么会变成这样】

要理解你为什么会陷入这种完全不受控制的情绪状态，我们需要深入分析你内在认知功能的工作机制。

在你的认知功能结构中，排在第一位的主导功能是内倾思考（Ti），它负责保持冷静、客观和严密的逻辑分析。这是你的核心力量。而排在第四位的劣势功能是外倾情感（Fe），它负责感知他人的情绪、维护人际关系的和谐。因为大脑的能量是有限的，为了保证Ti的高效运转，你的大脑在日常生活中会有意无意地压抑Fe的活动，不让情绪干扰你的逻辑判断。

但是，当你面临超出你处理能力的重大危机、遭遇严重的人际冲突、或者长期从事需要大量情感付出却得不到逻辑回报的工作时，你的主导功能Ti会被过度透支。你一直在试图用逻辑去解决那些根本没有逻辑可言的情绪问题。当你的Ti耗尽了所有的心理能量，再也无法维持正常运转时，它就会彻底崩溃并暂时下线。

当作为防御系统的Ti失效后，原本被压抑在潜意识底层的劣势功能Fe就失去了所有的束缚。它就像是被关了很久之后突然被释放出来一样，带着巨大的、未经处理的原始能量，直接冲到了你的意识表面，强行接管了你的心理控制权。这就是Grip状态产生的根本原因：不是你的情绪变多了，而是你用来控制情绪的理智闸门彻底坏掉了。

【劣势功能失控的逻辑】

当劣势功能Fe接管你的大脑时，它表现出来的运作方式是非常粗糙和极端的。

因为你平时很少主动去锻炼和使用这个功能，所以你的Fe处于一种非常原始的发展阶段。成熟的外倾情感功能可以很自然地理解和照顾别人的感受，并且能够在人际交往中保持适当的边界。但是，你现在爆发出来的Fe，是没有边界感且极其非黑即白的。

在失控的Fe看来，人际关系只有两种状态：要么所有人都要完全接纳我、认可我，要么我就被整个世界彻底抛弃了。它不接受任何中间地带。这就解释了为什么你会对别人的态度如此敏感。因为现在的你，正在用一种极度匮乏和不安的视角去审视周围的所有人。

同时，由于你的逻辑分析功能（Ti）已经下线，你现在完全失去了客观评估事实的能力。当你在情绪崩溃时觉得“大家都觉得我是个没用的人”时，这个结论其实没有任何客观证据支持，它完全是你的劣势功能在极度焦虑下捏造出来的幻觉。但是，因为你的理智不在场，你对这个幻觉深信不疑，并且会根据这个幻觉做出非常极端的反应。比如发送大段情绪化的小作文去质问别人，或者突然拉黑某个朋友，试图通过这种破坏性的行为来提前结束你想象中的被抛弃的过程。你现在的行为逻辑，完全是由一种对失去连接的极度恐惧所驱动的。

【30天状态恢复与调整计划】

针对目前这种劣势功能全面爆发、情绪处于失控边缘的状态，调整的核心思路非常明确：绝对不要试图在这个时候去解决任何人际关系问题，也绝对不要试图用你残留的逻辑去分析你现在的情绪。你现在的情绪是没有逻辑可言的，越分析你会越觉得自己不可理喻，从而陷入更深的羞耻感中。

恢复的顺序必须是：首先通过物理隔离切断所有的人际刺激源，进行紧急的降温处理；其次，通过感官层面的放松和无压力的发泄，让沸腾的情绪自然冷却；最后，通过极其客观的、不涉及人的具体事务，慢慢把你的主导逻辑功能重新唤醒。以下是为你制定的、严格分为三个阶段的30天恢复计划：

【第一阶段：物理隔离与情绪急救（第1-3天）】

【具体行动建议】

在这个阶段，你正处于情绪爆发的最高峰，你的判断力是极其不可靠的。你需要做的是最大限度地减少破坏。

立刻切断所有非必要的人际互动。如果可以，请病假待在家里。在这三天里，不要去回复任何让你感到有压力的微信消息，不要去接任何需要你进行情感回应的电话。如果你感到极其愤怒或者极其委屈，想要给别人发一段很长的话去争论或者道歉，把这段话打在手机备忘录里，然后立刻锁屏，绝对不要发送出去。不要在朋友圈或者任何社交媒体上发表任何带有情绪倾向的文字。

你的任务是允许这些负面情绪在你的体内存在，但坚决不做出任何回应行为。如果你想哭，就拉上窗帘在房间里大哭一场；如果你觉得烦躁，就找个没人的地方大喊几声，或者撕扯一些废纸。不要去问自己“我为什么会这么失态”，不要去评判自己的情绪。接受你现在就是一个情绪极度不稳定的人这个事实。

【阶段目标】

这个阶段的核心目标是止损和情绪泄压。处于Grip状态的人，非常容易在冲动之下做出破坏现有关系或者损害自己职业形象的事情。通过物理上的隔离和强制的社交静音，你可以避免在理智下线的时候说出或做出让你事后极度后悔的举动。同时，允许情绪进行物理层面的发泄，不加评判地接纳它的存在，能够最快速地消耗掉劣势功能Fe爆发带来的原始动能，防止情绪进一步堆积。

【第二阶段：无压力感官放松与身体照顾（第4-10天）】

【具体行动建议】

当最剧烈的情绪冲动过去之后，你会感到一种极其严重的疲惫感和空虚感。这时，你需要调动你的第三功能内倾感觉（Si），通过照顾身体的感官来稳定你的心智。

在这个阶段，把所有的注意力都集中在你的身体需求上。去洗一个很长时间的热水澡，感受水流在皮肤上的温度。去吃一些你平时非常喜欢、口味相对浓郁的热食，不要去管热量和健康配比。换上你觉得最柔软、最舒服的睡衣。把房间的灯光调暗，放一些白噪音或者没有歌词的轻音乐。

在这几天里，你可以进行一些完全没有压力的倾诉。如果你有非常信任、并且能够客观倾听不加评判的朋友，你可以告诉他们你最近状态很差。但在倾诉之前，一定要明确告诉对方：“我只是想把这些话说出来，我不需要你给我任何建议，也不需要你来评判对错。”如果找不到这样的人，你也可以对着手机的录音功能，把脑子里的混乱想法全部说出来，说完就删掉。

【阶段目标】

这个阶段有两重目标。第一重目标是通过具体的感官刺激，把你的注意力从混乱的人际关系想象中拉回到现实的物理躯体上。温暖的水流、好吃的食物，这些切实的物理感受能够给你的潜意识传递一个安全信号，让高度紧张的神经系统逐渐放松下来。

第二重目标是给劣势功能Fe提供一个安全的排气阀。你的Fe现在非常渴望表达和被听见，通过无压力的倾诉或者自我录音，你满足了它的这种渴望，但又没有把它暴露在真实的人际关系风险中。当它把积累的垃圾情绪清空之后，它就会慢慢退回到潜意识的底层，不再强行占据主导位置。

【第三阶段：重启主导功能与逻辑归位（第11-30天）】

【具体行动建议】

到了这个阶段，你的情绪已经基本平复，不再有过激的冲动，但你的主导逻辑功能（Ti）还在沉睡。你需要通过一些完全不涉及人际关系、客观且有固定规律的事务，把它重新唤醒。

你需要去寻找一些纯逻辑的、事物导向的任务来做。比如，如果你擅长修理东西，可以把家里坏掉的小家电拆开，弄清楚它的内部原理并尝试修好它。如果你懂编程，可以去写一段用来整理电脑本地文件的自动化脚本。你也可以去玩一些高度依赖逻辑推理的单机解谜游戏，比如数独，或者极其复杂的城市规划模拟游戏。

这里的关键在于：这些任务必须是完全客观的，不存在任何人类情感的干扰。一个代码跑不通就是跑不通，里面没有任何偏见或者人际冲突；一个零件装反了就是装反了，它不会因为你态度不好而生气。

【阶段目标】

这个阶段的核心目标是让内倾思考（Ti）重新掌权。通过处理这些纯粹的客观问题，你的大脑重新开始使用它最熟悉的逻辑分析工具。当你的Ti发现它可以完美地掌控眼前的物理结构和逻辑代码时，它的自信心就会逐渐恢复。

在这个过程中，你会发现你的思考变得越来越清晰，你不再轻易被情绪牵着鼻子走。当你的主导功能彻底醒来，重新接管了信息处理的最高权限时，那个冷静、客观、理性的你就完全回来了。这时，你再回头去看第一阶段发生的事情，你会觉得那就像是一场荒诞的梦。此时，你已经彻底走出了Grip状态的阴影，恢复到了正常的认知循环之中。"""
        },
        "loop": {
            "title": "越想越乱：出去走走换个脑子",
            "text": """
【当前心理状态与行为表现评估】

综合你目前的各项测试数据和行为反馈，你现在正处于一种被称为“Loop（负向循环）”的心理状态。在荣格认知功能理论的框架下，你目前的评估结果显示，你的外倾辅助功能已经暂时关闭，导致你的心理活动完全局限在内部。具体到你的情况，你正在经历“内倾思考（Ti）与内倾感觉（Si）的负向循环”。

这种状态与彻底失控爆发的叠加态不同。在单纯的Loop状态中，你并没有表现出极度的情绪化，也没有频繁地发脾气或者崩溃。从表面上看，你可能依然显得很平静、很理智，甚至还能维持最基本的生活和工作运转。但是，你的内在实际上处于一种极度停滞和封闭的状态。你的心理能量没有向外流动，而是全部在内部打转。你的大脑正在使用极高的算力，去处理完全没有实际价值的旧信息，导致你陷入了严重的行动瘫痪。

【具体困境与思考特征】

在日常生活中，处于Ti-Si Loop状态会让你表现出非常隐蔽但严重的拖延和抗拒行为。首先，你会发现自己失去了探索新事物的兴趣和动力。面对任何新的任务、新的工作安排或者新的生活提议，你的第一反应不再是好奇，而是排斥。你会本能地觉得这些新东西会带来麻烦，会破坏你现有的安全感。

在面对必须解决的现实问题时，你会陷入一种被称为“过度准备”的假性忙碌中。你会花费大量的时间去查阅资料、收集信息、进行各种可能性的逻辑推导。但是，你永远不会采取实际行动。你总是觉得自己的准备还不够充分，逻辑还不够严密，还需要再思考一下。这种行为本质上是用思考来逃避行动。

你的注意力会不可控制地集中在过去的经历上，尤其是那些失败的、尴尬的或者留有遗憾的经历。你会经常在深夜或者独处的时候，反复回想几年前发生的一件小事，或者自己曾经说过的一句不太合适的话。你的核心逻辑分析能力（Ti）把这些过去的记忆片段（Si）拿出来，一遍又一遍地进行重新分析，试图找出一个完美的解决方案，或者证明当时的自己有多么愚蠢。

此外，你的生活模式会变得极其刻板。为了节省心理能量，你会拒绝任何改变。你会每天吃一样的食物，走同样的路线上下班，反复观看已经看过很多遍的电影或电视剧。你害怕任何不确定性，任何打破你既定常规的突发事件都会让你感到极度烦躁和疲惫。整体来看，你的生活变成了一潭死水，你被困在了自己过去的经验和过度繁琐的内部逻辑之中。

【深层心理机制分析：为什么会变成这样】

这种状态的根本原因，在于你为了防御外界的压力和不确定性，主动切断了大脑获取新信息的通道。

在你处于健康状态时，你的主导功能内倾思考（Ti）负责在内部进行逻辑判断，而你的辅助功能外倾直觉（Ne）负责从外部世界为你收集各种新鲜的视角和可能性。Ne为你提供原材料，Ti负责加工这些原材料。

但是，当你长期处于一个充满挫折、缺乏正向反馈，或者变化过于剧烈导致你无法掌控的外部环境中时，你的大脑会感到极度的疲惫。外倾直觉（Ne）去外部探索是需要消耗大量能量的，并且探索带来的新信息往往伴随着风险。为了保护你不再受到外界的刺激，你的大脑强制关闭了Ne功能。

当Ne被关闭后，你的逻辑加工厂（Ti）就断绝了外部原材料的输入。但是，Ti是一个必须时刻保持运转的功能，它停不下来。既然外部没有新东西进来，它就只能转身向内部去寻找材料。于是，它对接上了你的第三功能内倾感觉（Si）。内倾感觉（Si）是一个庞大的内部数据库，它记录了你过去所有的生活经验、细节和感受。

问题在于，因为你是在压力下进入这种状态的，大脑的记忆提取机制会优先提取那些带有警告意味的负面记录。所以，Si提供给Ti的，全都是你过去做错决定的记录、别人拒绝你的经历，以及各种失败的教训。

【认知功能受阻的逻辑】

当Ti和Si这两个内倾功能开始单独配合时，一个无解的死循环就形成了。

首先，主导功能Ti提出一个问题：“我现在该怎么办？”

接着，第三功能Si从数据库里调取资料，回答说：“根据过去的记录，你上次尝试新方法的时候失败了，并且显得很可笑。”

然后，Ti对这个资料进行严密的逻辑分析，得出一个客观的结论：“既然过去的客观数据证明行动会导致失败，那么为了避免失败，最合理的选择就是不采取任何行动，维持现状。”

这个结论被Si记录下来，变成了新的经验：“今天我没有采取行动，虽然没有进展，但是很安全。”

到了第二天，当Ti再次问“我现在该怎么办”时，Si不仅会提供以前的失败记录，还会提供昨天“不行动很安全”的记录。Ti再次分析，更加坚定地认为不行动才是唯一正确的逻辑。

这就是你陷入停滞的底层逻辑。你并不是在无理取闹，相反，你是在用一种极其严密的逻辑在论证“我为什么不能改变”。你用你最擅长的分析能力，给自己打造了一个坚不可摧的逻辑牢笼。因为整个推导过程完全没有外部新信息（Ne）的参与，所以你在内部完全找不到破局的切入点。你越思考，越觉得过去的错误不可原谅；你越思考，越觉得未来的行动充满风险。在这个过程中，你变得越来越固执，越来越害怕犯错，最终失去了所有前进的动力。

【30天状态恢复与调整计划】

针对目前这种认知功能陷入内部死循环的状态，调整的核心思路非常明确：你绝对无法通过单纯的内部思考来打破这个循环。Ti和Si的结合是非常紧密的，你越是在脑子里想“我该怎么走出来”，你就陷得越深，因为这本身就是在继续使用Ti和Si。

唯一的出路是强制重启被你关闭的辅助功能——外倾直觉（Ne）。你必须通过具体的、物理层面的行动，把新的变量强行塞进你的认知系统里。只有当你的大脑接收到了完全陌生的新数据，旧的逻辑循环才会被打破。以下是为你制定的分为三个阶段的30天恢复计划：

【第一阶段：停止内部反刍与客观现实确认（第1-7天）】

【具体行动建议】

在这个阶段，你的首要任务是打断Ti和Si的不断对话。当你发现自己又开始回想过去的某件尴尬事，或者又开始在脑子里反复推演明天要做的一件小事的每一个细节时，你需要在物理层面上叫停。

你可以直接从椅子上站起来，或者用手拍一下桌子，甚至可以小声对自己说一句“停”。然后，立刻强制你的注意力转移到你身体周围的客观物理环境上。去感受你坐的椅子的硬度，去听窗外的声音，去观察桌子上杯子的纹理。

在这个星期里，不要对自己提出任何长远的规划要求。把每天需要做的事情拆解成极其微小的物理动作。不要去想“我要完成这份报告”，而是去想“我现在要打开电脑，新建一个文档，敲下标题”。只关注眼前的这一个动作，做完这一个，再去想下一个。

【阶段目标】

这个阶段的核心目标是切断负面记忆的持续供给。通过强制把注意力转移到当下的物理现实，你剥夺了内倾感觉（Si）继续向内倾思考（Ti）输送旧数据的机会。你不需要解决任何问题，你只需要让你的大脑知道：现在这一刻，没有发生任何糟糕的事情，过去的经验在这一刻是不起作用的。这能初步降低你大脑的过度防御机制。

【第二阶段：微量新变量导入与打破刻板常规（第8-14天）】

【具体行动建议】

当内部的反刍稍微减少后，你需要开始用极其微小、完全没有任何风险的外部新变量，去刺激你的外倾直觉（Ne）。这里的关键是“零风险”和“打破常规”。

你需要在接下来的七天里，每天刻意改变一到两件生活中的琐事。比如，如果你每天早晨都吃包子，明天早晨去买一根油条；如果你平时总是走同一条路去地铁站，今天故意绕远一点走另一条街道；如果你从来不听古典音乐，今天打开播放器随便听半个小时；去超市买一种你从来没有见过的饮料喝一口。

在做这些事情的时候，不需要去分析这些新事物好不好吃、好不好听、有没有效率。你只需要去“经历”它们。

【阶段目标】

处于Loop状态的你，极度排斥新事物，因为大脑默认新事物代表着危险。这个阶段的目标就是通过这些毫无压力的微小改变，向你的认知系统证明一个事实：输入新信息并不会导致灾难。

当你喝了一口没喝过的饮料，发现虽然难喝但并没有造成什么后果时，你的外倾直觉（Ne）就会得到一次微弱的鼓励。随着这些零风险的新变量不断输入，你的主导功能Ti会发现，原来世界上还有很多不在旧数据库（Si）里的东西。这就为你重新建立向外探索的习惯打下了基础。

【第三阶段：无目的外部信息探索（第15-30天）】

【具体行动建议】

经过前两个阶段的铺垫，你的大脑对新信息的抗拒感已经大大降低。现在，你需要主动去外部世界获取更大规模的新数据。但是，这种获取必须是“无目的”的。

千万不要带着“我要学会某个技能”或者“我要解决某个工作难题”的目的去探索，因为那会立刻唤醒你害怕失败的防御机制。你需要去做一些没有任何标准答案、没有考核压力的事情。

比如，去书店随便拿起一本你完全不懂的领域的杂志翻看；去一个你从来没有去过的公园或者街区闲逛几个小时，仅仅是观察路边的建筑和人群；如果条件允许，去参加一个你完全不熟悉的领域的线下单次体验课，比如陶艺、射箭或者某种简单的手工制作。在做这些事情的过程中，不要去评判自己做得好不好，也不要总结什么深刻的道理，只是单纯地收集视觉、听觉和触觉的新信息。

【阶段目标】

这是彻底打破Ti-Si Loop的最后一步。当你在进行这些无目的的探索时，你的外倾直觉（Ne）被完全激活了。它开始源源不断地把外部丰富多彩、充满随机性的信息输送进你的大脑。

你的主导功能内倾思考（Ti）终于获得了新的原材料。它不再需要去翻找过去的旧账，而是开始忙于处理眼前这些新奇的客观数据。在这个过程中，你对外部世界的兴趣会重新被点燃，你会发现事情并没有你之前推演的那么糟糕和无解。一旦Ti和Ne重新建立了顺畅的合作关系，你就会自然而然地从停滞不前的封闭状态中走出来，恢复到那个能够理性分析外部世界、并对未知保持好奇的正常状态。
"""
        },
        "growth": {
            "title": "状态不错：动手把想法做出来",
            "text": """
Gemini said
【当前心理状态与行为表现评估】

综合当前的测试数据和行为反馈，你目前正处于一种极其良好的认知功能协调期，也就是我们所说的“健康态”。在荣格认知功能理论的框架下，这意味着你作为INTP的四个核心认知功能——内倾思考（Ti）、外倾直觉（Ne）、内倾感觉（Si）和外倾情感（Fe），正在按照最合理的顺序和健康的能量分配比例进行工作。

你目前的心理能量非常充沛且流动顺畅。你不仅没有陷入内耗，反而能够把大脑的算力全部集中在处理外部客观信息和构建内在逻辑上。你的主观感受应该是相对平静的，既没有极度亢奋，也没有陷入低落。你对生活中的大部分事物保持着适度的兴趣，并且具备随时调用理智去解决复杂问题的能力。在这个状态下，你不会觉得日常运转是一件极其吃力的事情，你的大脑运作效率处于最高峰值。

【具体优势与核心竞争力表现】

处于健康态的你，在日常生活和工作学习中会表现出非常明显的行为优势。首先，你的客观分析能力达到了最佳状态。当你面对一个极其复杂、线索杂乱的问题时，你不会被表面现象或者周围人的情绪所干扰。你可以非常冷静地把问题拆解开，剔除掉那些无关紧要的感性因素，直接找到事物内部的核心矛盾和客观规律。

其次，你的学习能力和信息吸收速度非常快。你不会对未知的领域感到恐惧，相反，你会主动去搜寻那些你以前没有接触过的知识。你会发现自己很容易理解那些抽象的理论和复杂的系统运作原理。

此外，在人际关系方面，你现在的表现也是非常得体的。虽然你依然不喜欢过于热闹或者需要大量情感付出的社交场合，但你不再对社交感到强烈的抗拒或焦虑。你可以跟同事、同学或者朋友进行正常的、有逻辑的沟通。在别人需要帮助时，你能够给出非常中肯、理性的建议，并且你的态度是平和友善的。别人会觉得你是一个聪明、讲理且情绪稳定的人。

【深层心理机制分析：各个认知功能的健康协作】

这种健康且高效的状态之所以能够存在，根本原因在于你内在的认知功能建立起了良性的信息处理回路。你的心理防御机制处于放松状态，不需要耗费额外的能量去压抑什么。

在健康状态下，你的心理能量流向是由外向内，再由内向外的顺畅循环。外界的新鲜信息能够顺利地进入你的大脑，经过你内部严密的逻辑加工后，得出客观的结论，然后再把这些结论应用到现实生活中，或者通过平和的交流表达出来。这个过程中没有任何一个功能被过度透支，也没有任何一个功能被强制关闭。

【主导功能与辅助功能的完美配合】

你现在状态好的核心，在于你的主导功能内倾思考（Ti）和辅助功能外倾直觉（Ne）达成了完美的配合。这两个功能是你日常运作的主力。

外倾直觉（Ne）在这个阶段非常活跃且健康。它负责对外开放，时刻从周围的环境、书本、网络以及与他人的交流中收集新的观点、新的可能性和不同的视角。Ne的存在保证了你的大脑不会封闭，它源源不断地为你提供新鲜的客观素材和思考的角度。

当Ne把这些杂乱但新颖的信息收集进来之后，你的主导功能内倾思考（Ti）就开始工作了。Ti负责对这些信息进行极其严格的逻辑检验。它会判断这些新信息是否符合客观事实，内部是否存在逻辑漏洞。如果一条信息经得起推敲，Ti就会把它分门别类地安插进你大脑中已有的知识框架里，让你的知识体系变得更加庞大和严密。如果信息不合理，Ti就会客观地将其剔除。

正是因为Ne不断提供新东西，Ti才有材料可以加工。同时，Ti的严密把控，又让Ne不至于胡思乱想脱离实际。这两个功能在处理问题时极其默契，让你既有广阔的视野，又有严谨的判断。

【第三功能与劣势功能的积极支撑】

在你处于健康态时，你平时不太常用或者不太擅长的第三功能内倾感觉（Si）和劣势功能外倾情感（Fe），并没有给你制造麻烦，反而提供了非常坚实的后勤保障。

你的内倾感觉（Si）现在起到了很好的稳定器作用。它安静地待在后台，为你提供准确的历史数据支持。当Ti和Ne在处理新问题时，Si会适时地调出你过去积累的常识和经验，告诉你哪些方法以前验证过是有效的，从而为你节省大量的试错时间。同时，Si帮助你在日常生活中维持了一个基本的作息规律。你可能养成了一些固定的习惯，比如每天在固定的时间吃饭、固定把东西放在特定的位置。这些看似不起眼的小习惯，极大地减少了你大脑在日常生活琐事上的决策消耗，让你能把宝贵的精力全部留给Ti去进行深度思考。

而你的劣势功能外倾情感（Fe），此时也没有因为受到压抑而暴走。因为你的核心逻辑功能运作得很顺畅，你对自己有充足的信心，这让你对外界有了更多的包容度。所以，你的Fe能够以一种非常健康、低强度的方式运作。你可以感知到周围环境的基本气氛，并且愿意用符合社会常规的礼貌去回应别人。你不会觉得说一句“谢谢”或者对别人微笑是一种虚伪的妥协，你只是把这当作一种维持人际关系正常运转的客观润滑剂。你不去强求深刻的情感共鸣，但也不排斥正常的善意交流。

【状态维持与日常保养建议】

虽然你目前处于非常理想的健康态，但需要明确的是，心理状态是动态变化的。如果没有合理的日常维护，INTP很容易因为外界环境的改变或者能量管理不当，再次滑落到负向循环或者情绪失控的状态中。因此，针对你目前的健康状况，重点不在于“治疗”，而在于“保养”和“能量分配”。以下是为你制定的、旨在长期维持这一健康态的日常运作建议：

【第一方面：信息输入与大脑活跃度管理】

【具体行动建议】

你需要刻意保持对未知领域的好奇心，持续给你的辅助功能Ne喂食。建议你保持每天或者每周阅读的习惯。这里的阅读不局限于你正在从事的专业领域。你可以去了解一些跨学科的知识，比如历史、物理、天文或者计算机科学。如果你觉得看书太累，看高质量的科普视频、听干货类的播客也是很好的方式。

同时，当你产生了一些看似不切实际的念头或者灵感时，不要立刻用逻辑去否定它们。你可以拿个本子或者用手机备忘录把这些零碎的想法记录下来。即使现在不去实现它们，这种记录行为本身也能让你的Ne功能保持活跃和满足。

【维持目标】

这样做的核心目的是防止你的知识体系僵化。INTP的大脑就像是一个需要不断运转的处理器，如果没有新鲜的数据输入，处理器就会开始空转，或者去翻找旧的负面数据，从而引发问题。持续、低压力的泛知识输入，能够保证你的Ne始终处于开启状态，为你提供持续的心理能量，让你始终觉得生活是有趣的、有东西可以研究的。

【第二方面：现实生活的低能耗运转】

【具体行动建议】

你需要极其刻意地利用你的第三功能Si，把你的日常生活“自动化”。尽量减少在吃、穿、住、行这些非核心事物上的选择时间。你可以尝试购买几套款式相近、穿着舒适的衣服轮换穿。你可以固定你的早餐种类，或者制定一个简单的、不需要多想的每周运动计划。

此外，建立一个可靠的外部备忘录系统。不要太相信你的大脑能记住所有需要交水电费、还信用卡或者去拿快递的琐碎日期。把所有的日程安排、截止日期和待办事项都写进手机日历，并设置提前提醒。一旦写下来，就从大脑的内存里把它们删掉。

【维持目标】

INTP的认知能量上限虽然不低，但在处理现实琐事时消耗极快。通过建立固定的日常常规和外部提醒系统，你可以把这些生活琐事对主导功能Ti的干扰降到最低。你不需要每天早晨醒来花费脑力去思考穿什么、吃什么。这种低能耗的现实生活运转模式，能够最大程度地为你节约心理能量，确保你始终有充足的算力去应对真正复杂的逻辑问题和工作挑战。

【第三方面：人际交往与情绪边界维护】

【具体行动建议】

在人际交往中，你要诚实地面对自己精力有限的事实。不要因为现在状态好，就去答应那些超出你能力范围或者需要耗费大量情绪价值的社交请求。保持一个让你觉得舒服的社交圈大小。

当你和别人发生意见分歧时，你可以表达你的逻辑和事实，但如果对方不接受，不要试图去说服对方，更不要去指责对方不讲逻辑。你可以直接终止这个话题。同时，如果别人向你倾诉情绪问题，你可以提供客观的解决方案，但不要强迫自己去共情或者承担对方的负面情绪。如果觉得累了，就坦白告诉对方你需要一个人待一会儿。

【维持目标】

这个方面的建议是为了保护你的劣势功能Fe。虽然你现在状态好，Fe运作正常，但它依然是你认知架构中最脆弱的一环。过度密集的社交、过度卷入他人的是非纠纷，或者试图扮演一个“情绪导师”的角色，都会在短时间内彻底榨干你的能量，直接导致你从健康态掉入情绪失控的深渊。维持明确的情绪边界，用逻辑和礼貌去应对人际关系，而不是用深度的情绪羁绊去应对，是你能够长期保持理性和高效的最关键防线。只要你不被外界的非理性情绪拖垮，你的内在逻辑系统就能一直稳定地运转下去。
"""
        }
    },

    "INTJ": {
        "crisis": {
            "title": "急需调整：允许生活暂时脱离掌控",
            "text": """
【当前心理状态与行为表现评估】

综合当前的各项测试数据和你的行为反馈，你目前正处于由极度高压和持续挫折导致的认知功能全面过载状态。在荣格认知功能理论的框架下，你现在的评估结果为“Loop+Grip”双重叠加态。具体而言，作为INTJ，你正在经历“内倾直觉（Ni）与内倾情感（Fi）的负向循环（Loop）”，同时伴随着“劣势功能外倾感觉（Se）的失控爆发（Grip）”。

这种状态说明，你最核心的执行和规划能力已经完全停摆。你原本用来解决现实问题的外部逻辑架构已经失效，导致你的注意力完全向内收缩，陷入了极其悲观的未来预测和强烈的主观情绪之中。同时，你的大脑为了缓解这种内部的巨大压力，强制启动了你最不擅长的感官冲动机制。你现在不是在正常思考，你的大脑只是在进行极端情况下的能量强制转移。

【具体困境与情绪特征】

在日常生活中，这种双重叠加态会让你表现出极其矛盾且反常的行为模式。首先，你完全失去了把计划落地执行的能力。你的大脑（Ni功能）在不断地向你播放关于未来的负面画面。你坚定地认为接下来的事情一定会失败，所有的努力都是没有意义的。这种对未来的悲观预测让你觉得非常疲惫。

同时，由于内倾情感（Fi）的过度卷入，你把这种对未来的悲观预测转化成了对自我的深度否定和对外界的强烈敌意。你会觉得周围的人都极其愚蠢，或者觉得没有一个人能够理解你的真实想法和核心价值观。你会表现出一种极度的孤傲和防备心理，拒绝听取任何人的客观建议。哪怕别人给你提供了一个具有可行性的解决方案，你也会立刻在脑子里找出一万个理由去证明这个方案最终一定会失败。

在身体和行为层面，劣势功能的爆发会让你做出完全不符合你平时性格的事情。平时的你非常节制、注重长远利益。但在现在的状态下，你会出现严重的感官失控。你可能会无法控制地大量进食高热量食物，或者在深夜毫无目的地疯狂刷短视频，也可能会在网上冲动购买一堆完全不需要的物品。有些时候，你可能会突然开始强迫性地打扫房间，极其苛刻地整理桌面上的每一个小物件，却对真正需要交付的紧急工作视而不见。这种在极度悲观的思考和极度冲动的身体行为之间的拉扯，会让你在事后产生巨大的内疚感，进而加重你的精神内耗。

【深层心理机制分析：为什么会变成这样】

导致你变成现在这种状态的根本原因，在于你的辅助功能外倾思考（Te）被强制关闭了。你内在的认知信息处理链条发生了严重的断裂。

在正常的状态下，你的主导功能内倾直觉（Ni）负责看清事物的本质和制定长远目标，然后你的辅助功能外倾思考（Te）负责把这个目标拆解成具体的、可执行的现实步骤。这两个功能配合，让你成为一个高效的战略家。

但是，当你遭遇了重大的现实挫折、长期的计划被打乱，或者你身处一个完全不讲客观逻辑、只讲复杂人际关系的环境中时，你的外倾思考（Te）会感到极度的无力和疲劳。因为Te需要外界的客观反馈来确认自己的有效性。当外界环境持续给出混乱的反馈时，为了节省能量，你的大脑把负责对外执行的Te功能关闭了。

当Te关闭后，你的主导功能Ni依然在不断地预测未来，但它失去了把预测变成现实行动的工具。这时，Ni直接跳过了Te，对接上了你的第三功能内倾情感（Fi）。Fi是一个极其主观、完全基于个人内部价值观来评判事物的功能。

于是，一个严重的负向循环就开始了。Ni预测到一个糟糕的未来，Fi对这个糟糕的未来产生极度痛苦和排斥的情绪。接着，Ni把Fi产生的这种痛苦情绪当作了客观证据，反过来证明“未来确实非常糟糕，否则我怎么会这么痛苦”。你的大脑在这个没有外部现实参与的内部空间里不断推导，得出的结论越来越极端，越来越脱离实际。你被困在了自己的悲观预测和负面情绪里，彻底切断了与客观现实的联系。

【劣势功能失控的逻辑】

这种内部的Ni-Fi循环会极其快速地消耗你的心理能量。当你内部的压力达到临界点，维持理智的最后一点能量被耗尽时，平时被你严格压制的第四功能——劣势功能外倾感觉（Se）就彻底失控了。

你的外倾感觉（Se）负责处理当下的、具体的物理感官刺激。在正常情况下，你会认为过度关注吃喝玩乐或者眼前的物质享受是浪费时间。但是现在，你的大脑为了把你从Ni和Fi制造的内部精神折磨中拉出来，必须采取最直接、最极端的手段。这个手段就是通过强烈的物理感官刺激，强制中断你的思考。

这就是为什么你会突然暴饮暴食、疯狂购物或者沉迷于低级感官娱乐。这根本不是你自制力变差了，而是你的Se在进行一种粗暴的自救。它通过让你的胃部感到极度撑胀、让你的眼睛被高频闪烁的屏幕画面填满，来强迫你的注意力从内部的悲观预测转移到外部的物理现实上。

但是，因为你平时极少去健康地使用Se功能，它现在的使用方式是毫无节制和毫无策略的。这种失控的感官发泄只能带来极其短暂的麻木。当这种物理刺激结束时，你的主导功能Ni和Fi会重新上线。它们会极其严厉地审视你刚才失控的行为，认为你变得堕落、软弱、失去了对生活的掌控权。这种强烈的自我厌恶会再次加重你的心理负担，把你更深地推入循环和失控的泥潭中。

【30天状态恢复与调整计划】

针对目前这种行动完全瘫痪、感官时常失控的双重状态，你必须明确一个事实：你不可能通过在脑子里构思一个宏大完美的脱困计划来解决目前的问题。你现在的大脑系统不支持你做复杂的规划。

恢复的唯一路径是：首先通过物理手段强行停止感官失控的行为，然后通过极其微小且不需要动脑的现实行动，慢慢把关闭的执行功能（Te）重新激活，让客观事实去打破你脑子里的悲观预测。以下是为你制定的、严格分为三个阶段的30天恢复计划：

【第一阶段：物理隔离与彻底断联（第1-3天）】

【具体行动建议】

在这个阶段，你的首要任务是切断所有导致你进行极端感官发泄的途径，并停止对未来的任何预测。请假休息，如果不能请假，推掉所有非必要的工作和会议。

在物理环境上，你需要做出强制的限制。如果你最近在暴饮暴食，把家里所有的零食和高热量食物全部扔掉或者送人，只保留最基本的食材。如果你在疯狂购物，立刻卸载手机上的所有购物软件，把信用卡从支付软件上解绑。如果你在深夜刷手机，晚上十点之后把手机放在卧室外面的客厅里充电。

这三天里，不要去思考下个月的房租、明年的职业规划或者人生的意义。当你发现自己的脑子又开始预测未来的灾难时，立刻站起来，去喝一杯水，或者去洗把脸。只关注此时此刻这一个小时内你要做的事情。

【阶段目标】

这个阶段的核心目标是强制叫停劣势功能Se的破坏性行为，并阻断外界压力对你的继续消耗。你必须接受自己现在处于一个极其低效和停滞的状态。停止用你以前的高标准来要求现在的自己。只有当你先把物理层面上的混乱和失控制止住，你才有可能省出一点点力气去重启你的认知系统。

【第二阶段：低负荷输入与情绪安抚（第4-10天）】

【具体行动建议】

当感官失控的行为被强制停止后，你需要开始给你的身体和大脑提供健康的、低强度的现实输入。作为INTJ，你需要通过建立微小的外部秩序来安抚你内在的恐慌。

不要去处理任何涉及到复杂人际关系或者需要大量分析的工作。你需要做的是去执行那些有着明确对错标准、只要动手就能看到结果的物理任务。比如，把你的衣柜按照颜色重新挂一遍；去超市按照你写好的购物清单买菜，买完立刻回家；或者对着视频教程，做一组非常基础的身体拉伸动作。

在这个阶段，你依然需要避免过度思考。做这些事情的时候，只关注动作本身。衣服挂正了没有，清单上的东西买齐了没有，拉伸的角度到不到位。

【阶段目标】

这个阶段的目标是用健康的Se输入去替代失控的Se发泄。通过整理物品、基础运动或者按清单购物，你让你的感官接触到了有序的、受控的物理现实。这会让你的大脑收到一个明确的安全信号：外部世界是可以被组织和掌控的。同时，这些不需要动用深层价值观判断的客观小事，可以让你过度疲劳的内倾情感（Fi）得到休息，不再去评判是非对错。

【第三阶段：微型动手任务与功能重启（第11-30天）】

【具体行动建议】

到了这个阶段，你的内部情绪已经相对平静，破坏性的冲动已经消失。现在，你需要正式重启你的辅助功能——外倾思考（Te）。

你需要每天给自己设定一到两个极其微小的、具有建设性的外部任务。这些任务必须是只要你去做，十分钟内就能彻底完成的。比如：回复一封拖延了很久但只需要几句话就能说清楚的工作邮件；把电脑桌面上的乱七八糟的文件归类到一个文件夹里；或者支付一笔水电费。

完成任务后，在你的记事本上或者手机备忘录里，重重地打上一个勾。你需要去注视这个打勾的动作和结果。如果你在执行任务的过程中，脑子里再次冒出“做这件小事根本改变不了整体的糟糕局面”这种念头，直接忽略它，强迫自己先把手头这十分钟的事情做完。

【阶段目标】

这是彻底打破Ni-Fi循环最关键的一步。外倾思考（Te）的运转逻辑是“行动产生结果”。当你完成了一个微小的任务并看到那个打勾的标记时，你就向外部世界输出了一次客观行动，并且获得了一个确定的、客观的结果。

这个小小的客观结果会作为新的数据，被反馈给你的主导功能Ni。Ni会发现：“我刚才预测这封邮件发出去会很糟糕，但实际上什么都没发生，事情被解决了。”当这种客观成功的微小数据积累得越来越多时，Ni就会慢慢修正它之前极其悲观的预测模型。它会意识到，未来并不是完全不可挽回的，只要采取行动，局面是可以被改变的。

当Ni重新信任Te的执行能力，并且Te能够持续在外部世界取得成果时，你的认知处理顺序就恢复了正常。你的内部情绪（Fi）也会因为现实问题的解决而自然消散。此时，你将彻底摆脱停滞和失控，恢复到能够冷静规划并高效执行的正常状态。
"""
        },
        "grip": {
            "title": "太过紧绷：去吃顿好的，或者睡一觉",
            "text": """
【当前心理状态与行为表现评估】

综合你目前的各项测试数据和行为反馈，你现在正处于一种非常典型的、由长期忽视现实物理需求或遭遇重大计划破产而导致的“Grip（劣势功能失控爆发）”状态。在荣格认知功能理论的框架下，这意味着你作为INTJ，你最核心的、平时最依赖的战略预测和长远规划功能已经完全宕机。与此同时，你平时极力压抑在潜意识最底层的劣势功能——外倾感觉（Se），突破了理智的防线，全面接管了你的大脑和身体行为。

这种状态对于一个平时习惯于掌控全局、为了长远目标可以极其克制自己欲望的人来说，是非常陌生且充满破坏性的。你会感觉自己完全失去了自控力，变成了一个只追求眼前感官刺激的陌生人。你原本引以为傲的客观分析能力、对事物发展趋势的精准判断力，在这一刻全部消失了。取而代之的是极度剧烈、混乱且无法控制的物理冲动和对现实细节的强迫性关注。你并没有失去理智，只是你的心理能量已经耗尽，你的大脑被迫启动了一套你最不熟悉的、基于纯粹物理感官的备用应急系统来面对外界。这只是一种暂时的功能失调，是你内在心理压力超出承受极限后的一种强制排气反应。

【具体困境与行为特征】

在日常生活中，处于Grip状态会让你表现出与平时截然相反的反常行为。最明显的特征是，你出现了严重的感官失控和对现实物质的强迫性依赖。

正常状态下，你对周围的物理环境并不太在意，你认为食物只是维持身体运转的燃料，衣服只要整洁就可以，你的注意力永远在未来的计划和脑子里的抽象概念上。但在现在这个状态下，你对物理感官的刺激产生了极其强烈的、不合理的渴望。

具体表现在，你可能会无法控制地大量进食，尤其是高糖、高脂肪或者口味极重的食物。你吃东西不再是为了填饱肚子，而是为了感受咀嚼和吞咽的物理动作，甚至会吃到胃部极度不适才停下来。你可能会在深夜毫无目的地疯狂滑动手机屏幕，看那些毫无营养的短视频，仅仅是为了让高频闪烁的画面和吵闹的声音填满你的视觉和听觉。你还可能会在网上冲动购买大量你根本不需要的实体物品，你在乎的不是物品本身的价值，而是点击付款和拆开快递那一瞬间的物理快感。

此外，你还会表现出对周围物理环境细节的强迫性关注。你平时可以容忍桌面有些凌乱，只要不影响工作效率就行。但现在，你可能会突然花上几个小时去清理房间里的每一个死角，把书本按照严格的高度排列，把桌面上的笔平行摆放。你会把所有的精力都耗费在这些毫无意义的物理细节上，却对真正需要交付的紧急工作或者严重超期的重要任务视而不见。

事后，当你的理智短暂回归时，你会对自己的这些失控行为感到极度的内疚、自责和强烈的自我厌恶。你会觉得自己变得极其软弱、堕落，完全丧失了对生活的掌控权。这种强烈的羞耻感又会进一步加重你的心理负担，让你为了逃避这种痛苦，再次转身投入到新一轮的感官发泄中，形成一个极具破坏性的行为闭环。

【深层心理机制分析：为什么会变成这样】

要理解你为什么会陷入这种完全不受控制的感官冲动状态，我们需要深入分析你内在认知功能的工作机制以及它们之间的制衡关系。

在你的认知功能结构中，排在第一位的主导功能是内倾直觉（Ni），它负责在内部构建宏大的愿景、看清事物的本质并进行长远的战略预测。排在第四位的劣势功能是外倾感觉（Se），它负责处理当下的、具体的、外部的物理感官刺激，比如颜色、声音、味道和当下的身体动作。

内倾直觉（Ni）和外倾感觉（Se）在处理信息的方式上是完全对立的。Ni要求你脱离当下，去看遥远的未来；而Se要求你放弃思考，去感受此时此刻的物理现实。因为大脑的能量是有限的，为了保证主导功能Ni的高效运转，你的大脑在日常生活中会有意无意地压抑劣势功能Se的活动。你会习惯性地忽略身体的疲惫、忽略周围环境的变化，强迫自己把所有的精力都集中在脑海中的长远目标上。

但是，这种压抑是有限度的。当你长期处于极高压的工作环境中，连续几个月甚至几年都没有让身体得到真正的休息；或者当你投入了巨大心血、经过严密推演的长期计划突然遭遇了不可抗力的客观现实打击，宣告彻底失败时，你的主导功能Ni会遭受重创。你的大脑会发现，无论你怎么预测未来，现实总是会脱离你的掌控。此时，Ni消耗了所有的心理能量，再也无法维持正常运转，它彻底崩溃并暂时下线了。

当作为最高指挥官的Ni失效后，原本被压抑在潜意识底层的劣势功能Se就失去了所有的束缚。它带着巨大的、长年累积的原始能量，直接冲到了你的意识表面，强行接管了你的身体和行为控制权。这就是Grip状态产生的根本原因：不是你的自制力变差了，而是你用来控制物理冲动的最高级认知系统彻底停摆了。

【劣势功能失控的逻辑】

当劣势功能Se接管你的大脑时，它表现出来的运作方式是非常粗糙、极端且缺乏长远考虑的。

因为你平时很少主动去健康地使用这个功能，你的Se处于一种非常原始和饥渴的状态。成熟的外倾感觉功能可以很自然地享受当下的生活，品尝美食，进行适度的体育锻炼，并且能够在感官享受和长远利益之间保持平衡。但是，你现在爆发出来的Se，是没有任何节制和策略可言的。

在失控的Se看来，处理极度痛苦和焦虑的唯一方式，就是用更强烈的外部物理刺激来强行覆盖大脑内部的思考。它不关心明天会怎么样，它只关心现在这一秒钟的身体感受。所以它强迫你吃下过量的食物，因为胃部的撑胀感可以让你暂时忘记计划失败的痛苦；它强迫你疯狂购物，因为物质占有的快感可以短暂填补你内心的空虚；它强迫你过度关注排列物品的物理细节，因为控制这些小物件，能让你产生一种“我还在掌控现实”的虚假安全感。

由于你的主导预测功能（Ni）和辅助执行功能（Te）都已经下线，你现在完全失去了评估行为后果的能力。你不再去计算买这些东西会透支多少信用卡，也不再去考虑吃这么多垃圾食品会对身体造成什么不可逆的损伤。你现在的行为逻辑，完全是由一种对内部精神痛苦的极度逃避和对外部物理刺激的极度渴求所驱动的。你正在用一种极其低效且极其伤害自己的方式，试图把你的注意力从崩溃的内部世界强行拉回到外部的现实世界。

【30天状态恢复与调整计划】

针对目前这种劣势功能全面爆发、感官处于失控状态的情况，调整的核心思路非常明确：你绝对不能在这个时候试图通过制定新的长远计划来约束自己。你现在的大脑系统完全不支持任何关于未来的抽象思考。你越是逼迫自己去思考长远目标，你的内部压力就会越大，Se的爆发就会越猛烈。

恢复的顺序必须是：首先通过极其强硬的物理手段切断所有破坏性的感官刺激源，强制终止失控行为；其次，通过健康、低强度的物理接触，有意识地安抚和满足Se的现实需求；最后，通过极其微小且能立刻看到客观结果的现实任务，慢慢把你的执行功能和预测功能重新唤醒。以下是为你制定的、严格分为三个阶段的30天恢复计划：

【第一阶段：物理障碍设置与感官强制切断（第1-3天）】

【具体行动建议】

在这个阶段，你的判断力和自控力是完全不可靠的，你无法通过意志力来对抗感官冲动。你需要做的是在物理环境上制造极其强硬的阻断。

立刻切断所有导致你进行极端感官发泄的途径。如果你最近在暴饮暴食，请立刻把你住所里所有的高热量零食、含糖饮料全部打包扔进楼下的垃圾桶。如果你在疯狂购物，立刻注销或者卸载你手机上所有的电商应用，把所有的支付密码交给一个你绝对信任的现实朋友，或者直接把信用卡锁进抽屉的最深处。如果你沉迷于短视频或者游戏，请把家里的路由器电源拔掉，或者把手机交给家人保管，自己只留一个只能打电话的老年机。

这三天里，不要试图去思考你为什么会变成这样，也不要对自己的失控行为进行任何复盘。当你发现自己的感官冲动再次袭来，想要去买东西或者吃东西时，立刻去喝一大杯温水，然后躺在床上强迫自己闭上眼睛。你的唯一任务就是通过物理隔离，强制停止那些正在损害你身体和财务的行为。

【阶段目标】

这个阶段的核心目标是强行止损和阻断破坏性行为。处于Grip状态的人，必须首先被剥夺作恶的物理条件。通过设置不可逾越的物理障碍，你强制你的身体停止对高强度刺激的依赖。这会让你在短期内感到极度的烦躁、空虚甚至身体上的不适，但这都是正常的戒断反应。你必须忍耐过去，只有把这种极端的物理冲动硬生生地按住，你才有可能进入下一步的调整。

【第二阶段：健康感官输入与微型物理秩序（第4-10天）】

【具体行动建议】

当最剧烈的冲动和戒断反应稍微平息之后，你需要开始主动、有意识地给你的劣势功能Se提供健康的、低强度的物理输入。你要学会在不带任何破坏性的前提下，安全地与现实物理世界接触。

在这个阶段，把你的注意力全部集中在最基本的身体维护上。每天保证充足的睡眠，按时吃三顿成分简单的热饭。在吃饭的时候，不要看手机，不要想工作，只关注你嘴里食物的物理质感和温度。

每天安排至少四十分钟的户外步行。注意，是步行，不是为了减肥的剧烈运动。在走路的时候，不要戴耳机，不要听任何播客或者音乐。强迫你的眼睛去观察路边的树叶是什么形状，去观察地面上的砖块是什么颜色，去感受风吹在脸上的温度。

此外，你可以每天花二十分钟的时间，有意识地清理一个非常小的物理区域，比如你的书桌桌面或者洗手台。在做这些动作时，告诉自己：“我现在正在整理现实，现实是可以被我安排妥当的。”但切记，时间一到立刻停止，不要让它演变成强迫症。

【阶段目标】

这个阶段有两重目标。第一重目标是用健康的物理接触去满足Se的渴望。你的Se现在非常需要感知现实，通过专心吃饭、户外步行和简单的物理整理，你给它提供了一个安全的出口。当它得到了正常的满足后，它就不会再通过暴饮暴食或者疯狂购物来引起你的注意。

第二重目标是帮助你的大脑重新建立与客观物理世界的健康连接。过去你过度忽略身体，现在你通过这些具体的动作，向你的神经系统确认：当下是安全的，物理世界并不是只有破坏和失控，它也可以是平静和有序的。这能够极大地缓解你内在的焦虑感。

【第三阶段：主导功能重启与战略归位（第11-30天）】

【具体行动建议】

到了这个阶段，你的感官冲动已经基本消失，生活节奏恢复了基础的平稳。现在，你需要通过具体的执行动作，把你断线的辅助功能外倾思考（Te）和主导功能内倾直觉（Ni）重新拉回工作状态。

你需要开始做一些有明确客观结果、需要极少量逻辑判断的现实任务。不要去制定一年的宏大计划，只去制定明天一天的待办清单。这个清单上的任务必须是非常具体的动作。比如：“明天上午十点，把那份文档的错别字修改完并发送出去”或者“明天下午两点，去银行把那笔款项转掉”。

把你写下的任务认真执行，并且在完成的那一刻，用笔在纸上重重地划掉它。你需要去看着这个任务被划掉的物理现实。如果在执行的过程中，你脑子里又冒出“做这些小事没用，大局已经完了”的悲观想法，立刻用手掐一下自己的手腕，用短暂的物理痛觉打断这个想法，然后继续做手头的事。

【阶段目标】

这个阶段的核心目标是让你的执行和预测功能重新掌权。外倾思考（Te）的运转依赖于外部的客观反馈。当你完成了一个具体的任务，并看到了它被解决的客观结果时，你的Te就获得了一次成功的运转经验。

这种客观成功的微小数据会不断向上反馈给你的主导功能Ni。你的Ni会逐渐发现，虽然之前的宏大计划失败了，但当下的现实依然可以通过具体的行动去改变和掌控。随着这种正向反馈的积累，Ni的信心会逐渐恢复。它会重新开始运转，去构建新的、更加切合实际的未来规划。当你的预测能力和执行能力重新结合，劣势功能Se就会安静地退回到潜意识中去。此时，那个冷静、克制、极具长远眼光的你，就彻底回归了。
"""
        },
        "loop": {
            "title": "想得太多：事情其实没那么糟糕",
            "text": """
Gemini said
【当前心理状态与行为表现评估】

综合你目前的各项测试数据和行为反馈，你现在正处于一种被称为“Loop（负向循环）”的心理状态。在荣格认知功能理论的框架下，你目前的评估结果显示，你的外倾辅助功能已经被强制关闭，导致你的心理活动完全局限在内部。具体到你作为INTJ的情况，你正在经历“内倾直觉（Ni）与内倾情感（Fi）的负向循环”。

这种状态与彻底失控爆发的Grip状态完全不同。在单纯的Loop状态中，你并不会表现出明显的感官失控或者极度的情绪暴躁。从外部表现来看，你甚至比平时显得更加安静、孤僻和冷漠。你依然能够维持最基本的生活运转，别人很难立刻察觉到你的异常。但是，你的内在实际上处于一种极度封闭和偏执的状态。你的大脑把所有的注意力都撤回到了内部世界，完全切断了与外部客观事实和逻辑的联系。你正在使用极高的脑力去处理完全没有实际现实依据的主观预测和负面情绪，导致你陷入了极其严重的行动瘫痪。

【具体困境与思考特征】

在日常生活中，处于Ni-Fi Loop状态会让你表现出非常隐蔽但极具破坏性的固执和防御行为。首先，你会发现自己完全丧失了去执行具体任务的动力。面对工作或生活中的问题，你的第一反应不再是去寻找解决步骤，而是直接在脑子里判定这件事情没有任何意义。

你会对未来产生一种极其笃定且毫无根据的悲观预测。你坚信接下来的发展一定会非常糟糕，所有的努力最终都会被证明是白费力气。当你身边的同事或者朋友试图给你提供一些客观的建议或者事实数据时，你会表现出极度的抗拒。你会立刻在脑子里挑出对方话语里的漏洞，主观上认定对方根本不懂事情的本质，或者认为对方的价值观与你背道而驰。你拒绝听取任何外部的声音，认定全世界只有你一个人看透了事情的真相，而这个真相是极其灰暗的。

你的注意力会不可控制地集中在自我价值的内部审查上。你会花费大量的时间独处，在脑子里反复推演某些极其抽象且负面的概念，比如人际关系的虚伪、所处环境的不可救药，或者自己内心的某种缺失感。你最核心的预测能力（Ni）把这些内部产生的负面情绪（Fi）当成了唯一的参考资料，一遍又一遍地进行重新组合，最后得出一套只在你脑子里成立的、极其偏执的阴谋论或者悲观定论。

此外，你的社交意愿会降到冰点。为了避免外部世界干扰你内部的这套悲观逻辑，你会主动切断大部分的人际交往。你觉得和别人沟通不仅非常疲惫，而且完全是在浪费时间。整体来看，你的生活变成了一个完全封闭的黑盒子，你被困在了自己对未来的负面预测和对外界的强烈不信任之中。

【深层心理机制分析：为什么会变成这样】

这种状态的根本原因，在于你为了防御外界的混乱和无效反馈，主动切断了大脑与外部客观现实对接的通道。

在你处于健康状态时，你的主导功能内倾直觉（Ni）负责在内部洞察事物的本质并制定长远目标，而你的辅助功能外倾思考（Te）负责在外部世界收集客观数据、制定执行步骤并验证目标的有效性。Ni为你提供方向，Te负责铺设通往目标的现实轨道。

但是，当你长期处于一个缺乏客观标准的外部环境中，或者当你制定的严密计划在现实中因为其他人的极其不专业而屡次受挫时，你的大脑会感到极度的疲惫。外倾思考（Te）去外部组织和执行是需要耗费能量的，尤其是在遇到阻力时。为了保护你不再受到外部现实的反复打击和消耗，你的大脑选择了一种极端的自我保护方式：它直接关闭了负责对外执行和验证的Te功能。

当Te被关闭后，你的战略预测中心（Ni）就断绝了外部客观数据的输入。但是，Ni是一个必须时刻保持运转的功能，它必须不断地去预测和洞察。既然外部没有事实数据进来，它就只能转身向内部去寻找材料。于是，它直接对接上了你的第三功能内倾情感（Fi）。内倾情感（Fi）是一个完全基于个人主观价值观和极其私密的个人情绪来进行判断的功能。

问题在于，因为你是在遭受现实挫折和压力下进入这种状态的，你内部的情绪底色是非常灰暗的。所以，Fi提供给Ni的，全都是对挫折的痛苦感受、对他人不讲逻辑的愤怒，以及对自己不被理解的委屈。

【认知功能受阻的逻辑】

当Ni和Fi这两个内倾功能开始单独配合时，一个完全脱离现实的死循环就彻底形成了。

首先，主导功能Ni提出一个预测：“接下来这个项目或者这段关系会怎么发展？”

接着，第三功能Fi根据内部的受伤体验给出回答：“这里的人都不讲理，我的价值观在这里得不到任何尊重，这让我感到极度反感和痛苦。”

然后，Ni对这个主观情绪进行深度加工，得出一个看似看透本质的结论：“既然我感受到了如此强烈的排斥和痛苦，这就证明了整个环境的底层逻辑是极其恶劣的。因此，未来的结果必定是全盘失败，任何现实的挽救行动都是对自我价值观的违背。”

这个结论被Fi接收后，会进一步加深你的痛苦和孤傲感，让你觉得“我果然是对的，外界确实不值得我付出任何努力”。

到了第二天，当Ni再次进行预测时，它不仅会参考之前的判断，还会把Fi新产生的这份痛苦作为更加确凿的证据。Ni再次分析，更加坚定地认为外界是充满敌意的，不采取任何行动才是保护自己核心价值的唯一方式。

这就是你陷入停滞并且变得极其固执的底层逻辑。你并不是在发泄情绪，你是在用你最强大的洞察力，给自己编织一套坚不可摧的悲观理论。你用内部的情绪去证明内部的预测，然后又用内部的预测去强化内部的情绪。因为整个推导过程完全没有外部客观数据（Te）的参与和纠错，你觉得自己的逻辑天衣无缝。你越推演，越觉得别人愚蠢；你越推演，越觉得没有必要去采取任何现实行动。最终，你彻底失去了在现实世界中解决问题的能力。

【30天状态恢复与调整计划】

针对目前这种认知功能陷入内部死循环、完全排斥客观事实的状态，调整的核心思路非常明确：你绝对无法通过在脑子里把事情想通来打破这个循环。Ni和Fi的结合会排斥一切内部的自我反驳。你越是在脑子里试图说服自己乐观一点，你就陷得越深，因为这依然是在使用内倾功能打转。

唯一的出路是强制重启被你关闭的辅助功能——外倾思考（Te）。你必须通过具体的、涉及外部物理现实的客观行动，把冷冰冰的事实数据强行塞进你的认知系统里。只有当你的大脑接收到了不可辩驳的客观结果，旧的悲观预测链条才会被打断。以下是为你制定的分为三个阶段的30天恢复计划：

【第一阶段：停止内部推演与现实阻断（第1-7天）】

【具体行动建议】

在这个阶段，你的首要任务是打断Ni和Fi的不断对话。当你发现自己又开始对某个还没有发生的事情进行毫无根据的负面预测，或者又开始在脑子里审判某个人的价值观有多么糟糕时，你需要在物理层面上叫停这种行为。

你可以直接站起来走动，去洗个冷水脸，或者强制自己大声读出一段没有任何情感色彩的产品说明书。立刻强制你的注意力转移到没有任何主观判断空间的客观事物上。去算一笔账，去核对一下上个月的账单明细，或者去背诵几个毫无关联的英语单词。

在这个星期里，绝对不要去思考任何关于人生意义、未来发展或者人际关系本质的问题。把你每天的注意力限制在最基础的物理生存层面上。不要去问“为什么会这样”，只去问“现在几点了”以及“我该做哪一件具体的事”。

【阶段目标】

这个阶段的核心目标是切断主观情绪向预测中心供电的链条。通过强制把注意力转移到毫无情绪波澜的客观数据上，你剥夺了内倾情感（Fi）继续向内倾直觉（Ni）输送负面感受的机会。你不需要去证明你的预测是错的，你只需要让大脑停止预测。只要大脑不再继续编织那套悲观的理论，你内部的紧绷感就会出现松动。

【第二阶段：客观数据收集与微小执行（第8-14天）】

【具体行动建议】

当内部的无休止推演稍微停歇后，你需要开始用极其微小、并且完全客观的外部任务，去刺激你的外倾思考（Te）。这里的关键是“只讲客观事实”和“立刻看到结果”。

你需要在接下来的七天里，每天刻意去执行两到三个完全不需要动用任何价值观判断的机械性任务。比如，去把你的书架按照书名首字母的拼音顺序重新排列一遍；打开电脑，把一个混乱的Excel表格里面的数据按照固定的规则进行清洗和排版；或者去组装一个简单的收纳柜，严格按照说明书上的每一个步骤去拧螺丝。

在做这些事情的时候，禁止去思考这些事情对你的未来有没有帮助，也禁止去评判这些事情是否符合你的身份。你只需要去执行规则，并确认结果是否符合规则。

【阶段目标】

处于Loop状态的你，极度排斥外部行动，因为大脑默认外部行动会被别人的愚蠢或者不可控的因素破坏。这个阶段的目标就是通过这些只涉及死物、完全受规则控制的客观任务，向你的认知系统证明一个事实：按照客观逻辑去执行动作，就必定会得到一个可控的客观结果。

当你把表格排版得整整齐齐，发现没有任何人际关系或者主观情绪能够干扰这个结果时，你的外倾思考（Te）就会得到一次微弱的唤醒。随着这些没有情绪风险的客观结果不断产生，你的主导功能Ni会发现，外部世界并不是只有混乱和失败，有些东西是可以通过纯粹的逻辑去掌控的。这就为你重新建立对外执行的信心打下了基础。

【第三阶段：外部秩序重建与全面行动（第15-30天）】

【具体行动建议】

经过前两个阶段的铺垫，你的大脑对外部客观事实的抗拒感已经大大降低，Te功能已经处于待机状态。现在，你需要主动把它应用到你真实的日常生活和工作中去。

你必须开始使用外部工具来强制管理你的行为。买一个实体的笔记本或者使用一个界面极其简单的待办事项软件。每天晚上，写下明天必须完成的三项具体工作。这三项工作必须是有着明确的衡量标准的。不要写“改善和某某的关系”，要写“明天下午三点前，把修改好的方案发送给某某，并确认对方收到”。

到了第二天，不要去管你心里愿不愿意做，也不要去预测做完之后对方会是什么反应。你只需要把你写下来的那句话当作一个没有感情的机器指令，去执行它。做完之后，在那个待办事项上重重地划一根线。你需要去凝视这根代表着事情已经被客观解决的线条。

【阶段目标】

这是彻底打破Ni-Fi Loop的最后一步。当你在强制执行这些外部指令时，你的外倾思考（Te）被完全激活了。它重新承担起了把内部想法转化为外部现实结果的责任。

你的主导功能内倾直觉（Ni）终于重新获得了来自外部的客观反馈数据。它不再需要去翻找内部的痛苦情绪，而是开始忙于处理眼前这些被你亲手解决掉的现实问题。当Ni看到那个被划掉的待办事项时，它会被迫承认：之前那个“所有努力都没有意义”的预测是错误的。一旦客观事实推翻了内部的主观定论，Ni和Te就会重新建立起健康的合作关系。你的情绪（Fi）也会因为现实秩序的恢复而自然退回到后台。此时，你将彻底走出停滞不前和偏执封闭的死循环，恢复到那个能够冷静面对现实、制定有效策略并高效执行的正常状态。
"""
        },
        "growth": {
            "title": "步入正轨：把心里的计划落实下来",
            "text": """
Gemini said
【当前心理状态与行为表现评估】

综合你目前的各项测试数据和日常行为反馈，你现在正处于一种认知功能运作极其顺畅、心理能量分配极其合理的理想状态，也就是我们通常所说的“健康态”。在荣格认知功能理论的框架下，这意味着你作为INTJ的四个核心认知功能——内倾直觉（Ni）、外倾思考（Te）、内倾情感（Fi）和外倾感觉（Se），完全按照它们最健康的顺序和比例在工作。

你现在的心理系统没有任何内部损耗。你主观上的感受应该是极其清晰、专注且充满掌控感的。你既没有陷入对未来的无端恐慌，也没有受到感官失控的困扰。你的大脑算力被完全集中在最有价值的地方：看清事物的本质规律，并把这些规律转化为现实世界中实实在在的成果。在这个状态下，你不会觉得每天的生活和工作是在应对麻烦，而是把它们当成一个个可以被拆解、被客观解决的具体项目。你现在的运作效率处于你个人能力的最高峰。

【具体优势与核心竞争力表现】

处于健康态的你，在工作、学习和日常生活中会表现出极其明显的行为优势。首先，你的战略规划和落地执行能力达到了完美的统一。当你接手一个极其复杂、长期的任务时，你不会感到畏惧或混乱。你可以非常冷静地在一大堆杂乱无章的信息中，一眼看出最核心的问题在哪里。你能迅速在脑子里生成一个指向最终结果的清晰路线图。

更重要的是，你现在完全具备把这个路线图变成现实的能力。你不再停留在脑子里的空想，你会立刻着手制定具体的步骤、时间节点和衡量标准。你不仅知道第一步该做什么，你还会在第一步做完之后，根据客观的反馈立刻调整第二步的做法。你的行动力极强，并且这种行动力是带有明确目的性的，没有任何多余的动作。

在人际关系和沟通方面，你现在的表现非常直接且高效。你不会去过度揣测别人的情绪，也不会因为别人对你有不同的看法而感到被冒犯。在工作场合，你只关注事情能不能解决、逻辑对不对。你可以用极其精炼、客观的语言把你的要求和计划传达给别人。如果别人犯了错，你会直接指出错误的事实并给出修改方案，而不会带入个人的情绪指责。别人会觉得你是一个极其可靠、讲道理且专业能力极强的人。虽然你依然不喜欢无意义的闲聊，但你现在能够为了达成某个客观目标，得体地去进行必要的社交沟通，你把这视作一种解决问题的常规工具，而不会觉得它是一种心理负担。

【深层心理机制分析：各个认知功能的健康协作】

这种极其高效且稳定的状态之所以能够维持，根本原因在于你内在的认知功能建立了一个良性的、不断向外输出并获取反馈的信息处理回路。你的心理防御机制处于完全放松的状态，你不需要耗费额外的精力去压抑任何负面情绪或冲动。

在健康状态下，你的心理能量流向是极其顺畅的。你的大脑内部产生了一个长远的想法，这个想法立刻被转化为外部的实际行动，行动产生了客观的结果，这个结果又反过来证明了你的想法是正确的。整个过程中，没有任何一个功能被过度透支，也没有任何一个功能被强制关闭或者被迫接管不属于它的工作。

【主导功能与辅助功能的完美配合】

你现在状态极佳的核心，在于你的主导功能内倾直觉（Ni）和辅助功能外倾思考（Te）达成了极其默契的配合。这两个功能是你日常运作的绝对主力，它们现在的合作是毫无阻碍的。

你的主导功能内倾直觉（Ni）在这个阶段非常清晰且稳定。它安静地在后台运行，不断地整合你收集到的所有信息，去预测事物未来的发展趋势。它为你提供了一个极其笃定的大方向和最终目标。因为你处于健康态，Ni现在的预测完全是基于客观事实的，而不是基于焦虑和恐惧的，所以它的预测结果非常准确且具有前瞻性。

当Ni给出了目标之后，你的辅助功能外倾思考（Te）立刻接手工作。Te负责对外部世界进行组织和控制。它把Ni提出的那个遥远且抽象的目标，硬生生地拆解成今天下午要打的三个电话、明天要写的两页文档、以及下周要核对的一份数据。Te把你脑子里的想法变成了外部世界可以被衡量和操作的具体事物。

这两个功能的配合构成了一个无懈可击的循环。Ni负责“看”，Te负责“做”。Te在做的过程中，会不断遇到外部现实的反馈。比如一个方法行不通，或者一个数据不准确。Te会把这些客观的错误数据立刻送回给脑子里的Ni。Ni接收到这些新数据后，会立刻修正它对未来的预测模型，然后给Te下达新的、更准确的指令。正是因为有了Te在外部世界不断地试错和确认，你的Ni才不会陷入偏执的脱轨状态；也正是因为有了Ni在内部指引方向，你的Te才不会变成一个像无头苍蝇一样只知道瞎忙的机器。

【第三功能与劣势功能的积极支撑】

在你处于健康态时，你平时深藏不露的第三功能内倾情感（Fi）和劣势功能外倾感觉（Se），不仅没有给你制造任何麻烦，反而为你提供了非常关键的内部动力和现实支撑。

你的第三功能内倾情感（Fi）现在起到了极其重要的指南针作用。它不再是那个在受挫时让你感到极度痛苦和自我怀疑的源头。在健康状态下，Fi为你所有的努力提供了一个最底层的意义支撑。它让你非常清楚自己正在做的事情是符合你个人核心价值观的。当你为了一个长远目标而加班熬夜时，你并不觉得委屈，因为你的Fi明确地告诉你：这件事是我真心认可的，它对我个人的内在成长有极大的价值。这种坚定的内部认同感，让你在面对外部的困难和不理解时，能够保持一种极其平静的定力。你不需要别人的夸奖，你自己的Fi就已经给了你足够的自我肯定。

而你的劣势功能外倾感觉（Se），此时也处于一种非常安全和受控的状态。它不再像失控时那样强迫你去暴饮暴食或者疯狂购物。在健康状态下，Se能够以一种极低强度、极其有益的方式参与你的生活。它让你能够在高强度的脑力劳动之后，真正地放松下来去享受一下物理世界。你可以在周末花两个小时去公园里走走，切实地感受一下阳光和空气；或者自己动手做一顿成分简单的饭菜，体会切菜和烹饪的物理过程。这些适度的感官活动不仅没有消耗你，反而成了你清空大脑内存、恢复心理能量的最佳方式。

【状态维持与日常保养建议】

虽然你目前处于非常理想的健康态，执行力极强，情绪极其稳定，但作为INTJ，你极其容易因为过度投入工作、忽略现实反馈或者长期压抑个人感受，而再次滑落到偏执的内部循环或者感官失控的状态中。因此，针对你目前的健康状况，重点在于如何合理地分配精力，以及如何刻意地维护这条健康的认知回路。以下是为你制定的、旨在长期维持这一健康态的日常运作建议：

【第一方面：外部事实与执行标准的持续输入】

【具体行动建议】

你需要刻意保持你大脑与外部客观现实的对接状态。在日常工作和生活中，不管你脑子里的想法有多么宏大和完美，你都必须强迫自己把它拆解成可以立刻动手的具体步骤。不要允许自己连续三天只在脑子里思考而不去碰任何实际的工具。

当你遇到问题时，不要试图在脑子里通过推演来找到唯一正确的完美答案。你需要去外部寻找客观的参考标准。去查阅行业内已有的数据报告，去参考别人的失败案例，或者直接动手做一个成本极低的测试版去试错。让客观发生的事实来告诉你对错，而不是让你脑子里的预测来判定对错。

【维持目标】

这样做的核心目的是防止你的辅助功能Te生锈，避免你再次掉入只有Ni和Fi参与的内部死循环。只要你始终保持“用客观数据说话”和“用实际行动验证”的习惯，你的大脑就不会脱离现实。不断产生的外部结果，无论好坏，都是维持你整个认知系统健康运转的必需燃料。

【第二方面：个人原则与现实妥协的平衡】

【具体行动建议】

在人际交往和团队协作中，你要时刻提醒自己：外部世界和周围的人，是不可能完全按照你的逻辑和价值观来运转的。你需要提前在心里设置一个对他人效率和理解能力的“宽容度区间”。

当别人的做法看起来很笨拙，或者别人的价值观跟你不一致时，只要这件事没有严重阻碍你达成最终的客观目标，你就不要去进行纠正，更不要在心里对别人进行价值观层面的审判。你需要把注意力死死地盯在“事情的最终交付结果”上。学会使用那些你觉得没有效率、但是符合社会常规的沟通方式去推动事情的发展。把这些沟通当作一种获取资源的客观手段，而不是一种情感的交流。

【维持目标】

这个方面的建议是为了保护你的第三功能Fi不被外界的混乱所激怒。INTJ非常容易因为看不惯别人的做事方式或者价值观，而产生强烈的排斥情绪，进而切断与外界的联系。通过刻意降低对外部环境的道德和智力要求，你把自己的核心价值观保护在了一个安全的内部区域。只要你不去强求外界的绝对完美，你的内部情绪就会一直保持稳定，你也就不会因为对环境失望而放弃你原本的计划。

【第三方面：基础物理能量的刻意储备】

【具体行动建议】

你需要极其刻意地、像对待一个重要项目一样去管理你的身体。你必须把吃饭、睡觉和适度运动，当作不可更改的硬性任务写进你的每日日程表里，并且要设置严格的执行标准。

不要等到胃部极度疼痛了才去吃东西，不要等到大脑完全转不动了才去睡觉。你要在身体还没发出严重警报的时候，就主动去满足它的基本需求。每个周末，强制自己安排至少半天的时间，彻底远离所有的电子屏幕和工作文档。去从事一些纯物理的、不需要任何逻辑思考的活动。比如去游泳、去徒步，或者把家里的地板彻底拖一遍。

【维持目标】

这是你能够长期保持健康态的最关键防线。你的主导功能Ni在运转时极其消耗生理能量，而你平时又极容易忽略身体的疲惫感。如果不刻意去维护物理身体的运转，当你的生理能量被彻底榨干时，劣势功能Se就会不可避免地迎来爆发。通过把基础的身体维护变成一种客观的日常任务，你提前释放了Se的压力，保证了整个认知系统的底层供电网络始终处于满电状态。只要你的身体不崩溃，你强大的大脑就能持续不断地为你输出精准的战略和高效的行动。
"""
        }
    },

    "ENTJ": {
        "crisis": {
            "title": "严重透支：把工作全扔一边去休息",
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
            "title": "心里难受：你不必时刻都那么强大",
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
            "title": "太急躁了：慢下来，别为了做而做",
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
            "title": "找回节奏：带着大家把事办成",
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
            "title": "彻底乱了：先收收心，把日子过正常",
            "text": """
【当前心理状态与行为表现评估】

综合你目前的各项测试数据和行为反馈，你现在正处于一种由长期高压、极度疲劳或者严重的人际关系挫折导致的认知功能全面过载状态。在荣格认知功能理论的框架下，你目前的评估结果为“Loop+Grip”双重叠加态。具体而言，作为ENTP，你正在经历“外倾直觉（Ne）与外倾情感（Fe）的负向循环（Loop）”，并且同时伴随着“劣势功能内倾感觉（Si）的失控爆发（Grip）”。

这种状态意味着你最核心的理性分析和独立判断能力已经完全停摆。你原本用来过滤信息和寻找事物底层客观规律的逻辑系统已经失效。现在，你的注意力一方面被强制绑定在别人对你的看法和外界的社交反馈上，另一方面又被完全困在过去的负面经验和极其琐碎的现实细节中。你现在不是在用理智思考问题，你的大脑只是在极度的社交焦虑和对过去的悔恨中来回拉扯，进行着极其消耗体力的无效运转。

【具体困境与情绪特征】

在日常生活中，这种双重叠加态会让你表现出极其反常且让你自己感到极度屈辱的行为模式。首先，你完全失去了平时那种自信、独立且不在乎别人眼光的态度。你会变得极度讨好周围的人，对人际关系中的任何微小变化都极其敏感。

你的大脑会不受控制地去过度解读别人的话语和表情。别人一个稍微迟缓的信息回复，或者一个没有明显情绪的眼神，都会被你立刻捕捉到。然后你会开始疯狂地猜测对方是不是讨厌你、你是不是哪里做错了。为了获得别人的认可或者确认别人没有生气，你会违背自己的真实想法，去迎合别人的观点，说出很多你平时根本不屑于说的客套话。但这种讨好行为做完之后，你又会觉得非常恶心，对自己的软弱感到极度愤怒。

同时，由于劣势功能内倾感觉（Si）的爆发，你会变得极其刻板、多疑且容易大惊小怪。平时的你非常讨厌关注细节，看重的是未来的可能性。但在现在的状态下，你的注意力会死死地盯住那些已经发生过的、极其微小的错误。你会经常在深夜反复回想几年前发生的一件尴尬小事，或者你在某次会议上说错的一个字。你的大脑把这些微小的旧账翻出来，当作你是一个彻底失败者的确凿证据。

此外，你对自己的身体状况和物理环境会产生一种不合理的恐慌。你可能会因为一点轻微的头痛或者肠胃不适，就立刻认定自己得了非常严重的疾病，然后在网上疯狂搜索相关症状，越看越害怕。你还可能会突然开始极其苛刻地要求生活环境的整洁，因为一点点摆放不整齐的物品就大发雷霆。这种在极度渴望社交认同和极度害怕现实细节之间的来回横跳，会迅速抽干你的精力，让你整个人处于一种高度紧绷、随时可能崩溃的边缘状态。

【深层心理机制分析：为什么会变成这样】

导致你变成现在这种状态的根本原因，在于你的辅助功能内倾思考（Ti）被强制关闭了。你内在认知系统中唯一用来踩刹车和进行客观判断的工具彻底坏掉了。

在正常且健康的状态下，你的主导功能外倾直觉（Ne）负责在外部世界寻找各种新奇的想法、概念和可能性。然后，你的辅助功能内倾思考（Ti）负责把这些发散的想法拉回来，用极其严密的内部逻辑去检验它们，剔除掉那些不合理的、不符合客观规律的部分。这两个功能配合，让你成为一个既有创造力又讲逻辑的人。

但是，当你长期处于一个逻辑根本讲不通的环境中，比如面对极其复杂且充满情绪化的人际斗争，或者你的所有理性分析都被现实中不讲道理的规则强行否决时，你的内倾思考（Ti）会感到极度的挫败和疲劳。因为Ti需要客观和讲理的空间才能运作。当外界持续拒绝你的逻辑时，为了节省能量，你的大脑强行把负责理性判断的Ti功能关闭了。

当Ti关闭后，你的主导功能Ne依然在高速运转，不断地向外发射信号。但因为它失去了Ti的逻辑过滤，它直接对接上了你的第三功能外倾情感（Fe）。Fe是一个专门用来感知群体情绪、维护人际和谐的功能。

这就形成了一个极其糟糕的负向循环。Ne不再去寻找有趣的新知识，而是把全部算力用来寻找“别人对我的看法”的各种可能性；Fe接收到这些可能性后，产生强烈的焦虑感，迫使你去采取行动获取别人的好感。接着，Ne又根据别人最新的反应，继续生成更多糟糕的猜测。你的大脑在这个没有逻辑参与的过程中不断空转，导致你彻底丧失了自我立场，变成了一个完全被外界情绪牵着鼻子走的人。

【劣势功能失控与负向循环的叠加逻辑】

这种Ne与Fe的循环不仅让你失去了独立思考的能力，还会极其快速地消耗你的心理能量。当你内部的压力达到最高点，维持日常运转的最后一点能量被耗尽时，平时被你完全忽视和压抑的第四功能——劣势功能内倾感觉（Si）就彻底失控了。

你的内倾感觉（Si）负责记录过去的具体经验、处理繁琐的现实细节以及感知身体的内部状态。在正常情况下，为了让Ne能够无拘无束地去想未来，你的大脑会刻意压制Si，让你不去在意过去的失败和眼前的琐事。

但是现在，作为最高逻辑长官的Ti下线了。被长期压抑的Si带着巨大的原始能量冲了出来，强行接管了你的意识。它开始向你的大脑疯狂地倾倒过去的负面数据。

当Ne-Fe循环和Si爆发同时发生时，你的心理系统就陷入了最彻底的混乱。你的Ne在预测“所有人都会因为我今天说错的话而孤立我”，你的Fe因此感到极度的恐慌。这时候，如果是正常的你，Ti会出来说：“这不符合逻辑，大家都很忙，没人会记住你的一句话。”但是现在Ti不在场，出来的是失控的Si。

Si非但没有反驳这种恐慌，反而提供了一大堆历史记录作为证据。Si会告诉你：“是的，他们会孤立你。你还记得三年前你做砸了那个项目时，老板看你的眼神吗？你还记得小学的时候你被全班嘲笑的场景吗？”

你的大脑把对未来的社交恐慌（Ne-Fe）和对过去确凿失败经历的重复体验（Si）死死地绑定在了一起。你完全失去了对当下的客观判断力。你现在的行为逻辑，完全是由对社交被拒的极度恐惧，以及对过去错误的极度懊悔所共同驱动的。你用你最强大的联想能力，配合最负面的历史数据，给自己定下了无法翻案的死刑。

【30天状态恢复与调整计划】

针对目前这种逻辑完全瘫痪、情绪和感官双重失控的状态，你必须明确一个事实：你不可能通过去找别人要一个明确的说法，或者通过在脑子里把过去的事情想通来解决问题。你现在的情绪和记忆系统是完全损坏的，越是去触碰人际关系和过去的回忆，你就会陷得越深。

恢复的唯一路径是：首先通过物理手段强行切断外界的人际反馈，饿死正在发疯的Ne-Fe循环；其次，用最简单、最机械的现实任务去安抚暴躁的Si；最后，通过纯粹客观的、不涉及任何人的逻辑分析任务，把你关闭的内倾思考（Ti）重新强制开机。以下是为你制定的、严格分为三个阶段的30天恢复计划：

【第一阶段：人际断联与信息静音（第1-3天）】

【具体行动建议】

在这个阶段，你的首要任务是切断所有给你提供社交反馈的源头，强制打断Ne-Fe的循环。如果条件允许，请假三天待在家里。在这三天里，不要去见任何朋友，不要参与任何社交活动。

把你手机上所有的社交软件全部关闭消息通知。不要去发任何朋友圈，绝对不要去试探性地给别人发信息看别人回不回复。即使别人给你发了信息，只要不是涉及生死存亡的紧急事件，一律不回。

这三天里，不要去揣测任何人的想法。当你的脑子里又冒出“他为什么不理我”、“我是不是得罪他了”这样的念头时，立刻站起来，去喝一口冷水，或者直接去洗个澡。你的唯一任务就是切断与外部人的所有联系，强迫自己去承受那种“不知道别人怎么看我”的不适感。

【阶段目标】

这个阶段的核心目标是饿死你的外倾情感（Fe）。Fe需要外界的反应作为食物才能继续制造焦虑。通过绝对的物理隔离，你切断了Fe的食物来源。同时，这也剥夺了外倾直觉（Ne）继续发散社交可能性的素材。你需要接受自己现在就是一个不需要向任何人证明自己、也不需要任何人喜欢的独立物理实体。只有把外部的杂音彻底关掉，你内部的疯狂运转才会慢慢停下来。

【第二阶段：客观事实锚定与单一任务（第4-10天）】

【具体行动建议】

当社交焦虑因为断联而稍微减轻后，你需要开始处理失控的内倾感觉（Si）。你需要用健康的、低强度的物理细节去满足Si，而不是让它去翻找过去的负面记忆。

在这个阶段，你需要去做一些完全不涉及任何人际交往、且步骤极其固定的单一任务。比如，把你的电脑桌面上的所有文件，严格按照日期和文件类型，建立十个文件夹进行归类存放。把家里的书架上的书，全部拿下来，擦干净灰尘，然后按照厚度或者颜色重新放回去。或者去厨房，严格按照网上的克数和时间要求，去煮一锅米饭或者煎一个鸡蛋。

在做这些事情的时候，你的脑子可能会极其抗拒，觉得这些琐事毫无意义。不要理会这种抗拒，强迫你的身体去执行这些死板的动作。只关注眼前的物理细节：文件放进去了没有，书本对齐了没有，时间到了没有。不要去想昨天，也不要去想明天。

【阶段目标】

处于Grip状态的你，被过去的负面细节折磨得痛不欲生。这个阶段的目标就是通过这些极其枯燥、有着明确步骤规则的现实任务，把你的注意力从大脑里的历史垃圾堆中硬拽出来，死死地按在当下的物理现实上。当你在整理文件或者排列物品时，你的Si被迫去处理眼前这些安全的、没有任何情绪色彩的客观细节。这会让你的大脑收到一个明确的信号：当下的现实是可控的，没有危险的。这就初步安抚了Si的暴躁情绪。

【第三阶段：逻辑重建与独立思考（第11-30天）】

【具体行动建议】

经过前两个阶段的隔离和安抚，你的情绪已经相对平静，破坏性的冲动已经减弱。现在，你需要正式重启你的核心武器——辅助功能内倾思考（Ti）。

你必须开始进行纯粹的、不涉及任何个人情感和人际关系的逻辑分析。不要去分析你的生活，去分析客观的系统。比如，去学习一门基础的编程语言，哪怕只是学会写出一段最简单的条件判断代码。或者去阅读一本关于形式逻辑、经济学基础原理或者硬科幻设定的书。

如果看书和学习觉得困难，你可以拿出一张白纸，随便找一个跟你生活完全无关的客观议题，比如“某个城市的交通拥堵问题”。在纸上列出导致这个问题的所有客观变量，然后写下三条不带任何感情色彩的解决方案，并论证每条方案的逻辑可行性。在这个过程中，只讲事实和因果关系，绝对不要带入任何个人的喜欢或讨厌。

【阶段目标】

这是彻底打破Loop+Grip叠加态最关键的一步。内倾思考（Ti）的运转逻辑是极其冷酷和客观的。当你强迫自己去分析代码、系统原理或者社会议题时，你的大脑被迫重新启动了这套荒废已久的逻辑处理程序。

当Ti被完全唤醒并重新接管信息处理的最高权限时，它会立刻展现出强大的纠错能力。它会直接切断Ne和Fe之间的无效连接，告诉你：“别人怎么想根本不重要，因为这不影响客观事实的成立。”同时，Ti也会把Si按回它该待的地方，它会客观地判定：“过去的那些失败只是历史数据，它们和当下的逻辑推导没有必然的因果关系。”

当理性和客观重新成为你大脑的运作核心时，你的自信心和独立思考能力就会全面回归。你会发现之前让你极度痛苦的社交焦虑和过去回忆，在严密的逻辑面前变得根本不值一提。此时，你就彻底走出了这种混乱的双重叠加态，恢复到了那个头脑清醒、逻辑严密、不受外界干扰的正常状态。
"""
        },
        "grip": {
            "title": "疑神疑鬼：别老觉得自己身体有病",
            "text": """
【当前心理状态与行为表现评估】

综合你目前的各项测试数据和日常行为反馈，你现在正处于一种非常典型的“Grip（劣势功能失控爆发）”状态。在荣格认知功能理论的框架下，这意味着你作为ENTP，平时最依赖的核心认知架构——也就是负责探索未来可能性的外倾直觉（Ne）和负责客观逻辑判断的内倾思考（Ti）——已经完全停止了工作。与此同时，你平时极力忽略、压抑在潜意识最底层的第四功能，也就是劣势功能内倾感觉（Si），完全突破了理智的限制，全面接管了你的思维和行为控制权。

对于一个习惯了发散思维、总是在思考新点子和宏大未来的ENTP来说，进入这种状态是非常反常且让人极度痛苦的。你原本引以为傲的快速反应能力、对全局的掌控感以及对新鲜事物的好奇心，在这一刻全部消失了。你发现自己不仅想不出任何新的主意，反而被困在了极其琐碎的现实细节和对过去的负面回忆中。这并不是因为你突然变笨了，或者你的性格发生了改变。这仅仅是因为你的心理能量在长期的压力下被彻底耗尽，你的大脑为了自我保护，强制关闭了极其消耗能量的高级认知功能，启动了一套你完全不熟悉、且运作极其原始的备用处理系统。

【具体困境与行为特征】

在日常生活中，处于Si Grip状态会让你表现出与平时截然相反的行为模式。总体来说，你的注意力从“广阔的未来”被强制拉回到了“狭窄的过去”和“微小的身体感受”上。

最明显的一个特征是，你对自己的身体状况和周围的物理环境细节产生了极度不合理的关注和恐慌。平时的你，只要身体没有大毛病，你根本不会去注意自己偶尔的头痛或者肌肉酸痛，你总是忙着去思考更有趣的事情。但是现在，你的注意力死死地绑定在这些极其微小的躯体感受上。你可能会因为一次轻微的肠胃不适，或者心跳稍微快了一点，就立刻产生极其严重的恐慌感。你会控制不住地在网络上反复搜索这些普通的身体反应，然后非常主观地认定自己患上了某种极其严重的疾病。这种恐慌感是非常真实的，无论别人怎么用客观概率来劝说你，你都听不进去。

其次，你会表现出一种极其反常的刻板和对细节的强迫症。ENTP平时是最讨厌繁文缛节和枯燥细节的，你们喜欢大框架。但在现在的状态下，你可能会突然花上好几个小时，去整理电脑里某个根本不重要的文件夹，要求每一个文件的命名格式必须绝对统一。或者你会突然对房间的卫生要求极高，如果桌子上的某本书没有对齐边缘，你就会感到极其烦躁并发脾气。你会把所有的精力都消耗在这些毫无意义的微小物理细节上，却对真正重要、需要你动脑子去解决的核心工作完全视而不见。

另外，你会不可控制地陷入对过去的负面反刍之中。外倾直觉（Ne）原本是让你往前看的，现在内倾感觉（Si）强迫你往后看。你的大脑会不断地、不受控制地播放你过去犯过的错误、经历过的失败，甚至是你很多年前说错的一句非常不起眼的话。你会花费大量的时间去反复回味这些过去的尴尬和挫败，并在脑子里不断地进行自我批判。你认定过去的失败已经彻底锁死了你的未来，你觉得自己的人生已经没有任何新的出路和可能性了。这种对未来的极度悲观和对过去的极度执念，是你处于劣势功能爆发状态时最典型的表现。

【深层心理机制分析：为什么会变成这样】

要弄清楚你为什么会陷入这种完全不受控制的琐碎和恐慌状态，我们需要深入分析你内在认知功能的工作机制，以及它们在极端压力下是如何发生错乱的。

在你的认知功能排序中，第一位的主导功能是外倾直觉（Ne），它负责源源不断地提供新的想法、寻找事物的多种可能性，并且极其讨厌被规则束缚。排在第二位的辅助功能是内倾思考（Ti），它负责用严密的逻辑去检验Ne找来的这些想法，判断它们是否真的可行。这两个功能构成了你日常高效运转的核心。

而排在第四位的劣势功能，是内倾感觉（Si）。Si的作用是记录过去发生的具体客观事实，维护日常生活中的固定程序，以及感知身体内部的具体物理状态。因为大脑的运算能量是有限的，为了保证主导功能Ne能够无拘无束地去天马行空，你的大脑在日常生活中会非常刻意地压制Si的活动。你会习惯性地忽略过去的经验，忽略身体的疲劳，甚至忽略生活环境中不整洁的细节，强迫自己把所有的精力都集中在脑海中那些有趣的新概念上。

但是，这种长期的压抑是有代价的。当你长期处于一个要求你必须去处理大量枯燥数据、没有任何创新空间的工作环境中，或者当你遭遇了重大的现实挫折，发现你那些绝妙的想法在现实中根本推行不下去时，你的主导功能Ne和辅助功能Ti会感到极度的挫败。你越是试图用发散思维去解决问题，现实给你的打击就越大。当你的Ne和Ti在现实的铜墙铁壁面前耗尽了所有的心理能量，再也无法维持正常运转时，它们就会彻底宕机并暂时下线。

当作为最高指挥官的Ne和Ti失效后，原本被压抑在潜意识底层的劣势功能Si就失去了所有的压制。它带着长年累积的原始能量，直接冲到了你的意识表面，强行接管了你的思考和行为。这就是Grip状态产生的根本原因：不是你突然变得胆小和琐碎了，而是你用来探索未来和进行逻辑分析的高级认知系统彻底停摆了，你只能被迫使用这个你最不擅长的系统来面对世界。

【劣势功能失控的逻辑】

当劣势功能Si接管你的大脑时，它的运作方式是非常粗糙、极端且充满恐惧的。

因为你平时极少去健康地使用内倾感觉这个功能，你的Si处于一种非常原始和缺乏锻炼的状态。一个Si功能成熟的人，可以很自然地从过去的经验中获得安全感，并且能够把日常生活打理得井井有条。但是，你现在爆发出来的Si，是没有任何安全感可言的。

在失控的Si看来，因为你之前总是不顾一切地往前冲（过度使用Ne），导致了现在的失败和精疲力尽，所以它现在的唯一任务就是强迫你停下来，让你看清楚现实有多么危险。它通过放大你身体的微小不适感，来警告你必须关注物理生存；它通过强迫你去整理那些毫无意义的桌面细节，来为你建立一种非常虚假的、微小的“一切尽在掌握”的现实秩序感；它通过不断向你播放过去的失败记录，来恐吓你绝对不要再去尝试任何新的事物。

由于你的主导预测功能（Ne）和逻辑分析功能（Ti）都已经下线，你现在完全失去了客观评估这些警告的能力。你不再去思考“整理这个文件夹对整个项目有没有帮助”，也不再去计算“这种头痛是严重疾病的概率到底有多低”。你现在的行为逻辑，完全是由对现实细节的极度恐惧和对过去经验的盲目服从所驱动的。你正在用一种极其低效且极其折磨自己的方式，试图在彻底混乱的心理状态中抓住一根现实的救命稻草。

【30天状态恢复与调整计划】

针对目前这种劣势功能全面爆发、注意力被琐碎细节和负面记忆完全绑架的状态，调整的核心思路非常明确：你绝对不能在这个时候试图去构思任何新的大项目，也绝对不能试图用你残留的逻辑去反驳你脑子里的那些健康恐慌。你现在的逻辑系统是瘫痪的，你越是去搜索资料或者反复思考，Si的恐慌感就会越强。

恢复的顺序必须是：首先通过物理手段强行阻断你去关注那些引发恐慌的细节，停止无意义的强迫行为；其次，通过极其基础的、健康的身体节律，让暴躁的Si得到真实的安抚；最后，通过没有压力的、开放式的小话题，慢慢把你关闭的外倾直觉和内倾思考重新唤醒。以下是为你制定的、严格分为三个阶段的30天恢复计划：

【第一阶段：切断细节纠缠与物理阻断（第1-3天）】

【具体行动建议】

在这个阶段，你的判断力是完全不可靠的，你无法通过告诉自己“别想了”来停止那些强迫性的动作和恐慌。你需要做的是在外部环境上制造硬性的阻断。

立刻停止所有在网络上搜索身体症状的行为。把手机里所有的医疗健康类咨询软件全部卸载。如果你觉得身体不舒服，直接去正规医院挂号做个基础检查，拿到医生的诊断报告后，把报告锁进抽屉里，绝对不要自己在网上对照症状进行瞎猜。

如果这段时间你发现自己又在强迫性地整理某个不重要的文件，或者死死地盯着房间里的某个角落觉得它不够干净，你需要立刻离开那个物理环境。直接走出房间，去客厅或者阳台待着。不要去要求现在的环境有多完美，允许你的桌子是乱的，允许你的文件是没有分类的。这三天里，你的唯一任务就是克制住自己去处理这些微小细节的冲动。当你想去整理或者想去搜索时，立刻去喝一大杯温水，然后闭上眼睛深呼吸五次。

【阶段目标】

这个阶段的核心目标是强行止损和阻断破坏性的Si发泄。处于Grip状态的ENTP，必须首先被剥夺去过度关注细节的条件。通过设置不可逾越的规则，你强制你的身体停止对过去错误和当下细微不适的反复确认。这会让你在短期内感到极度的焦虑和不适，因为你失去了那种虚假的掌控感。但你必须忍耐过去，只有硬生生地把这种对细节的病态执着按住，你才有可能省出精力去进入下一步的调整。

【第二阶段：重建基础现实节律与感官安抚（第4-10天）】

【具体行动建议】

当最剧烈的强迫冲动稍微平息之后，你需要开始主动地、有意识地给你的劣势功能Si提供健康的、低强度的现实输入。你要学会在不带任何恐慌的前提下，安全地与你自己的身体和物理现实相处。

在这个阶段，你需要极其刻板地执行一套最基础的生活作息。规定自己每天在固定的时间起床，在固定的时间吃三顿饭，在固定的时间睡觉。在吃饭的时候，不要去想工作上的任何事情，也不要去回忆过去。把注意力全部集中在食物的客观物理属性上：这口饭是热的还是冷的，咸的还是淡的。

每天安排半个小时的无目的散步。去一个你熟悉的环境里走一走，不要带任何工作任务，也不要听任何播客。强迫你的眼睛去观察周围那些确定的、不会改变的物理实体。去看看路边的树木，去看看周围的建筑物。在做这些事情的时候，告诉自己：“现实世界是非常稳固的，我的身体正在按照正常的规律运转。”

【阶段目标】

这个阶段的目标是用健康的物理节律去满足Si的安全需求。你的Si现在极度缺乏安全感，它通过制造恐慌来引起你的注意。现在，通过按时吃饭、规律作息和观察熟悉的物理环境，你给它提供了一个稳定的、可预测的现实反馈。当它得到了正常的满足后，它就会逐渐安静下来，不再通过制造身体不适的幻觉或者翻找过去的负面记录来折磨你。你的神经系统会从高度紧绷的警报状态中慢慢放松下来。

【第三阶段：重启发散思维与主导功能归位（第11-30天）】

【具体行动建议】

到了这个阶段，你对身体的恐慌和对细节的强迫已经基本消失，生活节奏恢复了基础的平稳。现在，你需要把断线的核心功能——外倾直觉（Ne）和内倾思考（Ti）重新拉回工作状态。

你需要开始做一些没有任何现实压力、纯粹只是为了好玩的思维发散任务。不要去碰那些导致你崩溃的核心工作项目。你可以去找一个你完全不了解的全新领域，比如一种你从来没见过的冷门乐器、一个极其小众的历史事件，或者一个非常奇葩的科学假说。去阅读相关的资料，不要带着任何要掌握这项技能或者要参加考试的目的。

在了解这些新信息的过程中，你可以拿出一张白纸，随便写下这些新事物与其他事物之间可能存在的奇怪联系。不管这些想法多么不切实际，都把它们记录下来。当你的脑子里又冒出“想这些根本没有用，过去那个失败的问题还没解决”这种念头时，直接忽略它，强迫自己继续去思考眼前这个好玩的新话题。

【阶段目标】

这个阶段的核心目标是让你的主导预测功能和逻辑分析功能重新掌权。外倾直觉（Ne）的运转逻辑是“寻找新奇和可能性”。当你开始去接触那些没有历史包袱的全新信息，并且允许自己进行没有压力的联想时，你的Ne就被完全激活了。

当Ne开始提供新鲜有趣的素材时，你的辅助功能内倾思考（Ti）就会自然而然地苏醒过来，去对这些新素材进行客观的逻辑分析。当这两个功能重新建立起顺畅的合作关系，开始在外部世界寻找新的出路时，那个总是被困在过去和琐碎细节里的劣势功能Si，就会安静地退回到潜意识中去。此时，那个思维极其活跃、不受规则拘束、永远对未来充满好奇的你，就彻底回归了。
"""
        },
        "loop": {
            "title": "太爱演了：沉下来，听听自己的真话",
            "text": """
Gemini said
【当前心理状态与行为表现评估】

综合你目前的各项测试数据和行为反馈，你现在正处于一种被称为“Loop（负向循环）”的心理状态。在荣格认知功能理论的框架下，你目前的评估结果显示，你的内倾辅助功能已经被强制关闭，导致你的心理活动完全暴露在外部环境中，失去了内部的逻辑支撑。具体到你作为ENTP的情况，你正在经历“外倾直觉（Ne）与外倾情感（Fe）的负向循环”。

这种状态与彻底失控爆发的叠加态有所不同。在单纯的Loop状态中，你并没有表现出对过去的极度悔恨或者对现实物理细节的强迫性恐慌。从表面上看，你依然在正常地进行社交，甚至可能表现得比平时更加活跃和合群。但是，你的内在实际上处于一种极度虚弱和失去主见的状态。你的心理能量完全向外发散，被周围人的情绪和看法彻底绑架。你正在使用极高的算力，去处理那些完全没有客观标准的人际关系反馈，导致你陷入了严重的情感内耗和自我立场的丧失。

【具体困境与思考特征】

在日常生活中，处于Ne-Fe Loop状态会让你表现出非常隐蔽但极其内耗的讨好行为。首先，你会发现自己完全丧失了平时那种独立思考、敢于质疑一切的客观态度。面对任何新的问题或者讨论，你的第一反应不再是去分析这件事的底层逻辑对不对，而是去观察周围人的脸色，去猜测大家希望听到什么答案。

你的注意力不可控制地集中在社交环境的微小变化上。在一个群体中，你会极度关注是否有人感到不高兴，是否有人对你的发言表现出不耐烦。如果别人的反应不如你预期的那么热烈，你的外倾直觉（Ne）会立刻开始发散，生成几十种糟糕的可能性。你会主观地认定对方觉得你很愚蠢，或者你刚才的话冒犯了对方。为了弥补这种想象出来的社交危机，你的外倾情感（Fe）会迫使你立刻采取行动去讨好对方，比如不停地解释、过度地道歉，或者完全顺从对方的观点。

在这个过程中，你最核心的独立逻辑分析能力（Ti）完全没有参与工作。你心里其实很清楚对方的观点在事实上是错误的，或者对方的要求是不讲道理的。如果是健康状态下的你，你会直接指出其中的逻辑漏洞。但是现在，你为了维持表面的社交和谐，强行把自己的真实想法咽了下去，甚至附和对方的错误观点。

这种行为会让你在事后感到极度的屈辱和疲惫。ENTP在本质上是非常看重理性和客观事实的。当你发现自己变成了一个没有底线、只知道迎合别人的社交附庸时，你会对自己的软弱产生强烈的自我厌恶。你觉得周围的人都很虚伪，但你发现自己表现得比他们更虚伪。整体来看，你的生活变成了一场极其耗费精力的社交表演，你被困在了别人对你的评价和不断变幻的人际关系网之中。

【深层心理机制分析：为什么会变成这样】

这种状态的根本原因，在于你为了适应极端不讲理的外部环境，或者为了获取某种必须的外部资源，主动放弃了大脑内部的逻辑评判标准。

在你处于健康状态时，你的主导功能外倾直觉（Ne）负责在外部世界寻找各种新奇的想法和可能性，而你的辅助功能内倾思考（Ti）负责在内部建立一套极其严密的客观逻辑标准。当Ne带回一个新想法时，Ti会冷酷地对其进行拆解和检验，判断它是否符合事实。这两个功能配合，让你能够客观、犀利地看待世界，不被任何权威或群体情绪所左右。

但是，当你长期处于一个逻辑完全失效的环境中时，情况就发生了改变。比如，你身处一个只看重资历不看重能力的职场，或者你面对一个极其情绪化、只要你讲道理就会爆发激烈冲突的伴侣。在这些环境里，你的内倾思考（Ti）发现它所坚持的客观真理不仅解决不了问题，反而会给你带来更多的麻烦和排挤。为了让你能够在这个糟糕的环境中生存下去，你的大脑采取了最直接的防御手段：它强行切断了Ti功能的供电。

当负责逻辑检验的Ti被关闭后，你的主导功能Ne依然在高速运转，它需要一个新的功能来配合处理信息。于是，它直接跨过了Ti，对接上了你的第三功能外倾情感（Fe）。外倾情感（Fe）是一个专门用来感知外部群体情绪、建立人际连接的功能。

问题在于，因为你是在压力下进入这种状态的，大脑的信息处理机制发生了严重的偏差。Fe不再被用来进行健康的社交互动，而是被当成了一个极度敏感的雷达，专门用来探测外界对你的负面评价和排斥信号。

【认知功能受阻的逻辑】

当Ne和Fe这两个外倾功能开始单独配合，并且完全没有内部的Ti来进行制衡时，一个极其混乱的死循环就彻底形成了。

首先，主导功能Ne在外部环境中捕捉到一个极其微小的信息：“今天开会时，主管看了我一眼然后皱了一下眉头。”

接着，第三功能Fe接收到这个信息，立刻产生强烈的恐慌情绪：“主管是不是对我的工作非常不满意？我是不是要被开除了？”

然后，Ne开始针对这种恐慌情绪进行毫无节制的发散预测：“如果我被开除了，我就找不到工作了，我身边的朋友也会看不起我，我的人生就彻底毁了。”

面对Ne制造出来的这些极其恐怖的未来画面，Fe为了自保，迫使你做出极端的迎合行为：“我必须立刻去向主管表忠心，我要主动承担所有的脏活累活，我要对办公室里的每一个人都笑脸相迎，这样他们就不会赶我走了。”

这个迎合行为做出之后，Ne会继续密切监控周围人的反应。如果别人对你的讨好表现出一点点的不自然，Ne又会生成新的糟糕预测，导致Fe产生新的焦虑，从而迫使你进行更深度的讨好。

这就是你陷入严重社交内耗的底层逻辑。你并不是真的在关心别人，你是在用一种极其卑微的方式试图控制别人对你的评价。你用你最强大的发散思维，给自己制造了无数个根本不存在的社交危机。因为整个推导过程完全没有内倾思考（Ti）的参与，所以没有任何一个声音站出来告诉你：“主管皱眉头只是因为他昨天没睡好，这在逻辑上和你没有任何关系。”你失去了分辨客观事实的能力，完全活在自己编造的社交恐惧之中。

【30天状态恢复与调整计划】

针对目前这种认知功能陷入完全外倾的死循环、彻底丧失独立逻辑判断的状态，调整的核心思路非常明确：你绝对无法通过改善人际关系来打破这个循环。你越是去跟别人沟通、越是去解释自己，你就越深地陷在Ne和Fe的纠缠中。

唯一的出路是强制重启被你关闭的辅助功能——内倾思考（Ti）。你必须通过具体的、不涉及任何人类情绪的客观事物，把你向外发散的注意力强行拉回到内部的理性分析上。只有当你的大脑重新开始使用冷冰冰的客观逻辑去处理问题时，那些关于别人怎么看你的主观猜测才会被彻底粉碎。以下是为你制定的分为三个阶段的30天恢复计划：

【第一阶段：社交阻断与外部评价屏蔽（第1-7天）】

【具体行动建议】

在这个阶段，你的首要任务是打断Ne和Fe的不断对话。当你发现自己又开始猜测别人发的那句话是什么意思，或者又在为了迎合别人而准备修改自己的方案时，你需要在物理层面上叫停这种行为。

你需要尽可能地减少所有的非必要社交。推掉所有的聚餐、闲聊和娱乐活动。在工作和生活中，把沟通降到最低限度。别人问你一个问题，只回答“是”、“不是”或者“我不知道”，不要加任何多余的解释，也不要带任何语气词。

在这七天里，绝对不要去社交媒体上看别人对你的评论或者点赞。如果有人对你提出批评或者表达不满，不要去反驳，也不要去道歉，直接回复“我听到了”，然后终止对话。不要去想对方听了这句话会怎么想。你的唯一任务就是切断外界对你情绪的影响，忍受那种不去讨好别人所带来的焦虑感。

【阶段目标】

这个阶段的核心目标是饿死你的外倾情感（Fe）。通过强制减少社交互动和拒绝回应外部评价，你剥夺了Fe继续产生社交焦虑的素材。你不需要去证明自己是一个好人或者聪明人，你只需要让你的大脑习惯不去处理别人的情绪。当大脑发现没有新的社交数据输入时，它那种过度运转的恐慌状态就会慢慢降温。

【第二阶段：单一事实确立与非社交任务（第8-14天）】

【具体行动建议】

当社交焦虑因为断联而稍微减轻后，你需要开始用极其枯燥、完全受客观规则支配的任务，去刺激你的内倾思考（Ti）。这里的关键是“只讲客观逻辑”和“绝对没有人的因素参与”。

你需要在接下来的七天里，每天刻意去做一些只有对错标准、没有主观偏好的事情。比如，去学习一门非常基础的编程语言，照着教程写一段只有几行代码的计算程序。或者买一个极其复杂的机械拼装模型，严格按照说明书上的零件编号去组装。你也可以去阅读一本关于形式逻辑、数学基础或者机械原理的专业书籍。

在做这些事情的时候，禁止去想这些技能对你的人际关系有没有帮助。你只需要去执行逻辑规则，并确认结果是否符合规则。如果代码报错了，那就是逻辑写错了，这跟你的态度好不好没有任何关系。

【阶段目标】

处于Loop状态的你，极度依赖别人的反馈来确认自己的价值。这个阶段的目标就是通过这些只涉及死物、完全受客观定律控制的任务，向你的认知系统证明一个事实：世界上存在一种不需要任何人同意就能独立成立的客观真理。

当你的代码成功运行，或者你的模型组装完成时，你的内倾思考（Ti）就会得到一次微弱的唤醒。你的大脑会发现，处理这些没有情绪的客观逻辑，比处理复杂的人际关系要轻松和确定得多。这就为你重新建立内部的逻辑自信打下了基础。

【第三阶段：独立立场重建与边界确认（第15-30天）】

【具体行动建议】

经过前两个阶段的铺垫，你对外部评价的极度依赖已经大大降低，Ti功能已经处于待机状态。现在，你需要主动把它应用到你真实的日常表达中去。

你必须开始强迫自己在生活和工作中表达你真实的、基于客观事实的观点，并且完全放弃对别人反应的预期。当别人提出一个不合理的方案时，直接用平和的语气指出其中的逻辑错误，比如“这个方案在时间上无法实现，因为数据不匹配”。说完这句话后，如果对方生气或者不高兴，不要去安抚对方，直接站在原地，保持沉默。

每天晚上，在纸上写下今天发生的三个客观事实，以及你对这三个事实的独立逻辑判断。不要写任何带有情绪色彩的词语。只写原因和结果。

【阶段目标】

这是彻底打破Ne-Fe Loop的最后一步。当你在强制表达独立观点并且拒绝承担别人的情绪时，你的内倾思考（Ti）被完全激活了。它重新承担起了过滤外部信息和建立内部判断标准的责任。

你的主导功能外倾直觉（Ne）终于重新获得了来自内部的逻辑支撑。它不再需要去猜测别人的心思，而是开始忙于处理眼前这些被Ti筛选过的客观事实。当Ti明确地告诉你“我不欠任何人的情绪价值，我只对事实负责”时，那个总是被困在社交恐惧里的外倾情感（Fe），就会安静地退回到辅助位置。此时，你将彻底走出讨好和内耗的死循环，恢复到那个思维敏捷、独立客观、敢于质疑一切的正常状态。
"""
        },
        "growth": {
            "title": "变得靠谱：把吹过的牛都变成真的",
            "text": """
Gemini said
【当前心理状态与行为表现评估】

综合当前的各项测试数据和你的日常行为反馈，你目前正处于认知功能运作极其顺畅、心理能量分配极其合理的理想状态，也就是我们通常所说的“健康态”。在荣格认知功能理论的框架下，这意味着你作为ENTP的四个核心认知功能——外倾直觉（Ne）、内倾思考（Ti）、外倾情感（Fe）和内倾感觉（Si），完全按照它们最健康的顺序和比例在进行工作。

你现在的心理系统没有任何内部的损耗和冲突。你主观上的感受应该是极其轻松、头脑清晰且充满探索欲的。你既没有陷入为了讨好别人而丧失原则的社交焦虑，也没有受到对过去细节强迫性恐慌的困扰。你的大脑算力被完全集中在最有价值的地方：去发现外部世界各种有趣的新机会，然后用极其严密的逻辑去判断这些机会能不能在现实中走得通。在这个状态下，你不会觉得每天的生活和工作是在应付麻烦，而是把它们当成一个个可以去研究、去拆解、去优化的有趣议题。你现在的思维活跃度和解决问题的效率处于你个人能力的最高峰。

【具体优势与核心竞争力表现】

处于健康态的你，在工作、学习和日常生活中会表现出极其明显的行为优势。首先，你极其擅长在复杂杂乱的信息中找出新的出路。当你面对一个所有人都觉得无解的死局时，你不会感到畏惧或者绝望。你可以非常迅速地跳出原有的常规框架，从多个完全不同的角度提出好几种备选方案。你现在不仅想法多，而且你看问题非常客观。

更重要的是，你现在具备把这些发散的想法进行严密论证的能力。你不再是那种只负责提出想法然后就不管了的人。当你提出一个新点子之后，你会立刻在脑子里对其进行逻辑推演，去寻找这个点子里面有没有自相矛盾的地方，有没有违背客观事实的漏洞。如果发现不合理，你会立刻抛弃它，不会觉得舍不得。你的行动和思考是高度一致的，没有任何多余的情绪内耗。

在人际关系和沟通方面，你现在的表现非常灵活且有分寸。你完全知道在什么场合该说什么话，你懂得如何用幽默和轻松的语言去活跃气氛，也懂得如何把你的复杂想法用别人能听懂的简单语言表达出来。但是，你现在的这种社交能力是建立在独立客观的基础上的。你不会为了让别人高兴而去赞同一个你认为逻辑上有错误的观点。在工作讨论中，你可以非常激烈地跟别人争论一个问题的对错，但你完全对事不对人。争论结束后，你可以立刻和对方去吃饭聊天，心里不留任何芥蒂。别人会觉得你是一个思维极其敏捷、很好相处，但同时又极具个人原则和专业素养的人。

【深层心理机制分析：各个认知功能的健康协作】

这种极其活跃且稳定的状态之所以能够维持，根本原因在于你内在的认知功能建立了一个良性的、不断接收新信息并进行内部客观加工的处理回路。你的心理防御机制处于完全放松的状态，你不需要耗费额外的精力去压抑任何负面情绪或防御外界的评价。

在健康状态下，你的心理能量流向是由外向内，再由内向外的顺畅循环。外界的新奇信息顺利地进入你的大脑，经过你内部严密的逻辑检验后，得出客观可行的结论，然后再把这些结论通过得体的社交方式表达给外界，或者应用到现实生活中去。整个过程中，没有任何一个功能被过度透支，也没有任何一个功能被强制关闭或者被迫接管不属于它的工作。

【主导功能与辅助功能的完美配合】

你现在状态极佳的核心，在于你的主导功能外倾直觉（Ne）和辅助功能内倾思考（Ti）达成了极其默契的配合。这两个功能是你日常运作的绝对主力，它们现在的合作是毫无阻碍的。

你的主导功能外倾直觉（Ne）在这个阶段非常活跃且健康。它负责时刻对外开放，从周围的环境、网络资讯、书籍以及与他人的交流中，收集各种新的概念、新的趋势和不同的观点。Ne的存在保证了你的大脑永远不会封闭，它源源不断地为你提供新鲜的思考素材，让你始终觉得生活是有趣的。

当Ne把这些大量且杂乱的信息收集进来之后，你的辅助功能内倾思考（Ti）立刻接手工作。Ti负责对这些信息进行极其严格的逻辑把关。它会逐一判断这些新信息是否符合客观规律，内部的因果关系是否成立。如果一条信息经得起逻辑推敲，Ti就会把它整合进你大脑中已有的知识体系里，让你的认知变得更加全面。如果信息存在明显的逻辑硬伤，Ti就会客观地将其剔除，不管这个信息听起来有多么吸引人。

这两个功能的配合构成了一个完美的筛选机制。Ne负责提供大量的选项，Ti负责选出唯一正确的那一个。正是因为有了Ti在内部严密把控，你的Ne才不至于变成不切实际的胡思乱想；也正是因为有了Ne不断提供新东西，你的Ti才不会变成一潭死水，总是有新的逻辑难题可以去拆解。这种配合让你既具备广阔的视野，又拥有极度严谨的判断力。

【第三功能与劣势功能的积极支撑】

在你处于健康态时，你平时深藏不露的第三功能外倾情感（Fe）和劣势功能内倾感觉（Si），不仅没有给你制造任何麻烦，反而为你提供了非常关键的外部润滑和现实兜底。

你的第三功能外倾情感（Fe）现在起到了极其重要的沟通桥梁作用。它不再是那个让你陷入社交焦虑、迫使你去讨好别人的恐慌源头。在健康状态下，Fe被你当作一个极其好用的客观工具。你用它来感知周围人的情绪状态，从而调整你说话的语气和方式。当你需要推行一个你用Ti论证过的正确方案时，你的Fe会告诉你怎么说服别人最有效。你能够照顾到别人的感受，让别人在听取你意见的时候感到舒服，但你绝对不会为了维护表面和谐而放弃你的核心逻辑。这种健康的Fe运作，让你在团队中具有极强的说服力和影响力。

而你的劣势功能内倾感觉（Si），此时也处于一种非常安全和受控的状态。它不再像失控时那样强迫你去纠结过去的失败或者反复检查微小的物理细节。在健康状态下，Si能够以一种极低强度、极其有益的方式参与你的生活。它负责接管你生活中那些不需要动脑子的常规操作。比如，它让你能够记住每天出门要带钥匙，让你能够按时交水电费，让你在工作时能够把必要的文件存放在固定的位置。这些看似微不足道的基础现实秩序，极大地减少了你大脑在日常生活琐事上的决策消耗，让你能把宝贵的精力全部留给Ne和Ti去进行深度思考。

【状态维持与日常保养建议】

虽然你目前处于非常理想的健康态，思维活跃度极高，但作为ENTP，你极其容易因为长时间待在枯燥刻板的环境中、为了追求新鲜感而过度透支精力，或者过度在意他人的评价，而再次滑落到社交内耗的循环或者对细节强迫恐慌的状态中。因此，针对你目前的健康状况，重点在于如何合理地分配注意力，以及如何刻意地维护这条健康的认知回路。以下是为你制定的、旨在长期维持这一健康态的日常运作建议：

【第一方面：新旧信息的平衡与逻辑深度的刻意维持】

【具体行动建议】

你需要刻意保持你大脑接收新信息的频率，但同时必须强制要求自己对这些信息进行深度加工。不要让自己仅仅停留在“知道了一个新概念”的表面兴奋上。当你接触到一个新的行业动态、一本新书的观点或者一个复杂的社会事件时，强迫自己花半个小时的时间，在脑子里或者在纸上，把这个事情的来龙去脉、因果关系清清楚楚地推演一遍。

如果遇到你不懂的逻辑节点，不要跳过去，去查阅客观的资料把它弄懂。同时，不要完全抛弃你以前学过的旧知识。每隔一段时间，把你以前觉得已经弄懂的理论拿出来，用你现在新获取的视角重新去检验一遍，看看有没有可以改进的地方。

【维持目标】

这样做的核心目的是强制锻炼你的辅助功能Ti，防止你的主导功能Ne因为跑得太快而脱离了逻辑的控制。ENTP很容易犯的毛病是只管开局不管结尾，对什么都只懂个皮毛。通过强制要求自己进行深度逻辑推演，你确保了进入大脑的信息都是经过严格检验的有效数据。这不仅能让你的知识体系变得极其扎实，还能在你面对未来的复杂问题时，提供绝对客观的判断依据，防止你再次陷入盲目猜测的混乱之中。

【第二方面：人际边界的绝对划分与情绪隔离】

【具体行动建议】

在人际交往和团队协作中，你要时刻提醒自己：你不需要对任何人的情绪负责，你只对客观事实和事情的最终结果负责。你需要提前在心里设置一条明确的社交边界。

当别人的观点和你在逻辑上发生严重冲突时，直接用平和且确定的语气陈述你的客观论据。陈述完毕后，如果对方因为没有逻辑而开始对你进行情绪化的指责，或者表现出极度的委屈，你绝对不要去反驳对方的情绪，也绝对不要去为了安抚对方而收回你刚才的话。你可以直接停止对话，告诉对方等大家都能客观讨论问题的时候再谈。在日常工作中，不要去刻意猜测上司或者同事对你有什么私人的看法。只要他们没有在公开的工作场合指出你的工作失误，你就默认一切正常。

【维持目标】

这个方面的建议是为了保护你的第三功能Fe不被外界的混乱情绪所绑架。ENTP非常容易因为察觉到别人的不高兴，而主动放弃自己的客观立场去迎合别人，从而掉入Ne-Fe的负向循环。通过刻意拉开与他人的情绪距离，只在客观事实的层面上进行沟通，你把自己的核心判断力保护在了一个安全的内部区域。只要你不去过度读取别人那些没有意义的面部表情和言外之意，你的内部逻辑系统就会一直保持稳定和独立。

【第三方面：物理生存底线的强制管理】

【具体行动建议】

你需要极其刻意地、像对待一个重要项目一样去管理你的身体和日常生活环境。因为你的注意力永远在外面，你必须使用外部工具来强制帮你完成Si（内倾感觉）的工作。

去买几十双完全一模一样的袜子，去买几件不需要熨烫的基础款衣服。把你的早餐固定为两三种不需要花费时间选择的食物。在你的手机里设置好所有必须要交的费用的自动扣款功能。更重要的是，在手机日历里设定严格的睡眠时间和吃饭时间的提醒闹钟。当闹钟响起的时候，不管你脑子里正在思考多么有趣的问题，或者你正在跟别人聊得多开心，强迫自己立刻停下来，去吃饭或者去睡觉。

【维持目标】

这是你能够长期保持健康态的最关键防线。你的大脑在进行高速的直觉发散和逻辑推演时，极其消耗生理能量。如果不刻意去维护物理身体的运转和基础的生活秩序，当你的生理能量被彻底榨干、生活陷入一团糟时，劣势功能Si就会不可避免地迎来恐慌性的爆发。通过把基础的身体维护和生活琐事变成一种外部强制的自动化流程，你提前释放了Si的压力，保证了整个认知系统的底层供电网络始终处于满电状态。只要你的身体不垮，现实生活不乱，你强大的大脑就能持续不断地为你输出绝佳的创意和严密的逻辑。
"""
        }
    },
    
    "INFJ": {
        "crisis": {
            "title": "彻底累了：先把拯救世界的任务放一放",
            "text": """
【当前心理状态与行为表现评估】

综合你目前的各项测试数据和日常行为反馈，你现在正处于一种由长期过度承担他人情绪、严重的人际关系透支或核心信念崩塌所导致的认知功能全面过载状态。在荣格认知功能理论的框架下，你目前的评估结果为“Loop+Grip”双重叠加态。具体而言，作为INFJ，你正在经历“内倾直觉（Ni）与内倾思考（Ti）的负向循环（Loop）”，并且同时伴随着“劣势功能外倾感觉（Se）的失控爆发（Grip）”。

这种状态意味着你平时最依赖的、用来连接和理解外部人群的情感通道已经完全彻底地关闭了。你原本用来感知他人需求、维护外部和谐的辅助功能已经罢工。现在，你的全部注意力一方面被死死地困在自己的大脑内部，进行着极其冷酷、充满怀疑的过度逻辑分析；另一方面，你的身体为了逃避这种内部的精神折磨，强制启动了最底层的感官冲动。你现在既不是在用正常的直觉看世界，也不是在用正常的情感去生活。你的大脑只是在极度的内部偏执和极端的外部感官发泄之间来回冲撞，这是一种极其消耗心理能量且让你感到深度痛苦的错乱状态。

【具体困境与行为特征】

在日常生活中，这种双重叠加态会让你表现出极其矛盾且让你自己感到极其陌生的行为模式。首先，你会彻底切断与外界的情感联系。平时那个温和、善解人意、愿意倾听别人烦恼的你完全消失了。你会对所有人产生一种极其笃定的防备心和不信任感。

你的大脑会不受控制地去过度分析别人说过的话、做过的事。你会把别人几周前甚至几个月前的一个微小举动拿出来，用一种极其苛刻的逻辑去推导背后的动机。最终，你会得出一个非常负面的结论：这些人都是自私的，他们接近我都是有目的的，或者这个世界根本没有任何真正的善意。一旦得出这个结论，你会极其果断、毫无留恋地把这些人从你的生活中彻底拉黑，拒绝任何沟通和解释。这种在内部完成审判然后直接切断联系的行为，让你变得极其孤僻和冷漠。

同时，由于劣势功能外倾感觉（Se）的爆发，你在身体和物理行为上会表现出严重的失控。INFJ平时非常注重精神世界的纯粹，对物质和感官享受并不贪恋。但在现在的状态下，你会突然对强烈的物理刺激产生极其病态的渴望。你可能会在深夜毫无节制地吃下大量高热量、重口味的垃圾食品，吃到胃部极其难受才停下来。你可能会疯狂地在网上购买完全不需要的昂贵物品，或者连续十几个小时沉迷于高强度的电子游戏、短视频，让极度喧闹的声音和画面填满你的感官。

更严重的是，这种状态会带来极其猛烈的内部冲突。当你的感官发泄暂时停止时，你大脑里的过度分析机制（Ni-Ti）会立刻调转枪口，开始对你刚才的失控行为进行极其严厉的逻辑批判。你会觉得自己变得极其堕落、肤浅，完全背叛了自己一直坚守的高尚精神追求。这种强烈的自我厌恶和羞耻感会让你感到极度绝望，而为了逃避这种绝望，你又会再次投入新一轮的感官发泄中，形成一个完全无法自控的破坏性闭环。

【深层心理机制分析：为什么会变成这样】

导致你变成现在这种状态的根本原因，在于你的辅助功能外倾情感（Fe）被彻底耗尽并强制关闭了。你内在认知系统中唯一用来跟真实人类建立温暖连接的工具断电了。

在正常且健康的状态下，你的主导功能内倾直觉（Ni）负责在内部洞察事物的深层意义和未来走向。然后，你的辅助功能外倾情感（Fe）负责把你看到的这些深层意义，通过充满同理心和人情味的方式表达出来，去帮助和影响周围的人。Ni提供深刻的思想，Fe提供温暖的人际接口。这两个功能配合，让你成为一个既有思想深度又让人感到温暖的人。

但是，INFJ极其容易在人际关系中过度付出。当你长期身处一个不断向你索取情绪价值、却从不回馈你的环境中，或者当你发现你倾注了大量心血去帮助的人最终背叛了你、违背了你的核心价值观时，你的外倾情感（Fe）会感到极度的痛苦和疲惫。因为Fe需要外界的正向反馈来维持运转。当外界持续给你带来情感伤害时，为了保护你不再继续受伤，你的大脑采取了最极端的防御手段：它直接把负责感受外部情绪的Fe功能彻底关闭了。

当Fe关闭后，你的主导功能Ni依然在高速运转，它需要一个功能来配合处理信息。因为不能再向外寻找情感连接，它只能向内寻找，于是它对接上了你的第三功能内倾思考（Ti）。内倾思考（Ti）是一个极其冷酷、只讲客观逻辑和分类的功能。

【劣势功能失控与负向循环的叠加逻辑】

当Ni和Ti这两个内倾功能开始单独配合时，一个完全脱离了人类温度的死循环就彻底形成了。

你的Ni依然在洞察，但因为它失去了Fe带来的善意滤镜，它现在只盯着事物最黑暗、最负面的可能性。接着，Ni把这些关于人性阴暗面的预测交给Ti。Ti根本不关心人的感受，它只负责找证据。于是，Ti开始在你过去的记忆中翻找各种细节，用极其严密的逻辑去证明Ni的负面预测是对的。

比如，Ni提出：“这个人其实在利用我。”Ti立刻补充：“没错，逻辑上完全成立，因为上个月他找你帮忙时，他的语气里缺乏应有的尊重，并且事后也没有提供对等的回报。”

在这个过程中，你觉得自己非常理智、非常清醒，你觉得你终于看透了世界的真相。但实际上，你是在用一种极其偏执的内部逻辑，给自己打造了一个没有任何光亮的牢笼。你切断了所有外部真实信息的输入，只在自己的脑子里进行单向的定罪推导。

这种持续的内部审判和极度悲观的思考，会极其快速地榨干你的心理能量。大脑为了阻止你因为过度思考而彻底崩溃，必须强行转移你的注意力。这时，平时被你严格压制的第四功能——劣势功能外倾感觉（Se）就彻底失控了。

Se强行切断了你的内部思考，它要求你立刻、马上关注眼前的物理现实。因为你平时极少去健康地使用它，它现在的使用方式是极其粗暴和没有节制的。它通过让你暴饮暴食、疯狂购物或者沉迷感官刺激，用极其强烈的物理快感或者痛感，来强行覆盖你大脑内部那些痛苦的逻辑推演。你现在的行为，完全是由内部对人性的极度失望和外部对感官刺激的极度依赖共同驱动的。你完全失去了平衡。

【30天状态恢复与调整计划】

针对目前这种情感通道完全封闭、内部过度分析和外部感官双重失控的状态，你必须明确一个事实：你不可能通过在脑子里把事情想通来解决问题。你脑子里的逻辑系统现在是专门用来制造痛苦的。你越是去分析别人的动机，你陷得就越深。

恢复的唯一路径是：首先通过极其强硬的物理手段，阻断破坏性的感官失控行为；其次，通过低强度、无压力的现实接触，让身体恢复基本的物理平静；最后，通过极其微小且安全的客观互动，把你关闭的外倾情感（Fe）重新强制开机。以下是为你制定的、严格分为三个阶段的30天恢复计划：

【第一阶段：感官阻断与物理隔离（第1-3天）】

【具体行动建议】

在这个阶段，你的意志力是完全不可靠的。你必须在物理环境上制造硬性的阻断，强行停止Se的破坏行为。

立刻清理你的居住环境。把你用来暴饮暴食的零食全部扔掉，只保留最基础的食材。卸载手机上所有的购物软件、短视频软件和游戏。把信用卡交给家人保管，或者直接锁起来。如果在深夜你感到极其强烈的冲动想要去买东西或者吃东西，立刻去洗手间用冷水洗脸，然后强迫自己躺在床上闭上眼睛，哪怕睡不着也必须躺着。

在这三天里，不要去思考任何关于人际关系、人性善恶或者未来人生走向的问题。当你发现自己的脑子又开始对某个人进行逻辑定罪时，立刻大声对自己喊“停”。你的唯一任务就是克制住身体的失控冲动，允许大脑里有一大堆没有答案的疑问存在，不去理会它们。

【阶段目标】

这个阶段的核心目标是强行止损。处于双重叠加态的INFJ，最致命的消耗来自于失控行为发生后的严重自我攻击。通过设置物理障碍，你强制身体停止制造新的糟糕事实。只要你不去暴饮暴食或者疯狂花钱，你就切断了事后那个极度痛苦的自我批判环节。这会让你虽然感到焦虑，但至少不会让局面继续恶化。

【第二阶段：无压力现实接触与情绪出口（第4-10天）】

【具体行动建议】

当最剧烈的感官冲动被按住之后，你需要开始主动地给劣势功能Se提供健康的、毫无压力的物理输入，同时给你的内部压力寻找一个不会伤害别人的安全出口。

在身体层面，你需要极其刻板地执行每天的作息。按时吃饭，并且去吃那些成分简单、对身体有益的食物。每天花四十分钟去外面散步。在散步的时候，强迫你的眼睛去看具体的物体：去看这栋楼有几层，去看路边的指示牌上写了什么字。不要去想这些东西背后的意义，只看它们表面的物理状态。

在心理层面，拿出一个没有任何人能看到的实体笔记本。把你脑子里那些极其负面、极度偏执的想法，那些对别人的怀疑和攻击，全部原封不动地写在纸上。写的时候不要去管逻辑对不对，也不要去管这些话有多难听。把脑子里的东西全部倒在纸上。写完之后，立刻把本子合上藏起来，绝对不要去翻看你写了什么。

【阶段目标】

这个阶段有两个目标。第一个目标是用健康的物理节律去安抚Se，让大脑确认当前的现实环境是安全的、不需要用极端方式来逃避的。第二个目标是把Ni和Ti在内部制造的认知垃圾排出体外。写字这个物理动作，强迫你的内部想法变成具体的文字。一旦这些想法落在了纸上，它们就不再在你的脑子里无限循环了。你的大脑内存会被逐渐清理干净。

【第三阶段：重启辅助功能与认知归位（第11-30天）】

【具体行动建议】

经过前两个阶段的清理和安抚，你的破坏冲动已经消失，内部的偏执也大大减轻。现在，你需要正式重启你断线的核心功能——外倾情感（Fe）。你必须重新建立与外部人类的连接，但这种连接必须是极其安全、极其微小的。

绝对不要立刻回到以前那种去承担别人情绪、去当别人心理医生的状态。你需要去做一些没有任何情感负担的外部互动。比如，去楼下的便利店买东西时，看着收银员的眼睛，用正常的声音说一句“谢谢”。在网上看到别人提出一个客观的技术问题时，如果你知道答案，用最简短的话给出回复，不要带任何多余的情感交流。

如果条件允许，去参加一个完全陌生、只需要动手不需要深聊的线下活动，比如陶艺课或者社区的植树活动。在活动中，只进行必要的操作沟通，去感受周围一群人为了一个具体目标而共同做事的客观氛围，不去评判任何人的动机。

【阶段目标】

这是彻底打破Loop+Grip叠加态最关键的一步。外倾情感（Fe）需要通过外部的真实反馈来恢复功能。当你开始进行这些最基础的、没有任何伤害风险的礼貌互动时，你的Fe被重新激活了。

你的主导功能内倾直觉（Ni）终于重新获得了来自外部的真实人类数据。它会发现，虽然世界上确实有自私的人，但那个便利店店员的微笑是真实的，网友的一句感谢也是真实的。当这些正常的、不带恶意的外部数据不断输入时，Ni会立刻修正之前那个“世界上全都是坏人”的极端模型。同时，那个冷酷的内倾思考（Ti）也会因为有了正确的数据而停止进行负面推导。当你的情感通道重新打开，能够以一种有边界、不过度卷入的方式感知外部世界时，你将彻底走出这片黑暗的认知泥潭，恢复到那个思想深邃、温和且具有清晰个人原则的正常状态。
"""
        },
        "grip": {
            "title": "身体失控：别折腾自己，去吃顿美食",
            "text": """
【当前心理状态与行为表现评估】

综合你目前的各项测试数据和日常行为反馈，你现在正处于一种非常典型的“Grip（劣势功能失控爆发）”状态。在荣格认知功能理论的框架下，这意味着你作为INFJ，你平时最核心、最依赖的那个用来思考未来和寻找事物深层意义的功能——内倾直觉（Ni）——已经完全停止了工作。与此同时，你平时极力忽略、压抑在潜意识最底层的第四功能，也就是劣势功能外倾感觉（Se），突破了理智的限制，全面接管了你的思维和身体行为。

对于一个习惯了深思熟虑、总是追求精神纯粹和长远目标的INFJ来说，进入这种状态是非常反常且让人极其痛苦的。你原本引以为傲的洞察力、对复杂事物的理解能力，在这一刻全部消失了。你发现自己完全失去了思考未来的能力，反而被困在了极其强烈的物理感官冲动和对眼前物质的病态渴求中。这并不是因为你的性格突然变坏了，或者你失去了自制力。这仅仅是因为你的心理能量在长期的精神内耗中被彻底榨干，你的大脑为了防止系统彻底崩溃，强制关闭了极其消耗能量的高级思考功能，启动了一套基于纯粹物理感官的备用应急系统来面对外部环境。

【具体困境与行为特征】

在日常生活中，处于Se Grip状态会让你表现出与平时截然相反的行为模式。总体来说，你的注意力从“深刻的精神世界”被强制拉回到了“肤浅的物理感官”上。

最明显的一个特征是，你出现了严重的感官失控和对物质刺激的强迫性依赖。平时的你对吃喝玩乐这些外在的感官享受并不怎么在意，你更在乎精神上的共鸣和内心的平静。但在现在的状态下，你对物理感官的刺激产生了极其强烈的渴求。

具体表现在，你可能会无法控制地大量进食，尤其是那些平时你觉得不健康的高糖、高脂肪食物。你吃东西根本不是因为肚子饿，而是为了感受食物在口腔里的咀嚼动作，为了让强烈的味道刺激你的味觉，你甚至会一直吃到胃部极其难受、产生物理痛觉才停下来。你可能会在深夜毫无目的地疯狂滑动手机屏幕，看那些毫无营养的短视频，仅仅是为了让高频闪烁的画面和吵闹的声音填满你的视觉和听觉。你还可能会在网上冲动购买大量你根本不需要的实体物品，你在乎的不是物品本身的实用价值，而是点击付款和拆开快递包装那一瞬间的物理刺激。

此外，你会表现出对周围物理环境细节的强迫性关注。你平时更关注事情的整体意义，可以容忍生活环境有一些凌乱。但现在，你可能会突然花上好几个小时去清理房间里的每一个角落，把书本按照严格的高度排列，极其苛刻地要求桌面上一尘不染。你会把所有的精力都耗费在整理这些毫无意义的物理细节上，却对真正需要交付的紧急工作或者重要的人际沟通视而不见。

事后，当你的主导思考功能有短暂的恢复时，你会对自己的这些失控行为感到极度的内疚、自责和强烈的自我厌恶。你会觉得自己变得极其软弱、堕落，完全丧失了对生活的掌控权，觉得现在的自己极其肤浅。这种强烈的羞耻感又会进一步加重你的心理负担，让你为了逃避这种痛苦，再次转身投入到新一轮的感官发泄中，形成一个极具破坏性的行为闭环。

【深层心理机制分析：为什么会变成这样】

要弄清楚你为什么会陷入这种完全不受控制的感官冲动状态，我们需要深入分析你内在认知功能的工作机制，以及它们在极端压力下是如何发生错乱的。

在你的认知功能排序中，第一位的主导功能是内倾直觉（Ni），它负责在内部构建宏大的精神愿景、看清事物的本质并进行长远的战略预测。排在第四位的劣势功能是外倾感觉（Se），它负责处理当下的、具体的、外部的物理感官刺激，包括颜色、声音、味道和当下的身体动作。

内倾直觉（Ni）和外倾感觉（Se）在处理信息的方式上是完全对立的。Ni要求你脱离当下，去思考遥远的未来和抽象的意义；而Se要求你放弃思考，去感受此时此刻的物理现实。因为大脑的能量是有限的，为了保证主导功能Ni的高效运转，你的大脑在日常生活中会有意无意地压抑劣势功能Se的活动。你会习惯性地忽略身体的疲惫，忽略周围环境的物理变化，强迫自己把所有的精力都集中在脑海中的长远目标和复杂的精神思考上。

但是，这种压抑是有限度的。当你长期处于极度消耗精神能量的环境中，比如为了一个毫无希望的项目苦苦支撑，或者长年累月地处理极其复杂且充满冲突的人际关系，你的身体一直没有得到真正的休息。或者，当你投入了巨大心血、经过严密思考的长期信念突然遭遇了现实的毁灭性打击，宣告彻底失败时，你的主导功能Ni会遭受重创。你的大脑会发现，无论你怎么深刻地去思考未来，现实总是极其糟糕且脱离你的掌控。此时，Ni消耗了所有的心理能量，再也无法维持正常运转，它彻底崩溃并暂时下线了。

当作为最高指挥官的Ni失效后，原本被压抑在潜意识底层的劣势功能Se就失去了所有的束缚。它带着巨大的、长年累积的原始能量，直接冲到了你的意识表面，强行接管了你的身体和行为控制权。这就是Grip状态产生的根本原因：不是你的自制力变差了，而是你用来控制物理冲动的最高级认知系统彻底停摆了。

【劣势功能失控的逻辑】

当劣势功能Se接管你的大脑时，它表现出来的运作方式是非常粗糙、极端且缺乏任何长远考虑的。

因为你平时很少主动去健康地使用这个功能，你的Se处于一种非常原始和饥渴的状态。一个外倾感觉功能成熟的人，可以很自然地享受当下的生活，品尝美食，进行适度的体育锻炼，并且能够在感官享受和长远利益之间保持平衡。但是，你现在爆发出来的Se，是没有任何节制和策略可言的。

在失控的Se看来，处理你当前极度痛苦和焦虑的唯一方式，就是用更强烈的外部物理刺激来强行覆盖大脑内部的思考。它不关心你的未来会怎么样，它也不关心你的精神追求，它只关心现在这一秒钟的身体感受。所以它强迫你吃下过量的食物，因为胃部的撑胀感可以让你暂时停止思考；它强迫你疯狂购物，因为物质占有的动作可以短暂填补你内心的空虚；它强迫你过度关注排列物品的物理细节，因为控制这些现实的小物件，能让你产生一种虚假的安全感。

由于你的主导预测功能（Ni）已经下线，你现在完全失去了评估行为后果的能力。你不再去计算买这些东西会透支多少钱，也不再去考虑吃这么多垃圾食品会对身体造成什么损害。你现在的行为逻辑，完全是由一种对内部精神痛苦的极度逃避和对外部物理刺激的极度渴求所驱动的。你正在用一种极其低效且极其伤害自己的方式，试图把你的注意力从崩溃的内部精神世界强行拉回到外部的物理现实中。

【30天状态恢复与调整计划】

针对目前这种劣势功能全面爆发、感官处于失控状态的情况，调整的核心思路非常明确：你绝对不能在这个时候试图去进行任何深刻的精神反思，也绝对不能试图用你残留的自制力去批评自己。你现在的大脑系统完全不支持任何关于未来的抽象思考。你越是逼迫自己去思考意义，你的内部压力就会越大，Se的爆发就会越猛烈。

恢复的顺序必须是：首先通过极其强硬的物理手段切断所有破坏性的感官刺激源，强制终止失控行为；其次，通过健康、低强度的物理接触，有意识地安抚和满足Se的现实需求；最后，通过极其微小且能立刻看到正向结果的现实任务，慢慢把你的内部思考功能重新唤醒。以下是为你制定的、严格分为三个阶段的30天恢复计划：

【第一阶段：物理障碍设置与感官强制切断（第1-3天）】

【具体行动建议】

在这个阶段，你的判断力和自控力是完全不可靠的，你无法通过告诉自己“不要做”来对抗感官冲动。你需要做的是在物理环境上制造极其强硬的阻断。

立刻切断所有导致你进行极端感官发泄的途径。如果你最近在暴饮暴食，请立刻把你住所里所有的高热量零食、含糖饮料全部清理掉，只保留最基础的米面和蔬菜。如果你在疯狂购物，立刻卸载你手机上所有的电商应用，把支付密码改成一个极其复杂的随机数字并记在纸上锁起来。如果你沉迷于短视频或者游戏，请把家里的路由器电源拔掉，自己只保留最基本的通讯功能。

这三天里，不要试图去思考你为什么会变成这样，也不要对自己的失控行为进行任何复盘。当你发现自己的感官冲动再次袭来，想要去买东西或者吃东西时，立刻去喝一大杯温水，然后躺在床上强迫自己闭上眼睛。你的唯一任务就是通过物理隔离，强制停止那些正在损害你身体和财务的行为。

【阶段目标】

这个阶段的核心目标是强行止损和阻断破坏性行为。处于Grip状态的INFJ，必须首先被剥夺作恶的物理条件。通过设置不可逾越的物理障碍，你强制你的身体停止对高强度刺激的依赖。这会让你在短期内感到极度的烦躁、空虚甚至身体上的戒断反应。你必须忍耐过去，只有把这种极端的物理冲动硬生生地按住，你才有可能省出一点点力气去进入下一步的调整。停止制造新的糟糕事实，是你当前唯一需要做的事情。

【第二阶段：健康感官输入与微型物理秩序（第4-10天）】

【具体行动建议】

当最剧烈的冲动和戒断反应稍微平息之后，你需要开始主动、有意识地给你的劣势功能Se提供健康的、低强度的物理输入。你要学会在不带任何破坏性的前提下，安全地与现实物理世界接触。

在这个阶段，把你的注意力全部集中在最基本的身体维护上。每天保证充足的睡眠，按时吃三顿成分简单的热饭。在吃饭的时候，不要看手机，不要思考人生的意义，只关注你嘴里食物的物理质感、温度和咸淡。

每天安排至少四十分钟的户外步行。在走路的时候，不要戴耳机，不要听任何播客或者音乐。强迫你的眼睛去观察路边物体的物理状态，去看树叶的边缘，去看地面上的纹理，去感受空气吹在皮肤上的温度。

此外，你可以每天花二十分钟的时间，有意识地清理一个非常小的物理区域，比如洗手台或者你的床铺。在做这些动作时，告诉自己现在的物理环境是干净和安全的。但是时间一到必须立刻停止，不要让它演变成一种强迫行为。

【阶段目标】

这个阶段有两重目标。第一重目标是用健康的物理接触去满足Se的渴望。你的Se现在非常需要感知现实，通过专心吃饭、户外步行和简单的物理整理，你给它提供了一个安全的出口。当它得到了正常的满足后，它就不会再通过暴饮暴食或者疯狂购物来强行夺取控制权。

第二重目标是帮助你的大脑重新建立与客观物理世界的健康连接。过去你过度忽略身体，现在你通过这些具体的动作，向你的神经系统确认：当下是安全的，物理世界并不是只有破坏和失控，它也可以是平静和有序的。这能够极大地缓解你内在的焦虑感和悬空感。

【第三阶段：主导功能重启与意义归位（第11-30天）】

【具体行动建议】

到了这个阶段，你的感官冲动已经基本消失，生活节奏恢复了基础的平稳。现在，你需要通过极其微小但具有正面意义的行动，把你断线的核心功能内倾直觉（Ni）和外倾情感（Fe）重新拉回工作状态。

你需要开始做一些非常具体的、能够立刻给别人或者给自己带来微小帮助的现实任务。不要去制定一年的宏大计划，只去做眼前的具体小事。比如，去解答网友提出的一个非常基础的客观问题，去把积攒了很久的书本捐赠给旧书回收机构，或者去认认真真地写一封只有几句话的感谢信给曾经帮助过你的人。

完成这些任务后，你需要去注视这些任务产生的客观结果。如果你在执行的过程中，脑子里又冒出“做这些小事根本改变不了世界”的悲观想法，直接忽略它，强迫自己先把手头这十分钟的事情做完。

【阶段目标】

这个阶段的核心目标是让你的精神预测功能和情感连接功能重新掌权。你的内在系统需要外部的正面反馈来重新启动。当你完成了一个具体的任务，并看到了它产生的微小但确定的正面结果时，你的大脑就获得了一次成功的运转经验。

这种客观成功的微小数据会不断向上反馈给你的主导功能Ni。你的Ni会逐渐发现，虽然之前的宏大愿景失败了，但当下的现实依然可以通过具体的行动去产生正向的意义。随着这种正向反馈的积累，Ni的信心会逐渐恢复。它会重新开始运转，去构建新的、更加切合实际的精神目标。当你的精神思考能力和现实行动能力重新结合，劣势功能Se就会安静地退回到潜意识中去。此时，那个具备深度洞察力、温和且充满内在力量的你，就彻底回归了。
"""
        },
        "loop": {
            "title": "越想越偏：别把自己关起来，找人聊聊",
            "text": """
【当前心理状态与行为表现评估】

综合目前的各项测试数据和你的日常反馈，你现在正处于一种极其隐蔽但极度消耗能量的“Loop（负向循环）”状态。在荣格认知功能理论的框架下，你作为INFJ，目前的评估结果显示，你负责与外部世界进行情感连接的辅助功能已经被大脑强制关闭。你现在正在经历“内倾直觉（Ni）与内倾思考（Ti）的负向循环”。

这种状态与彻底失控、充满破坏性的Grip状态完全不同。在单纯的Loop状态中，你并不会表现出暴饮暴食或者疯狂购物等物理层面的失控。从外部表现来看，你比平时显得更加安静、冷静，甚至看起来极其理智。但是，这是一种极其病态的理智。你的内在实际上处于一种完全封闭、极度偏执且对外界充满防备的状态。你的心理能量没有用来感知他人的善意，而是全部在内部打转。你的大脑正在使用极高的算力，去对周围的人和事进行毫无必要的冷酷拆解，导致你陷入了极其严重的人际隔离和精神内耗。

【具体困境与思考特征】

在日常生活中，处于Ni-Ti Loop状态会让你表现出极其隐蔽但极其伤人的固执和冷漠。首先，你会发现自己完全丧失了平时那种同理心和共情能力。面对别人的求助或者倾诉，你的第一反应不再是去理解对方的感受，而是在脑子里直接开始分析对方说话的逻辑漏洞，或者审视对方是不是在利用你。

你会对周围的人和环境产生一种极其笃定且难以被说服的怀疑态度。你的注意力不可控制地集中在寻找别人的“真实动机”上。你会花费几个小时的时间独处，在脑子里反复推演同事今天对你说的一句普通的话。你会把你内心的悲观预测（Ni），配合上极其严苛的逻辑分析（Ti），去证明对方是一个虚伪、自私或者不值得信任的人。一旦你在脑子里完成了这套严密的逻辑定罪，你会毫不犹豫地在心里把这个人彻底划掉，切断与对方的所有情感联系。

在这个过程中，你拒绝听取任何外部的解释。如果别人试图向你澄清误会，你会表现出极度的抗拒和不屑。你会在心里觉得：“你说的这些表面理由根本骗不了我，我已经看透了你底层的运转逻辑。”你觉得自己掌握了绝对的真理，觉得世界上只有你一个人是清醒的，其他人都非常愚蠢和虚伪。

此外，你的社交意愿会降到极低的水平。为了避免外部世界的“愚蠢”干扰你内部的这套分析系统，你会主动拒绝绝大部分的人际交往。你觉得和别人沟通不仅非常疲惫，而且完全是在浪费时间。整体来看，你的生活变成了一个完全与世隔绝的内部法庭，你每天都在脑子里对外界进行审判，你被困在了自己对人性的负面预测和极度冷酷的逻辑推导之中。

【深层心理机制分析：为什么会变成这样】

这种状态的根本原因，在于你为了防御外界的情感伤害和无效消耗，主动切断了大脑获取外部人类情感反馈的通道。

在你处于健康状态时，你的主导功能内倾直觉（Ni）负责在内部洞察事物的深层规律，而你的辅助功能外倾情感（Fe）负责在外部世界感知他人的情绪、建立温暖的人际连接。Ni为你提供深刻的思想，Fe负责把这些思想用别人能接受的方式表达出来。这两个功能配合，让你能够温和且深刻地影响周围的环境。

但是，INFJ极其容易在人际关系中过度透支自己。当你长期处于一个不断向你索取情绪价值却从不回馈你的环境中，或者当你发现你极度信任的人违背了你的核心原则，给你带来了巨大的情感创伤时，你的外倾情感（Fe）会感到极度的痛苦和疲劳。因为Fe需要外界的正向情感反馈来维持正常的运转。当外界持续给你带来伤害和失望时，为了保护你不再继续受伤，你的大脑采取了最直接的防御手段：它强行关闭了负责对外感受情绪的Fe功能。

当Fe被关闭后，你的洞察和预测中心（Ni）就断绝了外部真实情感数据的输入。但是，Ni是一个必须时刻保持运转的功能，它必须不断地去预测和分析。既然外部的情感通道被堵死了，它就只能转身向内部去寻找合作对象。于是，它直接对接上了你的第三功能内倾思考（Ti）。内倾思考（Ti）是一个极其冷酷、完全不考虑人情世故、只看重客观逻辑和分类的功能。

【认知功能受阻的逻辑】

当Ni和Ti这两个完全向内运作的功能开始单独配合，并且完全没有外部情感（Fe）参与时，一个完全脱离了人类温度的死循环就彻底形成了。

首先，主导功能Ni提出一个预测：“我的这个朋友最近不怎么联系我，他以后肯定会彻底背叛我或者抛弃我。”

如果是健康状态，Fe会让你直接去问这个朋友最近是不是遇到了什么困难，从而获取外部的真实反馈。但是现在Fe关闭了。

接着，第三功能Ti接到了Ni的这个预测。Ti根本不关心这个朋友的死活，它只负责找证据来验证这个预测。于是，Ti开始在你的记忆库里翻找数据。它找到了半年前这个朋友迟到的一次经历，找到了这个朋友曾经说过的一句不太妥当的话。Ti把这些零碎的数据用极其严密的逻辑拼凑起来，得出一个结论：“根据历史行为数据和逻辑推导，这个人确实存在不可靠的特质。”

然后，Ni接收到了Ti的这个逻辑结论。Ni会把这个结论当作确凿的证据，进一步加深对未来的负面预测：“你看，我的直觉是对的，逻辑也证明了这一点，人就是不可靠的。”

这个被加强的悲观预测，又会促使Ti去寻找更多别人身上的逻辑漏洞。这就形成了一个坚不可摧的内部闭环。你并不是在发泄情绪，你是在用你最强大的洞察力配合最严密的逻辑，给自己编织一套“世界充满恶意”的定论。你用内部的逻辑去证明内部的直觉，然后又用内部的直觉去强化内部的逻辑。因为整个推导过程完全没有去核实当事人的真实想法，你觉得自己的分析天衣无缝。你越分析，越觉得别人不堪；你越分析，越觉得没有必要去和任何人建立联系。最终，你彻底失去了在现实世界中与他人正常交往的能力。

【30天状态恢复与调整计划】

针对目前这种认知功能陷入内部死循环、完全排斥外部情感反馈的状态，调整的核心思路非常明确：你绝对无法通过在脑子里把事情想通来打破这个循环。Ni和Ti的结合会排斥一切内部的自我反驳。你越是在脑子里试图说服自己“别人没有那么坏”，你就陷得越深，因为这依然是在使用内倾功能进行分析。

唯一的出路是强制重启被你关闭的辅助功能——外倾情感（Fe）。你必须通过具体的、涉及外部真实人类的客观互动，把带有温度的现实数据强行塞进你的认知系统里。只有当你的大脑接收到了真实的、非恶意的外部反馈，旧的冷酷预测链条才会被打断。以下是为你制定的分为三个阶段的30天恢复计划：

【第一阶段：停止内部审判与转移注意力（第1-7天）】

【具体行动建议】

在这个阶段，你的首要任务是打断Ni和Ti的不断对话。当你发现自己又开始在脑子里分析某个人的动机，或者又开始用逻辑去推演某段关系注定会失败时，你需要在物理层面上叫停这种行为。

你可以直接从椅子上站起来，或者用冷水洗脸。然后，立刻强制你的注意力转移到完全不需要动用逻辑分析的物理动作上。去把家里的碗洗了，去用拖把把地板拖一遍，或者按照说明书去拼装一个简单的物件。

在这个星期里，绝对不要去思考任何关于人性、道德或者长远关系的问题。把你每天的注意力限制在最基础的物理操作上。不要去问“这个人为什么要这么做”，只去关注“这件衣服有没有洗干净”。

【阶段目标】

这个阶段的核心目标是切断内倾思考（Ti）向内倾直觉（Ni）输送负面逻辑证据的链条。通过强制把注意力转移到毫无逻辑深度的物理动作上，你剥夺了大脑继续进行内部定罪的机会。你不需要去证明你的分析是错的，你只需要让大脑停止分析。只要大脑不再继续编织那套冷酷的理论，你内部的紧绷感和对外界的敌意就会出现松动。

【第二阶段：无害社交观察与停止评判（第8-14天）】

【具体行动建议】

当内部的无休止分析稍微停歇后，你需要开始用极其微小、并且完全没有压力的外部观察，去刺激你的外倾情感（Fe）。这里的关键是“只观察，不互动，不评判”。

你需要在接下来的七天里，每天刻意去一个人多但是不需要你说话的地方待半个小时。比如，去商场一楼的长椅上坐着，去一家人流量很大的咖啡馆的角落里待着，或者去公园看那些完全陌生的人。

在观察这些人的时候，禁止在脑子里去分析他们的职业、性格或者他们说话的动机。你只需要去观察他们表面的情绪状态。看到那个小孩在笑，你就在心里确认“他在笑”；看到那个人在皱眉头，你就确认“他在皱眉头”。绝对不要去推导他们为什么笑或者为什么皱眉。

【阶段目标】

处于Loop状态的你，极度排斥真实的人类，因为大脑默认人类的动机都是复杂的、会带来伤害的。这个阶段的目标就是通过这些毫无压力的表面观察，向你的认知系统证明一个事实：世界上有很多普通的人类情绪是简单的、没有恶意的。

当你看到一个母亲在耐心哄孩子，或者两个陌生人互相让路时，你的外倾情感（Fe）就会接收到这些正常的、不带攻击性的信号。随着这些安全的人类情绪不断输入，你的主导功能Ni会发现，外部世界并不是完全按照你脑子里那个冷酷的逻辑模型在运转的。这就为你重新建立与他人的连接打下了基础。

【第三阶段：微量外部互动与情感通道重启（第15-30天）】

【具体行动建议】

经过前两个阶段的铺垫，你的大脑对外部人类的抗拒感已经大大降低，Fe功能已经处于待机状态。现在，你需要主动把它应用到你真实的日常生活中去。

你必须开始强制自己进行一些极其微小、明确且安全的善意互动。每天给自己设定一个指标，对三个不同的人进行一次简单的正面反馈。比如，在买咖啡的时候，看着店员的眼睛认真地说一句“谢谢你”；在电梯里帮别人按一下楼层；或者在同事顺手帮你递东西的时候，给出一个明确的微笑。

做这些事情的时候，不要去预设对方会有多感动，也不要去分析对方的回答是不是足够真诚。你只需要把这个表达善意的动作做出来，然后接受对方最表面的回应。不要去深究。

【阶段目标】

这是彻底打破Ni-Ti Loop的最后一步。当你在强制执行这些外部的互动时，你的外倾情感（Fe）被完全激活了。它重新承担起了与外部人类进行情感交换的责任。

你的主导功能内倾直觉（Ni）终于重新获得了来自外部的真实反馈数据。它不再需要去翻找内部的负面逻辑证据，而是开始忙于处理眼前这些确定的、带有温度的正面回应。当Ni看到别人因为你的一个简单道谢而露出自然的微笑时，它会被迫承认：之前那个“所有人都是自私虚伪”的预测是极其片面的。一旦客观的情感事实推翻了内部的主观逻辑定论，Ni和Fe就会重新建立起健康的合作关系。那个总是试图用逻辑来防御一切的内倾思考（Ti），也会退回到辅助判断的位置上。此时，你将彻底走出冷漠和偏执的死循环，恢复到那个具备深层洞察力、并且愿意对世界释放真实善意的正常状态。
"""
        },
        "growth": {
            "title": "温柔坚定：把心里的理想变成真的",
            "text": """
【当前心理状态与行为表现评估】

综合你目前的各项测试数据和日常行为反馈，你现在正处于一种认知功能运作极其顺畅、心理能量分配极其合理且极其稳定的理想状态，也就是我们通常所说的“健康态”。在荣格认知功能理论的框架下，这意味着你作为INFJ的四个核心认知功能——内倾直觉（Ni）、外倾情感（Fe）、内倾思考（Ti）和外倾感觉（Se），完全按照它们最健康的顺序和比例在进行日常工作。

你现在的心理系统没有任何内部的过度损耗，也没有出现任何功能被强制关闭或者越权接管的情况。你主观上的感受应该是极其平静、通透且充满内在力量的。你既没有陷入为了迎合别人而委屈自己的过度付出中，也没有陷入对外部世界充满防备和敌意的冷漠隔离中，更没有被极端的物理感官冲动所控制。你的大脑算力被完全集中在最有价值的地方：去深刻地理解事物发展的本质规律，并且用一种温和但有明确边界的方式，去和周围的人建立真实有效的连接。在这个状态下，你对自己的生活有着极强的掌控感，你不再觉得每天面对人群是一件极其耗费精力的事情。你现在的精神洞察力和现实生活能力处于你个人状态的最高峰。

【具体优势与核心竞争力表现】

处于健康态的你，在工作、学习和日常生活中会表现出极其明显的行为优势。首先，你的洞察力和对复杂人际局面的理解能力达到了最佳状态。当你身处一个复杂的团队或者面对一个棘手的人际冲突时，你不会被表面的情绪爆发或者争吵所迷惑。你可以非常冷静且极其迅速地看出每个人表面行为背后真实的心理需求和核心利益点。

更重要的是，你现在具备把这种深刻的洞察转化为实际行动的能力。你不再是那个只在心里默默看透一切但不采取行动的人，也不再是那个为了充当好人而去无底线满足所有人要求的人。你能够非常得体地去协调各方的诉求。如果有人向你提出不合理的要求，或者试图对你进行情绪上的勒索，你可以非常直接、语气平和地拒绝对方。你会在明确表达自己底线的同时，指出一条对双方都客观有利的解决路径。你拒绝别人的时候心里没有任何内疚感，因为你清楚地知道，你的拒绝是基于客观事实和长期利益的。

在个人生活和沟通方面，你现在的表现非常真实且有分寸。你不再试图去拯救身边的每一个人。你依然愿意倾听朋友的烦恼，但你现在完全可以把朋友的情绪和自己的情绪隔离开来。听完之后，你能给出一个直击问题核心的建议，如果朋友不采纳，你也不会觉得受挫或者愤怒，你会直接放下这件事，去忙你自己的生活。别人会觉得你是一个思想极其深刻、性格极其温和，但同时又极具原则和距离感的人。你让人感到安全，但绝对不容许别人去侵犯你的个人空间。

【深层心理机制分析：各个认知功能的健康协作】

这种极其平稳且具有力量的状态之所以能够维持，根本原因在于你内在的认知功能建立了一个良性的、不断接收外部真实反馈并进行内部深度加工的处理回路。你的心理防御机制处于完全放松的状态，你不需要耗费额外的精力去压抑任何对人性的失望，也不需要去防备别人的攻击。

在健康状态下，你的心理能量流向是由内向外，再由外向内的顺畅循环。你内部的深刻思想能够顺利地通过健康的情感通道表达给外界，外界的真实反馈也能被你客观地吸收进来，修正你对未来的预测。整个过程中，没有任何一个功能被过度透支，也没有任何一个功能被迫去承担它不擅长的工作。

【主导功能与辅助功能的完美配合】

你现在状态极佳的核心，在于你的主导功能内倾直觉（Ni）和辅助功能外倾情感（Fe）达成了极其默契的配合。这两个功能是你日常运作的绝对主力，它们现在的合作是毫无阻碍且极其高效的。

你的主导功能内倾直觉（Ni）在这个阶段非常清晰且稳定。它安静地在后台运行，不断地整合你收集到的所有信息，去预测事物未来的发展趋势和人的最终走向。它为你提供了一个极其笃定的精神内核和明确的价值观导向。因为你处于健康态，Ni现在的预测完全是基于客观事实和健康心态的，而不是基于防备和偏执的，所以它的判断极其准确。

当Ni给出了深刻的判断之后，你的辅助功能外倾情感（Fe）立刻接手工作。Fe负责把你脑子里那些极其抽象、甚至有些冷酷的真相，转化成带有温度的、符合社会常规的语言表达出来。比如，Ni看出了一个朋友正在交往的对象人品极其糟糕，未来的结果必定是灾难。如果直接说出来，朋友肯定无法接受。这时，健康的Fe就会发挥作用，它会教你在什么时间、用什么语气，通过提问或者分享类似客观案例的方式，去慢慢引导这个朋友自己发现问题。

这两个功能的配合构成了一个完美的社会化表达机制。Ni负责看清极其复杂的真相，Fe负责用最不伤人的方式把真相传递出去。正是因为有了Fe在外部世界不断地进行情感确认和润滑，你的Ni才不会变成一个脱离人群、愤世嫉俗的孤岛；也正是因为有了Ni在内部提供深度的思想支撑，你的Fe才不会变成一个只会讨好别人、没有自己立场的空壳。这种配合让你既具备极其长远的眼光，又拥有极强的人格魅力。

【第三功能与劣势功能的积极支撑】

在你处于健康态时，你平时不太常用或者不太擅长的第三功能内倾思考（Ti）和劣势功能外倾感觉（Se），不仅没有给你制造任何麻烦，反而为你提供了非常关键的内部逻辑校验和外部现实兜底。

你的第三功能内倾思考（Ti）现在起到了极其重要的逻辑防线作用。它不再是那个在受挫时帮你去论证“所有人都不怀好意”的负面工具。在健康状态下，Ti为你所有的情感付出设定了一个极其清晰的客观止损点。当你的Fe想要去帮助一个人的时候，Ti会在旁边冷酷地进行计算：这个人值不值得帮？这个帮助在客观逻辑上能不能解决他的根本问题？如果Ti判断出这个人只是在单方面索取情绪价值，根本不打算做出实际改变，Ti就会立刻给Fe下达停止付出的指令。这种健康的Ti运作，让你在面对极其复杂的人际纠纷时，能够做到极其干脆地抽身而退，绝对不让自己陷入无意义的泥潭。

而你的劣势功能外倾感觉（Se），此时也处于一种非常安全和受控的状态。它不再像失控时那样强迫你去暴饮暴食或者沉迷于低级的感官刺激。在健康状态下，Se能够以一种极低强度、极其有益的方式参与你的生活。它让你能够在高强度的精神思考和人际交往之后，真正地回到物理现实中来放松自己。你可以在下班后花半个小时去整理一下书桌，或者专心地去厨房给自己煮一碗面条，去感受水烧开的声音和食物的香味。这些极其普通的物理感官活动不仅没有消耗你，反而成了你清空大脑内存、把注意力从精神世界拉回现实世界的最佳方式。

【状态维持与日常保养建议】

虽然你目前处于非常理想的健康态，洞察力极强，情绪极其稳定，但作为INFJ，你极其容易因为外界的苦难、朋友的求助或者长期在一个价值观不匹配的环境中工作，而再次因为过度消耗Fe功能，滑落到冷漠偏执的内部循环或者感官彻底失控的状态中。因此，针对你目前的健康状况，重点在于如何极其严格地管理你的心理能量分配，以及如何刻意地维护这条健康的认知回路。以下是为你制定的、旨在长期维持这一健康态的日常运作建议：

【第一方面：人际边界的严格划分与能量保护】

【具体行动建议】

你必须极其刻意地、用硬性规则来管理你的人际交往份额。你需要认识到一个客观事实：你的外倾情感（Fe）虽然很强，但它的电量是极小的，极其容易被耗尽。

在日常生活中，你必须学会极其干脆地过滤掉那些对你进行无效消耗的人。对于那些总是向你抱怨同一个问题却从来不采取行动改变的人，或者那些在沟通中只在乎自己的感受、完全不听你客观建议的人，你必须立刻停止对他们提供任何情绪价值。不要去解释你为什么变冷淡了，直接用物理手段拉开距离：减少见面次数，拉长信息回复的时间，把回复的内容精简到只包含事实判断。

此外，永远不要主动去承担别人的人生课题。当别人遇到困难时，你只提供客观的信息和工具，绝对不去替别人做决定，也绝对不去替别人承担决定带来的后果。

【维持目标】

这样做的核心目的是保护你的辅助功能Fe不被彻底榨干。INFJ最容易犯的错误就是觉得如果自己不帮忙，别人就会很惨。通过建立极其严格的人际边界，强制停止对不值得的人付出，你把极其宝贵的情绪能量全部保留在了自己内部。只要你的Fe始终处于有电的状态，你的主导功能Ni就不会因为失去外部通道而被迫转身向内进行自我折磨。这是你维持心理健康的第一道、也是最重要的一道防线。

【第二方面：内部想法的现实转化与客观输出】

【具体行动建议】

你需要刻意保持你大脑与外部客观现实的对接状态。你脑子里每天都会产生大量极其深刻、极其复杂的关于人生、社会和未来的想法。你绝对不能让这些想法只停留在你的脑子里。

你必须强迫自己把这些抽象的精神产物转化成可以被别人看到的客观现实。你可以每天花一个小时的时间去写作，把你对某件事的深刻洞察用逻辑严密、客观平实的文字写下来；如果你在工作中发现了一个可以优化整体效率的新方法，不要只在心里觉得它很好，去写一份包含具体操作步骤的执行方案提交上去。

当你输出这些内容的时候，不要去在乎别人能不能完全理解你的深意，也不要去管别人会不会给你热烈的赞美。你只需要确认你把内部的思想变成了外部的实体。

【维持目标】

这个方面的建议是为了防止你掉入只有Ni和Ti参与的内部死循环。通过强制要求自己把想法写出来或者做出来，你强迫自己的大脑去使用那些负责处理现实和逻辑的外部工具。一旦你的想法变成了客观存在的文字或者方案，它们就不再属于你内部那些飘忽不定的情绪和预测了。不断产生外部的客观结果，能够极大地增强你的现实落地感，让你确信自己是对现实世界有实际掌控力的，而不是一个只会在脑子里空想的旁观者。

【第三方面：基础物理感官的刻意维护与放松】

【具体行动建议】

你需要极其刻意地、像完成一份重要工作一样去管理你的身体。因为你的注意力永远在关注长远的精神意义，你极其容易忽略当下身体的疲劳和周围物理环境的变化。如果不主动管理，这就是劣势功能爆发的巨大隐患。

你必须把日常的吃、穿、住、行当作非常重要的客观任务来对待。制定一个极其死板的作息时间表，不管你脑子里正在思考多么重要的问题，时间一到，必须放下一切去睡觉或者吃饭。在周末，强制自己安排至少半天的时间，彻底远离所有的电子设备、书籍和需要动脑子的人际交往。去从事一些纯粹的物理体力活动。比如去打扫卫生，去公园里进行没有任何目的的快步走，或者去超市买菜。在做这些事情的时候，只关注你的肌肉动作和物品的物理状态。

【维持目标】

这是你能够长期保持健康态的最底层支撑。你的主导功能Ni在运转时极其消耗生理能量，而你又最容易忽略身体发出的疲惫信号。通过把基础的身体维护变成一种必须执行的现实任务，你提前释放了劣势功能Se的压力，保证了整个认知系统的底层供电网络始终处于满电状态。只要你的身体器官运转正常，没有积累隐形的感官饥渴，你强大的大脑就能持续不断地为你输出精准的洞察和温和的力量。保持物理生活的极其规律和简单，是你维持精神世界极其深刻和复杂的必要条件。
"""
        }
    },

    "INFP": {
        "crisis": {
            "title": "放过自己：允许自己躲一会儿",
            "text": """
【当前心理状态与行为表现评估】

综合你目前的各项测试数据和日常行为反馈，你现在正处于一种由长期违背自身核心价值观、遭遇严重的情感否定，或者面对无法逃避的高压现实任务而导致的认知功能全面过载状态。在荣格认知功能理论的框架下，你目前的评估结果为“Loop+Grip”双重叠加态。具体而言，作为INFP，你正在经历“内倾情感（Fi）与内倾感觉（Si）的负向循环（Loop）”，并且同时伴随着“劣势功能外倾思考（Te）的失控爆发（Grip）”。

这种状态意味着，你平时最依赖的、用来保持内心平和与自我认同的情感评估系统，以及用来探索外部新鲜事物的直觉通道，已经完全瘫痪。你现在不仅完全失去了对生活的热情和对未来的想象力，反而被死死地困在过去痛苦的回忆中进行极其严厉的自我惩罚。与此同时，为了强行摆脱这种内部的极度痛苦，你的大脑强制启动了你平时最排斥的、极其冷酷和死板的外部控制功能。你现在的状态是在极度的自我厌恶和对外部世界极其暴躁的控制欲之间来回切换，这是一种极其消耗体力的心理停滞和行为错乱。

【具体困境与情绪特征】

在日常生活中，这种双重叠加态会让你表现出极其反常、且让你自己感到极度羞耻的行为模式。首先，你完全丧失了平时那种包容、温和且具有同理心的状态。你的注意力被迫全部向内收缩，死死地盯住自己过去犯下的每一个错误。

你的大脑会不受控制地去翻找几年前甚至十几年前发生的尴尬事件、你对别人造成的无心伤害，或者别人对你的负面评价。你会把这些过去的记忆片段拿出来，在脑子里极其清晰地反复播放。在这个过程中，你会重新体验到当时那种极其强烈的愧疚感和痛苦。你不仅没有因为时间流逝而释怀，反而用现在的标准去对过去的自己进行极其严厉的道德定罪。你主观上非常笃定地认为，自己是一个极其糟糕、充满缺陷、根本不值得被爱的人。这种强烈的自我否定让你彻底失去了去接触新鲜事物或者认识新朋友的动力。

但在另一方面，由于劣势功能外倾思考（Te）的爆发，你在外部行为上会表现出一种你平时极其讨厌的刻薄和控制欲。当内部的痛苦达到顶点时，你会突然对外在的物理环境或者周围的人产生极其强烈的暴躁情绪。

你可能会因为同事没有按照规定的时间提交文件，或者家人把东西放错了位置，突然爆发极其严厉的指责。你会用一种极其生硬、只讲规则不讲人情的语气去命令别人，甚至说出非常尖酸刻薄的话来攻击对方的能力低下。你可能会突然给自己制定一张极其苛刻、精确到分钟的工作时间表，强迫自己必须在几个小时内完成大量的工作，完全不顾及身体的疲惫。

但是，这种失控的强硬和暴躁只能维持很短的时间。当你发完脾气，或者那张苛刻的时间表执行失败后，你原本的内倾情感（Fi）会短暂地恢复一点点意识。这时，你会对刚才那个极其刻薄、毫无同理心的自己感到极度的震惊和厌恶。你会觉得现在的自己面目可憎，这种羞耻感又会把你重新推回那个不断回忆过去错误和自我定罪的内部循环中。你就在这种“对内极度自责”和“对外极度暴躁”之间来回撕扯。

【深层心理机制分析：为什么会变成这样】

导致你变成现在这种状态的根本原因，在于你的辅助功能外倾直觉（Ne）被彻底关闭了。你内在认知系统中唯一用来对外寻找希望和不同视角的工具断电了。

在正常且健康的状态下，你的主导功能内倾情感（Fi）负责在内部建立一套极其坚定的个人价值观，判断什么是对的、什么是善良的。然后，你的辅助功能外倾直觉（Ne）负责在外部世界去寻找各种不同的方式，来表达和实现你的这套价值观。Ne为你提供对未来的期待、新鲜的灵感和宽广的包容度。这两个功能配合，让你成为一个内心坚定同时又对世界充满好奇和善意的人。

但是，当你长期处于一个完全不尊重你个人感受、只看重极其死板的客观指标的现实环境中，或者当你遭遇了重大的现实挫折，发现你坚持的善意和价值观在现实中根本行不通时，你的外倾直觉（Ne）会感到极度的受挫。因为Ne去外部探索是需要消耗能量并且需要安全感的。当外界持续给出否定和打压的反馈时，为了保护你不受到更多的外界伤害，你的大脑采取了防御机制：它直接把负责对外开放和寻找可能性的Ne功能强行关闭了。

当Ne被关闭后，你的核心功能Fi就断绝了外部新鲜信息的输入。但是，Fi是一个必须时刻进行价值评估的功能，既然外部没有新的素材进来，它就只能转身向内部去寻找评估对象。于是，它直接对接上了你的第三功能内倾感觉（Si）。内倾感觉（Si）是一个专门用来记录过去的具体事实、细节和身体经验的功能库。

【劣势功能失控与负向循环的叠加逻辑】

当Fi和Si这两个完全向内的功能开始单独配合时，一个完全没有未来和希望的死循环就彻底形成了。

因为你是在极度受挫的高压状态下开启这个循环的，所以Si从记忆库里给你提取出来的，全部都是带有负面标记的数据。Si会非常尽职地向Fi提供你过去所有的失败记录、别人对你的批评、以及你搞砸过的事情的具体细节。

接着，主导功能Fi接收到这些负面记录，开始用它最擅长的价值判断去处理这些信息。Fi的判断是非常深刻和个人化的，它不会客观地看待这些失败，而是把它们全部上升到对自我人格的否定上。Fi得出一个结论：“我过去做错了这么多事，这证明我本质上就是一个没有价值的人。”

这个充满痛苦的结论被得出后，又会被Si当作新的事实记录下来。到了第二天，当Fi再次进行评估时，它不仅会看到过去的错误，还会看到昨天得出的“我没有价值”这个记录。这个循环不断加深，你切断了所有外部的客观反馈，只在自己的脑子里用过去的错误去证明自己当下的糟糕。你完全陷入了停滞。

这种持续的自我攻击和对过去的咀嚼，会极其快速地榨干你的心理能量。大脑为了阻止你因为极度的内部痛苦而彻底崩溃，必须强行转移你的注意力并夺回现实生活的控制权。这时，平时被你严格压制的第四功能——劣势功能外倾思考（Te）就彻底失控了。

Te的运作逻辑是追求外部客观秩序和绝对的执行效率，它完全不在乎人的情感。在你平时健康的时候，你会觉得这种逻辑太冷血。但现在，为了对抗内部那种毫无秩序的痛苦情绪，大脑强制启用了Te。

失控的Te接管身体后，它的做法极其简单粗暴。它认为，只要把外部的物理环境和客观指标强行规范好，内部的痛苦就会消失。所以它强迫你去制定那些根本不可能完成的苛刻计划，强迫你去严厉地挑剔别人的工作细节，强迫你用最生硬的规则去压制别人和自己。你现在的暴躁和控制欲，根本不是因为你变得有执行力了，而是因为你内在的情感系统彻底崩溃后，大脑在用一种极其拙劣和僵硬的方式，试图在外部世界抓取一点点可怜的控制感。

【30天状态恢复与调整计划】

针对目前这种内部极度自责、外部暴躁失控的双重叠加状态，你必须明确一个事实：你不可能通过在脑子里把过去的错误想通来获得原谅，你也绝对不可能通过对外界发脾气或者制定严苛的计划来解决当下的问题。你脑子里的评估系统和外部的执行系统现在都是完全损坏的。

恢复的唯一路径是：首先通过物理手段强行阻断Te的暴躁输出和Fi的内部惩罚；其次，通过毫无压力的、微小的外部接触，慢慢唤醒被你关闭的外倾直觉（Ne）；最后，在Ne的配合下，用极其温和的现实任务重新建立健康的认知秩序。以下是为你制定的、严格分为三个阶段的30天恢复计划：

【第一阶段：停止评判与物理隔离（第1-3天）】

【具体行动建议】

在这个阶段，你的首要任务是打断失控的外倾思考（Te）对外界的攻击，以及打断内倾情感（Fi）对你自己的道德审判。你需要把所有的评价标准强制清零。

在物理环境上，立刻停止制定任何形式的计划表、待办清单或者目标。如果你的桌子很乱，房间很乱，就让它们乱着，绝对不要在此时此刻去强迫自己整理它们。如果你觉得某个人做事极其没有效率，让你感到非常愤怒，立刻离开那个环境，不要去指出对方的错误，也不要去接手对方的工作。

当你独处时，如果脑子里又开始播放过去那些让你感到尴尬和羞耻的回忆，立刻站起来，用手重重地拍一下大腿或者桌子，用物理痛觉强行打断回忆。然后，立刻把注意力转移到最基础的生理活动上。去喝一杯温水，去洗个热水澡，或者直接躺在床上闭上眼睛。

【阶段目标】

这个阶段的核心目标是强制叫停破坏性行为和自我消耗。处于Grip状态的INFP，最容易在暴躁发泄后产生极其严重的内疚感。通过强制停止对外界的控制和指责，你切断了制造新内疚感的源头。同时，通过允许环境混乱、拒绝制定计划，你饿死了失控的Te功能。你需要接受自己现在就是一个完全没有执行力、也不需要去评判任何事情对错的普通物理实体。只有把外部的冲突和内部的定罪强行按住，你才有可能省出一点点力气去进入下一步的调整。

【第二阶段：无压力外部探索与微小变量（第4-10天）】

【具体行动建议】

当最剧烈的情绪波动和暴躁感稍微平息之后，你需要开始主动地去唤醒你被关闭的辅助功能外倾直觉（Ne）。这里的关键是，所有的探索必须是“绝对没有客观评判标准”和“绝对不涉及现实利益”的。

在接下来的七天里，你需要每天去做一件没有任何现实意义、但是带有一点点新意的小事。比如，下班或者放学后，故意走一条你从来没有走过的街道回家。去超市里买一种你完全没有见过的零食或者饮料尝一尝。在纸上随便画一些毫无逻辑的线条和形状，或者去听一种你平时绝对不会听的音乐类型。

在做这些事情的时候，绝对禁止去评价这个零食好不好吃、这首歌好不好听，或者你画的画有没有艺术价值。你只需要去经历这个新鲜的过程。不要去想这些事对你的未来有什么帮助。

【阶段目标】

这个阶段的目标是用毫无压力的微小变量去刺激你的外倾直觉（Ne）。处于Loop状态的你，极度害怕去接触外界，因为你觉得外界充满要求和否定。通过这些没有任何对错标准的新鲜刺激，你向大脑证明了一个事实：外部世界并不总是要求你讲究效率或者证明价值，外部世界也存在很多单纯的、可以随便看看的新东西。当你开始去注意那条新街道上的树木，或者那个新零食的包装时，你的注意力就被成功地从内部的痛苦回忆（Si）中拉出来了。你的Ne开始接收新数据了。

【第三阶段：重启辅助功能与客观执行（第11-30天）】

【具体行动建议】

经过前两个阶段的铺垫，你对外部世界的抗拒感已经大大降低，Ne功能已经处于待机状态。现在，你需要把Ne和健康的外部执行功能（Te）结合起来，应用到现实生活中。

你需要开始做一些非常微小、但能够立刻看到物理结果的客观任务。不要去碰那些让你感到焦虑的核心工作。你可以去清理你电脑里堆积了很久的不重要文件，把它们放进一个文件夹里。你可以去把家里的阳台或者书桌收拾干净。或者，你可以按照网上的教程，去折一个纸飞机，或者照着菜谱炒一盘最简单的青菜。

重点在于，在执行这些任务时，必须允许自己犯错。如果青菜炒糊了，或者纸飞机没折好，直接扔进垃圾桶，然后告诉自己：“这只是一个物理结果，它不代表我这个人没有价值。”

【阶段目标】

这是彻底打破Loop+Grip叠加态最关键的一步。当你在做这些微小的客观任务时，你的外倾直觉（Ne）和外倾思考（Te）重新建立了健康的配合。Ne提供了一个简单的想法（比如炒个菜），Te负责把它执行出来。

因为这些任务极其简单，你很容易就能获得成功的客观结果。当这些正常的、不带情绪压力的现实反馈不断输入时，你的主导功能内倾情感（Fi）终于发现：我可以通过具体的行动在现实中获得平静，而不是只能在脑子里回忆过去。同时，健康的执行过程让大脑确信外部秩序是可控的，那个暴躁失控的劣势功能Te就会自然退回到潜意识中去。此时，你将彻底走出自我惩罚和对外暴躁的死循环，恢复到那个内心温和坚定、对世界重新抱有好奇和宽容的正常状态。
"""
        },
        "grip": {
            "title": "太紧绷了：别逼自己非得像个机器",
            "text": """
【当前心理状态与行为表现评估】

综合你目前的各项测试数据和日常行为反馈，你现在正处于一种非常典型的、由突发性极高压力或者核心个人价值观遭到严重践踏而导致的“Grip（劣势功能失控爆发）”状态。在荣格认知功能理论的框架下，这意味着你作为INFP，你平时最核心、最依赖的那个用来感知情绪、坚守内心善良和道德准则的主导功能——内倾情感（Fi）——已经完全宕机。与此同时，你平时极力忽略、压抑在潜意识最底层的第四功能，也就是劣势功能外倾思考（Te），彻底突破了理智和情感的防线，全面接管了你的思维方式和外部行为。

对于一个平时习惯于共情他人、极度包容且非常反感生硬规则的INFP来说，进入这种状态是非常反常且让人极其恐慌的。你会感觉自己变成了一个极其冷酷、暴躁且不近人情的陌生人。你原本引以为傲的同理心、对事物美好面的感知力，在这一刻全部消失了。你发现自己不仅无法体会别人的难处，反而对周围的一切都充满了苛刻的控制欲和评判欲。这并不是因为你的人格变坏了，或者你变成了一个冷血的人。这仅仅是因为你的心理能量在长期的委屈和内耗中被彻底榨干，你的大脑为了防止你的情感系统彻底崩溃，强制关闭了极其消耗能量的情感感知功能，启动了一套极其生硬、只看重客观结果的备用控制系统来强行应对外界。

【具体困境与行为特征】

在日常生活中，处于Te Grip状态会让你表现出与平时截然相反、甚至让你周围的人感到极其震惊的行为模式。总体来说，你的注意力从“内心的感受和价值”被强制拉回到了“外部的效率和绝对控制”上。

最明显的一个特征是，你变得极其挑剔、毒舌且没有耐心。平时的你非常害怕伤害别人的感情，说话总是极其委婉。但在现在的状态下，你对别人工作上的失误、生活中的拖沓会产生一种无法克制的愤怒。如果同事或者家人没有按照你的要求把事情做好，你会直接爆发，用极其尖酸刻薄、直戳痛处的语言去攻击对方的能力。你完全不在乎对方听了会有多难过，你只在乎这件事情为什么没有高效率地完成。你会变得极其固执己见，采用一种居高临下的命令式语气跟别人说话，拒绝听取任何关于客观困难的解释。

其次，你会表现出一种极其病态的执行力和对外部秩序的强迫症。当这种状态爆发时，你会突然拿出一张纸，给自己制定一个极其严苛、连机器人都很难完成的时间表或待办清单。你会强迫自己立刻去清理极其杂乱的房间，把所有的东西都粗暴地扔掉或者归类；你会强迫自己坐在电脑前，试图在三个小时内处理完积累了一个月的工作。你对效率产生了一种极其不合理的痴迷，你试图用这种疯狂的外部行动来压制你内心的慌乱。

但是，这种失控的强硬状态是非常脆弱的。当你发完脾气，或者当你发现自己根本无法完成那个苛刻的计划表时，你原本的主导功能内倾情感（Fi）会有短暂的苏醒。那一瞬间，你会对刚才那个刻薄、毫无同理心、对别人大吼大叫的自己感到极度的震惊和强烈的自我厌恶。你会觉得现在的自己极其丑陋，完全背离了你一直坚守的善良本性。这种强烈的羞耻感和内疚感会把你彻底击垮，让你觉得自己是一个极其糟糕的人。为了逃避这种无法承受的内疚，你的大脑又会强制把情感功能关掉，再次把你推回那种暴躁和挑剔的状态中。你就一直在这个极具破坏性的闭环里不断挣扎。

【深层心理机制分析：为什么会变成这样】

要弄清楚你为什么会陷入这种完全丧失同理心、变得极其冷酷和暴躁的状态，我们需要深入分析你内在认知功能的工作机制，以及它们在极端压力下是如何发生错乱的。

在你的认知功能排序中，第一位的主导功能是内倾情感（Fi），它负责在你的内心深处建立一套极其坚定、不可侵犯的个人价值观和道德底线，它让你拥有极强的同理心和共情能力。而排在第四位的劣势功能是外倾思考（Te），它负责处理外部世界的客观逻辑、建立规则、追求绝对的执行效率和结果。

内倾情感（Fi）和外倾思考（Te）在处理问题的方式上是完全对立的。Fi要求你关注人的感受、理解背后的苦衷；而Te要求你抛弃所有个人感情，只看客观事实和最终效率。因为大脑的能量是有限的，为了保证主导功能Fi能够健康地去感受世界和维持内心的纯粹，你的大脑在日常生活中会有意无意地极力压制劣势功能Te的活动。你会习惯性地排斥那些死板的规章制度，反感那些为了利益而不择手段的行为，你强迫自己把所有的精力都集中在维护内心的善良和对他人的理解上。

但是，这种压抑是有限度的。当你长期处于一个极其看重冰冷KPI、完全不尊重个人感受的工作环境中；或者当你一直在人际关系中无限度地包容别人，最后却发现别人把你的善良当成软弱，甚至严重践踏了你最核心的价值观时，你的主导功能Fi会遭受毁灭性的打击。你投入了巨大的情感能量去理解世界，世界却给了你极其冷酷的回报。此时，Fi消耗了所有的心理能量，它无法再处理这种极度的痛苦和委屈，再也无法维持正常运转，于是它彻底崩溃并暂时下线了。

当作为最高指挥官的Fi失效后，原本被压抑在潜意识底层的劣势功能Te就失去了所有的束缚。它带着巨大的、长年累积的原始愤怒，直接冲到了你的意识表面，强行接管了你的思维和行为控制权。这就是Grip状态产生的根本原因：不是你突然变成了一个有执行力的强人，而是你用来处理感情的最高级认知系统彻底停摆了。

【劣势功能失控的逻辑】

当劣势功能Te接管你的大脑时，它表现出来的运作方式是非常粗糙、极端且缺乏任何灵活性的。

因为你平时极少去健康地使用这个外部控制功能，你的Te处于一种非常原始和饥渴的状态。一个外倾思考功能成熟的人，可以非常冷静、客观地安排工作，在追求效率的同时也能合理地分配资源。但是，你现在爆发出来的Te，是没有任何策略可言的。

在失控的Te看来，导致你现在如此痛苦的原因，就是因为你以前太软弱、太在乎别人的感受、太没有规矩了。因此，它现在给出的唯一解决方案，就是用最极端的手段把外部世界强行控制起来。它认为，只要外部的物品摆放整齐了，只要别人完全服从你的命令了，只要工作任务被强行推进了，你内心的痛苦就会消失。

由于你的主导情感功能（Fi）和辅助直觉功能（Ne）都已经下线，你现在完全失去了感知他人情绪和寻找其他解决可能性的能力。你不再去考虑你刚才那句话会给别人造成多大的心理创伤，你也不再去思考这件事情是不是有更温和的处理方式。你现在的行为逻辑，完全是由一种对内部情感崩溃的极度逃避和对外部秩序的病态渴求所驱动的。你正在用一种极其生硬且极其伤害周围人的方式，试图在彻底混乱的心理状态中强行建立一种虚假的掌控感。

【30天状态恢复与调整计划】

针对目前这种劣势功能全面爆发、行为变得极其刻薄和强迫的状态，调整的核心思路非常明确：你绝对不能在这个时候试图用这种暴躁的执行力去解决任何现实问题，也绝对不能在清醒的瞬间用极度内疚的情绪去惩罚自己。你现在的大脑系统完全不支持任何客观的计划执行，也不支持健康的情感反思。你越是逼迫自己去制定计划或者去道歉，你的内部压力就会越大，Te的爆发就会越猛烈。

恢复的顺序必须是：首先通过极其强硬的物理手段切断所有让你想要去控制和指责的外部触发点，强制终止失控的执行行为；其次，通过低强度、无压力的无目标输入，慢慢让极其紧绷的神经放松下来；最后，通过极其微小且能立刻唤起你内心认同的真实情感接触，慢慢把你的内部主导功能重新唤醒。以下是为你制定的、严格分为三个阶段的30天恢复计划：

【第一阶段：放弃控制与绝对隔离（第1-3天）】

【具体行动建议】

在这个阶段，你的脾气和控制欲是完全不可靠的，你无法通过告诉自己“我要温和一点”来压制住那种挑剔的冲动。你需要做的是在物理环境上制造极其强硬的阻断，强行剥夺自己发号施令的条件。

立刻停止制定任何形式的计划、清单或目标。把你写好的那些密密麻麻的待办事项直接撕掉或者扔进垃圾桶。如果你的房间很乱，直接关上门不要看，绝对不要在这个时候去强迫自己打扫卫生。

在人际关系上，立刻切断所有非必要的沟通。如果你觉得某个同事或者家人的行为让你极其愤怒，想要立刻发消息去指责对方，请立刻把手机静音并放到另一个房间。这三天里，不要去纠正任何人的错误，不要去教任何人做事。别人把事情搞砸了就让他搞砸，这不是你现在需要关心的问题。当你发现自己的喉咙里又涌起那种想要教训别人的冲动时，立刻去喝一大杯冰水，然后强迫自己离开那个现场。你的唯一任务就是通过物理隔离，强制停止那些正在伤害别人也伤害你自己的控制行为。

【阶段目标】

这个阶段的核心目标是强行止损和阻断破坏性行为。处于Grip状态的INFP，最致命的消耗来自于失控攻击别人之后产生的巨大内疚感。通过设置不可逾越的物理距离，你强制剥夺了劣势功能Te向外输出攻击的途径。你必须忍受那种“事情没有按规定做好”的极度烦躁感。你必须接受一个事实：就算天塌下来，这三天你也绝对不去管。只有硬生生地把这种病态的控制欲按住，你切断了制造新内疚感的源头，你才有可能省出一点点力气去进入下一步的调整。

【第二阶段：无目标感官体验与身体安抚（第4-10天）】

【具体行动建议】

当最剧烈的暴躁冲动稍微平息之后，你需要开始主动地给你的身体和神经系统降温。你需要向你的大脑证明，即使不保持极高的效率和绝对的控制，生活也是可以继续的。

在这个阶段，把你所有的注意力都集中在没有结果、不讲效率的纯粹体验上。你不需要去完成任何有意义的事情。每天保证充足的睡眠，饿了就去吃你最喜欢吃的食物，不要去管热量，也不要去计算营养搭配。

每天花一到两个小时的时间，去做一些完全不需要动脑子、也不会产出任何结果的事情。比如，你可以躺在沙发上看一部情节极其老套、你已经看过很多遍的喜剧电影；你可以拿出一张白纸随便涂鸦，画完直接扔掉；或者去公园里找个长椅坐着，看着前面走过的人群和天空的云彩，不要去思考他们是谁，也不要去想云彩是什么形状。

在这个星期里，如果有任何人向你提出工作上的紧迫要求，只要不是马上会造成严重后果的，一律回复“我现在处理不了，下周再说”。强迫自己去适应这种毫无生产力的状态。

【阶段目标】

这个阶段有两重目标。第一重目标是用健康的休息和低强度的感官输入去安抚你极度疲惫的身体。劣势功能Te的爆发极其消耗体力，你的身体其实早就透支了。通过吃饭、睡觉和无所事事，你强行关闭了大脑里的那个倒计时时钟。

第二重目标是极其微弱地唤醒你的辅助功能外倾直觉（Ne）。当你去看没有压力的电影、去公园发呆时，你开始接触外部世界，但这种接触是绝对安全的、不要求你做出任何判断和执行的。这能够极大地缓解你内在的焦虑感，让大脑知道外部世界并不是一个永远需要你去战斗和控制的战场。

【第三阶段：主导功能重启与核心价值回归（第11-30天）】

【具体行动建议】

到了这个阶段，你的暴躁和控制欲已经基本消失，生活节奏恢复了基础的平稳。现在，你需要通过极其微小但绝对符合你内心真实价值观的行动，把你断线的核心功能内倾情感（Fi）重新拉回工作状态。

你需要开始做一些非常具体的、能够让你内心真正感到舒适和认同的事情。不要去做那些为了赚钱或者为了获得别人夸奖的事情。比如，如果你平时喜欢照顾小动物，去小区的角落里给流浪猫喂一次食；如果你喜欢某种冷门的手工，花半个小时专心地去做那个手工；或者，去联系一个你绝对信任、绝对不会评判你的老朋友，不要去倾诉你之前的暴躁，只是简单地问候一下对方最近的生活。

在做这些事情的时候，你需要仔细去体会你内心的那种感受。去感受你把猫粮放下时心里的那种柔软，去感受你完成一个手工时的那种平静。如果在这个过程中，你的脑子里又冒出“做这些事一点效率都没有，纯粹是浪费时间”的冷酷念头，直接忽略它，强迫自己先把手头这件温暖的小事做完。

【阶段目标】

这个阶段的核心目标是让你断电的情感感知功能重新掌权。内倾情感（Fi）需要通过真实的、符合自身价值观的体验来重新启动。当你完成了一个极其微小、但绝对善良或者绝对真实的任务时，你的大脑就获得了一次成功的情感体验。

这种真实的温暖感受会不断向上反馈给你枯竭的Fi功能。你的Fi会逐渐发现，虽然之前的外界环境非常冷酷，但你依然可以在当下的现实中找到属于你自己的价值和意义。随着这种正向情感体验的积累，Fi的信心会逐渐恢复。它会重新开始运转，去构建你内心那套稳定的道德和情感评价体系。当你的情感感知能力重新恢复，能够再次包容自己和他人时，那个冷酷暴躁的劣势功能Te就会安静地退回到潜意识中去。此时，那个内心温和坚定、充满同理心、对世界重新抱有善意和期待的你，就彻底回归了。
"""
        },
        "loop": {
            "title": "越想越丧：别翻旧账，去晒晒太阳",
            "text": """
【当前心理状态与行为表现评估】

综合你目前的各项测试数据和日常行为反馈，你现在正处于一种极其隐蔽、极其内耗，且完全停止向外探索的“Loop（负向循环）”状态。在荣格认知功能理论的框架下，你目前的评估结果显示，你负责与外部世界接触、寻找新鲜可能性的辅助功能已经被大脑强制关闭。具体到你作为INFP的情况，你正在经历“内倾情感（Fi）与内倾感觉（Si）的负向循环”。

这种状态与彻底失控、对外暴躁的Grip状态完全不同。在单纯的Loop状态中，你并不会表现出对外部环境的强烈控制欲，也不会去严厉地指责别人。从外部表现来看，你甚至比平时显得更加安静、顺从和没有攻击性。别人可能只会觉得你最近有些疲惫或者不太爱说话。但是，你的内在实际上处于一种极度痛苦的自我封闭和自我惩罚状态。你的心理能量完全停止了向外流动，而是全部掉头向内。你的大脑正在使用极高的算力，去对你过去的历史记录进行毫无必要的反复翻找，导致你陷入了极其严重的行动瘫痪和自我价值否定。

【具体困境与思考特征】

在日常生活中，处于Fi-Si Loop状态会让你表现出非常隐蔽但极其伤人的自我折磨行为。首先，你会发现自己完全丧失了平时那种对未来的期待感和对新鲜事物的好奇心。面对任何新的机会、新的社交邀请或者新的兴趣爱好，你的第一反应不再是去尝试，而是直接在脑子里判定这件事情一定会带来糟糕的结果。

你的注意力不可控制地全部集中在过去的负面经历上。你会经常在深夜或者一个人独处的时候，不受控制地回想起几年前甚至十几年前发生的一件极其微小的尴尬事件。比如，你曾经在某次聚会上说错的一句话，或者你对某个朋友造成的一次无心伤害。你会把这些过去的记忆片段拿出来，在脑子里极其清晰、极其细致地反复播放。在这个过程中，你不仅重新体验到了当时的羞耻感和愧疚感，而且你会用你现在极其苛刻的标准，去对当时的自己进行严厉的道德审判。

在这个反复回忆的过程中，你完全拒绝听取任何外部的客观解释。如果别人试图安慰你，告诉你那件事情早就过去了，或者告诉你那根本不是你的错，你会表现出极度的抗拒。你会在心里觉得别人根本不懂你犯下的错误有多么严重。你觉得自己掌握了关于自己是一个糟糕的人的确凿证据。你觉得自己充满了缺陷，觉得世界上没有一个人会真正接纳这样糟糕的你。

此外，你的生活模式会变得极其刻板和封闭。为了避免在外部世界犯下新的错误，从而增加你内部的痛苦，你会主动切断绝大部分的外部接触。你会拒绝去没去过的地方，拒绝认识新的人，甚至每天只吃完全一样的食物。你觉得待在过去旧有的习惯里才是安全的。整体来看，你的生活变成了一个完全封闭的内部忏悔室，你每天都在脑子里对自己过去的错误进行审判，你被困在了自己对过去的执念和对自我的极度厌恶之中。

【深层心理机制分析：为什么会变成这样】

这种状态的根本原因，在于你为了防御外界未知的伤害和挫折，主动切断了大脑获取外部新鲜信息和可能性的通道。

在你处于健康状态时，你的主导功能内倾情感（Fi）负责在内部建立一套极其坚定的个人价值观，它让你清楚地知道什么是对的、什么是善良的。然后，你的辅助功能外倾直觉（Ne）负责在外部世界去寻找各种不同的方式、不同的人和事，来满足和表达你的这套价值观。Fi为你提供内心的底线，Ne负责为你寻找广阔的未来。这两个功能配合，让你能够坚持自我，同时又对世界保持开放和宽容。

但是，INFP极其容易在外部探索中感到受挫。当你长期处于一个不断否定你的想法、觉得你的创意不切实际的环境中，或者当你满怀期待地去尝试一件新事物，结果却遭遇了极其严重的失败和别人的嘲笑时，你的外倾直觉（Ne）会感到极度的恐惧和疲劳。因为Ne去外部探索是需要消耗能量并且伴随着风险的。当外界持续给你带来意想不到的打击时，为了保护你不再继续经历这种对未来的失望，你的大脑采取了最直接的防御手段：它强行关闭了负责对外探索的Ne功能。

当Ne被关闭后，你的核心价值观评估中心（Fi）就断绝了外部新鲜数据的输入。但是，Fi是一个必须时刻保持运转的功能，它必须不断地去评估事物的价值。既然外部没有新的可能性进来了，它就只能转身向内部去寻找评估材料。于是，它直接对接上了你的第三功能内倾感觉（Si）。内倾感觉（Si）是一个极其死板、专门用来记录过去发生过的具体事实和细节的静态数据库。

【认知功能受阻的逻辑】

当Fi和Si这两个完全向内的功能开始单独配合，并且完全没有外部直觉（Ne）参与时，一个完全脱离了未来希望的死循环就彻底形成了。

首先，主导功能Fi提出一个关于自我价值的问题：“我这个人到底有没有价值？我值得被爱吗？”

如果是健康状态，Ne会立刻去外部寻找证据，告诉你世界上还有很多美好的事情等着你去体验，未来还有很多认可你的人。但是现在Ne关闭了。

接着，第三功能Si接到了Fi的这个问题。Si根本不关心未来，它只负责翻账本。因为你现在正处于受挫的低谷期，根据记忆的提取规律，Si直接从数据库里给你提取了大量带有负面情绪的旧账。Si找到了你过去考试失败的经历，找到了你曾经搞砸过的人际关系，找到了你极其尴尬的社交瞬间。Si把这些零碎的历史数据全部摆在Fi的面前。

然后，Fi接收到了Si提供的这些负面事实。Fi开始用它极其深刻的价值判断去处理这些材料，得出一个结论：“根据这些过去的事实，我确实总是把事情搞砸，这证明我本质上就是一个毫无价值、充满缺陷的人。”

这个充满痛苦的结论被得出后，又会被Si当作新的事实记录下来。到了第二天，当Fi再次进行自我评估时，它不仅会看到过去的错误，还会看到昨天刚存进去的“我毫无价值”这个新记录。这就形成了一个坚不可摧的内部闭环。你并不是在无理取闹，你是在用你最深层的情感，配合最确凿的过去事实，给自己定下了一个无法翻案的死刑。你用过去的错误去证明自己当下的糟糕，然后又用当下的糟糕去确认未来的无望。因为整个推导过程完全没有去接触外部的新事物，你觉得自己的评估天衣无缝。最终，你彻底失去了在现实世界中重新开始的勇气。

【30天状态恢复与调整计划】

针对目前这种认知功能陷入内部死循环、完全排斥外部未来可能性的状态，调整的核心思路非常明确：你绝对无法通过在脑子里把过去的错误想通来打破这个循环。Fi和Si的结合会排斥一切内部的自我宽慰。你越是在脑子里试图告诉自己“过去的事情不重要”，你就陷得越深，因为这依然是在使用内倾功能去处理旧数据。

唯一的出路是强制重启被你关闭的辅助功能——外倾直觉（Ne）。你必须通过具体的、涉及外部不可预测的新鲜事物的客观接触，把没有历史包袱的全新数据强行塞进你的认知系统里。只有当你的大脑接收到了完全陌生的、不带任何过去负面标记的新反馈，旧的自我否定链条才会被打断。以下是为你制定的分为三个阶段的30天恢复计划：

【第一阶段：停止内部反刍与物理打断（第1-7天）】

【具体行动建议】

在这个阶段，你的首要任务是打断Fi和Si的不断对话。当你发现自己又开始在脑子里反复回放过去的那件尴尬事，或者又开始用过去的失败来证明自己现在有多差劲时，你需要在物理层面上叫停这种行为。

你可以直接从床上坐起来，或者用力搓一搓自己的脸。然后，立刻强制你的注意力转移到完全不需要动用任何价值判断和记忆的物理动作上。去整理一下你的衣柜，去用吸尘器把地毯吸一遍，或者去楼下扔一个垃圾。

在这个星期里，绝对不要去思考任何关于人生价值、过去对错或者未来规划的问题。把你每天的注意力限制在最基础的物理操作上。不要去问“我当时为什么那么蠢”，只去关注“现在我需要去倒一杯水”。

【阶段目标】

这个阶段的核心目标是切断内倾感觉（Si）向内倾情感（Fi）输送负面记忆的链条。通过强制把注意力转移到毫无记忆深度的物理动作上，你剥夺了大脑继续进行内部定罪的机会。你不需要去证明你的过去是可以被原谅的，你只需要让大脑停止去翻找过去。只要大脑不再继续编织那套自我厌恶的理论，你内部的紧绷感和对未来的抗拒感就会出现松动。

【第二阶段：极低压力的外部新变量导入（第8-14天）】

【具体行动建议】

当内部的无休止回忆稍微停歇后，你需要开始用极其微小、并且完全没有失败风险的外部新事物，去刺激你的外倾直觉（Ne）。这里的关键是“全新”和“绝对不评判”。

你需要在接下来的七天里，每天刻意去接触一个过去的数据本里绝对没有的新东西。比如，去听一种你这辈子从来没有听过的小众语言的歌曲；去便利店买一瓶包装最奇怪、你完全不知道什么味道的饮料喝下去；下班或者放学后，故意坐一辆你从来没坐过的公交车，随便坐几站再回来。

在做这些事情的时候，禁止在脑子里去评价这首歌好不好听，或者这个饮料好不好喝。你只需要去经历这个新鲜的物理过程。绝对不要去想这些行为对你的未来有没有实际用处。

【阶段目标】

处于Loop状态的你，极度排斥外部的未知，因为大脑默认未知就等于再次犯错。这个阶段的目标就是通过这些毫无压力的微小变量，向你的认知系统证明一个事实：外部世界存在很多完全新鲜的、并且不会伤害你的东西。

当你喝下一口完全陌生的饮料时，你的外倾直觉（Ne）就会接收到一个强烈的全新信号。随着这些安全的新鲜事物不断输入，你的主导功能Fi会发现，外部世界并不是只有过去的那些失败记录，还有很多中性的、甚至有趣的新鲜体验。这就为你重新建立对外部世界的期待打下了基础。

【第三阶段：无目的发散与直觉通道重启（第15-30天）】

【具体行动建议】

经过前两个阶段的铺垫，你的大脑对外部未知的抗拒感已经大大降低，Ne功能已经处于待机状态。现在，你需要主动把它应用到你真实的日常思维活动中去。

你必须开始强制自己进行一些没有任何现实目的的发散性思考和行动。拿出一张白纸，随便写下一个极其普通的物品，比如“回形针”。然后在纸上写出十种回形针的非正常用途，越离谱越好。或者，随便找一张没有任何文字的风景图片，给自己规定在十分钟内，编出一个发生在这个风景里的荒诞故事。

做这些事情的时候，不要去预设你写的东西有没有逻辑，也不要去管别人看了会不会觉得无聊。你只需要把这个产生新想法的过程执行完毕，然后直接把纸扔掉。不要去深究。

【阶段目标】

这是彻底打破Fi-Si Loop的最后一步。当你在强制执行这些没有规则的发散任务时，你的外倾直觉（Ne）被完全激活了。它重新承担起了在外部世界寻找新奇组合和可能性的责任。

你的主导功能内倾情感（Fi）终于重新获得了来自外部的全新反馈数据。它不再需要去翻找内部的负面历史记录，而是开始忙于处理眼前这些毫无历史包袱的有趣想法。当Fi看到你能够在一分钟内想出回形针的十种用法时，它会被迫承认：之前那个“我只能重复过去错误”的定论是完全站不住脚的。一旦新鲜的外部可能性推翻了内部陈旧的自我定罪，Fi和Ne就会重新建立起健康的合作关系。那个总是试图用过去来惩罚现在的内倾感觉（Si），也会退回到辅助记录的位置上。此时，你将彻底走出自我封闭和停滞的死循环，恢复到那个对未来充满好奇、愿意接纳新事物并且内心坚定平和的正常状态。
"""
        },
        "growth": {
            "title": "自在发光：把你的才华秀出来",
            "text": """
【深度分析】
【当前心理状态与行为表现评估】

综合你目前的各项测试数据和日常行为反馈，你现在正处于一种认知功能运作极其顺畅、心理能量分配极其合理且稳定的理想状态，也就是我们通常所说的“健康态”。在荣格认知功能理论的框架下，这意味着你作为INFP的四个核心认知功能——内倾情感（Fi）、外倾直觉（Ne）、内倾感觉（Si）和外倾思考（Te），完全按照它们最健康的顺序和比例在进行日常工作。

你现在的心理系统没有任何内部的严重消耗，也没有出现功能被强制关闭或者越权接管的情况。你主观上的感受应该是极其平和、内心充实且充满自我确信的。你既没有陷入对过去错误的无尽自责和自我否定中，也没有被极端的暴躁情绪和对外界的苛刻控制欲所绑架。你的大脑算力被完全集中在最有价值的地方：去坚定地守护你内心深处最核心的善良与道德准则，同时对外部世界保持高度的开放和好奇，并且能够用实际行动去实现你的想法。在这个状态下，你对自己的生活有着极强的认同感，你不再觉得坚持自我是非常痛苦的事情。你现在的共情能力和现实创造力处于你个人状态的最高峰。

【具体优势与核心竞争力表现】

处于健康态的你，在工作、学习和日常生活中会表现出极其明显的行为优势。首先，你拥有极其强大的内在稳定性和自我认同感。当你面对外部环境的压力、别人的不理解或者社会主流的功利要求时，你不会陷入自我怀疑。你可以非常平静地坚持你认为正确的事情。你心里非常清楚自己的底线在哪里，什么是你绝对不能妥协的。因为这种内心的确信，你不再需要去向别人证明什么，整个人散发出一种非常温和但是极其坚定的力量。

更重要的是，你现在具备把这种内在的善意和理想转化为现实的能力。你不再是那个只在脑子里构思美好世界、但面对现实任务就严重拖延的人。你能够极其自然地把你的兴趣和价值观，拆解成每天可以去执行的具体步骤。你对待工作的态度变得非常务实，你不再要求每一件事情都必须具有绝对的完美意义。你可以为了达成一个长远的理想，去耐心地处理眼前那些有些枯燥的客观任务。你的行动力得到了极大的提升，并且这种行动力不会让你觉得压抑。

在人际关系和沟通方面，你现在的表现非常包容且具有极其健康的边界感。你依然拥有极强的同理心，你可以非常敏锐地感知到别人的痛苦和需求。但是，你现在完全可以把别人的情绪和自己的情绪彻底隔离开来。你可以给朋友提供极其深刻的理解和陪伴，但当朋友离开后，你不会把对方的负面情绪留在自己身上进行内耗。如果别人提出了违背你原则的要求，你可以非常直接、语气平和地拒绝对方，心里没有任何内疚感。你尊重世界的多样性，你允许别人和你有不同的价值观，你不再试图去改变别人，也不允许别人来强行改变你。别人会觉得你是一个极其温暖、真诚，但同时又极具个人原则、绝对不好欺负的人。

【深层心理机制分析：各个认知功能的健康协作】

这种极其平稳且具有创造力的状态之所以能够维持，根本原因在于你内在的认知功能建立了一个良性的、不断接收外部新鲜信息并进行内部深度评估、最后再输出为现实行动的处理回路。你的心理防御机制处于完全放松的状态，你不需要耗费额外的精力去压抑任何对自我的厌恶，也不需要去防备别人的否定。

在健康状态下，你的心理能量流向是由内向外，再由外向内，最后再落到现实层面的顺畅循环。你内部坚定的价值观能够顺利地通过探索外部的可能性来获得表达，外界的新鲜事物也能被你包容地吸收进来，丰富你的内心世界，最后你通过客观的执行力把这一切变成现实。整个过程中，没有任何一个功能被过度透支，也没有任何一个功能被迫去承担它不擅长的工作。

【主导功能与辅助功能的完美配合】

你现在状态极佳的核心，在于你的主导功能内倾情感（Fi）和辅助功能外倾直觉（Ne）达成了极其默契的配合。这两个功能是你日常运作的绝对主力，它们现在的合作是毫无阻碍且极其高效的。

你的主导功能内倾情感（Fi）在这个阶段非常清晰且稳定。它安静地在后台运行，不断地为你所有的想法和行为提供一个极其明确的道德和价值判断。它让你清楚地知道你喜欢什么、讨厌什么、在乎什么。因为你处于健康态，Fi现在的评估完全是基于对自我的接纳和对世界的善意，而不是基于受挫后的自卑，所以它的判断极其准确且充满包容性。

当Fi确定了你内心的追求之后，你的辅助功能外倾直觉（Ne）立刻接手工作。Ne负责对外开放，去外部世界寻找各种不同的方式来满足Fi的需求。比如，Fi觉得“帮助别人、传递温暖”是极其重要的事情。如果是不健康的状态，你可能会因为找不到完美的方法而陷入痛苦。但在健康状态下，你的Ne会极其活跃地提供十几种不同的思路：你可以去写一篇充满力量的文章，你可以去参加一个动物保护活动，你也可以只是在今天下班路上对那个卖东西的人多说一句感谢。

这两个功能的配合构成了一个完美的内部评估与外部探索机制。Fi负责提供绝对稳定的核心方向，Ne负责提供极其丰富和灵活的实现路径。正是因为有了Ne在外部世界不断地寻找新的可能性，你的Fi才不会变成一个死板、偏执、只知道自我感动的封闭系统；也正是因为有了Fi在内部提供极其坚定的价值支撑，你的Ne才不会变成一个见异思迁、毫无原则的瞎想。这种配合让你既具备极其深刻的情感体验，又拥有极强的创造力和适应能力。

【第三功能与劣势功能的积极支撑】

在你处于健康态时，你平时不太常用或者不太擅长的第三功能内倾感觉（Si）和劣势功能外倾思考（Te），不仅没有给你制造任何麻烦，反而为你提供了非常关键的现实稳定性和客观执行力。

你的第三功能内倾感觉（Si）现在起到了极其重要的现实稳定器作用。它不再是那个在受挫时专门用来向你播放过去失败记录的痛苦源头。在健康状态下，Si为你极其丰富和发散的精神世界提供了一个安全的物理底座。它让你在日常生活中能够保持一些极其健康的个人习惯。比如，你会每天在固定的时间去喝一杯特定口味的咖啡，你会把你喜欢的一本书放在床头的固定位置，你会在周末去一家你已经去了很多次的熟悉的店里吃顿饭。这些极其具体、熟悉的物理细节和旧有习惯，给你提供了极大的安全感和舒适感。它们让你的大脑在进行高强度的情感评估和未来探索时，有一个随时可以回来休息的熟悉环境。

而你的劣势功能外倾思考（Te），此时也处于一种非常安全和受控的状态。它不再像失控时那样强迫你去制定极其苛刻的计划或者对别人大发雷霆。在健康状态下，Te能够以一种极低强度、极其有用的方式参与你的生活。它负责接管你生活中那些需要客观标准的执行任务。当你的Fi和Ne共同决定要做一个具体的项目时，健康的Te会非常自然地跳出来，帮你把这个项目拆分成三个阶段，并告诉你第一天应该先完成哪一部分。你不再排斥这种客观的条理性，你把Te当作一个极其好用的外部工具。你能够心平气和地按照客观规律去完成任务，这种持续的、小步快跑的现实产出，极大地增强了你的自信心，让你确信自己完全具备在现实世界中生存和创造价值的能力。

【状态维持与日常保养建议】

虽然你目前处于非常理想的健康态，创造力极强，情绪极其稳定，但作为INFP，你极其容易因为长时间待在一个严重违背你价值观的环境中、遭遇他人的严重否定，或者为了逃避现实的枯燥任务而过度沉浸在内部幻想中，从而再次滑落到自我厌恶的内部循环或者暴躁失控的状态中。因此，针对你目前的健康状况，重点在于如何极其严格地保护你的核心价值观，以及如何刻意地维护这条从内部情感走向外部现实的认知回路。以下是为你制定的、旨在长期维持这一健康态的日常运作建议：

【第一方面：核心价值观的绝对保护与外部探索的持续】

【具体行动建议】

你必须极其刻意地去保护你的内部情感系统（Fi）不被外界的恶意所污染。在日常生活中，如果有人对你的个人爱好、你的生活方式或者你极其看重的某项原则提出否定或者嘲笑，你绝对不要在心里去反复咀嚼对方的话，也绝对不要试图去向对方证明你是对的。你需要立刻在心里给这个人打上一个“价值观不匹配”的客观标签，然后直接在物理层面和心理层面上远离这个人。

同时，你必须强迫自己保持对外倾直觉（Ne）的使用。不管你的日常工作有多么忙碌或者枯燥，你必须每周给自己安排至少三个小时的时间，去接触完全不涉及现实利益的新鲜事物。去读一本跟你专业完全无关的书，去看一部非常冷门的独立电影，或者去参加一个全是陌生人的兴趣分享会。

【维持目标】

这样做的核心目的是保护你的主导功能Fi不受内伤，同时防止辅助功能Ne生锈。INFP最容易犯的错误就是因为一次外界的不理解，就彻底关上心门，拒绝再接触新的东西。通过极其果断地切断负面评价源，你保护了内心的纯粹；通过持续不断地接触新鲜事物，你确保了大脑始终有新的正面数据输入。只要你的Ne始终处于对外开放的状态，你的Fi就不会陷入没有材料可以评估的死循环。这是你维持心理健康和持续创造力的最重要防线。

【第二方面：基础现实秩序的低耗能运转】

【具体行动建议】

你需要极其刻意地去利用你的第三功能Si，把你的基础现实生活打理得极其规律。因为你的注意力永远在情感和未知的可能性上，你必须让日常生活变得极其简单，简单到不需要你动脑子。

固定你的作息时间，固定你的基础饮食结构。把你需要用到的重要物品永远放在同一个位置。对于交水电费、还信用卡这种纯粹的现实琐事，全部设置成自动扣款。不要让这些客观的物理细节去占据你大脑的处理空间。

当你在经历极其强烈的情感波动，或者刚刚完成了一项非常耗费精力的创造性工作后，立刻去执行一项你极其熟悉的、带有重复性的物理动作。比如去洗个澡，去把家里熟悉的路线走几遍，或者去整理你的书桌。

【维持目标】

这个方面的建议是为了防止你因为现实生活的混乱而引发焦虑。通过建立极其稳固且低耗能的日常物理习惯，你让内倾感觉（Si）发挥了最大的正面作用。它为你提供了一个绝对安全的现实避风港。当你把现实生活打理得井井有条且不需要额外操心时，你就有充足的心理能量去面对外部世界的各种复杂挑战，而不会因为找不到钥匙这种小事而突然崩溃。

【第三方面：微型客观目标的持续执行与确认】

【具体行动建议】

你需要极其刻意地、每天都去锻炼你的劣势功能Te。你绝对不能让自己的想法只停留在构思阶段。你必须把执行变成一种日常的客观习惯。

每天早晨，不要去想你这辈子要达成什么伟大的成就，只在纸上写下今天必须完成的一件、最多两件最基础的现实任务。这个任务必须是完全客观的，没有任何模糊地带。比如：“今天下午三点前，把这份文件的排版做好并发送出去”。

当你把这件客观的小事做完之后，用笔在纸上重重地划掉它。你必须去注视这个被划掉的动作，并且在心里向自己确认：“我已经完成了这个客观任务，我对现实世界产生了具体的改变。”在这个过程中，不要去评判这个任务对整个人类的意义有多大，只关注任务本身被完成了这个客观事实。

【维持目标】

这是你能够长期保持健康态的最关键收尾动作。你的认知系统极其需要外部的客观结果来增强现实感。如果不刻意去执行具体的任务，你就会永远飘在天上，最终因为觉得自己一事无成而陷入自我否定。通过每天强制执行极其微小的客观任务，你让外倾思考（Te）以一种极其健康的方式参与到你的生活中。不断累积的微小成功，会向你的主导功能Fi证明，你完全有能力在这个现实世界中很好地生存下去。只要你始终保持这种持续向外输出客观结果的习惯，你的整个认知系统就会一直保持极度的稳定、自信和高效。
"""
        }
    },

    "ENFJ": {
        "crisis": {
            "title": "彻底没电：不用再演那个“大好人”",
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
            "title": "变得冷漠：别在那死扣逻辑挑刺了",
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
            "title": "讨好型瞎忙：停一停，别为了别人转",
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
            "title": "真心换真心：带大家一起变好",
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
            "title": "彻底累了：允许自己消失几天",
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
            "title": "变得死板：别在那抠细节吓自己",
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
            "title": "瞎折腾：停下来，思考下自己真的喜欢吗？",
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
            "title": "专心一点：把你最棒的那个点子做成",
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
            "title": "彻底乱了：允许生活暂时脱离正轨",
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
            "title": "胡思乱想：哪有那么多“万一”",
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
            "title": "越想越累：别总盯着以前那点错",
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
            "title": "松弛有度：不用事事都自己盯着",
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
            "title": "实在太累：把那些责任和顾虑都先扔一边",
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
            "title": "事情没有那么糟糕，都是自己吓自己，别瞎想，天塌不下来",
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
            "title": "死抠旧账：别纠结过去了，翻篇吧",
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
            "title": "学会松手：对自己好点，先爱自己",
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
            "title": "压力太大了：必须得承认你也是肉做的",
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
            "title": "心里委屈：别硬撑，你不必永远当铁人",
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
            "title": "瞎折腾：别想一出是一出，先稳住",
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
            "title": "真正服众：有人情味儿，大家才听你的",
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
            "title": "心里委屈：不想理人就先别理",
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
            "title": "变得尖酸：别在那冷冰冰地算计了",
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
            "title": "患得患失：别总担心别人怎么看你",
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
            "title": "温暖靠谱：有底线的对人好",
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
            "title": "极度烦躁：谁都别来烦我",
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
            "title": "情绪失控：允许自己发疯",
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
            "title": "想不通：别在那死扣逻辑了，动动手",
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
            "title": "游刃有余：这事儿还得你来摆平",
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
            "title": "彻底躺平：什么都不想管了",
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
            "title": "变得暴躁：少说两句难听的话",
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
            "title": "越想越气：别一个人在那钻牛角尖",
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
            "title": "自在随心：做点让你开心的事",
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
            "title": "玩脱了：老实待着别乱动",
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
            "title": "疑神疑鬼：别觉得谁都要害你",
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
            "title": "瞎忙活：停下来想清楚再干",
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
            "title": "搞定难题：你是解决问题的高手",
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
            "title": "彻底玩不动了：不用非得去搞气氛",
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
            "title": "胡思乱想：别老觉得要出大事",
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
            "title": "太急躁了：停一停，这真是你想要的吗",
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
            "title": "自带光芒：大家就喜欢真实的你",
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
# 5. 社交关系库 (新增)
# ==========================================
# 逻辑：根据当前状态 (growth/loop/grip/crisis) 推荐 CP 和 天敌
# 这是一个示例结构，你需要填入具体的文案

RELATIONSHIP_DATA = {
    "INTP": {
        "growth": {
            "cp_name": "ENTJ / ESTJ",
            "cp_desc": "你的逻辑架构需要他们的强力执行（Te），把想法变成现实，这是强强联合。",
            "enemy_name": "ESFJ",
            "enemy_desc": "过度关注琐碎的人情世故（Fe），会打断你思考时的思维和心流。"
        },
        "loop": {
            "cp_name": "ENTP / ENFP",
            "cp_desc": "你需要 Ne 的脑洞冲击。只有他们能把你从“越想越钻牛角尖”的死胡同里硬拉出来。",
            "enemy_name": "ISTJ",
            "enemy_desc": "他比你还讲规矩和过去（Si），跟他在一起你会彻底困死在旧逻辑里。"
        },
        "grip": {
            "cp_name": "INFJ / ENFJ",
            "cp_desc": "你情绪爆发时像个孩子，只有高阶 Fe 能温柔地接住你那些没逻辑的委屈。",
            "enemy_name": "ESTJ",
            "enemy_desc": "在你最脆弱的时候跟你讲效率和KPI（Te），简直是火上浇油。"
        },
        "crisis": {
            "cp_name": "ISFJ",
            "cp_desc": "你需要无微不至的物理照顾（投喂、强制休息），别说话，照顾就好。",
            "enemy_name": "ENTJ",
            "enemy_desc": "这时候的强势压迫会让你彻底断电（Te），甚至对人类产生敌意。"
        }
    },

    "INTJ": {
        "growth": {
            "cp_name": "ENTJ",
            "cp_desc": "你们是最佳搞钱拍档。你的远见（Ni）加上他的手段（Te），效率高到吓人。",
            "enemy_name": "ESFP",
            "enemy_desc": "过于追求享乐和缺乏计划，会让你觉得是在浪费生命。"
        },
        "loop": {
            "cp_name": "ESTJ / ENTJ",
            "cp_desc": "你需要 Te 的客观数据。他会用冷冰冰的事实直接打碎你的“被害妄想”。",
            "enemy_name": "ISFP",
            "enemy_desc": "他会陪着你一起情绪化（Fi），让你在“没人懂我”的自闭怪圈里越陷越深。"
        },
        "grip": {
            "cp_name": "ESFP / ESTP",
            "cp_desc": "你需要 Se 的感官引导。别讲大道理了，让他带你去吃顿好的、玩点刺激的。",
            "enemy_name": "INTP",
            "enemy_desc": "这时候你不需要分析（Ti），分析只会让你觉得现在的堕落更不可原谅。"
        },
        "crisis": {
            "cp_name": "ISTJ",
            "cp_desc": "你需要极致的稳定。他不会问你未来怎么走，只会保证你今天有饭吃、有觉睡。",
            "enemy_name": "ENFP",
            "enemy_desc": "太吵了。这时候任何新的可能性（Ne）对你来说都是噪音。"
        }
    },

    "INFP": {
        "growth": {
            "cp_name": "ENFJ / ENTJ",
            "cp_desc": "你的才华需要秩序。他能欣赏你的内核（Fi），同时帮你把梦想落地（Te/Fe）。",
            "enemy_name": "ESTJ",
            "enemy_desc": "如果不成熟，他会粗暴地否定你的感受，把你变成一个只会干活的机器。"
        },
        "loop": {
            "cp_name": "ENFP / ENTP",
            "cp_desc": "你需要 Ne 的新鲜空气。他能把你从“回忆旧账”的房间里拖出去，看看外面的世界。",
            "enemy_name": "ISFJ",
            "enemy_desc": "他会陪你一起回忆过去（Si），让你在遗憾和自责的泥潭里躺得更平。"
        },
        "grip": {
            "cp_name": "ISFP / ENFP",
            "cp_desc": "你需要 Fi 的共情。只有同样敏感的人，才能让你觉得“原来我不是怪物”。",
            "enemy_name": "ESTJ",
            "enemy_desc": "你越焦虑越想控制（劣势Te），碰上真正的掌控者，你会彻底崩盘。"
        },
        "crisis": {
            "cp_name": "ISFJ",
            "cp_desc": "你需要像妈妈一样的安全感。不评判，不讲道理，只是给你做顿热饭。",
            "enemy_name": "ENTP",
            "enemy_desc": "这时候的辩论和玩笑（Ti/Ne）对你来说就是一种残忍的攻击。"
        }
    },

    "INFJ": {
        "growth": {
            "cp_name": "ENTP / ENFP",
            "cp_desc": "你的深刻需要他的发散（Ne）。他能懂你的潜台词，还能带你看不一样的风景。",
            "enemy_name": "ESTJ",
            "enemy_desc": "过于强调传统和服从，会让你觉得灵魂被囚禁了。"
        },
        "loop": {
            "cp_name": "ENFJ / ESFJ",
            "cp_desc": "你需要 Fe 的连接。他能把你从冷漠的逻辑塔楼里拉出来，让你重新感受到人的温度。",
            "enemy_name": "INTP",
            "enemy_desc": "你们会一起陷入冷冰冰的分析（Ti），让你觉得这个世界更没救了。"
        },
        "grip": {
            "cp_name": "ESTP / ESFP",
            "cp_desc": "你需要 Se 的落地。别想深意了，让他带你去运动、去兜风，回到真实世界。",
            "enemy_name": "INFP",
            "enemy_desc": "两个情绪漩涡撞在一起，只会互相淹没，谁也救不了谁。"
        },
        "crisis": {
            "cp_name": "ISTJ",
            "cp_desc": "你需要与世隔绝的安稳。他话少靠谱（Si），能帮你守住门，挡住外面的洪水。",
            "enemy_name": "ENFJ",
            "enemy_desc": "这时候你需要独处，过度的情感关怀（Fe）反而是一种负担。"
        }
    },

    "ISTP": {
        "growth": {
            "cp_name": "ESTJ / ENTJ",
            "cp_desc": "你的手艺需要他的规划。你负责解决单点问题，他负责把这变成大项目。",
            "enemy_name": "ENFP",
            "enemy_desc": "太飘了。你想聊具体怎么做，他跟你聊梦想和宇宙，你会想翻白眼。"
        },
        "loop": {
            "cp_name": "ESTP / ESFP",
            "cp_desc": "你需要 Se 的行动。别在脑子里空想了，跟他出门，干点出汗的事，立刻就好。",
            "enemy_name": "INTJ",
            "enemy_desc": "他会把你带进更深的阴谋论（Ni）里，让你觉得什么都没意义，不用动了。"
        },
        "grip": {
            "cp_name": "ESFJ / ISFJ",
            "cp_desc": "你情绪失控时需要 Fe 的包容。他们不会跟你讲道理，只会温柔地哄你。",
            "enemy_name": "ENTJ",
            "enemy_desc": "他会试图用逻辑压制你的情绪，这会让你直接炸毛，甚至动手。"
        },
        "crisis": {
            "cp_name": "ISFP",
            "cp_desc": "你需要无声的陪伴。他懂你的独立，会在旁边安静地做自己的事，陪着你。",
            "enemy_name": "ESFJ",
            "enemy_desc": "这时候哪怕是善意的唠叨（Fe），对你来说也是噪音污染。"
        }
    },

    "ISFP": {
        "growth": {
            "cp_name": "ESFP / ESTP",
            "cp_desc": "你需要 Se 的活力。跟他们在一起，你的艺术才华才能变成看得见的快乐。",
            "enemy_name": "ENTJ",
            "enemy_desc": "如果你没准备好，他的强势规划会让你觉得自我被吞噬了。"
        },
        "loop": {
            "cp_name": "ESFP / ESTP",
            "cp_desc": "出门！你需要 Se 的刺激。别躲在家里被害妄想了，去看看真实的阳光和人群。",
            "enemy_name": "INFJ",
            "enemy_desc": "他可能会过度解读你的情绪（Ni），让你觉得那个虚假的噩梦是真的。"
        },
        "grip": {
            "cp_name": "INFP / ISFP",
            "cp_desc": "你需要 Fi 的共鸣。当你因为做不到而暴躁时，只有他能告诉你“这没关系”。",
            "enemy_name": "ESTJ",
            "enemy_desc": "你正在模仿劣势的 Te（强权），遇到真正的 Te 使用者，会被秒杀成渣。"
        },
        "crisis": {
            "cp_name": "ISFJ",
            "cp_desc": "你需要安全感。他能把生活琐事打理好，让你在这个小窝里慢慢回血。",
            "enemy_name": "ENTP",
            "enemy_desc": "他的玩笑和质疑（Ne/Ti）会让你觉得世界充满了恶意。"
        }
    },

    "ISTJ": {
        "growth": {
            "cp_name": "ESTJ",
            "cp_desc": "效率最大化组合。你们都讲逻辑、守规矩（Te/Si），在一起做事极其舒服。",
            "enemy_name": "ENFP",
            "enemy_desc": "如果是工作伙伴，他的随性和变卦会让你每天都在崩溃边缘。"
        },
        "loop": {
            "cp_name": "ESTJ / ENTJ",
            "cp_desc": "你需要 Te 的客观。别翻旧账了，让他帮你分析现在的利弊，向前看。",
            "enemy_name": "ISFP",
            "enemy_desc": "他会陪你一起情绪化（Fi），让你觉得委屈是理所当然的，永远走不出来。"
        },
        "grip": {
            "cp_name": "ESFJ / ISFJ",
            "cp_desc": "你需要 Fe 的安抚。当你灾难化想象（Ne）时，听听他们的安慰：“没事的，大家都在”。",
            "enemy_name": "ENTP",
            "enemy_desc": "他是制造混乱的高手（Ne），会把你脑子里的灾难片变成现实版。"
        },
        "crisis": {
            "cp_name": "ISTP",
            "cp_desc": "你需要极简。他话少、务实，能帮你解决眼前具体的麻烦，绝不废话。",
            "enemy_name": "ENFP",
            "enemy_desc": "这时候任何“惊喜”对你来说都是惊吓。你需要绝对的确定性。"
        }
    },

    "ISFJ": {
        "growth": {
            "cp_name": "ESFJ",
            "cp_desc": "最温暖的组合。Fe 的共鸣让你们互相理解，Si 的稳重让生活井井有条。",
            "enemy_name": "ENTP",
            "enemy_desc": "他的跳跃思维和爱抬杠（Ne/Ti），会让你时刻处于不安之中。"
        },
        "loop": {
            "cp_name": "ENFJ / ESFJ",
            "cp_desc": "你需要 Fe 的出口。别闷头算账了，找他们聊聊，把心里的怨气吐出来。",
            "enemy_name": "ISTP",
            "enemy_desc": "他的冷漠逻辑（Ti）会让你觉得人心凉薄，更加封闭自己。"
        },
        "grip": {
            "cp_name": "ESTP / ISTP",
            "cp_desc": "你需要 Se/Ti 的破局。当你被恐惧吓瘫时，他能直接帮你把问题解决了。",
            "enemy_name": "INFP",
            "enemy_desc": "你已经很慌了，他比你还慌（Ne/Fi），两人抱在一起哭解决不了问题。"
        },
        "crisis": {
            "cp_name": "ENTJ",
            "cp_desc": "你需要一个强权者。让他来接管一切，告诉你该做什么。你只需要服从，这很安心。",
            "enemy_name": "INTP",
            "enemy_desc": "他的撒手不管和理性分析，会让你觉得被全世界抛弃了。"
        }
    },

    "ENTJ": {
        "growth": {
            "cp_name": "INTP / ISTP",
            "cp_desc": "你需要一个顶级智囊。你负责打江山，他负责提供技术蓝图，省得你瞎指挥。",
            "enemy_name": "ISFP",
            "enemy_desc": "他的缓慢、随性和情绪化（Fi）会让你急出高血压。"
        },
        "loop": {
            "cp_name": "INTJ / INFJ",
            "cp_desc": "你需要 Ni 的深度。只有他们敢按住你的头说：“停下来，你的方向错了。”",
            "enemy_name": "ESFP",
            "enemy_desc": "他会带着你一起疯狂行动（Se），让你在错误的道路上狂奔到底。"
        },
        "grip": {
            "cp_name": "INFP / ISFP",
            "cp_desc": "你需要 Fi 的温室。当你觉得自己没人爱时，只有他们能接住你那别扭的脆弱。",
            "enemy_name": "ESTJ",
            "enemy_desc": "他会让你“别矫情，起来干活”，这会让你直接心态崩盘。"
        },
        "crisis": {
            "cp_name": "ISFJ",
            "cp_desc": "你需要强制关机。他能帮你挡住外面的事，给你做顿饭，让你像植物一样静养。",
            "enemy_name": "ENTP",
            "enemy_desc": "他制造的混乱（Ne）会让你那个已经过载的大脑彻底烧毁。"
        }
    },

    "ENTP": {
        "growth": {
            "cp_name": "INFJ / INTJ",
            "cp_desc": "你需要一个能看懂你疯癫背后的逻辑，还能帮你把坑填上的人。",
            "enemy_name": "ISTJ",
            "enemy_desc": "在你想搞大事的时候，他只会拿着规章制度告诉你“这不合规矩”。"
        },
        "loop": {
            "cp_name": "INTP / ISTP",
            "cp_desc": "你需要 Ti 的冷水。当你为了博眼球在表演时，只有他会冷冷地说：“你看起来像个傻子。”",
            "enemy_name": "ESFJ",
            "enemy_desc": "他会给你鼓掌（Fe），鼓励你继续哗众取宠，让你彻底迷失。"
        },
        "grip": {
            "cp_name": "ISFJ / ISTJ",
            "cp_desc": "你需要 Si 的安抚。当你疑神疑鬼怕得病时，他拿出的体检报告比什么都管用。",
            "enemy_name": "ENFP",
            "enemy_desc": "两个生活不能自理的人凑在一起，只会把焦虑放大十倍。"
        },
        "crisis": {
            "cp_name": "INFJ",
            "cp_desc": "你需要深度的精神按摩。他能穿透你的面具，安抚那个破碎的灵魂。",
            "enemy_name": "ESTP",
            "enemy_desc": "他会带你去寻欢作乐（Se），让你在狂欢后感到更深的虚无。"
        }
    },

    "ENFJ": {
        "growth": {
            "cp_name": "INFP / ISFP",
            "cp_desc": "你需要保护的人。他们的纯粹（Fi）能让你感到付出的意义，互相滋养。",
            "enemy_name": "ESTJ",
            "enemy_desc": "他的冷酷指令会让你觉得自己的善意被践踏了。"
        },
        "loop": {
            "cp_name": "INTJ / INFJ",
            "cp_desc": "你需要 Ni 的独处。他能把你从无效社交里拽出来，按在椅子上读本书。",
            "enemy_name": "ESFP",
            "enemy_desc": "他会拉你去更多的局，把你最后一点电量耗干。"
        },
        "grip": {
            "cp_name": "ISTP / INTP",
            "cp_desc": "你需要 Ti 的逻辑免疫。当你变得刻薄时，他们反而觉得“你终于肯说实话了”，不会受伤。",
            "enemy_name": "INFP",
            "enemy_desc": "你这时候的毒舌会直接把他骂哭，然后你醒了会后悔死。"
        },
        "crisis": {
            "cp_name": "ISFJ",
            "cp_desc": "你需要被反向照顾。一直当保姆的你，现在需要一个不需要你操心的真保姆。",
            "enemy_name": "ENTJ",
            "enemy_desc": "他会分析你的情绪毫无价值，这会让你对自己彻底绝望。"
        }
    },

    "ENFP": {
        "growth": {
            "cp_name": "INTJ / INFJ",
            "cp_desc": "经典的官配。你负责发疯，他负责把你拉回地球，顺便帮你把PPT做了。",
            "enemy_name": "ISTJ",
            "enemy_desc": "在你想飞的时候，他就是拴在你脚上的那个铁球。"
        },
        "loop": {
            "cp_name": "INFP / ISFP",
            "cp_desc": "你需要 Fi 的灵魂拷问。他会问你：“你忙成这样，真的开心吗？”让你瞬间清醒。",
            "enemy_name": "ENTJ",
            "enemy_desc": "他会递给你一根鞭子，让你跑得更快，直到累死为止。"
        },
        "grip": {
            "cp_name": "ISTJ / ISFJ",
            "cp_desc": "你需要 Si 的老妈子。当你瘫在床上抑郁时，他会默默给你收拾屋子、端茶送水。",
            "enemy_name": "ENTP",
            "enemy_desc": "他也没长生活自理那根筋，你俩会一起烂在家里。"
        },
        "crisis": {
            "cp_name": "INFJ",
            "cp_desc": "你需要精神避难所。他能无条件接纳你的阴暗面，让你觉得安全。",
            "enemy_name": "ESTJ",
            "enemy_desc": "他对混乱的零容忍，会让你觉得自己是个无可救药的垃圾。"
        }
    },

    "ESTJ": {
        "growth": {
            "cp_name": "ISTJ / ISFJ",
            "cp_desc": "你需要靠谱的执行者。你下命令，他落实细节，没有任何废话。",
            "enemy_name": "INFP",
            "enemy_desc": "他的拖延和情绪化会每天挑战你的血压极限。"
        },
        "loop": {
            "cp_name": "ISTJ",
            "cp_desc": "你需要 Si 的证据。当你瞎焦虑（Ne）时，他会拿出数据告诉你“以前没出过这事”。",
            "enemy_name": "ENFP",
            "enemy_desc": "他那些天马行空的“万一”，会把你那个焦虑的火坑浇上一桶油。"
        },
        "grip": {
            "cp_name": "ISFP / INFP",
            "cp_desc": "你需要 Fi 的允许。只有他们能让你卸下铠甲，像个孩子一样哭一场。",
            "enemy_name": "ENTP",
            "enemy_desc": "他会嘲笑你的脆弱，让你恼羞成怒，直接开战。"
        },
        "crisis": {
            "cp_name": "ISFJ",
            "cp_desc": "你需要隐形的服务。他会把一切打理好，且不打扰你，让你有空间自我修复。",
            "enemy_name": "ENTJ",
            "enemy_desc": "两个暴君撞在一起，只会把房子拆了。"
        }
    },

    "ESTP": {
        "growth": {
            "cp_name": "ISTJ / ISFJ",
            "cp_desc": "你需要一个刹车片。你往前冲，他帮你盯着后院起没起火，这就稳了。",
            "enemy_name": "INFJ",
            "enemy_desc": "他那些神神叨叨的哲学话题，会让你觉得像在听天书，只想逃跑。"
        },
        "loop": {
            "cp_name": "ISTP / INTP",
            "cp_desc": "你需要 Ti 的嘲讽。当你为了面子（Fe）装X时，他一句“好蠢”能让你瞬间冷静。",
            "enemy_name": "ESFP",
            "enemy_desc": "他会给你递酒，让你继续装，直到你把脸丢光为止。"
        },
        "grip": {
            "cp_name": "INTJ / INFJ",
            "cp_desc": "你需要 Ni 的导航。当你迷信怕死时，他能逻辑清晰地告诉你未来的剧本，让你安心。",
            "enemy_name": "ENFP",
            "enemy_desc": "他比你还神神叨叨，会跟你一起相信世界末日要来了。"
        },
        "crisis": {
            "cp_name": "ISTJ",
            "cp_desc": "你需要物理拘留。让他没收你的车钥匙和钱包，直到你脑子清醒为止。",
            "enemy_name": "ESFP",
            "enemy_desc": "他会怂恿你“今朝有酒今朝醉”，那是通往悬崖的路。"
        }
    },

    "ESFJ": {
        "growth": {
            "cp_name": "ISFJ / ISTP",
            "cp_desc": "你需要安稳。ISFJ 懂你的付出，ISTP 能帮你搞定那些你不懂的麻烦事。",
            "enemy_name": "ENTJ",
            "enemy_desc": "他只看利益不讲人情，会让你觉得这个世界冷酷得可怕。"
        },
        "loop": {
            "cp_name": "ISTJ / ISFJ",
            "cp_desc": "你需要 Si 的现实感。当你脑补大家都在恨你时，他会告诉你“没人有空理你”。",
            "enemy_name": "ENTP",
            "enemy_desc": "他会编造更多的阴谋论来逗你玩，把你吓得半死。"
        },
        "grip": {
            "cp_name": "INTP / ISTP",
            "cp_desc": "你需要 Ti 的冷处理。当你变得刻薄时，他们根本不在乎，正好帮你降降温。",
            "enemy_name": "INFP",
            "enemy_desc": "你这时候的攻击性会严重伤害他，让他从此躲着你走。"
        },
        "crisis": {
            "cp_name": "ISTJ",
            "cp_desc": "你需要秩序。别管人际关系了，跟他一起把家里打扫一遍，心里就踏实了。",
            "enemy_name": "ENFP",
            "enemy_desc": "他的情绪化和不可预测，会让你本就紧绷的神经彻底断裂。"
        }
    },

    "ESFP": {
        "growth": {
            "cp_name": "ISFP / ISTJ",
            "cp_desc": "ISTJ 是你最好的锚。你负责让生活有趣，他负责让生活不崩盘。",
            "enemy_name": "INTJ",
            "enemy_desc": "他的严肃和说教（Te/Ni），瞬间就能把你的快乐火苗掐灭。"
        },
        "loop": {
            "cp_name": "INFP / ISFP",
            "cp_desc": "你需要 Fi 的初心。他会问你：“你是真的快乐，还是在表演快乐？”",
            "enemy_name": "ESTJ",
            "enemy_desc": "他会逼你去做更有用的事，让你在空虚的忙碌中越陷越深。"
        },
        "grip": {
            "cp_name": "INTJ / INFJ",
            "cp_desc": "你需要 Ni 的灯塔。当你觉得人生没希望时，他能带你看到隧道尽头的光。",
            "enemy_name": "ENTP",
            "enemy_desc": "他会用逻辑论证“人生确实没意义”，把你推向深渊。"
        },
        "crisis": {
            "cp_name": "ISFJ",
            "cp_desc": "你需要回血站。别在外面浪了，回家喝他煲的汤，睡个好觉。",
            "enemy_name": "ENTJ",
            "enemy_desc": "他会觉得你软弱无能，这种轻视会成为压垮你的最后一根稻草。"
        }
    }
}

# 默认兜底数据 (防止忘了填报错)
DEFAULT_RELATION = {
    "cp_name": "???",
    "cp_desc": "数据正在计算中...",
    "enemy_name": "???",
    "enemy_desc": "数据正在计算中..."
}


CP_TITLE_MAP = {
        "growth": "当下最佳的合伙人/战友",      # Stable / Growth
        "loop":   "当下最佳的开心果/破局者",    # Loop
        "grip":   "当下最佳的陪伴者/听众",      # Grip
        "crisis": "当下最佳的守护者"              # Crisis
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
    cp_name: str       # 最佳CP类型，
    cp_desc: str       # 为什么是CP
    enemy_name: str    # 天敌类型
    enemy_desc: str    # 为什么是天敌
    cp_title:str
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
    if res_l >= 55 and res_g >= 55:
        state_key = "crisis"
    # 对应 advice_key 的 "grip" (注意这里原本叫 overload)
    elif res_g >= 55:
        state_key = "overload"
    # 对应 advice_key 的 "loop" (注意这里原本叫 highLoop)
    elif res_l >= 55:
        state_key = "highLoop"
    else:
        state_key = "stable"

    # 获取 narrative
    narrative_pack = NARRATIVE_TEMPLATES.get(mbti, DEFAULT_NARRATIVE)
    content = narrative_pack.get(state_key, narrative_pack.get("overload", DEFAULT_NARRATIVE["overload"]))

    # 未来建议
    CRISIS_THRESHOLD = 55  # 两个都高于此值算危机
    HIGH_THRESHOLD = 55  # 单个高于此值算高

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

    pill_text = "正常"
    if res_overall >= 80:
        pill_text = "充盈"
    elif res_overall >= 60:
        pill_text = "平稳"
    elif res_overall >= 40:
        pill_text = "耗竭"
    else:
        pill_text = "高压"

        # 获取动态标题，默认为“能量补给”
    dynamic_cp_title = CP_TITLE_MAP.get(advice_key, "你的最佳CP")

        # 获取关系数据 (这部分保持上一轮的逻辑)
    type_rel_data = RELATIONSHIP_DATA.get(mbti, {})
    current_rel = type_rel_data.get(advice_key, DEFAULT_RELATION)

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
        chart_data=[res_m, res_coh, 100 - res_l, 100 - res_g, 100 - res_load, res_overall],
        cp_name = current_rel["cp_name"],
        cp_desc = current_rel["cp_desc"],
        enemy_name = current_rel["enemy_name"],
        enemy_desc = current_rel["enemy_desc"],
        cp_title = dynamic_cp_title
    )



# ========== 配置（建议改成环境变量）==========
ZPAY_BASE = "https://zpayz.cn"
ZPAY_MAPI = f"{ZPAY_BASE}/mapi.php"
ZPAY_SUBMIT = "https://zpayz.cn/submit.php"

ZPAY_PID = os.getenv("ZPAY_PID", "2026020316192039")  # 文档里的 PID :contentReference[oaicite:6]{index=6}
ZPAY_KEY = os.getenv("ZPAY_KEY", "34ecGidqcWlTTOfp9p1QC0zi6s2OWUum")  # 文档里的 PKEY :contentReference[oaicite:7]{index=7}

# 你自己的域名（用于拼 notify_url / return_url）
FRONTEND_RETURN = os.getenv("FRONTEND_RETURN", "http://127.0.0.1:5500/index.html")  # 你的前端页面地址

PRICE_YUAN = os.getenv("PRICE_YUAN", "9.90")
PRODUCT_NAME = os.getenv("PRODUCT_NAME", "舒木罗盘-完整报告解锁")  # 文档要求：商品名要具体 :contentReference[oaicite:8]{index=8}


# ========== 简易订单存储（生产请换 DB/Redis）==========
ORDERS: Dict[str, Dict[str, Any]] = {}


# ========== ZPAY 常见易支付签名（如规则不同我再帮你改）==========
def md5(s: str) -> str:
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def build_sign(params: Dict[str, Any], key: str) -> str:
    """
    通用易支付 MD5 签名：
    1) 去掉空值、去掉 sign/sign_type
    2) key 排序
    3) k=v&k2=v2... + key
    4) md5
    """
    filtered = {k: str(v) for k, v in params.items()
                if v is not None and str(v) != "" and k not in ("sign", "sign_type")}
    pieces = [f"{k}={filtered[k]}" for k in sorted(filtered.keys())]
    base = "&".join(pieces) + key
    return md5(base)

def verify_sign(params: Dict[str, Any], key: str) -> bool:
    sign = str(params.get("sign", "")).lower()
    expect = build_sign(params, key).lower()
    return sign == expect


# ========== API ==========
class PayReq(BaseModel):
    payment_type: str = "alipay"  # 前端传 { payment_type: 'alipay' } :contentReference[oaicite:9]{index=9}
    param: Optional[str] = None   # 你想带回来的附加参数（会原样回传） :contentReference[oaicite:10]{index=10}
    device: str = "pc"

@app.post("/api/pay")
async def create_order(req: PayReq, request: Request):
    out_trade_no = uuid.uuid4().hex
    client_ip = request.client.host if request.client else "127.0.0.1"
    proto = request.headers.get("x-forwarded-proto", "https")
    host = request.headers.get("x-forwarded-host") or request.headers.get("host")
    site_origin = f"{proto}://{host}"
    notify_url = f"{site_origin}/api/notify"
    return_url = f"{site_origin}/"

    # 先记录订单
    ORDERS[out_trade_no] = {"paid": False, "created_at": int(time.time()), "raw": {}}

    # ✅ 手机：走 submit.php 收银台（图2体验）
    if req.device == "mobile":
        payload = {
            "pid": ZPAY_PID,
            "type": req.payment_type,
            "out_trade_no": out_trade_no,
            "notify_url": notify_url,
            "return_url": return_url,
            "name": PRODUCT_NAME,
            "money": PRICE_YUAN,
            "clientip": client_ip,
            "param": req.param or "",
            "sign_type": "MD5",
        }
        payload["sign"] = build_sign(payload, ZPAY_KEY)

        checkout_url = ZPAY_SUBMIT + "?" + urlencode(payload)
        return {"code": 200, "order_id": out_trade_no, "checkout_url": checkout_url}

    payload = {
        "pid": ZPAY_PID,
        "type": req.payment_type,
        "out_trade_no": out_trade_no,
        "notify_url": notify_url,
        "return_url": return_url,
        "name": PRODUCT_NAME,
        "money": PRICE_YUAN,
        "clientip": client_ip,
        "device": "pc",   # PC 就写死 pc
        "param": req.param or "",
        "sign_type": "MD5",
    }
    payload["sign"] = build_sign(payload, ZPAY_KEY)
    
    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.post(ZPAY_MAPI, data=payload)  # 文档：POST form-data :contentReference[oaicite:14]{index=14}
        try:
            data = resp.json()
        except Exception:
            raise HTTPException(status_code=502, detail=f"gateway bad response: {resp.text[:200]}")

    # 文档成功返回会有 payurl/qrcode/img :contentReference[oaicite:15]{index=15}
    if str(data.get("code")) != "1":
        raise HTTPException(status_code=400, detail=f"create order failed: {data}")

    pay_url = data.get("img") or data.get("qrcode") or data.get("payurl") or data.get("payurl2")
    if not pay_url:
        raise HTTPException(status_code=502, detail=f"missing pay url fields: {data}")

    ORDERS[out_trade_no]["raw"] = data
    ORDERS[out_trade_no]["zpay_trade_no"] = data.get("trade_no")

    return {
        "code": 200,
        "order_id": out_trade_no,
        "payment_type": req.payment_type,
        "payurl": data.get("payurl"),
        "qrcode": data.get("qrcode"),
        "img": data.get("img"),
        "pay_url": pay_url,  # 你当前合并字段也保留
    }


from fastapi import HTTPException
import httpx

ZPAY_API = "https://zpayz.cn/api.php"

@app.get("/api/check_order")
async def check_order(order_id: str):
    # 基本校验
    if not order_id:
        return {"paid": False, "reason": "missing order_id"}

    params = {
        "act": "order",
        "pid": ZPAY_PID,
        "key": ZPAY_KEY,
        "out_trade_no": order_id,
    }

    try:
        async with httpx.AsyncClient(timeout=12) as client:
            r = await client.get(ZPAY_API, params=params)

        # 网关偶尔会返回 HTML（比如被拦/参数错），先按文本保底
        raw_text = r.text

        # 尝试解析 JSON
        try:
            data = r.json()
        except Exception:
            # ✅ 永远返回 JSON，不要 500
            return {
                "paid": False,
                "reason": "gateway_non_json",
                "status_code": r.status_code,
                "gateway_text_head": raw_text[:200],
            }

        # 约定：code=1 成功，status=1 已支付（以网关实际返回为准）
        if str(data.get("code")) != "1":
            return {"paid": False, "reason": "gateway_code_not_1", "gateway": data}

        paid = str(data.get("status")) == "1"
        if paid:
            return {"paid": True, "data": {"msg": "unlocked"}}

        return {"paid": False, "gateway": data}

    except Exception as e:
        # ✅ 永远返回 JSON，不要 500
        return {"paid": False, "reason": "server_exception", "detail": str(e)}



@app.post("/api/notify", response_class=PlainTextResponse)
async def zpay_notify(request: Request):
    """
    ZPAY 异步通知回调（notify_url） :contentReference[oaicite:19]{index=19}
    通常要求返回 'success' / 'ok' 字样（以网关要求为准）
    """
    form = await request.form()
    params = dict(form)

    # 1) 验签
    if not verify_sign(params, ZPAY_KEY):
        return PlainTextResponse("sign_error", status_code=400)

    out_trade_no = params.get("out_trade_no")
    trade_status = params.get("trade_status") or params.get("status") or "SUCCESS"
    money = params.get("money")

    if not out_trade_no or out_trade_no not in ORDERS:
        return PlainTextResponse("order_not_found", status_code=404)

    # 2) 标记支付成功
    if str(trade_status).upper() in ("SUCCESS", "TRADE_SUCCESS", "1"):
        ORDERS[out_trade_no]["paid"] = True
        ORDERS[out_trade_no]["paid_at"] = int(time.time())
        ORDERS[out_trade_no]["paid_money"] = money
        ORDERS[out_trade_no]["notify_payload"] = params

        # TODO：把“完整报告数据”塞进去，供 check_order 返回
        # 例如：根据 out_trade_no 找到用户上一次测评结果，然后组合成前端 unlockContent 需要的字段
        ORDERS[out_trade_no]["unlocked_data"] = {
            "paid": True,
            "msg": "unlocked",
            # 你可以放：insight/advice/cp_name/cp_desc/enemy_name/enemy_desc/month_title/month_text 等等
        }

        return PlainTextResponse("success")

    return PlainTextResponse("ignored")
