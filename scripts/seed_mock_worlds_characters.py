from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.core.db import get_session
from app.models.db_models import CharacterCard, WorldBook, WorldEntry


ASSET_ROOT = Path("workspace/assets")
TURNAROUND_DIR = ASSET_ROOT / "mock-turnarounds"


def now() -> datetime:
    return datetime.now(timezone.utc)


def asset_url(filename: str) -> str:
    return f"/api/assets/mock-turnarounds/{filename}"


def local_path(filename: str) -> str:
    return str(TURNAROUND_DIR / filename)


WORLD_BOOKS = [
    {
        "id": "mock-world-europe-medieval",
        "name": "灰堡王国",
        "genre": "欧洲中世纪奇幻",
        "era_background": "王权衰落、边境领主割据的中世纪晚期。旧王都仍维持法统，北境黑松林和南方港城分别掌握军力与贸易。",
        "world_rules": "贵族宣誓、教会裁决和骑士契约共同约束社会秩序。魔法只以遗物、草药秘术和古代誓言的形式低调存在，不能公开改变战局。",
        "organizations": "王室摄政议会、银烛教会、黑松边境骑士团、港城商会、草药师行会。",
        "locations": "灰堡王都、黑松林边境、月湾港、废弃修道院、雾谷古道。",
        "social_structure": "国王名义统治，实权由摄政贵族、教会和边境军团分割。平民依附庄园，商会正在挑战传统贵族权力。",
        "taboo_or_constraints": "禁止公开研究旧王朝遗物；骑士不得违背正式誓言；教会审判文书具有最高证词效力。",
        "tone_style": "冷峻、克制、带悬疑感的宫廷与边境叙事，适合权谋、誓言和身份秘密。",
        "summary": "一个王权衰落、骑士誓言与古代遗物交织的欧洲中世纪奇幻世界。",
        "entries": [
            {
                "id": "mock-entry-europe-oath",
                "title": "骑士誓言",
                "entry_type": "世界规则",
                "keywords": "骑士,誓言,契约",
                "content": "正式骑士誓言必须在领主、教士和见证人面前完成。违誓者会失去封地继承权，并被各地城堡拒绝接纳。",
                "applicable_scope": "骑士、领主、军事剧情",
                "priority": 90,
            },
            {
                "id": "mock-entry-europe-greycastle",
                "title": "灰堡王都",
                "entry_type": "地点",
                "keywords": "王都,宫廷,审判",
                "content": "灰堡王都由旧石城墙和高塔组成，王宫、教会法庭和贵族宅邸集中在内城区，是权谋和审判剧情的中心。",
                "applicable_scope": "宫廷、审判、政治交易",
                "priority": 80,
            },
        ],
    },
    {
        "id": "mock-world-honghuang-casual",
        "name": "云梦洪荒闲游记",
        "genre": "中国洪荒休闲",
        "era_background": "天地初开后的漫长岁月，山海、灵泽和人间市集尚未完全分界。神兽偶尔路过茶棚，散仙也会为房租发愁。",
        "world_rules": "灵气来自山川风物，修行讲究因缘和日常功课。强行逆天会欠下天道账，但帮邻里修屋、种灵草也能积攒功德。",
        "organizations": "云梦集、山君巡游司、桃源客栈、灵植铺、散仙互助会。",
        "locations": "云梦集市、桃花渡、浮云茶棚、青岚山、旧天梯遗址。",
        "social_structure": "人、妖、灵、散仙混居，身份不以血脉高低决定，而以信誉、功德和能否按时还账决定。",
        "taboo_or_constraints": "不能在人间市集显露巨大法相；不能偷摘有主灵植；欠下的天道账必须用善行或承诺偿还。",
        "tone_style": "轻松、温暖、带神话想象力的日常喜剧，可穿插小危机和治愈型成长。",
        "summary": "一个洪荒神话被日常生活软化后的休闲奇幻世界，适合轻喜剧和治愈短剧。",
        "entries": [
            {
                "id": "mock-entry-honghuang-cloudmarket",
                "title": "云梦集市",
                "entry_type": "地点",
                "keywords": "集市,人妖混居,交易",
                "content": "云梦集市每逢三日开市，凡人用铜钱，散仙用灵露，山灵常用故事或承诺抵账。",
                "applicable_scope": "日常交易、轻喜剧冲突",
                "priority": 90,
            },
            {
                "id": "mock-entry-honghuang-karma",
                "title": "天道账",
                "entry_type": "世界规则",
                "keywords": "功德,因果,轻惩罚",
                "content": "违背约定或滥用灵力会产生天道账，表现为小霉运、法术失灵或被安排一件麻烦善事。",
                "applicable_scope": "喜剧惩罚、角色成长",
                "priority": 85,
            },
        ],
    },
    {
        "id": "mock-world-modern-urban",
        "name": "镜城二十四小时",
        "genre": "现代都市",
        "era_background": "当代一线城市镜城，医院、媒体、自媒体平台、老社区和资本集团共同构成高压生活网络。",
        "world_rules": "所有冲突都必须能落在现实社会逻辑里：职业伦理、舆论传播、家庭关系、合同证据和城市公共事件。",
        "organizations": "镜城中心医院、城南派出所、深夜电台、星河资本、旧街社区委员会。",
        "locations": "中心医院急诊科、旧街社区、地铁换乘站、直播工作室、城市天台。",
        "social_structure": "年轻职业人夹在事业压力、家庭期待和公共舆论之间。信息传播速度快，误会和反转通常来自片段化证据。",
        "taboo_or_constraints": "现实题材不使用超自然设定；医疗、新闻和法律信息必须保持可信；人物行为需要有清晰动机。",
        "tone_style": "节奏快、现实感强，兼具悬疑、情感拉扯和都市烟火气。",
        "summary": "以医院、媒体和旧街社区为核心的现代都市现实短剧背景。",
        "entries": [
            {
                "id": "mock-entry-modern-er",
                "title": "中心医院急诊科",
                "entry_type": "地点",
                "keywords": "医院,急诊,职业伦理",
                "content": "镜城中心医院急诊科二十四小时运转，既是公共事件入口，也是人物关系被迫碰撞的高压空间。",
                "applicable_scope": "医疗事件、职业抉择",
                "priority": 90,
            },
            {
                "id": "mock-entry-modern-publicopinion",
                "title": "碎片化舆论",
                "entry_type": "世界规则",
                "keywords": "舆论,证据,反转",
                "content": "短视频平台上的片段证据会迅速放大冲突，但完整真相通常藏在监控盲区、病历细节或当事人的沉默里。",
                "applicable_scope": "悬疑反转、媒体线",
                "priority": 85,
            },
        ],
    },
]


CHARACTERS = [
    {
        "id": "mock-char-europe-knight-m",
        "name": "莱昂·黑松",
        "gender": "男",
        "role_type": "守护骑士",
        "world": "灰堡王国",
        "identity": "黑松边境骑士团年轻队长，负责护送密令与守卫北境古道。",
        "background": "出身没落骑士家族，父亲因旧王朝遗物案被污名化。莱昂靠军功重新获得领主信任，却始终怀疑当年的审判另有隐情。",
        "personality": "克制、守信、警觉，习惯先观察再行动。",
        "goal": "查清父亲被定罪的真相，同时守住边境不被贵族私斗拖垮。",
        "motivation": "他相信誓言不该成为权力遮羞布，真正的荣誉必须保护弱者。",
        "secret": "随身短剑里藏有旧王朝遗物碎片。",
        "conflict_points": "忠于骑士团与追查父亲冤案之间冲突；不擅长表达情绪。",
        "relationship_notes": "与伊薇特互相试探又彼此依赖。",
        "speech_style": "短句、低声、直接，很少开玩笑。",
        "catchphrases": "誓言不是给别人听的。",
        "emotional_arc": "从只相信军令，到学会相信同伴和自己的判断。",
        "story_function": "行动线主角、秘密护送者、权谋漩涡中的道德锚点。",
        "visual_description": "二十七八岁，短深金发，轻胡茬，皮革与链甲混合护甲，深绿披风，常年风霜感。",
        "image_keywords": "European medieval knight, dark green cloak, leather armor, chainmail, grounded realism",
        "filename": "europe-medieval-male-knight.png",
    },
    {
        "id": "mock-char-europe-herbalist-f",
        "name": "伊薇特·蓝蓟",
        "gender": "女",
        "role_type": "草药师密使",
        "world": "灰堡王国",
        "identity": "宫廷草药师行会成员，表面替贵族调配药剂，暗中为王室递送密信。",
        "background": "在修道院长大，熟悉草药、毒理和教会档案。她知道许多贵族病症背后的政治秘密。",
        "personality": "温和、聪明、善于倾听，关键时刻极其果断。",
        "goal": "找到能证明摄政议会伪造审判文书的证据。",
        "motivation": "她的导师因拒绝篡改诊断记录被处死，她想让真相重见天日。",
        "secret": "她能辨认旧王朝遗物留下的特殊银锈。",
        "conflict_points": "常被低估为普通草药师，也因此能接近危险人物。",
        "relationship_notes": "与莱昂共享同一桩旧案线索，但起初互不信任。",
        "speech_style": "礼貌、含蓄，常用草药和病症作比喻。",
        "catchphrases": "毒药和真话，都要看剂量。",
        "emotional_arc": "从谨慎旁观者成长为主动揭露真相的人。",
        "story_function": "情报线主角、医学与档案知识提供者。",
        "visual_description": "二十五六岁，红褐色长辫，深蓝羊毛外袍，皮革草药包，气质沉静敏锐。",
        "image_keywords": "medieval herbalist, auburn braid, dark blue gown, leather satchel, court intrigue",
        "filename": "europe-medieval-female-herbalist.png",
    },
    {
        "id": "mock-char-honghuang-spirit-m",
        "name": "青岚",
        "gender": "男",
        "role_type": "山灵散仙",
        "world": "云梦洪荒闲游记",
        "identity": "青岚山化形的年轻山灵，常在云梦集市帮人修伞、找猫、调停小纠纷。",
        "background": "原本守着一座无人古山，因欠下天道账被迫下山做一百件小善事。",
        "personality": "散漫、乐观、嘴上不靠谱，实际很护短。",
        "goal": "还清天道账，顺便弄明白人间为什么总把小事过成大事。",
        "motivation": "他不想再做孤零零的山，也想知道被人惦记是什么感觉。",
        "secret": "情绪波动时，附近植物会不受控制地疯长。",
        "conflict_points": "怕麻烦却总被卷入麻烦；不懂人情账比天道账更难还。",
        "relationship_notes": "经常赖在桃夭的客栈，欠了不少茶钱。",
        "speech_style": "轻快、调侃，爱把大道理说成市井闲话。",
        "catchphrases": "小事小事，天塌下来也先喝茶。",
        "emotional_arc": "从旁观人间，到愿意为别人承担因果。",
        "story_function": "轻喜剧男主、法术解决问题与制造问题的来源。",
        "visual_description": "二十岁出头外貌，黑色长发松束，青灰与白色休闲汉服，腰间挂葫芦，气质清爽松弛。",
        "image_keywords": "Chinese primordial casual fantasy, mountain spirit, celadon robe, gourd flask, relaxed cultivator",
        "filename": "honghuang-casual-male-spirit.png",
    },
    {
        "id": "mock-char-honghuang-innkeeper-f",
        "name": "桃夭",
        "gender": "女",
        "role_type": "桃花客栈掌柜",
        "world": "云梦洪荒闲游记",
        "identity": "桃花渡客栈掌柜，也是半个云梦集消息中心。",
        "background": "由千年桃树灵化形，见过许多仙妖来去，却选择在人间开客栈收留无处可去的人。",
        "personality": "明快、精明、心软，算账很准但经常赊账给可怜人。",
        "goal": "守住桃花渡客栈，让人、妖、灵都能有一个安全落脚处。",
        "motivation": "她相信热饭和床铺能解决大多数怨气。",
        "secret": "客栈后院的老桃树连着一段废弃天梯。",
        "conflict_points": "想过安生日子，却总因客栈秘密被各路势力盯上。",
        "relationship_notes": "嘴上嫌弃青岚欠账，实际会替他留最好的茶。",
        "speech_style": "爽利、俏皮，夹杂掌柜式算账口吻。",
        "catchphrases": "先把账结了，再谈天命。",
        "emotional_arc": "从守着小客栈，到敢于保护更大的云梦集。",
        "story_function": "日常据点核心、女主、信息与情感连接者。",
        "visual_description": "二十岁出头外貌，黑色长发配桃花发饰，桃色与青绿色休闲汉服，笑容明亮。",
        "image_keywords": "Chinese fantasy innkeeper, peach blossom spirit, peach hanfu, lively warm expression, casual myth",
        "filename": "honghuang-casual-female-innkeeper.png",
    },
    {
        "id": "mock-char-modern-doctor-m",
        "name": "沈砚",
        "gender": "男",
        "role_type": "急诊医生",
        "world": "镜城二十四小时",
        "identity": "镜城中心医院急诊医生，以冷静和判断快出名。",
        "background": "曾在一次公共事故中被网暴误解，之后对媒体和镜头保持距离。",
        "personality": "理性、克制、责任感强，容易把所有压力自己扛。",
        "goal": "在复杂舆论和医院制度中保护患者，也保护一线医生的尊严。",
        "motivation": "他相信生命优先于立场，但现实总逼他做不完美选择。",
        "secret": "当年的事故里，他替一位同事隐瞒了足以毁掉职业生涯的失误。",
        "conflict_points": "面对媒体时防御心很强；不擅长向亲近的人求助。",
        "relationship_notes": "与林望舒因一场急诊视频误会相识，之后共同追查真相。",
        "speech_style": "简洁、专业，情绪越紧张越冷静。",
        "catchphrases": "先救人，其他事之后再说。",
        "emotional_arc": "从封闭自保，到愿意公开面对伤口和真相。",
        "story_function": "医疗线男主、现实伦理冲突承载者。",
        "visual_description": "三十岁出头，黑色短发，白衬衫配深色夹克，胸前医院工牌，气质冷静专业。",
        "image_keywords": "modern urban doctor, East Asian male, charcoal bomber jacket, hospital ID, realistic wardrobe",
        "filename": "modern-urban-male-doctor.png",
    },
    {
        "id": "mock-char-modern-journalist-f",
        "name": "林望舒",
        "gender": "女",
        "role_type": "调查记者",
        "world": "镜城二十四小时",
        "identity": "前传统媒体记者，现经营城市调查类播客和短视频账号。",
        "background": "因拒绝删除一篇旧街拆迁调查报道离职，转做独立内容后更接近一线普通人。",
        "personality": "敏锐、执拗、有同理心，不轻易相信单一证词。",
        "goal": "用完整证据还原公共事件真相，而不是追逐流量反转。",
        "motivation": "她见过太多人被片段舆论吞没，想给沉默者一个说清楚的机会。",
        "secret": "她父亲与星河资本的旧街项目有隐秘关系。",
        "conflict_points": "理想主义和平台流量规则冲突；调查越深入越牵扯家人。",
        "relationship_notes": "最初误判沈砚，后来成为彼此最可靠的事实校验者。",
        "speech_style": "追问式、逻辑清楚，采访时温和但不退让。",
        "catchphrases": "别急着站队，先把时间线摆出来。",
        "emotional_arc": "从只相信证据，到理解真相也需要被人承受。",
        "story_function": "媒体线女主、调查推进者、都市公共议题连接者。",
        "visual_description": "二十七八岁，齐肩黑发，米色风衣、黑色高领、牛仔裤和帆布斜挎包，观察感强。",
        "image_keywords": "modern investigative journalist, East Asian female, beige trench coat, canvas bag, realistic urban style",
        "filename": "modern-urban-female-journalist.png",
    },
]


def upsert_world(session, payload: dict) -> None:
    timestamp = now()
    world = session.get(WorldBook, payload["id"])
    if not world:
        world = WorldBook(id=payload["id"], created_at=timestamp, updated_at=timestamp)
        session.add(world)

    for field in [
        "name",
        "genre",
        "era_background",
        "world_rules",
        "organizations",
        "locations",
        "social_structure",
        "taboo_or_constraints",
        "tone_style",
        "summary",
    ]:
        setattr(world, field, payload[field])
    world.status = "active"
    world.version = max(world.version or 1, 1)
    world.updated_at = timestamp

    for entry_payload in payload["entries"]:
        entry = session.get(WorldEntry, entry_payload["id"])
        if not entry:
            entry = WorldEntry(id=entry_payload["id"], world_book_id=world.id, created_at=timestamp, updated_at=timestamp)
            session.add(entry)
        entry.world_book_id = world.id
        entry.title = entry_payload["title"]
        entry.entry_type = entry_payload["entry_type"]
        entry.keywords = entry_payload["keywords"]
        entry.content = entry_payload["content"]
        entry.applicable_scope = entry_payload["applicable_scope"]
        entry.priority = entry_payload["priority"]
        entry.status = "active"
        entry.updated_at = timestamp


def upsert_character(session, payload: dict) -> None:
    timestamp = now()
    card = session.get(CharacterCard, payload["id"])
    if not card:
        card = CharacterCard(id=payload["id"], created_at=timestamp, updated_at=timestamp)
        session.add(card)

    filename = payload["filename"]
    prompt = (
        "请生成同一角色的人物三视图，画面包含正面、侧面、背面，全身，统一服装，干净背景。\n"
        f"角色名：{payload['name']}\n"
        f"性别：{payload['gender']}\n"
        f"所属世界观：{payload['world']}\n"
        f"身份摘要：{payload['identity']}\n"
        f"视觉描述：{payload['visual_description']}\n"
        f"形象关键词：{payload['image_keywords']}"
    )

    for field in [
        "name",
        "gender",
        "role_type",
        "identity",
        "background",
        "personality",
        "goal",
        "motivation",
        "secret",
        "conflict_points",
        "relationship_notes",
        "speech_style",
        "catchphrases",
        "emotional_arc",
        "story_function",
        "visual_description",
        "image_keywords",
    ]:
        setattr(card, field, payload[field])

    card.reference_image_url = asset_url(filename)
    card.reference_local_path = local_path(filename)
    card.turnaround_prompt = prompt
    card.turnaround_image_url = asset_url(filename)
    card.turnaround_local_path = local_path(filename)
    card.turnaround_generation_prompt = prompt
    card.turnaround_status = "confirmed"
    card.turnaround_version = max(card.turnaround_version or 0, 1)
    card.turnaround_confirmed_at = timestamp
    card.version = max(card.version or 1, 1)
    card.status = "active"
    card.updated_at = timestamp


def main() -> None:
    missing_assets = [payload["filename"] for payload in CHARACTERS if not (TURNAROUND_DIR / payload["filename"]).exists()]
    if missing_assets:
        raise SystemExit(f"缺少三视图图片文件：{', '.join(missing_assets)}")

    with get_session() as session:
        for world in WORLD_BOOKS:
            upsert_world(session, world)
        for character in CHARACTERS:
            upsert_character(session, character)

    print(f"Seeded {len(WORLD_BOOKS)} mock world books and {len(CHARACTERS)} mock character cards.")


if __name__ == "__main__":
    main()
